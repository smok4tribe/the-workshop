#!/usr/bin/env python3
"""Positive and adversarial tests for the Sprint 2 Task 30 simulation contracts.

Positive tests confirm the committed policy, contracts, card semantics, question,
renderer, and valid fixtures are internally coherent. Adversarial tests copy the
repository into a temporary directory, corrupt one thing, and prove the contracts
validator rejects it. Fixture-conformance tests exercise the committed valid and
invalid instance fixtures against the instance contracts.
"""

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
VALIDATION = REPO_ROOT / "workshop" / "tests" / "validation"
PROJECT = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
SIM = PROJECT / "simulation"
CONTRACTS = SIM / "contracts"
FIXTURES = REPO_ROOT / "workshop" / "tests" / "fixtures" / "simulation"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACTS_MODULE = load_module(
    "validate_simulation_contracts", VALIDATION / "validate_simulation_contracts.py"
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1


class ReferencePCG32:
    """Independent reference implementation of pcg32-v1 built only from the
    written policy specification, used to verify the known-answer test vector."""

    MULTIPLIER = 6364136223846793005

    def __init__(self, initstate, initseq):
        self.state = 0
        self.inc = ((initseq << 1) | 1) & MASK64
        self._step()
        self.state = (self.state + (initstate & MASK64)) & MASK64
        self._step()

    def _step(self):
        self.state = (self.state * self.MULTIPLIER + self.inc) & MASK64

    def next_u32(self):
        old = self.state
        self._step()
        xorshifted = (((old >> 18) ^ old) >> 27) & MASK32
        rot = (old >> 59) & 31
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & MASK32

    def bounded(self, bound):
        threshold = ((1 << 32) - bound) % bound
        while True:
            value = self.next_u32()
            if value >= threshold:
                return value % bound

    def shuffle(self, array):
        result = list(array)
        for i in range(len(result) - 1, 0, -1):
            j = self.bounded(i + 1)
            result[i], result[j] = result[j], result[i]
        return result


class CommittedArtifactTests(unittest.TestCase):
    def test_validator_passes_on_committed_artifacts(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATION / "validate_simulation_contracts.py")],
            cwd=REPO_ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_fingerprint_is_deterministic_and_matches_policy(self):
        policy = load_json(SIM / "simulation_policy.json")
        reference = policy["deck_fingerprint_policy"]["reference_fingerprints"]
        for version_id in ("v1.0", "v1.1"):
            version = load_json(PROJECT / "versions" / f"{version_id}.json")
            first = CONTRACTS_MODULE.deck_content_fingerprint(version)
            second = CONTRACTS_MODULE.deck_content_fingerprint(version)
            self.assertEqual(first, second)
            self.assertEqual(first, reference[version_id])
        self.assertNotEqual(reference["v1.0"], reference["v1.1"])

    def test_seed_derivation_is_deterministic(self):
        fp = "deck-content-sha256-v1:064801f0679b6dea14e52695efb0c1e92b095e810612d9d0929b45d6223c7cf4"
        seed_a = CONTRACTS_MODULE.derive_seed("question-001-mana-color", "sim-policy-v1", fp, "candidate_v1.1")
        seed_b = CONTRACTS_MODULE.derive_seed("question-001-mana-color", "sim-policy-v1", fp, "candidate_v1.1")
        self.assertEqual(seed_a, seed_b)
        self.assertTrue(0 <= seed_a < 2 ** 64)
        other = CONTRACTS_MODULE.derive_seed("question-001-mana-color", "sim-policy-v1", fp, "baseline_v1.0")
        self.assertNotEqual(seed_a, other)

    def test_pcg32_known_answer_vector(self):
        algorithm = load_json(SIM / "simulation_policy.json")["randomness_policy"]["rng_algorithm"]
        vector = algorithm["known_answer_test_vector"]
        rng = ReferencePCG32(vector["seed_initstate"], algorithm["stream_selector"])
        outputs = [rng.next_u32() for _ in range(len(vector["first_5_u32_outputs"]))]
        self.assertEqual(outputs, vector["first_5_u32_outputs"])
        shuffle_rng = ReferencePCG32(vector["seed_initstate"], algorithm["stream_selector"])
        self.assertEqual(shuffle_rng.shuffle(vector["shuffle_input"]), vector["shuffle_result"])

    def test_renderer_is_no_drift(self):
        with tempfile.TemporaryDirectory(prefix="sim-render-") as tmp:
            repo = Path(tmp)
            shutil.copytree(REPO_ROOT / "workshop", repo / "workshop")
            committed_policy_md = (SIM / "simulation_policy.md").read_text(encoding="utf-8")
            committed_question_md = (SIM / "questions" / "question-001-mana-color.md").read_text(encoding="utf-8")
            subprocess.run(
                [sys.executable, str(repo / "workshop" / "scripts" / "render_simulation_policy.py")],
                cwd=repo, text=True, capture_output=True, check=True,
            )
            rendered_policy_md = (repo / "workshop" / "projects" / "the-myr-singularity"
                                  / "simulation" / "simulation_policy.md").read_text(encoding="utf-8")
            rendered_question_md = (repo / "workshop" / "projects" / "the-myr-singularity"
                                    / "simulation" / "questions" / "question-001-mana-color.md").read_text(encoding="utf-8")
            self.assertEqual(committed_policy_md, rendered_policy_md)
            self.assertEqual(committed_question_md, rendered_question_md)


class FixtureConformanceTests(unittest.TestCase):
    """Exercise committed valid/invalid instance fixtures against the contracts."""

    def setUp(self):
        self.run_required = list(load_json(CONTRACTS / "simulation_run.contract.json")["required_fields"])
        self.result_required = list(load_json(CONTRACTS / "simulation_result.contract.json")["required_fields"])
        self.comparison_required = list(load_json(CONTRACTS / "comparison_result.contract.json")["required_fields"])
        self.taxonomy_ids = {
            c["category_id"] for c in load_json(CONTRACTS / "failure_pattern_taxonomy.json")["categories"]
        }

    def check_run_instance(self, run):
        errors = [f"missing {field}" for field in self.run_required if field not in run]
        version = load_json(REPO_ROOT / run["deck_version_path"]) if run.get("deck_version_path") else None
        if version is not None:
            expected_fp = CONTRACTS_MODULE.deck_content_fingerprint(version)
            if run.get("deck_content_fingerprint") != expected_fp:
                errors.append("fingerprint does not match DeckVersion")
        if "seed" not in run:
            errors.append("missing seed")
        elif version is not None:
            expected_seed = CONTRACTS_MODULE.derive_seed(
                run["question_id"], run["policy_version"], run["deck_content_fingerprint"], run["run_role"]
            )
            if run["seed"] != expected_seed:
                errors.append("seed is not policy-derived")
        if isinstance(run.get("iteration_count"), int) and run["iteration_count"] < 10000:
            errors.append("iteration_count below minimum")
        flags = run.get("explicit_boundary", {})
        if any(flags.get(flag) for flag in ("carries_metrics", "carries_interpretation", "creates_deck_version")):
            errors.append("boundary flag is true")
        return errors

    def check_result_instance(self, result):
        errors = [f"missing {field}" for field in self.result_required if field not in result]
        if "reasoning_interpretation" in result or "product_owner_decision" in result:
            errors.append("carries interpretation or decision")
        text_fields = [result.get("readable_summary", "")] + list(result.get("observations", []))
        for text in text_fields:
            if CONTRACTS_MODULE.find_forbidden(text):
                errors.append("forbidden evidence-language claim")
        for pattern in result.get("failure_patterns", []):
            if pattern.get("category_id") not in self.taxonomy_ids:
                errors.append("failure pattern references undefined category")
        for metric in result.get("metrics", []):
            interval = metric.get("confidence_interval", {})
            if not all(k in interval for k in ("method", "level", "lower", "upper")):
                errors.append("metric missing Wilson interval fields")
        return errors

    def check_comparison_instance(self, comparison):
        errors = [f"missing {field}" for field in self.comparison_required if field not in comparison]
        parity = comparison.get("config_parity", {})
        if not all(parity.get(flag) for flag in (
            "identical_policy_version", "identical_question_id", "identical_iteration_count",
            "identical_config", "only_difference_is_deck_version",
        )):
            errors.append("config parity broken")
        base_fp = comparison.get("baseline", {}).get("deck_content_fingerprint")
        cand_fp = comparison.get("candidate", {}).get("deck_content_fingerprint")
        if base_fp == cand_fp:
            errors.append("baseline and candidate fingerprints must differ")
        for delta in comparison.get("metric_deltas", []):
            expected = round(delta.get("candidate_probability", 0) - delta.get("baseline_probability", 0), 9)
            if round(delta.get("absolute_delta", 0), 9) != expected:
                errors.append("absolute_delta is inconsistent")
            if delta.get("baseline_probability") == 0 and delta.get("relative_delta") is not None:
                errors.append("relative_delta present with zero baseline")
        return errors

    def test_valid_fixtures_conform(self):
        self.assertEqual(self.check_run_instance(load_json(FIXTURES / "valid" / "simulation_run.valid.json")), [])
        self.assertEqual(self.check_result_instance(load_json(FIXTURES / "valid" / "simulation_result.valid.json")), [])
        self.assertEqual(self.check_comparison_instance(load_json(FIXTURES / "valid" / "comparison_result.valid.json")), [])

    def test_invalid_run_missing_seed(self):
        errors = self.check_run_instance(load_json(FIXTURES / "invalid" / "simulation_run.missing_seed.json"))
        self.assertIn("missing seed", errors)

    def test_invalid_run_fingerprint_mismatch(self):
        errors = self.check_run_instance(load_json(FIXTURES / "invalid" / "simulation_run.fingerprint_mismatch.json"))
        self.assertIn("fingerprint does not match DeckVersion", errors)

    def test_invalid_result_carries_interpretation(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.carries_interpretation.json"))
        self.assertIn("carries interpretation or decision", errors)

    def test_invalid_result_forbidden_claim(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.forbidden_claim.json"))
        self.assertIn("forbidden evidence-language claim", errors)

    def test_invalid_result_unknown_failure_category(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.unknown_failure_category.json"))
        self.assertIn("failure pattern references undefined category", errors)

    def test_invalid_comparison_no_parity(self):
        errors = self.check_comparison_instance(load_json(FIXTURES / "invalid" / "comparison_result.no_parity.json"))
        self.assertIn("config parity broken", errors)


class AdversarialContractTests(unittest.TestCase):
    """Corrupt one committed artifact in a temp repo and require validator failure."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="sim-contracts-")
        self.repo = Path(self.temp_dir.name)
        shutil.copytree(REPO_ROOT / "workshop", self.repo / "workshop")
        self.sim = self.repo / "workshop" / "projects" / "the-myr-singularity" / "simulation"
        self.validation = self.repo / "workshop" / "tests" / "validation"

    def tearDown(self):
        self.temp_dir.cleanup()

    def load(self, relative):
        return json.loads((self.sim / relative).read_text(encoding="utf-8"))

    def write(self, relative, value):
        (self.sim / relative).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def run_validator(self):
        return subprocess.run(
            [sys.executable, str(self.validation / "validate_simulation_contracts.py")],
            cwd=self.repo, text=True, capture_output=True, check=False,
        )

    def assert_fails(self, expected):
        result = self.run_validator()
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn(expected, output)

    def test_baseline_temp_copy_passes(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_policy_owning_fixture_card_behavior_fails(self):
        policy = self.load("simulation_policy.json")
        policy["keep_rule"]["base_rule"]["note"] = "City of Brass is a rainbow land."
        self.write("simulation_policy.json", policy)
        self.assert_fails("must not encode fixture-specific card behavior")

    def test_keep_rule_accepting_zero_land_fails(self):
        policy = self.load("simulation_policy.json")
        policy["keep_rule"]["base_rule"]["zero_land_hands"] = "keep"
        self.write("simulation_policy.json", policy)
        self.assert_fails("must reject zero-land hands")

    def test_mulligan_policy_change_fails(self):
        policy = self.load("simulation_policy.json")
        policy["mulligan_policy"]["policy_name"] = "no_mulligan"
        self.write("simulation_policy.json", policy)
        self.assert_fails("one_free_mulligan_then_london")

    def test_bottoming_order_change_fails(self):
        policy = self.load("simulation_policy.json")
        policy["bottoming_rule"]["priority_order"][0]["selector"] = "lands_above_three"
        self.write("simulation_policy.json", policy)
        self.assert_fails("bottoming priority order")

    def test_iteration_minimum_change_fails(self):
        policy = self.load("simulation_policy.json")
        policy["iteration_policy"]["minimum_saved_iterations"] = 100
        self.write("simulation_policy.json", policy)
        self.assert_fails("minimum_saved_iterations must be 10000")

    def test_urza_saga_five_color_credit_fails(self):
        semantics = self.load("card_semantics.json")
        for entry in semantics["entries"]:
            if entry["card_identity"]["name"] == "Urza's Saga":
                entry["modeled_behavior"]["counts_as_five_color_source"] = True
                entry["modeled_behavior"]["produces_colors"] = ["W", "U", "B", "R", "G"]
        self.write("card_semantics.json", semantics)
        self.assert_fails("Urza's Saga modeled_behavior")

    def test_override_without_compensation_flag_fails(self):
        semantics = self.load("card_semantics.json")
        for entry in semantics["entries"]:
            if entry["card_identity"]["name"] == "City of Brass":
                entry["compensates_for_missing_canonical_produced_mana"] = False
        self.write("card_semantics.json", semantics)
        self.assert_fails("compensates_for_missing_canonical_produced_mana true")

    def test_fingerprint_tamper_via_deck_change_fails(self):
        version_path = self.repo / "workshop" / "projects" / "the-myr-singularity" / "versions" / "v1.1.json"
        version = json.loads(version_path.read_text(encoding="utf-8"))
        version["main_deck"][0]["name"] = "Swamp"
        version_path.write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assert_fails("does not match recomputation")

    def test_question_executed_with_results_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["execution_status"] = "executed"
        question["metrics"] = [{"metric_id": "five_color_availability_by_turn", "probability": 0.6}]
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("execution_status must be 'not_executed'")

    def test_question_forbidden_language_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["question_text"] = "Does v1.1 have a higher win rate than v1.0?"
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("forbidden claim")

    def test_urza_saga_permanent_land_fails(self):
        semantics = self.load("card_semantics.json")
        for entry in semantics["entries"]:
            if entry["card_identity"]["name"] == "Urza's Saga":
                entry["time_dependent_availability"]["persists_as_permanent_land"] = True
        self.write("card_semantics.json", semantics)
        self.assert_fails("must not persist as a permanent land")

    def test_urza_saga_window_through_horizon_fails(self):
        semantics = self.load("card_semantics.json")
        for entry in semantics["entries"]:
            if entry["card_identity"]["name"] == "Urza's Saga":
                entry["time_dependent_availability"]["availability_window"]["end_offset"] = 6
        self.write("card_semantics.json", semantics)
        self.assert_fails("availability window must end before the observation horizon")

    def test_reproducibility_without_rng_params_fails(self):
        policy = self.load("simulation_policy.json")
        del policy["randomness_policy"]["rng_algorithm"]
        self.write("simulation_policy.json", policy)
        self.assert_fails("omits versioned RNG algorithm parameters")

    def test_modeled_zones_including_sideboard_fails(self):
        policy = self.load("simulation_policy.json")
        policy["modeled_deck_zones"]["included"] = ["commander", "main_deck", "sideboard"]
        self.write("simulation_policy.json", policy)
        self.assert_fails("included must be commander and main_deck only")

    def test_run_contract_dropping_required_field_fails(self):
        contract = self.load("contracts/simulation_run.contract.json")
        contract["required_fields"].pop("seed", None)
        self.write("contracts/simulation_run.contract.json", contract)
        self.assert_fails("run contract must require 'seed'")

    def test_production_instance_in_project_dir_fails(self):
        instance = json.loads(
            (FIXTURES / "valid" / "simulation_run.valid.json").read_text(encoding="utf-8")
        )
        self.write("planted_run.json", instance)
        self.assert_fails("production simulation instance present")


if __name__ == "__main__":
    unittest.main()
