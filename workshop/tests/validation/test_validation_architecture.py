#!/usr/bin/env python3
"""Regression tests for validation failures found by the Sprint 1 audit."""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
