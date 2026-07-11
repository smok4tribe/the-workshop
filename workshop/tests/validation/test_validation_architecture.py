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
            card for card in candidates["candidate_cards"] if card["name"] == "City of Brass"
        )
        candidates["candidate_cards"] = [
            card for card in candidates["candidate_cards"] if card["name"] != "City of Brass"
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


if __name__ == "__main__":
    unittest.main()
