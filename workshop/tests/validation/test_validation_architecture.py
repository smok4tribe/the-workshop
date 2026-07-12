#!/usr/bin/env python3
"""Regression tests for validation failures found by the Sprint 1 audit."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class ValidationArchitectureRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="workshop-validation-")
        self.repo = Path(self.temp_dir.name)
        shutil.copytree(REPO_ROOT / "workshop", self.repo / "workshop")
        self.project = self.repo / "workshop" / "projects" / "the-myr-singularity"
        self.validation = self.repo / "workshop" / "tests" / "validation"

    def tearDown(self):
        self.temp_dir.cleanup()

    def load_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, path, value):
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_validator(self, name, env=None):
        process_env = os.environ.copy()
        if env:
            process_env.update({key: str(value) for key, value in env.items()})
        return subprocess.run(
            [sys.executable, str(self.validation / name)],
            cwd=self.repo,
            env=process_env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def assert_validation_fails(self, result, expected_text):
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn(expected_text, output)

    def test_current_deck_divergence_fails(self):
        current = self.project / "deck" / "current.txt"
        text = current.read_text(encoding="utf-8")
        current.write_text(
            text.replace("1 City of Brass", "1 Krark-Clan Ironworks"),
            encoding="utf-8",
        )

        result = self.run_validator("validate_deck_versions.py")

        self.assert_validation_fails(
            result,
            "current deck main_deck differs from resolved DeckVersion",
        )

    def test_main_deck_quantity_corruption_fails(self):
        version_path = self.project / "versions" / "v1.1.json"
        version = self.load_json(version_path)
        version["main_deck"][0]["quantity"] = 2
        self.write_json(version_path, version)

        result = self.run_validator("validate_deck_versions.py")

        self.assert_validation_fails(result, "main-deck quantity total is 100, expected 99")

    def test_sideboard_replacement_fails_even_when_current_matches(self):
        version_path = self.project / "versions" / "v1.1.json"
        version = self.load_json(version_path)
        version["sideboard"][0]["name"] = "Mana Echoes"
        self.write_json(version_path, version)

        current = self.project / "deck" / "current.txt"
        text = current.read_text(encoding="utf-8")
        current.write_text(text.replace("1 Aetherize", "1 Mana Echoes"), encoding="utf-8")

        result = self.run_validator("validate_deck_versions.py")

        self.assert_validation_fails(
            result,
            "sideboard differs from parent despite no approved sideboard change",
        )

    def test_needs_testing_candidate_in_design_fails(self):
        decisions_dir = self.project / "decisions"
        decision = self.load_json(decisions_dir / "decision-004.json")
        decision.update(
            {
                "decision_id": "decision-005",
                "source_candidate_id": "cand-010",
                "candidate_status_at_review": "needs_testing",
                "incoming_cards": ["Mana Echoes"],
                "outgoing_cards": [],
            }
        )
        self.write_json(decisions_dir / "decision-005.json", decision)

        design_path = decisions_dir / "deck-change-design-v1.1.json"
        design = self.load_json(design_path)
        design["source_decision_ids"].append("decision-005")
        design["incoming_cards"].append(
            {
                "name": "Mana Echoes",
                "reference": "candidate:scryfall:bd079929-fa58-4484-91b7-31305b87ee43",
                "source_decision_id": "decision-005",
                "slot": "nonland",
            }
        )
        self.write_json(design_path, design)

        result = self.run_validator("validate_decision_pipeline.py")

        self.assert_validation_fails(
            result,
            "decision-005 references 'cand-010' with unapproved review status 'needs_testing'",
        )

    def test_historical_candidate_reference_survives_canonical_promotion(self):
        cards_path = self.repo / "workshop" / "card-data" / "cards.json"
        candidate_path = self.repo / "workshop" / "card-data" / "candidate_cards.json"
        cards = self.load_json(cards_path)
        candidates = self.load_json(candidate_path)
        promoted = next(
            card for card in candidates["candidate_cards"] if card["name"] == "Mana Echoes"
        )
        candidates["candidate_cards"] = [
            card for card in candidates["candidate_cards"] if card["name"] != "Mana Echoes"
        ]
        cards["cards"].append(promoted)
        self.write_json(cards_path, cards)
        self.write_json(candidate_path, candidates)

        recommendation_result = self.run_validator(
            "validate_recommendation_schema.py",
            {
                "WORKSHOP_RECOMMENDATION_JSON": self.project
                / "recommendations"
                / "rec-002.json",
                "WORKSHOP_RECOMMENDATION_MD": self.project
                / "recommendations"
                / "rec-002.md",
            },
        )
        review_result = self.run_validator("validate_recommendation_review.py")

        recommendation_output = recommendation_result.stdout + recommendation_result.stderr
        self.assertEqual(recommendation_result.returncode, 0, recommendation_output)
        self.assertIn(
            "PASS: all 21 recommendation schema validation checks passed.",
            recommendation_output,
        )
        review_output = review_result.stdout + review_result.stderr
        self.assertEqual(review_result.returncode, 0, review_output)
        self.assertIn("PASS: all 15 recommendation review validation checks passed.", review_output)

    def test_canonical_only_id_cannot_masquerade_as_candidate(self):
        cards = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        academy_ruins = next(card for card in cards["cards"] if card["name"] == "Academy Ruins")
        recommendation_path = self.project / "recommendations" / "rec-002.json"
        recommendation = self.load_json(recommendation_path)
        city_of_brass_id = "c21565d0-fc40-4d89-9b27-87c03385e0af"
        academy_ruins_id = academy_ruins["scryfall_id"]

        def replace_reference(value):
            if isinstance(value, dict):
                return {key: replace_reference(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace_reference(item) for item in value]
            if value == f"candidate:scryfall:{city_of_brass_id}":
                return f"candidate:scryfall:{academy_ruins_id}"
            return value

        self.write_json(recommendation_path, replace_reference(recommendation))

        result = self.run_validator(
            "validate_recommendation_schema.py",
            {
                "WORKSHOP_RECOMMENDATION_JSON": recommendation_path,
                "WORKSHOP_RECOMMENDATION_MD": self.project / "recommendations" / "rec-002.md",
            },
        )

        self.assert_validation_fails(result, "candidate reference has no candidate intake provenance")

    def test_approved_sideboard_replacement_passes(self):
        decisions_dir = self.project / "decisions"
        design_path = decisions_dir / "deck-change-design-v1.1.json"
        version_path = self.project / "versions" / "v1.1.json"
        design = self.load_json(design_path)
        version = self.load_json(version_path)
        decision = self.load_json(decisions_dir / "decision-004.json")
        review_path = self.project / "recommendations" / "review-rec-002.json"
        review = self.load_json(review_path)

        decision.update(
            {
                "decision_id": "decision-005",
                "source_candidate_id": "cand-010",
                "incoming_cards": ["Mana Echoes"],
                "outgoing_cards": ["Aetherize"],
            }
        )
        self.write_json(decisions_dir / "decision-005.json", decision)

        for entry in review["review_entries"]:
            if entry["candidate_id"] == "cand-010":
                entry["review_status"] = "accepted_for_decision"
        self.write_json(review_path, review)

        design["source_decision_ids"].append("decision-005")
        design["incoming_cards"].append(
            {
                "name": "Mana Echoes",
                "reference": "candidate:scryfall:bd079929-fa58-4484-91b7-31305b87ee43",
                "source_decision_id": "decision-005",
                "slot": "sideboard",
            }
        )
        design["proposed_outgoing_cards"].append(
            {
                "name": "Aetherize",
                "reference": "deck:scryfall:sideboard-aetherize-fixture",
                "slot": "sideboard",
            }
        )
        self.write_json(design_path, design)

        version["source_decision_ids"].append("decision-005")
        version["sideboard"][0]["name"] = "Mana Echoes"
        changes = version["changes_from_v1.0"]
        changes["added"].append({"name": "Mana Echoes", "source_decision_id": "decision-005"})
        changes["removed"].append({"name": "Aetherize", "source_decision_id": "decision-005"})
        self.write_json(version_path, version)

        current = self.project / "deck" / "current.txt"
        current.write_text(
            current.read_text(encoding="utf-8").replace("1 Aetherize", "1 Mana Echoes"),
            encoding="utf-8",
        )

        pipeline_result = self.run_validator("validate_decision_pipeline.py")
        pipeline_output = pipeline_result.stdout + pipeline_result.stderr
        self.assertEqual(pipeline_result.returncode, 0, pipeline_output)

        result = self.run_validator("validate_deck_versions.py")

        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("PASS: all 14 DeckVersion validation checks passed.", output)

    def test_unapproved_sideboard_quantity_change_fails(self):
        version_path = self.project / "versions" / "v1.1.json"
        version = self.load_json(version_path)
        version["sideboard"][0]["quantity"] = 2
        self.write_json(version_path, version)

        current = self.project / "deck" / "current.txt"
        current.write_text(
            current.read_text(encoding="utf-8").replace("1 Aetherize", "2 Aetherize"),
            encoding="utf-8",
        )

        result = self.run_validator("validate_deck_versions.py")

        self.assert_validation_fails(result, "sideboard quantity total is 8, expected 7")

    def test_v1_1_promotions_are_canonical_assigned_and_historically_resolvable(self):
        expected_ids = {
            "City of Brass": "c21565d0-fc40-4d89-9b27-87c03385e0af",
            "Mana Confluence": "504a69eb-3c2d-4bb1-b117-252b15acf0c2",
            "Urza's Saga": "c1e0f201-42cb-46a1-901a-65bb4fc18f6c",
            "Tezzeret the Seeker": "cf339735-eb1a-46f0-8c3e-eae06f278eca",
        }
        cards = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        candidates = self.load_json(self.repo / "workshop" / "card-data" / "candidate_cards.json")
        metadata = self.load_json(
            self.repo / "workshop" / "card-data" / "candidate_card_import_metadata.json"
        )
        assignments = self.load_json(
            self.repo / "workshop" / "knowledge" / "functional_roles.json"
        )

        canonical_by_name = {card["name"]: card["scryfall_id"] for card in cards["cards"]}
        self.assertEqual(
            {name: canonical_by_name.get(name) for name in expected_ids}, expected_ids
        )
        active_names = {card["name"] for card in candidates["candidate_cards"]}
        self.assertEqual(active_names, {"Krark-Clan Ironworks", "Mana Echoes"})
        self.assertTrue(active_names.isdisjoint(expected_ids))
        promoted_by_id = {
            record["scryfall_id"]: record["card_name"]
            for record in metadata["promoted_candidate_records"]
        }
        self.assertEqual(promoted_by_id, {scryfall_id: name for name, scryfall_id in expected_ids.items()})

        assignment_ids = [entry["card_source_ref"]["id"] for entry in assignments["assignments"]]
        for scryfall_id in expected_ids.values():
            self.assertEqual(assignment_ids.count(scryfall_id), 1)

        recommendation_result = self.run_validator(
            "validate_recommendation_schema.py",
            {
                "WORKSHOP_RECOMMENDATION_JSON": self.project
                / "recommendations"
                / "rec-002.json",
                "WORKSHOP_RECOMMENDATION_MD": self.project / "recommendations" / "rec-002.md",
            },
        )
        review_result = self.run_validator("validate_recommendation_review.py")
        self.assertEqual(recommendation_result.returncode, 0, recommendation_result.stdout)
        self.assertEqual(review_result.returncode, 0, review_result.stdout)

    def test_missing_promoted_canonical_fact_fails(self):
        cards_path = self.repo / "workshop" / "card-data" / "cards.json"
        cards = self.load_json(cards_path)
        cards["cards"] = [card for card in cards["cards"] if card["name"] != "City of Brass"]
        self.write_json(cards_path, cards)

        result = self.run_validator("validate_candidate_card_facts.py")

        self.assert_validation_fails(result, "promoted candidate IDs are missing from cards.json")

    def test_conflicting_promoted_candidate_facts_fail(self):
        cards = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        candidates_path = self.repo / "workshop" / "card-data" / "candidate_cards.json"
        candidates = self.load_json(candidates_path)
        duplicate = next(card for card in cards["cards"] if card["name"] == "City of Brass")
        duplicate["candidate_card_id"] = "candidate-card-conflict"
        duplicate["recommendation_status"] = "facts_only"
        duplicate["oracle_text"] = "Conflicting fixture facts."
        candidates["candidate_cards"].append(duplicate)
        self.write_json(candidates_path, candidates)

        result = self.run_validator(
            "validate_recommendation_schema.py",
            {
                "WORKSHOP_RECOMMENDATION_JSON": self.project
                / "recommendations"
                / "rec-002.json",
                "WORKSHOP_RECOMMENDATION_MD": self.project / "recommendations" / "rec-002.md",
            },
        )

        self.assert_validation_fails(result, "conflicting canonical and candidate facts")

    def test_promoted_name_to_id_mismatch_fails(self):
        metadata_path = self.repo / "workshop" / "card-data" / "candidate_card_import_metadata.json"
        metadata = self.load_json(metadata_path)
        records = metadata["promoted_candidate_records"]
        records[0]["card_name"], records[1]["card_name"] = (
            records[1]["card_name"],
            records[0]["card_name"],
        )
        self.write_json(metadata_path, metadata)

        result = self.run_validator("validate_candidate_card_facts.py")

        self.assert_validation_fails(
            result,
            "promoted candidate metadata name does not match canonical Card Facts",
        )

    def test_canonical_promotion_metadata_mismatch_fails(self):
        metadata_path = self.repo / "workshop" / "card-data" / "card_import_metadata.json"
        metadata = self.load_json(metadata_path)
        metadata["promoted_candidate_records"][0].update(
            {
                "scryfall_id": "a95b7645-154f-4904-bf71-db7eb24d4df2",
                "card_name": "Academy Ruins",
            }
        )
        self.write_json(metadata_path, metadata)

        result = self.run_validator("validate_knowledge_layer.py")

        self.assert_validation_fails(
            result,
            "canonical promotion metadata does not match candidate lifecycle metadata",
        )

    def test_duplicate_promoted_id_fails(self):
        metadata_path = self.repo / "workshop" / "card-data" / "candidate_card_import_metadata.json"
        metadata = self.load_json(metadata_path)
        metadata["promoted_candidate_records"].append(
            dict(metadata["promoted_candidate_records"][0])
        )
        metadata["promoted_candidate_card_count"] = 5
        self.write_json(metadata_path, metadata)

        result = self.run_validator("validate_candidate_card_facts.py")

        self.assert_validation_fails(result, "duplicate promoted Scryfall ID")

    def test_project_report_positive_validation_passes(self):
        result = self.run_validator("validate_project_reports.py")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_report_invalid_resulting_version_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["resulting_deck_version_id"] = "v9.9"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(result, "resulting DeckVersion 'v9.9' does not resolve")

    def test_report_incorrect_delta_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["version_delta"]["added"].pop()
        self.write_json(report_path, report)
        self.regenerate_report(report_path)

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(
            result,
            "report version delta does not match the derived parent-child DeckVersion diff",
        )

    def test_report_measured_outcome_claim_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["evidence_status"]["performance_claim"]["status"] = "measured"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(
            result,
            "measured evidence 'performance_claim' requires a structured source",
        )

    def test_report_candidate_disposition_mismatch_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        item = next(
            entry
            for entry in report["candidate_dispositions"]
            if entry["candidate_id"] == "cand-009"
        )
        item["implementation_status"] = "implemented"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(
            result,
            "candidate disposition for 'cand-009' does not match derived implementation state",
        )

    def test_report_markdown_drift_fails(self):
        markdown_path = self.project / "reports" / "project_report_v1.1.md"
        markdown_path.write_text(
            markdown_path.read_text(encoding="utf-8") + "\nManual drift.\n",
            encoding="utf-8",
        )

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(
            result,
            "committed Markdown differs from deterministic renderer output",
        )

    def regenerate_report(self, report_path):
        renderer = self.repo / "workshop" / "scripts" / "render_project_report.py"
        result = subprocess.run(
            [sys.executable, str(renderer), str(report_path)],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def renderer_module(self):
        renderer = self.repo / "workshop" / "scripts" / "render_project_report.py"
        spec = importlib.util.spec_from_file_location("report_renderer_test", renderer)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_report_missing_source_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["source_references"]["baseline_analysis"]["path"] = "missing.json"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)

        result = self.run_validator("validate_project_reports.py")

        self.assert_validation_fails(result, "source 'baseline_analysis' does not exist")

    def test_report_current_deck_divergence_fails(self):
        current = self.project / "deck" / "current.txt"
        current.write_text(
            current.read_text(encoding="utf-8").replace("1 City of Brass", "1 Academy Ruins"),
            encoding="utf-8",
        )
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "current deck main_deck differs from report resulting DeckVersion")

    def test_report_wrong_decision_attribution_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["version_delta"]["added"][0]["source_decision_id"] = "decision-003"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "has wrong decision attribution")

    def test_report_decision_summary_drift_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["decision_summary"][0]["incoming_cards"][0] = "Academy Ruins"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "decision summary for 'decision-002' does not match source decision")

    def test_report_existing_wrong_source_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["source_references"]["brief"]["path"] = (
            "workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json"
        )
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "brief source identity does not match project")

    def test_report_false_knowledge_alignment_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["knowledge_alignment"]["implemented_cards_in_canonical_facts"].append("Academy Ruins")
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "implemented-card Knowledge set does not match derived additions")

    def test_report_missing_knowledge_alignment_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["knowledge_alignment"]["implemented_cards_in_canonical_facts"].pop()
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "implemented-card Knowledge set does not match derived additions")

    def test_report_false_provenance_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        report = self.load_json(report_path)
        report["knowledge_alignment"]["historical_candidate_provenance"] = "unresolvable"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assert_validation_fails(result, "historical candidate provenance claim does not match lifecycle state")

    def test_report_candidate_ids_are_relationship_driven(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        recommendation_path = self.project / "recommendations" / "rec-002.json"
        review_path = self.project / "recommendations" / "review-rec-002.json"
        decision_path = self.project / "decisions" / "decision-002.json"
        recommendation = self.load_json(recommendation_path)
        review = self.load_json(review_path)
        decision = self.load_json(decision_path)
        report = self.load_json(report_path)
        for candidate in recommendation["candidates"]:
            if candidate["candidate_id"] == "cand-007":
                candidate["candidate_id"] = "cand-107"
        for entry in review["review_entries"]:
            if entry["candidate_id"] == "cand-007":
                entry["candidate_id"] = "cand-107"
        decision["source_candidate_id"] = "cand-107"
        for entry in report["candidate_dispositions"]:
            if entry["candidate_id"] == "cand-007":
                entry["candidate_id"] = "cand-107"
        for entry in report["decision_summary"]:
            if entry["decision_id"] == "decision-002":
                entry["candidate_id"] = "cand-107"
        self.write_json(recommendation_path, recommendation)
        self.write_json(review_path, review)
        self.write_json(decision_path, decision)
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_renderer_uses_dynamic_version_labels(self):
        report = self.load_json(self.project / "reports" / "project_report_v1.1.json")
        report["report_version"] = "v9.3"
        report["baseline_deck_version_id"] = "v8.1"
        report["resulting_deck_version_id"] = "v9.3"
        rendered = self.renderer_module().render_report(report)
        self.assertIn("## Baseline v8.1", rendered)
        self.assertIn("## Implemented DeckVersion v9.3", rendered)
        self.assertNotIn("## Baseline v1.0", rendered)

    def test_renderer_uses_dynamic_delta_counts(self):
        report = self.load_json(self.project / "reports" / "project_report_v1.1.json")
        report["version_delta"]["added"] = report["version_delta"]["added"][:2]
        report["version_delta"]["removed"] = report["version_delta"]["removed"][:1]
        rendered = self.renderer_module().render_report(report)
        self.assertIn("The report records 2 additions and 1 removals.", rendered)
        self.assertNotIn("four-card", rendered)

    def test_renderer_uses_dynamic_candidate_dispositions(self):
        report = self.load_json(self.project / "reports" / "project_report_v1.1.json")
        report["candidate_dispositions"] = [{
            "candidate_id": "cand-example", "candidate_name": "Example Candidate",
            "review_status": "deferred", "implementation_status": "not_implemented",
            "source_decision_ids": [],
        }]
        rendered = self.renderer_module().render_report(report)
        self.assertIn("Example Candidate: deferred; not_implemented.", rendered)
        self.assertNotIn("Krark-Clan Ironworks: needs_testing", rendered)

    def test_report_measured_evidence_with_valid_source_passes(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        evidence_path = self.project / "analysis" / "fixture-performance-evidence.json"
        report = self.load_json(report_path)
        self.write_json(evidence_path, {
            "artifact_type": "post_implementation_evidence",
            "evidence_kind": "performance_measurement",
            "project_id": "the-myr-singularity",
            "deck_version_id": "v1.1",
        })
        report["evidence_status"]["performance_claim"] = {
            "status": "measured",
            "sources": [{"path": "workshop/projects/the-myr-singularity/analysis/fixture-performance-evidence.json"}],
        }
        report["report_status"] = "implementation_verified_outcomes_measured"
        self.write_json(report_path, report)
        self.regenerate_report(report_path)
        result = self.run_validator("validate_project_reports.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_report_referenced_card_facts_missing_implemented_card_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        alternate = self.repo / "workshop" / "card-data" / "alternate_cards.json"
        cards = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        cards["cards"] = [card for card in cards["cards"] if card["name"] != "Tezzeret the Seeker"]
        self.write_json(alternate, cards)
        report = self.load_json(report_path)
        report["source_references"]["card_facts"]["path"] = "workshop/card-data/alternate_cards.json"
        self.write_json(report_path, report); self.regenerate_report(report_path)
        self.assert_validation_fails(self.run_validator("validate_project_reports.py"), "implemented card 'tezzeret the seeker' lacks canonical facts")

    def test_report_referenced_card_facts_wrong_identity_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        alternate = self.repo / "workshop" / "card-data" / "alternate_cards.json"
        cards = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        next(card for card in cards["cards"] if card["name"] == "Tezzeret the Seeker")["scryfall_id"] = "00000000-0000-0000-0000-000000000000"
        self.write_json(alternate, cards)
        report = self.load_json(report_path)
        report["source_references"]["card_facts"]["path"] = "workshop/card-data/alternate_cards.json"
        self.write_json(report_path, report); self.regenerate_report(report_path)
        self.assert_validation_fails(self.run_validator("validate_project_reports.py"), "has wrong referenced Card Facts identity")

    def test_report_active_candidate_source_missing_needs_testing_card_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        alternate = self.repo / "workshop" / "card-data" / "alternate_candidates.json"
        cards = self.load_json(self.repo / "workshop" / "card-data" / "candidate_cards.json")
        cards["candidate_cards"] = cards["candidate_cards"][:1]
        self.write_json(alternate, cards)
        report = self.load_json(report_path)
        report["source_references"]["active_candidate_facts"]["path"] = "workshop/card-data/alternate_candidates.json"
        self.write_json(report_path, report); self.regenerate_report(report_path)
        self.assert_validation_fails(self.run_validator("validate_project_reports.py"), "needs-testing candidate 'cand-010' is not an active candidate fact")

    def test_report_active_candidate_source_promoted_overlap_fails(self):
        report_path = self.project / "reports" / "project_report_v1.1.json"
        alternate = self.repo / "workshop" / "card-data" / "alternate_candidates.json"
        active = self.load_json(self.repo / "workshop" / "card-data" / "candidate_cards.json")
        canonical = self.load_json(self.repo / "workshop" / "card-data" / "cards.json")
        active["candidate_cards"].append(next(card for card in canonical["cards"] if card["name"] == "City of Brass"))
        self.write_json(alternate, active)
        report = self.load_json(report_path)
        report["source_references"]["active_candidate_facts"]["path"] = "workshop/card-data/alternate_candidates.json"
        self.write_json(report_path, report); self.regenerate_report(report_path)
        self.assert_validation_fails(self.run_validator("validate_project_reports.py"), "active candidate facts overlap promoted lifecycle records")

    def test_report_implementation_summary_claims_fail(self):
        cases = [
            ("design_id", "wrong-design", "implementation summary design_id does not match approved design"),
            ("product_owner_approved", False, "implementation summary approval state does not match design"),
            ("approval_by", "Invented", "implementation summary approver does not match design"),
            ("parent_version_id", "v9.9", "implementation summary parent version does not match resulting DeckVersion"),
            ("resulting_version_id", "v9.9", "implementation summary resulting version does not match sources"),
            ("current_decklist_matches_resulting_version", False, "implementation summary current-deck alignment does not match exact parsed deck content"),
        ]
        for field, value, expected in cases:
            with self.subTest(field=field):
                report_path = self.project / "reports" / "project_report_v1.1.json"
                report = self.load_json(report_path)
                report["implementation_summary"][field] = value
                self.write_json(report_path, report); self.regenerate_report(report_path)
                self.assert_validation_fails(self.run_validator("validate_project_reports.py"), expected)
                self.tearDown(); self.setUp()

    def test_report_project_brief_baseline_claims_fail(self):
        cases = [
            (lambda report: report["project_identity"].update({"commander": "Wrong"}), "report project commander does not match project metadata"),
            (lambda report: report["project_identity"].update({"format": "Legacy"}), "report project format does not match project metadata"),
            (lambda report: report["project_identity"].update({"name": "Wrong"}), "report project name does not match project metadata"),
            (lambda report: report["brief_summary"].update({"goals": ["Wrong"]}), "report brief goals do not match authoritative project goals"),
            (lambda report: report["baseline_summary"].update({"analysis_id": "wrong"}), "report baseline analysis ID does not match source analysis"),
            (lambda report: report["baseline_summary"].update({"deck_version_id": "wrong"}), "report baseline DeckVersion summary does not match source analysis"),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                report_path = self.project / "reports" / "project_report_v1.1.json"
                report = self.load_json(report_path)
                mutate(report)
                self.write_json(report_path, report); self.regenerate_report(report_path)
                self.assert_validation_fails(self.run_validator("validate_project_reports.py"), expected)
                self.tearDown(); self.setUp()

    def test_report_decision_rationale_is_source_derived(self):
        for value in ("Wrong rationale", "Tournament wins prove this change."):
            with self.subTest(value=value):
                report_path = self.project / "reports" / "project_report_v1.1.json"
                report = self.load_json(report_path)
                report["decision_summary"][0]["source_rationale"] = value
                self.write_json(report_path, report); self.regenerate_report(report_path)
                self.assert_validation_fails(self.run_validator("validate_project_reports.py"), "decision summary for 'decision-002' does not match source decision")
                self.tearDown(); self.setUp()

    def test_report_contradictory_implementation_status_fails(self):
        cases = [
            ("implementation_not_verified", "verified"),
            ("implementation_verified", "not_verified"),
        ]
        for validation_status, implementation_result in cases:
            with self.subTest(
                validation_status=validation_status,
                implementation_result=implementation_result,
            ):
                report_path = self.project / "reports" / "project_report_v1.1.json"
                report = self.load_json(report_path)
                report["implementation_summary"]["validation_status"] = validation_status
                report["evidence_status"]["implementation_result"] = implementation_result
                self.write_json(report_path, report)
                self.regenerate_report(report_path)

                result = self.run_validator("validate_project_reports.py")

                self.assert_validation_fails(
                    result,
                    "implementation summary validation_status does not agree with evidence implementation_result",
                )
                self.tearDown(); self.setUp()

    def test_sprint_certification_candidate_and_mutations(self):
        certification = self.project / "reports" / "sprint_1_certification.json"
        backlog = self.project / "notes" / "backlog.json"
        renderer = self.repo / "workshop" / "scripts" / "render_sprint_1_closure.py"

        def render():
            result = subprocess.run([sys.executable, str(renderer)], cwd=self.repo, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())

        def validate(expected=None):
            result = self.run_validator("validate_sprint_1_certification.py")
            if expected:
                self.assert_validation_fails(result, expected)
            else:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        validate()
        cases = [
            ("missing source", lambda c,b: c["source_references"]["project"].update({"path":"missing.json"}), "source 'project' does not resolve"),
            ("wrong current", lambda c,b: c.update({"project_id":"wrong"}), "certification identity or scope is invalid"),
            ("empty backlog", lambda c,b: b.update({"items":[]}), "required deferred backlog items are not captured"),
            ("missing KCI", lambda c,b: b.update({"items":[x for x in b["items"] if x["backlog_id"]!="backlog-003"]}), "required deferred backlog items are not captured"),
            ("missing Mana", lambda c,b: b.update({"items":[x for x in b["items"] if x["backlog_id"]!="backlog-004"]}), "required deferred backlog items are not captured"),
            ("premature certified", lambda c,b: c.update({"certification_status":"certified"}), "completed certification requires approving independent review"),
        ]
        for _, mutate, expected in cases:
            with self.subTest(expected=expected):
                c,b=self.load_json(certification),self.load_json(backlog); mutate(c,b); self.write_json(certification,c); self.write_json(backlog,b); render(); validate(expected); self.tearDown(); self.setUp(); certification=self.project/'reports'/'sprint_1_certification.json'; backlog=self.project/'notes'/'backlog.json'; renderer=self.repo/'workshop'/'scripts'/'render_sprint_1_closure.py'

    def test_sprint_certification_completed_review_can_pass_and_markdown_drift_fails(self):
        certification=self.project/'reports'/'sprint_1_certification.json'; data=self.load_json(certification)
        data['certification_status']='certified'; data['independent_review'].update({'status':'completed','reviewer':'Independent Reviewer','verdict':'APPROVE','reviewed_commit':'7387afcb9a6345a97083506245fa6414504ad654','reviewed_at':'2026-07-12T00:00:00Z','review_source':'fixture','blocking_findings':[]})
        self.write_json(certification,data); self.regenerate_closure()
        self.assertEqual(self.run_validator('validate_sprint_1_certification.py').returncode,0)
        markdown=certification.with_suffix('.md'); markdown.write_text(markdown.read_text(encoding='utf-8')+'\nDrift.\n',encoding='utf-8')
        self.assert_validation_fails(self.run_validator('validate_sprint_1_certification.py'),'certification Markdown differs from deterministic renderer output')

    def regenerate_closure(self):
        result=subprocess.run([sys.executable,str(self.repo/'workshop'/'scripts'/'render_sprint_1_closure.py')],cwd=self.repo,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__ == "__main__":
    unittest.main()
