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
INSTANCE_MODULE = load_module(
    "simulation_instance_validation", VALIDATION / "simulation_instance_validation.py"
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
        self.run_contract = load_json(CONTRACTS / "simulation_run.contract.json")
        self.result_contract = load_json(CONTRACTS / "simulation_result.contract.json")
        self.comparison_contract = load_json(CONTRACTS / "comparison_result.contract.json")
        self.question = load_json(SIM / "questions" / "question-001-mana-color.json")
        self.policy = load_json(SIM / "simulation_policy.json")
        self.valid_run = load_json(FIXTURES / "valid" / "simulation_run.valid.json")
        self.baseline_run = load_json(FIXTURES / "valid" / "simulation_run.baseline.valid.json")
        self.valid_result = load_json(FIXTURES / "valid" / "simulation_result.valid.json")
        self.baseline_result = load_json(FIXTURES / "valid" / "simulation_result.baseline.valid.json")
        self.taxonomy_ids = {
            c["category_id"] for c in load_json(CONTRACTS / "failure_pattern_taxonomy.json")["categories"]
        }

    @staticmethod
    def load_reference(path):
        return load_json(REPO_ROOT / path)

    def check_run_instance(self, run):
        return INSTANCE_MODULE.validate_simulation_run(
            run, question=self.question, policy=self.policy, run_contract=self.run_contract,
            project_id="the-myr-singularity", load_reference=self.load_reference,
            fingerprint_for_version=CONTRACTS_MODULE.deck_content_fingerprint,
            derive_seed=CONTRACTS_MODULE.derive_seed,
        )

    def check_result_instance(self, result, run=None):
        return INSTANCE_MODULE.validate_simulation_result(
            result, run=run or self.valid_run, policy=self.policy,
            result_contract=self.result_contract, taxonomy_ids=self.taxonomy_ids,
            forbidden_claims=CONTRACTS_MODULE.find_forbidden,
        )

    def check_comparison_instance(self, comparison):
        return INSTANCE_MODULE.validate_comparison_result(
            comparison, baseline_run=self.baseline_run, candidate_run=self.valid_run,
            baseline_result=self.baseline_result, candidate_result=self.valid_result,
            policy=self.policy, question=self.question, comparison_contract=self.comparison_contract,
            forbidden_claims=CONTRACTS_MODULE.find_forbidden, load_reference=self.load_reference,
        )

    def test_valid_fixtures_conform(self):
        self.assertEqual(self.check_run_instance(self.valid_run), [])
        self.assertEqual(self.check_result_instance(self.valid_result, self.valid_run), [])
        self.assertEqual(self.check_run_instance(self.baseline_run), [])
        self.assertEqual(self.check_result_instance(self.baseline_result, self.baseline_run), [])
        self.assertEqual(self.check_comparison_instance(load_json(FIXTURES / "valid" / "comparison_result.valid.json")), [])

    def test_invalid_run_missing_seed(self):
        errors = self.check_run_instance(load_json(FIXTURES / "invalid" / "simulation_run.missing_seed.json"))
        self.assertIn("run is missing required field 'seed'", errors)

    def test_invalid_run_fingerprint_mismatch(self):
        errors = self.check_run_instance(load_json(FIXTURES / "invalid" / "simulation_run.fingerprint_mismatch.json"))
        self.assertIn("run fingerprint does not match DeckVersion", errors)

    def test_invalid_result_carries_interpretation(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.carries_interpretation.json"))
        self.assertIn("result carries interpretation or decision", errors)

    def test_invalid_result_forbidden_claim(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.forbidden_claim.json"))
        self.assertIn("result contains forbidden evidence-language claim", errors)

    def test_invalid_result_unknown_failure_category(self):
        errors = self.check_result_instance(load_json(FIXTURES / "invalid" / "simulation_result.unknown_failure_category.json"))
        self.assertIn("failure pattern references undefined category", errors)

    def test_run_role_must_match_question_deck_version(self):
        run = dict(self.valid_run)
        run["run_role"] = "baseline_v1.0"
        errors = self.check_run_instance(run)
        self.assertIn("run role is not bound to the question DeckVersion", errors)

    def test_failure_pattern_inconsistent_frequency_fails(self):
        result = load_json(FIXTURES / "valid" / "simulation_result.valid.json")
        result["failure_patterns"][0]["frequency"] = 0.38
        errors = self.check_result_instance(result)
        self.assertIn("failure pattern frequency does not equal raw_count/sample_size", errors)

    def test_failure_pattern_denominator_must_match_run_iterations(self):
        result = load_json(FIXTURES / "valid" / "simulation_result.valid.json")
        result["failure_patterns"][0]["sample_size"] = 99999
        errors = self.check_result_instance(result)
        self.assertIn("failure pattern sample_size does not match run iteration_count", errors)

    def test_failure_pattern_count_must_be_in_range(self):
        result = load_json(FIXTURES / "valid" / "simulation_result.valid.json")
        result["failure_patterns"][0]["raw_count"] = 100001
        result["failure_patterns"][0]["frequency"] = 1.00001
        errors = self.check_result_instance(result)
        self.assertIn("failure pattern raw_count must be within 0..sample_size", errors)

    def test_failure_pattern_unknown_category_fails(self):
        result = load_json(FIXTURES / "valid" / "simulation_result.valid.json")
        result["failure_patterns"][0]["category_id"] = "not_a_real_category"
        errors = self.check_result_instance(result)
        self.assertIn("failure pattern references undefined category", errors)

    def test_invalid_comparison_no_parity(self):
        errors = self.check_comparison_instance(load_json(FIXTURES / "invalid" / "comparison_result.no_parity.json"))
        self.assertIn("comparison baseline_estimate does not match resolved result metric", errors)

    def test_comparison_computes_semantic_parity_from_resolved_runs(self):
        comparison = load_json(FIXTURES / "valid" / "comparison_result.valid.json")
        candidate_run = dict(self.valid_run)
        candidate_run["config"] = dict(candidate_run["config"])
        candidate_run["config"]["observation_horizon_turn"] = 5
        errors = INSTANCE_MODULE.validate_comparison_result(
            comparison, baseline_run=self.baseline_run, candidate_run=candidate_run,
            baseline_result=self.baseline_result, candidate_result=self.valid_result,
            policy=self.policy, question=self.question, comparison_contract=self.comparison_contract,
            forbidden_claims=CONTRACTS_MODULE.find_forbidden,
        )
        self.assertIn("comparison semantic parity failed: config differs", errors)

    def test_equal_content_comparison_is_structurally_valid_without_attribution(self):
        comparison = load_json(FIXTURES / "valid" / "comparison_result.valid.json")
        baseline_run = dict(self.baseline_run)
        baseline_result = json.loads(json.dumps(self.baseline_result))
        comparison = json.loads(json.dumps(comparison))
        baseline_run["deck_content_fingerprint"] = self.valid_run["deck_content_fingerprint"]
        baseline_result["deck_content_fingerprint"] = self.valid_run["deck_content_fingerprint"]
        comparison["baseline"]["deck_content_fingerprint"] = self.valid_run["deck_content_fingerprint"]
        self.assertEqual(
            INSTANCE_MODULE.validate_comparison_result(
                comparison, baseline_run=baseline_run, candidate_run=self.valid_run,
                baseline_result=baseline_result, candidate_result=self.valid_result,
                policy=self.policy, question=self.question, comparison_contract=self.comparison_contract,
                forbidden_claims=CONTRACTS_MODULE.find_forbidden,
            ), [],
        )
        comparison["explicit_boundary"]["attributes_deck_content_effect"] = True
        errors = INSTANCE_MODULE.validate_comparison_result(
            comparison, baseline_run=baseline_run, candidate_run=self.valid_run,
            baseline_result=baseline_result, candidate_result=self.valid_result,
            policy=self.policy, question=self.question, comparison_contract=self.comparison_contract,
            forbidden_claims=CONTRACTS_MODULE.find_forbidden,
        )
        self.assertIn("equal-content comparison must not attribute a deck-content effect", errors)


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

    def test_question_missing_role_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["compared_versions"][0].pop("run_role")
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("is missing run_role")

    def test_question_duplicate_role_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["compared_versions"][1]["run_role"] = "baseline_v1.0"
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("must use unique run_role values")

    def test_question_arbitrary_role_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["compared_versions"][1]["run_role"] = "experimental_v1.1"
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("must be 'candidate_v1.1'")

    def test_question_swapped_roles_fail(self):
        question = self.load("questions/question-001-mana-color.json")
        question["compared_versions"][0]["run_role"] = "candidate_v1.1"
        question["compared_versions"][1]["run_role"] = "baseline_v1.0"
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("question-001 role for v1.0 must be 'baseline_v1.0'")

    def test_question_unregistered_materiality_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["success_interpretation"]["directional_expectation"] += " v1.1 must be materially higher."
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("contains unregistered materiality term")

    def test_question_unregistered_acceptable_materiality_fails(self):
        question = self.load("questions/question-001-mana-color.json")
        question["success_interpretation"]["notes"] += " An acceptable result is required."
        self.write("questions/question-001-mana-color.json", question)
        self.assert_fails("contains unregistered materiality term")

    def test_urza_saga_removal_is_not_resolution_bound(self):
        semantics = self.load("card_semantics.json")
        for entry in semantics["entries"]:
            if entry["card_identity"]["name"] == "Urza's Saga":
                entry["time_dependent_availability"]["removal_event"]["trigger"] = "chapter_iii_resolves"
        self.write("card_semantics.json", semantics)
        self.assert_fails("must trigger when the final chapter ability leaves the stack")

    def test_first_turn_draw_must_be_normal_multiplayer_rule(self):
        policy = self.load("simulation_policy.json")
        policy["commander_scenario"]["first_turn_draw_note"] = "This is a deviation from paper rules."
        self.write("simulation_policy.json", policy)
        self.assert_fails("must describe normal multiplayer paper rules")

    def test_standalone_result_policy_must_not_require_absolute_delta(self):
        policy = self.load("simulation_policy.json")
        policy["uncertainty_policy"]["required_reported_fields"].append("absolute_delta")
        self.write("simulation_policy.json", policy)
        self.assert_fails("must not require absolute_delta")

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

    def test_run_contract_dropping_role_field_fails(self):
        contract = self.load("contracts/simulation_run.contract.json")
        contract["required_fields"].pop("run_role", None)
        self.write("contracts/simulation_run.contract.json", contract)
        self.assert_fails("run contract must require 'run_role'")

    def test_production_instance_in_project_dir_fails(self):
        instance = json.loads(
            (FIXTURES / "valid" / "simulation_run.valid.json").read_text(encoding="utf-8")
        )
        self.write("planted_run.json", instance)
        self.assert_fails("production simulation instance present")


if __name__ == "__main__":
    unittest.main()
