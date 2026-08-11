#!/usr/bin/env python3
"""Focused regressions for the post-v1.1 structural analysis."""

from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_RELATIVE = Path("workshop/projects/the-myr-singularity")


class StructuralAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="structural-analysis-")
        self.repo = Path(self.temp_dir.name)
        shutil.copytree(REPO_ROOT / "workshop", self.repo / "workshop")
        self.project = self.repo / PROJECT_RELATIVE
        self.analysis_path = self.project / "analysis" / "current_v1.1.json"
        self.validator = self.repo / "workshop" / "tests" / "validation" / "validate_structural_analysis.py"

    def tearDown(self):
        self.temp_dir.cleanup()

    def load_analysis(self):
        return json.loads(self.analysis_path.read_text(encoding="utf-8"))

    def write_analysis(self, analysis):
        self.analysis_path.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_validator(self):
        return subprocess.run(
            [sys.executable, str(self.validator)],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def load_temp_structural_analysis(self):
        path = self.repo / "workshop" / "tests" / "validation" / "structural_analysis.py"
        spec = importlib.util.spec_from_file_location("temp_structural_analysis", path)
        module = importlib.util.module_from_spec(spec)
        validation_dir = str(path.parent)
        sys.path.insert(0, validation_dir)
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(validation_dir)
        return module

    def assert_fails(self, expected):
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_committed_analysis_validates(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("6/6 checks passed", result.stdout)

    def test_renderer_is_deterministic(self):
        committed = (REPO_ROOT / PROJECT_RELATIVE / "analysis" / "current_v1.1.md").read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(self.repo / "workshop" / "scripts" / "render_structural_analysis.py")],
            cwd=self.repo,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rendered = (self.project / "analysis" / "current_v1.1.md").read_text(encoding="utf-8")
        self.assertEqual(committed, rendered)

    def test_stale_v1_0_identity_fails(self):
        analysis = self.load_analysis()
        analysis["deck_version_id"] = "v1.0"
        self.write_analysis(analysis)
        self.assert_fails("analysis must bind to DeckVersion v1.1")

    def test_tampered_v1_1_deck_fails_recomputation(self):
        version_path = self.project / "versions" / "v1.1.json"
        version = json.loads(version_path.read_text(encoding="utf-8"))
        version["main_deck"][0]["quantity"] = 2
        version_path.write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assert_fails("analysis computed structural facts do not match recomputation from DeckVersion v1.1")

    def test_category_counts_preserve_duplicate_quantities_without_role_multiplication(self):
        structural_analysis = self.load_temp_structural_analysis()
        baseline = structural_analysis.analysis_snapshot(self.repo)
        version_path = self.project / "versions" / "v1.1.json"
        version = json.loads(version_path.read_text(encoding="utf-8"))
        island = next(entry for entry in version["main_deck"] if entry["name"] == "Island")
        original_total_quantity = sum(
            entry["quantity"] for entry in version["main_deck"] if entry["name"] == "Island"
        )
        island["quantity"] += 1
        version_path.write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        roles_path = self.repo / "workshop" / "knowledge" / "functional_roles.json"
        roles = json.loads(roles_path.read_text(encoding="utf-8"))
        assignment = next(item for item in roles["assignments"] if item["canonical_card_name"] == "Island")
        assignment["roles"].append("fixing_land")
        assignment["primary_roles"].append("fixing_land")
        roles_path.write_text(json.dumps(roles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        mutated = structural_analysis.analysis_snapshot(self.repo)
        before = baseline["category_distribution"]["categories"]["lands_and_mana_base"]
        after = mutated["category_distribution"]["categories"]["lands_and_mana_base"]
        self.assertEqual(after["cards_with_any_role"], before["cards_with_any_role"] + 1)
        self.assertEqual(after["cards_with_primary_role"], before["cards_with_primary_role"] + 1)
        self.assertEqual(
            after["role_assignments_in_category"],
            before["role_assignments_in_category"]
            + (2 * (original_total_quantity + 1) - original_total_quantity),
        )

    def test_nonland_source_roles_do_not_change_land_only_counts(self):
        structural_analysis = self.load_temp_structural_analysis()
        baseline = structural_analysis.analysis_snapshot(self.repo)["color_requirements"]
        roles_path = self.repo / "workshop" / "knowledge" / "functional_roles.json"
        roles = json.loads(roles_path.read_text(encoding="utf-8"))
        assignment = next(item for item in roles["assignments"] if item["canonical_card_name"] == "Sol Ring")
        assignment["roles"].extend(["colored_source", "fixing_land"])
        roles_path.write_text(json.dumps(roles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        mutated = structural_analysis.analysis_snapshot(self.repo)["color_requirements"]
        self.assertEqual(mutated["colored_land_sources_by_role"], baseline["colored_land_sources_by_role"])
        self.assertEqual(mutated["fixing_lands_by_role"], baseline["fixing_lands_by_role"])

    def test_stale_deck_source_reference_fails(self):
        analysis = self.load_analysis()
        analysis["generated_from"]["deck_version"]["path"] = (
            "workshop/projects/the-myr-singularity/versions/v1.0.json"
        )
        self.write_analysis(analysis)
        self.assert_fails("analysis source reference 'deck_version' must use")

    def test_performance_claim_fails(self):
        analysis = self.load_analysis()
        analysis["structural_observations"].append("v1.1 has better mana.")
        self.write_analysis(analysis)
        self.assert_fails("analysis contains prohibited performance language 'better mana'")

    def test_nested_simulation_result_key_fails(self):
        analysis = self.load_analysis()
        analysis["historical_context"]["nested"] = {"simulation_result": {"result_id": "not-allowed"}}
        self.write_analysis(analysis)
        self.assert_fails(
            "analysis must not contain forbidden artifact key 'simulation_result' at "
            "historical_context.nested.simulation_result"
        )

    def test_recommendation_and_decision_keys_fail(self):
        analysis = self.load_analysis()
        analysis["recommendation_id"] = "rec-003"
        analysis["product_owner_decision"] = "decision-005"
        self.write_analysis(analysis)
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("analysis must not contain forbidden artifact key 'recommendation_id'", result.stdout)
        self.assertIn("analysis must not contain forbidden artifact key 'product_owner_decision'", result.stdout)


if __name__ == "__main__":
    unittest.main()
