"""Positive and adversarial coverage for the active simulation-policy-v6 contract."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from collections import UserDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from workshop.shared.identity import (  # noqa: E402
    artifact_content_fingerprint, deck_content_fingerprint, load_strict_json_bytes,
    resolve_card_fact,
)
from workshop.shared.simulation_determinism import (  # noqa: E402
    PCG32, choose_payment, condition_is_satisfied, derive_iteration_seed, derive_run_seed,
    observe_source_capability, select_bottom_tokens, select_land,
    select_payable_ramp,
)
from workshop.simulation.instance_validation import (  # noqa: E402
    METRIC_MEASUREMENT_CONTRACTS, build_runtime_state_authority, canonical_question_path, validate_comparison_result,
    evaluate_end_step_state_transitions, project_level_two_land, project_level_two_ramp,
    resolve_activation_profiles, resolve_question_metric_target,
    validate_card_semantics_registry_parity, validate_failure_pattern_taxonomy,
    validate_mana_source_semantics,
    validate_policy_metric_contracts, validate_recording_context,
    validate_result_failure_patterns, validate_simulation_question,
    validate_simulation_question_lifecycle, validate_simulation_question_lifecycle_transition,
    validate_simulation_result, validate_simulation_run,
)

PROJECT = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
SIM = PROJECT / "simulation"
CONTRACTS = SIM / "contracts"
FIXTURES = REPO_ROOT / "workshop" / "tests" / "fixtures" / "simulation" / "valid"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class IndependentPCG32:
    """Test-only reference for pcg32-v1 KATs; it never imports production RNG code."""
    MASK64 = (1 << 64) - 1
    MASK32 = (1 << 32) - 1
    MULTIPLIER = 6364136223846793005
    STREAM = 11400714819323198485

    def __init__(self, initstate, initseq=STREAM):
        self.state = 0; self.inc = ((initseq << 1) | 1) & self.MASK64
        self._step(); self.state = (self.state + initstate) & self.MASK64; self._step()

    def _step(self): self.state = (self.state * self.MULTIPLIER + self.inc) & self.MASK64

    def next_u32(self):
        old = self.state; self._step(); xorshifted = (((old >> 18) ^ old) >> 27) & self.MASK32; rotation = (old >> 59) & 31
        return ((xorshifted >> rotation) | (xorshifted << ((-rotation) & 31))) & self.MASK32

    def bounded_with_consumption(self, bound):
        threshold, consumed = (2 ** 32 - bound) % bound, []
        while True:
            value = self.next_u32(); consumed.append(value)
            if value >= threshold: return value % bound, consumed

    def shuffle(self, values):
        result = list(values)
        for index in range(len(result) - 1, 0, -1):
            swap, _ = self.bounded_with_consumption(index + 1); result[index], result[swap] = result[swap], result[index]
        return result


class SimulationContractV6Tests(unittest.TestCase):
    def setUp(self):
        self.policy = load(SIM / "simulation_policy.json")
        self.question = load(SIM / "questions" / "question-001-mana-color.json")
        self.cards = load(REPO_ROOT / "workshop" / "card-data" / "cards.json")
        self.contracts = {name: load(CONTRACTS / name) for name in (
            "simulation_question.contract.json", "simulation_question_lifecycle.contract.json",
            "simulation_run.contract.json", "simulation_result.contract.json", "comparison_result.contract.json",
        )}
        self.lifecycle = load(SIM / "lifecycle" / "question-001-mana-color.json")
        self.run = load(FIXTURES / "simulation_run.valid.json")
        self.baseline_run = load(FIXTURES / "simulation_run.baseline.valid.json")
        self.result = load(FIXTURES / "simulation_result.valid.json")
        self.baseline_result = load(FIXTURES / "simulation_result.baseline.valid.json")
        self.comparison = load(FIXTURES / "comparison_result.valid.json")
        self.documents = {
            "workshop/projects/the-myr-singularity/simulation/simulation_policy.json": self.policy,
            "workshop/projects/the-myr-singularity/simulation/questions/question-001-mana-color.json": self.question,
            "workshop/projects/the-myr-singularity/simulation/card_semantics.json": load(SIM / "card_semantics.json"),
            "workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json": load(SIM / "mana_source_semantics.json"),
            "workshop/card-data/cards.json": self.cards,
            "workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json": load(CONTRACTS / "failure_pattern_taxonomy.json"),
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json": load(CONTRACTS / "simulation_question.contract.json"),
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question_lifecycle.contract.json": self.contracts["simulation_question_lifecycle.contract.json"],
            "workshop/projects/the-myr-singularity/simulation/lifecycle/question-001-mana-color.json": self.lifecycle,
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_run.contract.json": self.contracts["simulation_run.contract.json"],
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_result.contract.json": self.contracts["simulation_result.contract.json"],
            "workshop/projects/the-myr-singularity/simulation/contracts/comparison_result.contract.json": self.contracts["comparison_result.contract.json"],
            "workshop/projects/the-myr-singularity/versions/v1.0.json": load(PROJECT / "versions" / "v1.0.json"),
            "workshop/projects/the-myr-singularity/versions/v1.1.json": load(PROJECT / "versions" / "v1.1.json"),
            "workshop/tests/fixtures/simulation/valid/simulation_run.valid.json": self.run,
            "workshop/tests/fixtures/simulation/valid/simulation_run.baseline.valid.json": self.baseline_run,
            "workshop/tests/fixtures/simulation/valid/simulation_result.valid.json": self.result,
            "workshop/tests/fixtures/simulation/valid/simulation_result.baseline.valid.json": self.baseline_result,
        }
        self.taxonomy = self.documents["workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json"]
        self.taxonomy_ids = {x["category_id"] for x in self.taxonomy["categories"]}
        self.versions = [
            self.documents["workshop/projects/the-myr-singularity/versions/v1.0.json"],
            self.documents["workshop/projects/the-myr-singularity/versions/v1.1.json"],
        ]
        self.runtime_authority, authority_errors = build_runtime_state_authority(
            self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"],
            policy=self.policy,
            cards=self.cards["cards"],
            versions=self.versions,
        )
        self.assertEqual([], authority_errors)

    def loader(self, path):
        return self.documents[path]

    def fingerprint(self, version):
        return deck_content_fingerprint(version, self.cards["cards"])

    def check_question(self, question=None, question_path=None, question_contract=None):
        return validate_simulation_question(
            question or self.question, policy=self.policy,
            question_contract=question_contract or self.contracts["simulation_question.contract.json"],
            project_id="the-myr-singularity", load_reference=self.loader,
            fingerprint_for_version=self.fingerprint,
            question_path=question_path or canonical_question_path((question or self.question)["question_id"]),
        )

    def check_run(self, run=None, question=None, run_contract=None):
        return validate_simulation_run(run or self.run, question=question or self.question, policy=self.policy, question_contract=self.contracts["simulation_question.contract.json"], run_contract=run_contract or self.contracts["simulation_run.contract.json"], project_id="the-myr-singularity", load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="creation")

    def check_result(self, result=None, run=None, question=None, result_contract=None):
        return validate_simulation_result(result or self.result, run=run or self.run, policy=self.policy, question=question or self.question, question_contract=self.contracts["simulation_question.contract.json"], result_contract=result_contract or self.contracts["simulation_result.contract.json"], taxonomy_ids=self.taxonomy, load_reference=self.loader, project_id="the-myr-singularity", fingerprint_for_version=self.fingerprint, lifecycle_mode="creation")

    def check_comparison(self, comparison=None, baseline_run=None, candidate_run=None, baseline_result=None, candidate_result=None, question=None, comparison_contract=None, run_contract=None, result_contract=None):
        return validate_comparison_result(comparison or self.comparison, baseline_run=baseline_run or self.baseline_run, candidate_run=candidate_run or self.run, baseline_result=baseline_result or self.baseline_result, candidate_result=candidate_result or self.result, policy=self.policy, question=question or self.question, question_contract=self.contracts["simulation_question.contract.json"], comparison_contract=comparison_contract or self.contracts["comparison_result.contract.json"], run_contract=run_contract or self.contracts["simulation_run.contract.json"], result_contract=result_contract or self.contracts["simulation_result.contract.json"], project_id="the-myr-singularity", taxonomy_ids=self.taxonomy, load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="creation")

    def check_registry(self, registry):
        return validate_mana_source_semantics(registry, policy=self.policy, cards=self.cards["cards"], versions=self.versions)

    def check_lifecycle(self, lifecycle):
        return validate_simulation_question_lifecycle(
            lifecycle, question=self.question,
            lifecycle_contract=self.contracts["simulation_question_lifecycle.contract.json"],
            project_id="the-myr-singularity", load_reference=self.loader,
            policy=self.policy, question_contract=self.contracts["simulation_question.contract.json"],
            fingerprint_for_version=self.fingerprint,
        )

    def test_committed_validator_passes(self):
        result = subprocess.run([sys.executable, "workshop/tests/validation/validate_simulation_contracts.py"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_v6_fixtures_validate(self):
        self.assertEqual([], self.check_run())
        self.assertEqual([], self.check_result())
        self.assertEqual([], self.check_comparison())

    def test_question_validation_is_fail_closed_through_downstream_evidence(self):
        cases = (
            ("legacy-status", lambda question: question.__setitem__("execution_status", "executed"), "unregistered top-level fields"),
            ("redirected-policy", lambda question: question["policy_reference"].__setitem__("path", "workshop/projects/the-myr-singularity/simulation/card_semantics.json"), "canonical SimulationPolicy path"),
            ("malformed-version", lambda question: question["compared_versions"][0].pop("run_role"), "invalid field set"),
            ("unknown-metric", lambda question: question["required_metrics"][0].__setitem__("metric_id", "unknown_metric"), "does not resolve to a Policy metric definition"),
            ("shifted-turn", lambda question: question["required_metrics"][0].__setitem__("target_turn", 1), "target_turn does not match"),
        )
        path = "workshop/projects/the-myr-singularity/simulation/questions/question-001-mana-color.json"
        original = self.documents[path]
        for label, mutate, diagnostic in cases:
            with self.subTest(label=label):
                question = copy.deepcopy(self.question)
                mutate(question)
                run = copy.deepcopy(self.run)
                self.documents[path] = question
                run["semantic_dependencies"]["question"]["content_fingerprint"] = artifact_content_fingerprint(question)
                run["seed"] = derive_run_seed(run["semantic_dependencies"]["question"]["content_fingerprint"], run["semantic_dependencies"]["policy"]["content_fingerprint"], run["deck_content_fingerprint"], run["run_role"])
                self.assertTrue(any(diagnostic in error for error in self.check_run(run, question=question)))
                self.assertTrue(any(diagnostic in error for error in self.check_result(question=question)))
                self.assertTrue(any(diagnostic in error for error in self.check_comparison(question=question)))
        self.documents[path] = original

    def test_selected_metrics_are_exact_and_immutable(self):
        self.assertEqual(self.question["required_metrics"], self.run["selected_metrics"])
        optional = self.question["optional_metrics"][0]
        result_with_unselected = copy.deepcopy(self.result)
        result_with_unselected["metrics"].append({
            "metric_id": optional["metric_id"], "target_turn": optional["target_turn"], "raw_count": 1,
            "sample_size": 100000, "probability": 0.00001,
            "confidence_interval": {"method": "wilson_score_interval", "level": 0.95, "lower": 0.0, "upper": 0.000057},
        })
        self.assertIn("result metrics must exactly equal the Run selected_metrics ordered set", self.check_result(result_with_unselected))
        selected_run = copy.deepcopy(self.run)
        selected_run["selected_metrics"].append(optional)
        self.assertIn("result metrics must exactly equal the Run selected_metrics ordered set", self.check_result(run=selected_run))
        candidate = copy.deepcopy(self.run)
        candidate["selected_metrics"].append(optional)
        errors = validate_comparison_result(self.comparison, baseline_run=self.baseline_run, candidate_run=candidate, baseline_result=self.baseline_result, candidate_result=self.result, policy=self.policy, question=self.question, question_contract=self.contracts["simulation_question.contract.json"], comparison_contract=self.contracts["comparison_result.contract.json"], run_contract=self.contracts["simulation_run.contract.json"], result_contract=self.contracts["simulation_result.contract.json"], project_id="the-myr-singularity", taxonomy_ids=self.taxonomy, load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="creation")
        self.assertTrue(any("comparison selected_metrics must be identical" in error for error in errors))

    def test_eot_source_capability_observation_helper_kats(self):
        level_two = self.policy["level_2_sequencing"]
        observation = level_two["mana_source_projection"]["source_capability_observation"]
        self.assertEqual("source-capability-observation-v1", observation["contract_id"])
        self.assertEqual("gross_surviving_online_capability", observation["projection"])
        self.assertIn("remaining untapped payable resources", observation["spendable_mana_rule"])
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        source_records = {record["oracle_id"]: record for record in records.values()}
        tower_states = [
            {"source_id": f"tower-{index}", "oracle_id": records["Command Tower"]["oracle_id"], "online": True, "tapped": True}
            for index in range(1, 6)
        ]
        shared = {"commander_colors": ["W", "U", "B", "R", "G"]}
        for card_name, source_id in (("Cascading Cataracts", "cataracts"), ("The Mycosynth Gardens", "gardens")):
            with self.subTest(card_name=card_name):
                outcome = observe_source_capability(
                    source_records=source_records,
                    source_states=[{"source_id": source_id, "oracle_id": records[card_name]["oracle_id"], "online": True, "tapped": False}, *tower_states],
                    candidate_source_id=source_id,
                    condition_state=shared,
                    runtime_authority=self.runtime_authority,
                )
                self.assertEqual(set("WUBRG"), set(outcome["source_capability"]))
                self.assertTrue(outcome["five_color_available"])
                self.assertEqual(5, outcome["external_base_capacity"])
                self.assertEqual(0, outcome["residual_external_payment_capacity"])
                self.assertTrue(outcome["survives"])
                self.assertTrue(outcome["online"])
                self.assertEqual(["C"], outcome["candidate_spendable_output_capabilities"])
        tower = observe_source_capability(
            source_records=source_records,
            source_states=[{"source_id": "tower", "oracle_id": records["Command Tower"]["oracle_id"], "online": True, "tapped": True}],
            candidate_source_id="tower", condition_state=shared,
            runtime_authority=self.runtime_authority,
        )
        self.assertEqual(set("WUBRG"), set(tower["source_capability"]))
        self.assertTrue(tower["survives"])
        self.assertTrue(tower["online"])
        self.assertEqual([], tower["candidate_spendable_output_capabilities"])
        glimmervoid = {"source_id": "glimmervoid", "oracle_id": records["Glimmervoid"]["oracle_id"], "online": True, "tapped": False}
        preserved = observe_source_capability(source_records=source_records, source_states=[glimmervoid], candidate_source_id="glimmervoid", condition_state={"artifact_controlled_count": 1})
        self.assertEqual(set("WUBRG"), set(preserved["source_capability"]))
        self.assertEqual(["B", "G", "R", "U", "W"], preserved["candidate_spendable_output_capabilities"])
        removed_glimmervoid = observe_source_capability(
            source_records=source_records, source_states=[glimmervoid], candidate_source_id="glimmervoid",
            condition_state={"artifact_controlled_count": 0},
        )
        self.assertEqual({
            "survives": False, "online": False, "source_capability": [], "five_color_available": False,
            "external_base_capacity": 0, "residual_external_payment_capacity": 0,
            "candidate_spendable_output_capabilities": [],
        }, removed_glimmervoid)
        saga = {"source_id": "saga", "oracle_id": records["Urza's Saga"]["oracle_id"], "online": True, "tapped": False}
        for offset in (2, 3):
            with self.subTest(saga_offset=offset):
                removed_saga = observe_source_capability(
                    source_records=source_records,
                    source_states=[{**saga, "condition_state": {"controller_turn_offset": offset}}],
                    candidate_source_id="saga",
                )
                self.assertEqual({
                    "survives": False, "online": False, "source_capability": [], "five_color_available": False,
                    "external_base_capacity": 0, "residual_external_payment_capacity": 0,
                    "candidate_spendable_output_capabilities": [],
                }, removed_saga)
        with self.assertRaisesRegex(ValueError, "unregistered keys: generic_payment_available_from_other_sources"):
            observe_source_capability(
                source_records=source_records,
                source_states=[{"source_id": "cataracts", "oracle_id": records["Cascading Cataracts"]["oracle_id"], "online": True, "tapped": False}],
                candidate_source_id="cataracts",
                condition_state={"generic_payment_available_from_other_sources": 5},
            )
        five_color = next(metric for metric in self.policy["metric_catalog"]["metrics"] if metric["metric_id"] == "five_color_availability_by_turn")
        self.assertFalse(five_color["measurement_contract"]["event"]["requires_simultaneous_spendable_mana"])
        self.assertIn("before end-of-turn observation", level_two["urzas_saga_final_chapter_timing"])

    def test_lifecycle_is_separate_and_transitions_fail_closed(self):
        question_fingerprint = artifact_content_fingerprint(self.question)
        before_seed = self.run["seed"]
        immutable_question = copy.deepcopy(self.question)
        invalidated = copy.deepcopy(self.lifecycle)
        invalidated["state"] = "invalidated"
        invalidated["invalidation"] = {"from_state": "preregistered", "reason_id": "operator_cancelled"}
        self.assertEqual(question_fingerprint, artifact_content_fingerprint(self.question))
        self.assertEqual(before_seed, derive_run_seed(self.run["semantic_dependencies"]["question"]["content_fingerprint"], self.run["semantic_dependencies"]["policy"]["content_fingerprint"], self.run["deck_content_fingerprint"], self.run["run_role"]))
        self.assertEqual([], self.check_lifecycle(invalidated))
        self.assertEqual([], self.check_run())
        self.assertEqual([], self.check_result())
        self.assertEqual([], self.check_comparison())
        self.assertEqual(immutable_question, self.question)
        self.assertIn("persistence lifecycle mode requires the canonical lifecycle artifact and contract", validate_simulation_run(self.run, question=self.question, policy=self.policy, question_contract=self.contracts["simulation_question.contract.json"], run_contract=self.contracts["simulation_run.contract.json"], project_id="the-myr-singularity", load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="persistence"))

    def _reference(self, document, identity_key, path):
        return {
            "id": document[identity_key],
            "path": path,
            "content_fingerprint": artifact_content_fingerprint(document),
        }

    def _lifecycle_states(self):
        candidate = copy.deepcopy(self.run); candidate["status"] = "executed"
        baseline = copy.deepcopy(self.baseline_run); baseline["status"] = "executed"
        candidate_path, baseline_path = "fixture-lifecycle-candidate", "fixture-lifecycle-baseline"
        candidate_result_path, baseline_result_path = "fixture-lifecycle-candidate-result", "fixture-lifecycle-baseline-result"
        comparison_path = "fixture-lifecycle-comparison"
        candidate_result = copy.deepcopy(self.result)
        candidate_result["source_references"]["run"] = self._reference(candidate, "run_id", candidate_path)
        baseline_result = copy.deepcopy(self.baseline_result)
        baseline_result["source_references"]["run"] = self._reference(baseline, "run_id", baseline_path)
        comparison_document = copy.deepcopy(self.comparison)
        comparison_document["source_references"] = {
            "baseline_run": self._reference(baseline, "run_id", baseline_path),
            "candidate_run": self._reference(candidate, "run_id", candidate_path),
            "baseline_result": self._reference(baseline_result, "result_id", baseline_result_path),
            "candidate_result": self._reference(candidate_result, "result_id", candidate_result_path),
        }
        self.documents.update({
            candidate_path: candidate, baseline_path: baseline,
            candidate_result_path: candidate_result, baseline_result_path: baseline_result,
            comparison_path: comparison_document,
        })
        runs = [
            self._reference(baseline, "run_id", baseline_path),
            self._reference(candidate, "run_id", candidate_path),
        ]
        results = [
            self._reference(baseline_result, "result_id", baseline_result_path),
            self._reference(candidate_result, "result_id", candidate_result_path),
        ]
        comparison = self._reference(comparison_document, "comparison_id", comparison_path)
        preregistered = copy.deepcopy(self.lifecycle)
        runs_recorded = copy.deepcopy(preregistered)
        runs_recorded.update({"state": "runs_recorded", "recorded_evidence": {"runs": runs, "results": [], "comparison": None}})
        results_recorded = copy.deepcopy(runs_recorded)
        results_recorded.update({"state": "results_recorded", "recorded_evidence": {"runs": copy.deepcopy(runs), "results": results, "comparison": None}})
        comparison_recorded = copy.deepcopy(results_recorded)
        comparison_recorded.update({"state": "comparison_recorded", "recorded_evidence": {"runs": copy.deepcopy(runs), "results": copy.deepcopy(results), "comparison": comparison}})
        return preregistered, runs_recorded, results_recorded, comparison_recorded, candidate, baseline

    def _check_transition(self, previous, current):
        return validate_simulation_question_lifecycle_transition(
            previous, current, question=self.question,
            lifecycle_contract=self.contracts["simulation_question_lifecycle.contract.json"],
            project_id="the-myr-singularity", load_reference=self.loader, policy=self.policy,
            question_contract=self.contracts["simulation_question.contract.json"],
            fingerprint_for_version=self.fingerprint,
        )

    def test_lifecycle_identity_is_binary_and_fail_closed(self):
        preregistered, runs, results, _, candidate, _ = self._lifecycle_states()
        self.assertEqual([], self.check_lifecycle(runs))
        duplicate_candidate = copy.deepcopy(candidate); duplicate_candidate["run_id"] = "fixture-run-candidate-duplicate"
        self.documents["fixture-lifecycle-candidate-duplicate"] = duplicate_candidate
        two_candidates = copy.deepcopy(runs)
        two_candidates["recorded_evidence"]["runs"][0] = self._reference(duplicate_candidate, "run_id", "fixture-lifecycle-candidate-duplicate")
        errors = self.check_lifecycle(two_candidates)
        self.assertIn("lifecycle runs must contain exactly one executed Run for each preregistered DeckVersion and run_role", errors)
        duplicate_result = copy.deepcopy(self.result); duplicate_result["result_id"] = "fixture-result-candidate-duplicate"
        self.documents["fixture-lifecycle-candidate-result-duplicate"] = duplicate_result
        duplicate_results = copy.deepcopy(results)
        duplicate_results["recorded_evidence"]["results"][0] = self._reference(duplicate_result, "result_id", "fixture-lifecycle-candidate-result-duplicate")
        errors = self.check_lifecycle(duplicate_results)
        self.assertIn("lifecycle results must contain exactly one Result for each recorded Run", errors)
        foreign_result = copy.deepcopy(self.result); foreign_result["result_id"] = "fixture-result-foreign"; foreign_result["run_id"] = "foreign-run"
        self.documents["fixture-lifecycle-foreign-result"] = foreign_result
        foreign_results = copy.deepcopy(results)
        foreign_results["recorded_evidence"]["results"][1] = self._reference(foreign_result, "result_id", "fixture-lifecycle-foreign-result")
        errors = self.check_lifecycle(foreign_results)
        self.assertIn("lifecycle Result is not bound to a recorded Run", errors)
        three_versions = copy.deepcopy(self.question)
        three_versions["compared_versions"].append(copy.deepcopy(three_versions["compared_versions"][0]))
        self.assertIn("question compared_versions must contain exactly 2 DeckVersions", self.check_question(three_versions))
        self.assertEqual("preregistered", preregistered["state"])

    def test_lifecycle_transitions_preserve_valid_evidence_prefixes(self):
        preregistered, runs, results, comparison, candidate, baseline = self._lifecycle_states()
        self.assertEqual([], self._check_transition(preregistered, runs))
        self.assertEqual([], self._check_transition(runs, results))
        self.assertEqual([], self._check_transition(results, comparison))
        replacement_run = copy.deepcopy(baseline); replacement_run["run_id"] = "fixture-run-baseline-replacement"
        self.documents["fixture-lifecycle-baseline-replacement"] = replacement_run
        replaced_runs = copy.deepcopy(results)
        replaced_runs["recorded_evidence"]["runs"][0] = self._reference(replacement_run, "run_id", "fixture-lifecycle-baseline-replacement")
        replacement_bound_result = copy.deepcopy(self.baseline_result)
        replacement_bound_result["run_id"] = replacement_run["run_id"]
        replacement_bound_result["source_references"]["run"] = self._reference(replacement_run, "run_id", "fixture-lifecycle-baseline-replacement")
        self.documents["fixture-lifecycle-baseline-replacement-result"] = replacement_bound_result
        replaced_runs["recorded_evidence"]["results"][0] = self._reference(replacement_bound_result, "result_id", "fixture-lifecycle-baseline-replacement-result")
        self.assertTrue(any("preserve recorded Run references exactly" in error for error in self._check_transition(runs, replaced_runs)))
        reordered_runs = copy.deepcopy(results)
        reordered_runs["recorded_evidence"]["runs"].reverse()
        self.assertTrue(any("preserve recorded Run references exactly" in error for error in self._check_transition(runs, reordered_runs)))
        removed_run = copy.deepcopy(results)
        removed_run["recorded_evidence"]["runs"].pop()
        self.assertTrue(any("recorded evidence cardinality does not match state" in error for error in self._check_transition(runs, removed_run)))
        replacement_result = copy.deepcopy(self.baseline_result); replacement_result["result_id"] = "fixture-result-baseline-replacement"
        replaced_results = copy.deepcopy(comparison)
        replacement_result["source_references"]["run"] = replaced_results["recorded_evidence"]["runs"][0]
        self.documents["fixture-lifecycle-baseline-result-replacement"] = replacement_result
        replaced_results["recorded_evidence"]["results"][0] = self._reference(replacement_result, "result_id", "fixture-lifecycle-baseline-result-replacement")
        replacement_comparison = copy.deepcopy(self.comparison)
        replacement_comparison["source_references"] = {
            "baseline_run": replaced_results["recorded_evidence"]["runs"][0],
            "candidate_run": replaced_results["recorded_evidence"]["runs"][1],
            "baseline_result": replaced_results["recorded_evidence"]["results"][0],
            "candidate_result": replaced_results["recorded_evidence"]["results"][1],
        }
        replacement_comparison["baseline"]["result_id"] = replacement_result["result_id"]
        self.documents["fixture-lifecycle-comparison-replacement-result"] = replacement_comparison
        replaced_results["recorded_evidence"]["comparison"] = self._reference(replacement_comparison, "comparison_id", "fixture-lifecycle-comparison-replacement-result")
        self.assertTrue(any("preserve Run and Result references exactly" in error for error in self._check_transition(results, replaced_results)))
        invalidated = copy.deepcopy(results)
        invalidated["state"] = "invalidated"
        invalidated["invalidation"] = {"from_state": "results_recorded", "reason_id": "operator_cancelled"}
        invalidated["recorded_evidence"]["runs"].reverse()
        self.assertTrue(any("preserve the prior evidence prefix exactly" in error for error in self._check_transition(results, invalidated)))

    def test_question_contract_authority_cannot_be_caller_weakened(self):
        def all_evidence_errors(policy, question_contract):
            run_errors = validate_simulation_run(
                self.run, question=self.question, policy=policy, question_contract=question_contract,
                run_contract=self.contracts["simulation_run.contract.json"], project_id="the-myr-singularity",
                load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="creation",
            )
            result_errors = validate_simulation_result(
                self.result, run=self.run, policy=policy, question=self.question, question_contract=question_contract,
                result_contract=self.contracts["simulation_result.contract.json"], taxonomy_ids=self.taxonomy,
                load_reference=self.loader, project_id="the-myr-singularity", fingerprint_for_version=self.fingerprint,
                lifecycle_mode="creation",
            )
            comparison_errors = validate_comparison_result(
                self.comparison, baseline_run=self.baseline_run, candidate_run=self.run,
                baseline_result=self.baseline_result, candidate_result=self.result, policy=policy,
                question=self.question, question_contract=question_contract,
                comparison_contract=self.contracts["comparison_result.contract.json"],
                run_contract=self.contracts["simulation_run.contract.json"],
                result_contract=self.contracts["simulation_result.contract.json"], project_id="the-myr-singularity",
                taxonomy_ids=self.taxonomy, load_reference=self.loader, fingerprint_for_version=self.fingerprint,
                lifecycle_mode="creation",
            )
            return run_errors, result_errors, comparison_errors

        cases = []
        changed_count = copy.deepcopy(self.contracts["simulation_question.contract.json"])
        changed_count["required_fields"]["compared_versions"]["exact_item_count"] = 1
        cases.append((self.policy, changed_count, "supplied question_contract does not match"))
        changed_required = copy.deepcopy(self.contracts["simulation_question.contract.json"])
        del changed_required["required_fields"]["question_text"]
        cases.append((self.policy, changed_required, "supplied question_contract does not match"))
        changed_identity = copy.deepcopy(self.contracts["simulation_question.contract.json"])
        changed_identity["contract_id"] = "simulation-question-contract-wrong"
        cases.append((self.policy, changed_identity, "supplied question_contract does not match"))
        stale_policy = copy.deepcopy(self.policy)
        stale_policy["references"]["simulation_question_contract"]["content_fingerprint"] = "artifact-content-sha256-v1:wrong"
        cases.append((stale_policy, self.contracts["simulation_question.contract.json"], "policy simulation_question_contract reference content fingerprint does not match resolved artifact"))
        for policy, contract, expected in cases:
            with self.subTest(expected=expected):
                for errors in all_evidence_errors(policy, contract):
                    self.assertTrue(any(expected in error for error in errors), errors)

    def test_evidence_contract_authority_cannot_be_caller_weakened(self):
        cases = (
            (
                "run", "simulation_run.contract.json", "run_contract",
                self.run, self.check_run,
                lambda contract: contract.__setitem__("semantic_override", True),
                lambda contract: contract["required_fields"].pop("run_id"),
                lambda contract: contract["required_fields"]["status"].__setitem__("allowed_values", ["caller_approved"]),
            ),
            (
                "result", "simulation_result.contract.json", "result_contract",
                self.result, self.check_result,
                lambda contract: contract.__setitem__("semantic_override", True),
                lambda contract: contract["required_fields"].pop("result_id"),
                lambda contract: contract["required_fields"]["confidence"].__setitem__("allowed_values", ["caller_approved"]),
            ),
            (
                "comparison", "comparison_result.contract.json", "comparison_contract",
                self.comparison, self.check_comparison,
                lambda contract: contract.__setitem__("semantic_override", True),
                lambda contract: contract["required_fields"].pop("comparison_id"),
                lambda contract: contract["required_fields"]["artifact_type"].__setitem__("allowed_values", ["caller_comparison"]),
            ),
        )
        for label, filename, argument, payload, validate, *mutations in cases:
            recording_mutation = lambda contract: contract["recording_context"]["engine_boundary"].__setitem__("recording_metadata_owner", "engine")
            for mutation_name, mutation in (*zip(("semantic_override", "required_field", "allowed_values"), mutations), ("recording_context", recording_mutation)):
                with self.subTest(artifact=label, mutation=mutation_name):
                    weakened = copy.deepcopy(self.contracts[filename])
                    mutation(weakened)
                    matching_payload = copy.deepcopy(payload)
                    if mutation_name == "required_field":
                        matching_payload.pop({"run": "run_id", "result": "result_id", "comparison": "comparison_id"}[label])
                    elif mutation_name == "allowed_values":
                        if label == "run":
                            matching_payload["status"] = "caller_approved"
                        elif label == "result":
                            matching_payload["confidence"] = "caller_approved"
                        else:
                            matching_payload["artifact_type"] = "caller_comparison"
                    errors = validate(matching_payload, **{argument: weakened})
                    self.assertTrue(any(f"supplied {argument} does not match" in error for error in errors), errors)

        weakened_run = copy.deepcopy(self.contracts["simulation_run.contract.json"])
        weakened_run["semantic_override"] = True
        errors = self.check_comparison(run_contract=weakened_run)
        self.assertTrue(any("supplied run_contract does not match" in error for error in errors), errors)
        weakened_result = copy.deepcopy(self.contracts["simulation_result.contract.json"])
        weakened_result["semantic_override"] = True
        errors = self.check_comparison(result_contract=weakened_result)
        self.assertTrue(any("supplied result_contract does not match" in error for error in errors), errors)

    def test_question_owns_comparison_direction_and_role_coverage(self):
        self.assertEqual([], self.check_question())
        mutations = (
            ("equal", lambda sides: sides.__setitem__("candidate_run_role", sides["baseline_run_role"]), "roles must be distinct"),
            ("missing", lambda sides: sides.pop("candidate_run_role"), "must contain exactly"),
            ("unknown", lambda sides: sides.__setitem__("candidate_run_role", "unknown-role"), "must resolve exactly one"),
            ("partial", lambda sides: sides.__setitem__("baseline_run_role", "unknown-baseline"), "exactly cover"),
        )
        for label, mutate, diagnostic in mutations:
            with self.subTest(label=label):
                question = copy.deepcopy(self.question)
                mutate(question["comparison_sides"])
                errors = validate_simulation_question(
                    question, policy=self.policy,
                    question_contract=self.contracts["simulation_question.contract.json"],
                    project_id="the-myr-singularity", load_reference=self.loader,
                    fingerprint_for_version=self.fingerprint,
                    question_path=canonical_question_path(question["question_id"]),
                )
                self.assertTrue(any(diagnostic in error for error in errors), errors)

    def _coherent_inverse_comparison(self):
        inverse = copy.deepcopy(self.comparison)
        refs = inverse["source_references"]
        refs["baseline_run"], refs["candidate_run"] = refs["candidate_run"], refs["baseline_run"]
        refs["baseline_result"], refs["candidate_result"] = refs["candidate_result"], refs["baseline_result"]
        inverse["baseline"], inverse["candidate"] = inverse["candidate"], inverse["baseline"]

        for delta in inverse["metric_deltas"]:
            delta["baseline_estimate"], delta["candidate_estimate"] = delta["candidate_estimate"], delta["baseline_estimate"]
            baseline = delta["baseline_estimate"]
            candidate = delta["candidate_estimate"]
            if "bins" in baseline:
                delta["mean_absolute_delta"] = candidate["mean"] - baseline["mean"]
                for item, baseline_bin, candidate_bin in zip(delta["bin_proportion_deltas"], baseline["bins"], candidate["bins"]):
                    item["absolute_delta"] = candidate_bin["proportion"] - baseline_bin["proportion"]
            else:
                delta["absolute_delta"] = candidate["probability"] - baseline["probability"]
                if baseline["probability"]:
                    delta["relative_delta"] = delta["absolute_delta"] / baseline["probability"]
                    delta["relative_delta_applicable"] = True
                else:
                    delta.pop("relative_delta", None)
                    delta["relative_delta_applicable"] = False
        deltas = {(item["metric_id"], item["target_turn"]): item for item in inverse["metric_deltas"]}
        for claim in inverse["evidence_claims"]:
            if claim.get("claim_type") == "comparison_delta":
                claim["comparison"] = copy.deepcopy(deltas[(claim["metric_id"], claim["target_turn"])])
        return inverse

    def test_fully_coherent_inverse_comparison_is_rejected_by_question_direction(self):
        inverse = self._coherent_inverse_comparison()
        errors = self.check_comparison(
            inverse, baseline_run=self.run, candidate_run=self.baseline_run,
            baseline_result=self.result, candidate_result=self.baseline_result,
        )
        self.assertTrue(any("baseline Run role does not match Question comparison_sides" in error for error in errors), errors)
        self.assertTrue(any("candidate Run role does not match Question comparison_sides" in error for error in errors), errors)

    def test_question_identity_and_canonical_path_are_fail_closed(self):
        self.assertEqual([], self.check_question())
        invalid_ids = (
            "", "   ", "Question-001", "question_001", "question/001",
            "question.001", "-question", "question-", "question--001",
        )
        for question_id in invalid_ids:
            with self.subTest(question_id=question_id):
                question = copy.deepcopy(self.question)
                question["question_id"] = question_id
                errors = validate_simulation_question(
                    question, policy=self.policy,
                    question_contract=self.contracts["simulation_question.contract.json"],
                    project_id="the-myr-singularity", load_reference=self.loader,
                    fingerprint_for_version=self.fingerprint,
                    question_path=canonical_question_path(self.question["question_id"]),
                )
                self.assertTrue(any("lowercase kebab-case identity" in error for error in errors), errors)
        omitted_path_errors = validate_simulation_question(
            self.question, policy=self.policy,
            question_contract=self.contracts["simulation_question.contract.json"],
            project_id="the-myr-singularity", load_reference=self.loader,
            fingerprint_for_version=self.fingerprint,
            question_path=None,
        )
        self.assertIn("question source path must be a non-empty caller-supplied string", omitted_path_errors)
        errors = validate_simulation_question(
            self.question, policy=self.policy,
            question_contract=self.contracts["simulation_question.contract.json"],
            project_id="the-myr-singularity", load_reference=self.loader,
            fingerprint_for_version=self.fingerprint,
            question_path="workshop/projects/the-myr-singularity/simulation/questions/other.json",
        )
        self.assertIn("question source path does not match the canonical path derived from question_id", errors)
        self.assertEqual(
            "workshop/projects/the-myr-singularity/simulation/questions/question-001-mana-color.json",
            canonical_question_path(self.question["question_id"]),
        )

    def test_removed_source_state_is_strictly_typed(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        record = next(item for item in registry["records"] if item["card_name"] == "Command Tower")
        records = {record["oracle_id"]: record}
        source = {"source_id": "tower", "oracle_id": record["oracle_id"], "online": True, "tapped": False}
        shared = {"commander_colors": ["W", "U", "B", "R", "G"]}
        kwargs = {
            "source_records": records,
            "candidate_source_id": "tower",
            "condition_state": shared,
            "runtime_authority": self.runtime_authority,
        }
        absent = observe_source_capability(source_states=[source], **kwargs)
        explicit_false = observe_source_capability(source_states=[{**source, "removed": False}], **kwargs)
        explicit_true = observe_source_capability(source_states=[{**source, "removed": True}], **kwargs)
        self.assertEqual(absent, explicit_false)
        self.assertTrue(absent["survives"])
        self.assertEqual([], explicit_true["source_capability"])
        self.assertFalse(explicit_true["survives"])
        for invalid in ("yes", 1, 0, 1.0, None, [], {}):
            with self.subTest(removed=invalid):
                with self.assertRaisesRegex(ValueError, "removed state must be a boolean"):
                    observe_source_capability(source_states=[{**source, "removed": invalid}], **kwargs)
        for field in ("online", "tapped"):
            for invalid in ("yes", 1, 0, 1.0, None, [], {}):
                with self.subTest(field=field, value=invalid):
                    malformed = {**source, field: invalid}
                    with self.assertRaisesRegex(ValueError, "requires explicit online and tapped state"):
                        observe_source_capability(source_states=[malformed], **kwargs)

    def test_lifecycle_contract_authority_cannot_be_caller_weakened(self):
        weakened = copy.deepcopy(self.contracts["simulation_question_lifecycle.contract.json"])
        del weakened["required_fields"]["recorded_evidence"]
        errors = validate_simulation_question_lifecycle(
            self.lifecycle, question=self.question, lifecycle_contract=weakened,
            project_id="the-myr-singularity", load_reference=self.loader, policy=self.policy,
            question_contract=self.contracts["simulation_question.contract.json"],
            fingerprint_for_version=self.fingerprint,
        )
        self.assertIn("supplied lifecycle_contract does not match the canonical v1 lifecycle contract", errors)

    def test_persistence_lifecycle_requires_canonical_consistent_recording(self):
        candidate = copy.deepcopy(self.run); candidate["status"] = "executed"
        baseline = copy.deepcopy(self.baseline_run); baseline["status"] = "executed"
        candidate_path = "fixture-lifecycle-candidate"; baseline_path = "fixture-lifecycle-baseline"
        self.documents[candidate_path] = candidate; self.documents[baseline_path] = baseline
        lifecycle = copy.deepcopy(self.lifecycle)
        lifecycle["state"] = "runs_recorded"
        lifecycle["recorded_evidence"] = {
            "runs": [
                {"id": baseline["run_id"], "path": baseline_path, "content_fingerprint": artifact_content_fingerprint(baseline)},
                {"id": candidate["run_id"], "path": candidate_path, "content_fingerprint": artifact_content_fingerprint(candidate)},
            ],
            "results": [], "comparison": None,
        }
        kwargs = dict(question=self.question, policy=self.policy, question_contract=self.contracts["simulation_question.contract.json"], run_contract=self.contracts["simulation_run.contract.json"], project_id="the-myr-singularity", load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="persistence", lifecycle=lifecycle, lifecycle_contract=self.contracts["simulation_question_lifecycle.contract.json"])
        self.assertEqual([], validate_simulation_run(candidate, lifecycle_path="workshop/projects/the-myr-singularity/simulation/lifecycle/question-001-mana-color.json", **kwargs))
        self.assertIn("persistence lifecycle mode requires the canonical lifecycle artifact and contract", validate_simulation_run(candidate, lifecycle_path="elsewhere.json", **kwargs))
        lifecycle["question_content_fingerprint"] = "artifact-content-sha256-v1:wrong"
        self.assertIn("lifecycle question_content_fingerprint does not match immutable Question", validate_simulation_run(candidate, lifecycle_path="workshop/projects/the-myr-singularity/simulation/lifecycle/question-001-mana-color.json", **kwargs))

    def test_all_nine_policy_measurement_contracts_are_complete(self):
        self.assertEqual([], validate_policy_metric_contracts(self.policy))
        actual = {metric["metric_id"]: metric["measurement_contract"] for metric in self.policy["metric_catalog"]["metrics"]}
        self.assertEqual(actual, METRIC_MEASUREMENT_CONTRACTS)

    def test_metric_measurement_contract_rejects_every_b02_drift(self):
        cases = (
            ("missing_contract", "keepable_opening_hand_rate", lambda contract: contract.clear()),
            ("population_identity", "keepable_opening_hand_rate", lambda contract: contract["population"].__setitem__("id", "successful_iterations")),
            ("conditional_population", "keepable_opening_hand_rate", lambda contract: contract["population"].__setitem__("conditional_exclusion_permitted", True)),
            ("iteration_range", "keepable_opening_hand_rate", lambda contract: contract["population"]["iteration_index_range"].__setitem__("first", 2)),
            ("denominator", "keepable_opening_hand_rate", lambda contract: contract["sample_size_rule"].__setitem__("source", "successful_iterations")),
            ("skippable_observation_failure", "keepable_opening_hand_rate", lambda contract: contract["population"].__setitem__("observation_failure", "exclude_iteration")),
            ("target_turn", "land_drop_success_by_turn", lambda contract: contract.__setitem__("target_turn", 5)),
            ("post_mulligan_keepability", "keepable_opening_hand_rate", lambda contract: contract["observation_point"].__setitem__("before_mulligan", False)),
            ("zero_land_threshold", "zero_land_hand_rate", lambda contract: contract["event"].__setitem__("land_count", 1)),
            ("one_land_threshold", "one_land_hand_rate", lambda contract: contract["event"].__setitem__("land_count", 2)),
            ("excessive_land_threshold", "excessive_land_hand_rate", lambda contract: contract["event"].__setitem__("minimum_land_count", 5)),
            ("keep_rule_redirect", "keepable_opening_hand_rate", lambda contract: contract["event"].__setitem__("keep_rule_id", "other-rule")),
            ("land_drop_not_cumulative", "land_drop_success_by_turn", lambda contract: contract["event"].__setitem__("id", "legal_land_drop_on_target_turn")),
            ("ramp_castability", "ramp_access_by_turn", lambda contract: contract["event"].__setitem__("requires_castability", True)),
            ("ramp_deployment", "ramp_access_by_turn", lambda contract: contract["event"].__setitem__("requires_deployment", True)),
            ("colorless_included", "distinct_commander_colors_by_turn", lambda contract: contract["value"].__setitem__("excluded_colors", [])),
            ("color_domain_changed", "distinct_commander_colors_by_turn", lambda contract: contract["value"].__setitem__("colors", ["W", "U", "B", "R"])),
            ("source_capability_drift", "distinct_commander_colors_by_turn", lambda contract: contract["value"].__setitem__("projection", "spendable_mana")),
            ("five_color_spendable", "five_color_availability_by_turn", lambda contract: contract["event"].__setitem__("requires_simultaneous_spendable_mana", True)),
            ("five_color_castability", "five_color_availability_by_turn", lambda contract: contract["event"].__setitem__("requires_commander_castability", True)),
            ("five_color_projection", "five_color_availability_by_turn", lambda contract: contract["event"].__setitem__("projection", "spendable_mana")),
            ("five_color_colorless", "five_color_availability_by_turn", lambda contract: contract["event"].__setitem__("excluded_colors", [])),
            ("commander_unsupported_resource", "commander_castability_by_turn", lambda contract: contract["event"].__setitem__("alternate_or_unmodeled_resources_allowed", True)),
            ("commander_tax_drift", "commander_castability_by_turn", lambda contract: contract["event"].__setitem__("commander_tax_generic", 1)),
            ("commander_previous_cast_drift", "commander_castability_by_turn", lambda contract: contract["event"].__setitem__("previous_commander_casts", 1)),
            ("commander_card_reference_drift", "commander_castability_by_turn", lambda contract: contract["event"]["commander_card_reference"].__setitem__("mana_cost", "{4}")),
        )
        for name, metric_id, mutate in cases:
            with self.subTest(name=name):
                policy = copy.deepcopy(self.policy)
                metric = next(item for item in policy["metric_catalog"]["metrics"] if item["metric_id"] == metric_id)
                mutate(metric["measurement_contract"])
                self.assertTrue(validate_policy_metric_contracts(policy))

    def test_result_and_comparison_cannot_redefine_policy_metric_semantics(self):
        result = copy.deepcopy(self.result)
        result["metrics"][0]["measurement_contract"] = {"population": "conditional"}
        self.assertIn("result Bernoulli metric must not redefine Policy measurement semantics", self.check_result(result))
        comparison = copy.deepcopy(self.comparison)
        comparison["metric_deltas"][0]["event"] = {"id": "different"}
        self.assertIn("comparison metric delta must not redefine Policy measurement semantics", self.check_comparison(comparison))

    def test_result_top_level_artifact_boundary_is_exact(self):
        for field in (
            "measurement_contract", "event", "value", "observation_point",
            "denominator_semantics", "sample_size_rule", "metric_definition",
            "arbitrary_unknown_field",
        ):
            with self.subTest(field=field):
                result = copy.deepcopy(self.result)
                result[field] = {"synthetic": True}
                self.assertIn(
                    f"result has unregistered top-level fields: {field}",
                    self.check_result(result),
                )

    def test_comparison_top_level_artifact_boundary_is_exact(self):
        for field in (
            "measurement_contract", "event", "value", "observation_point",
            "denominator_semantics", "sample_size_rule", "metric_definition",
            "arbitrary_unknown_field",
        ):
            with self.subTest(field=field):
                comparison = copy.deepcopy(self.comparison)
                comparison[field] = {"synthetic": True}
                self.assertIn(
                    f"comparison has unregistered top-level fields: {field}",
                    self.check_comparison(comparison),
                )

    def test_result_and_comparison_still_require_registered_fields(self):
        result = copy.deepcopy(self.result)
        del result["result_id"]
        self.assertIn("result is missing required field 'result_id'", self.check_result(result))
        comparison = copy.deepcopy(self.comparison)
        del comparison["comparison_id"]
        self.assertIn("comparison is missing required field 'comparison_id'", self.check_comparison(comparison))

    def test_optional_commander_metric_uses_complete_run_population(self):
        for sample_size in (99999, 100001):
            with self.subTest(sample_size=sample_size):
                result = copy.deepcopy(self.result)
                result["metrics"].append({
                    "metric_id": "commander_castability_by_turn", "target_turn": 3,
                    "raw_count": 1, "sample_size": sample_size, "probability": 1 / sample_size,
                    "confidence_interval": {"method": "wilson_score_interval", "level": 0.95, "lower": 0.0, "upper": 0.000057},
                })
                self.assertIn("result Bernoulli metric raw_count/sample_size is invalid", self.check_result(result))

    def test_alias_and_canonical_names_have_equal_fingerprint(self):
        alias = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/versions/v1.1.json"])
        canonical = copy.deepcopy(alias)
        for entry in canonical["main_deck"]:
            if entry["name"] == "Bridge of Khazad-dûm": entry["name"] = "Ensnaring Bridge"
        self.assertEqual(self.fingerprint(alias), self.fingerprint(canonical))

    def test_ambiguous_alias_resolution_fails(self):
        fact = copy.deepcopy(resolve_card_fact("Bridge of Khazad-dûm", self.cards["cards"]))
        fact["oracle_id"] = "00000000-0000-0000-0000-000000000000"
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_card_fact("Bridge of Khazad-dûm", self.cards["cards"] + [fact])

    def test_generic_content_identity_rejects_bom_duplicate_and_nan(self):
        for payload in (b'\xef\xbb\xbf{}', b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(ValueError): load_strict_json_bytes(payload)
        self.assertEqual(artifact_content_fingerprint({"b": 2, "a": 1}), artifact_content_fingerprint({"a": 1, "b": 2}))

    def test_independent_artifact_content_fingerprint_kat(self):
        # Category A: literal canonical bytes and hashlib digest, independent of identity.py.
        value = {"z": [3, {"e": True}], "a": 1}
        canonical_bytes = b'{"a":1,"z":[3,{"e":true}]}'
        expected = "artifact-content-sha256-v1:7e62975c0d2c5c5cb8c28746a6246be2e2c7ee2f138f55d5e9cbbcc842aeba3b"
        self.assertEqual(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8"), canonical_bytes)
        self.assertEqual("artifact-content-sha256-v1:" + hashlib.sha256(canonical_bytes).hexdigest(), expected)
        self.assertEqual(artifact_content_fingerprint(value), expected)

    def test_independent_canonical_deck_fingerprint_kat(self):
        # Category A: manually written v2 serialization with alias/canonical equivalent inputs.
        facts = [
            {"name": "Commander", "oracle_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"},
            {"name": "Alpha", "original_decklist_name": "Alpha Alias", "oracle_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
            {"name": "Beta", "oracle_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
        ]
        alias = {"commander": {"name": "Commander", "quantity": 1}, "main_deck": [{"name": "Alpha Alias", "quantity": 2}, {"name": "Beta", "quantity": 1}]}
        canonical = {"commander": {"name": "Commander", "quantity": 1}, "main_deck": [{"name": "Alpha", "quantity": 2}, {"name": "Beta", "quantity": 1}]}
        serialization = "commander\n1 cccccccc-cccc-cccc-cccc-cccccccccccc\n\x1e\nlibrary\n2 aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa\n1 bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        expected = "deck-content-sha256-canonical-v2:079460c9c4b8f3f74d28a2fc5f7de38d76db15724892fd991cc335fa6467dc77"
        self.assertEqual("deck-content-sha256-canonical-v2:" + hashlib.sha256(serialization.encode("utf-8")).hexdigest(), expected)
        self.assertEqual(deck_content_fingerprint(alias, facts), expected)
        self.assertEqual(deck_content_fingerprint(canonical, facts), expected)

    def test_independent_seed_and_iteration_seed_kats(self):
        # Category A: payloads and first-eight-byte conversion are visible here, not delegated to production.
        run_payload = "question-fp\x1fpolicy-fp\x1fdeck-fp\x1fbaseline"
        expected_run = 5245491670639618402
        self.assertEqual(int.from_bytes(hashlib.sha256(run_payload.encode("utf-8")).digest()[:8], "big"), expected_run)
        self.assertEqual(derive_run_seed("question-fp", "policy-fp", "deck-fp", "baseline"), expected_run)
        iteration_payload = "sim-iteration-seed-sha256-v1\x1f5245491670639618402\x1f7"
        expected_iteration = 14614229110605169793
        self.assertEqual(int.from_bytes(hashlib.sha256(iteration_payload.encode("utf-8")).digest()[:8], "big"), expected_iteration)
        self.assertEqual(derive_iteration_seed(expected_run, 7), expected_iteration)

    def test_independent_pcg_bounded_and_shuffle_kats(self):
        # Category A: IndependentPCG32 provides the reference stream and rejection trace.
        expected_stream = [1669314965, 1897367909, 478990646, 3341671233, 3520501898, 1655012689]
        reference = IndependentPCG32(42); self.assertEqual([reference.next_u32() for _ in range(6)], expected_stream)
        production = PCG32(42); self.assertEqual([production.next_u32() for _ in range(6)], expected_stream)
        expected_bounded, expected_consumption = 145482253, [1534532241, 2292965902]
        value, consumption = IndependentPCG32(1).bounded_with_consumption(2147483649)
        self.assertEqual((value, consumption), (expected_bounded, expected_consumption))
        self.assertEqual(PCG32(1).bounded(2147483649), expected_bounded)
        expected_shuffle = ["c", "e", "a", "g", "h", "d", "b", "i", "f"]
        self.assertEqual(IndependentPCG32(42).shuffle(list("abcdefghi")), expected_shuffle)
        self.assertEqual(PCG32(42).shuffle(list("abcdefghi")), expected_shuffle)

    def test_same_path_mutations_break_complete_provenance(self):
        paths = [
            "workshop/projects/the-myr-singularity/simulation/simulation_policy.json",
            "workshop/projects/the-myr-singularity/simulation/questions/question-001-mana-color.json",
            "workshop/projects/the-myr-singularity/simulation/card_semantics.json",
            "workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json",
            "workshop/card-data/cards.json",
            "workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json",
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json",
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_run.contract.json",
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_result.contract.json",
            "workshop/projects/the-myr-singularity/simulation/contracts/comparison_result.contract.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                original = self.documents[path]
                changed = copy.deepcopy(original)
                changed["audit_mutation"] = True
                self.documents[path] = changed
                self.assertTrue(any("content fingerprint" in error or "expected artifact" in error for error in self.check_run()))
                self.documents[path] = original

    def test_v6_seed_and_iteration_vectors(self):
        seed = derive_run_seed(self.run["semantic_dependencies"]["question"]["content_fingerprint"], self.run["semantic_dependencies"]["policy"]["content_fingerprint"], self.run["deck_content_fingerprint"], self.run["run_role"])
        self.assertEqual(seed, self.run["seed"])
        self.assertEqual(derive_iteration_seed(seed, 1), 18286694482864418478)
        self.assertEqual(derive_iteration_seed(seed, 2), 9245378503593541660)

    def test_trace_kat_freezes_canonical_expansion_and_opening_shuffle(self):
        kat = load(REPO_ROOT / "workshop" / "tests" / "fixtures" / "simulation" / "simulation_iteration_trace.v1.json")
        version = self.documents["workshop/projects/the-myr-singularity/versions/v1.1.json"]
        from workshop.shared.identity import canonical_deck_tokens
        tokens = canonical_deck_tokens(version, self.cards["cards"])
        self.assertEqual(len(tokens), kat["canonical_library"]["count"])
        self.assertEqual(tokens[:3], kat["canonical_library"]["first_tokens"])
        self.assertEqual(tokens[-3:], kat["canonical_library"]["last_tokens"])
        self.assertEqual(derive_iteration_seed(kat["run_seed"], kat["iteration_index"]), kat["iteration_seed"])
        self.assertEqual(PCG32(kat["iteration_seed"]).shuffle(tokens)[:7], kat["first_opening_hand"])
        self.assertEqual(
            kat["required_cases"],
            [
                "ordinary_keep", "rejected_free_mulligan_continues_same_rng_stream", "london_bottoming",
                "bounded_rng_rejection_consumption", "deep_london_remaining_lands", "level_2_land_tie_break",
                "level_2_ramp_deployment_order", "level_2_payment_tie_break", "mana_creature_online_delay",
                "urzas_saga_removal_before_end_of_turn_observation",
            ],
        )

    def test_iteration_stream_is_continuous_across_mulligans(self):
        rng = PCG32(derive_iteration_seed(self.run["seed"], 1))
        first = rng.shuffle(range(10)); second = rng.shuffle(range(10))
        reset_second = PCG32(derive_iteration_seed(self.run["seed"], 1)).shuffle(range(10))
        self.assertNotEqual(second, reset_second)
        self.assertNotEqual(first, second)

    def test_full_library_second_shuffle_literal_kat(self):
        from workshop.shared.identity import canonical_deck_tokens
        version = self.documents["workshop/projects/the-myr-singularity/versions/v1.1.json"]
        tokens = canonical_deck_tokens(version, self.cards["cards"])
        rng = IndependentPCG32(3124231310674535409)
        first = rng.shuffle(tokens)[:7]
        second = rng.shuffle(tokens)[:7]
        self.assertEqual(first, [
            "02f16726-f2f6-4943-b71a-93f8e26251d3#1", "d98b4250-3492-4864-9c4c-42db09b3ccd4#1",
            "8dc067bf-f78f-4ac4-b6e7-b305c42cf0bc#1", "e5e8e116-10fe-48b0-b3d8-6edb39bd5f90#1",
            "d5ad26cc-2bdb-46b7-b8bf-dd099d5fa09b#1", "4b515bb0-f275-4400-8032-3173b799ab40#1",
            "8b52f30c-5e38-4333-88ab-901b37105b36#1",
        ])
        self.assertEqual(second, [
            "65986c1b-8e51-4604-b685-d82fa7d1263a#1", "4c6a0c30-b547-4eff-8ff4-0ca25803c076#1",
            "42a3855d-25ab-45b3-9e5d-9a0f3da35a05#1", "2a838818-d590-4374-9a63-d9e6381a0f0d#1",
            "1787ac2f-762d-4f3a-b7e5-12db6d3d470d#1", "da3b17a2-e1e1-44e9-b9b1-ae54a92037db#1",
            "e87906d2-db1a-4e19-b910-adb4eb339945#1",
        ])

    def test_mulligan_transition_freezes_free_london_and_force_keep_boundaries(self):
        transition = self.policy["mulligan_policy"]["executable_state_transition"]
        self.assertEqual(transition["canonical_library"], "99 physical card-instance tokens in canonical token order")
        self.assertEqual(transition["initial_shuffle"], "fisher_yates_full_library_with_iteration_pcg32")
        self.assertEqual(transition["rejected_hand_transition"][:4], [
            "return_all_physical_tokens_to_eligibility",
            "reconstruct_full_library_in_canonical_instance_token_order",
            "increment_mulligans_taken_before_recording_next_attempt",
            "fisher_yates_full_library_with_same_continuous_iteration_pcg32",
        ])
        self.assertIn("fisher_yates_full_library_with_same_continuous_iteration_pcg32", transition["rejected_hand_transition"])
        self.assertFalse(transition["rng_reset_permitted"])
        self.assertEqual(transition["force_keep_when_mulligans_taken_equals"], 6)
        self.assertEqual(transition["bottom_count"], "max(0, mulligans_taken - free_mulligans)")
        self.assertFalse(transition["bottoming_consumes_rng"])

    def test_deep_london_bottoming_and_canonical_ties(self):
        hand = {"bottom_count": 5, "cards": ["b#1", "a#1", "land-c#1", "land-a#1", "land-b#1", "land-d#1", "land-e#1"]}
        mana = {"b#1": 6, "a#1": 3}
        selected = select_bottom_tokens(hand, mana_value=lambda t: mana.get(t, 0), is_land=lambda t: t.startswith("land"))
        self.assertEqual(selected, ["b#1", "a#1", "land-a#1", "land-b#1", "land-c#1"])

    def test_independent_bottoming_priority_kat(self):
        # Category A: literal expected order covers MV, oracle/ordinal, land-above-three, and fallback.
        hand = {"bottom_count": 6, "cards": ["b#2", "a#2", "a#1", "land-d#1", "land-c#1", "land-b#1", "land-a#1", "land-e#1"]}
        mana = {"b#2": 5, "a#2": 4, "a#1": 4}
        expected = ["b#2", "a#1", "a#2", "land-a#1", "land-b#1", "land-c#1"]
        self.assertEqual(select_bottom_tokens(hand, mana_value=lambda token: mana.get(token, 0), is_land=lambda token: token.startswith("land")), expected)

    def test_level_two_land_ramp_and_payment_ties(self):
        land = select_land([
            {"oracle_id":"b", "colors":["U"], "permanent":True},
            {"oracle_id":"a", "colors":["U"], "permanent":True},
        ], set(), 6, 1)
        self.assertEqual(land["oracle_id"], "a")
        ramp = select_payable_ramp([{"oracle_id":"creature","payable":True,"same_turn_online_noncreature":False,"output_units":1}, {"oracle_id":"rock","payable":True,"same_turn_online_noncreature":True,"output_units":1}])
        self.assertEqual(ramp["oracle_id"], "rock")
        payment = choose_payment([{"flexible_generic_spend":1,"tapped_source_count":1,"source_outputs":[("z",1,"W")]}, {"flexible_generic_spend":0,"tapped_source_count":2,"source_outputs":[("a",1,"C"), ("b",1,"C")]}])
        self.assertEqual(payment["flexible_generic_spend"], 0)

    def test_level_two_policy_preserves_urza_and_unsupported_boundaries(self):
        order = self.policy["level_2_sequencing"]["turn_order"]
        self.assertLess(order.index("resolve_pending_time_dependent_removals"), order.index("record_end_of_turn_observations"))
        self.assertIn("cannot be selected", self.policy["level_2_sequencing"]["unsupported_actions"])

    def test_independent_level_two_hand_auditable_kats(self):
        # Category A: hand-written scenario inputs and actions; no second simulation engine is introduced.
        city = {"oracle_id": "city", "colors": ["W", "U", "B", "R", "G"], "five_color_source": True, "permanent": True}
        island = {"oracle_id": "island", "colors": ["U"], "permanent": True}
        saga = {"oracle_id": "urza", "colors": ["C"], "permanent": False, "remaining_availability": 1}
        self.assertEqual(select_land([city, island, saga], set(), 6, 1)["oracle_id"], "city")
        self.assertEqual(select_land([island, saga], {"C", "W", "U", "B", "R", "G"}, 6, 2)["oracle_id"], "island")
        sol = {"oracle_id": "sol-ring", "payable": True, "same_turn_online_noncreature": True, "output_units": 2, "color_flexibility": 0, "mana_value": 1}
        copper = {"oracle_id": "copper-myr", "payable": True, "same_turn_online_noncreature": False, "output_units": 1, "color_flexibility": 1, "mana_value": 2, "online_timing": "next_controller_turn"}
        self.assertEqual(select_payable_ramp([copper, sol])["oracle_id"], "sol-ring")
        self.assertEqual(copper["online_timing"], "next_controller_turn")
        self.assertIn("offset 2", self.policy["level_2_sequencing"]["urzas_saga_final_chapter_timing"])
        self.assertIn("before end-of-turn observation", self.policy["level_2_sequencing"]["urzas_saga_final_chapter_timing"])
        payment = [{"flexible_generic_spend": 0, "tapped_source_count": 2, "source_outputs": [("b", 1, "C"), ("a", 1, "W")]}, {"flexible_generic_spend": 0, "tapped_source_count": 2, "source_outputs": [("a", 1, "C"), ("b", 1, "W")]}]
        self.assertEqual(choose_payment(payment)["source_outputs"], [("a", 1, "C"), ("b", 1, "W")])

    def test_result_rejects_empty_missing_duplicate_and_extra_metrics(self):
        empty = copy.deepcopy(self.result); empty["metrics"] = []
        self.assertIn("result metrics must be non-empty", self.check_result(empty))
        missing = copy.deepcopy(self.result); missing["metrics"] = missing["metrics"][1:]
        self.assertIn("result metrics must exactly equal the Run selected_metrics ordered set", self.check_result(missing))
        duplicate = copy.deepcopy(self.result); duplicate["metrics"].append(copy.deepcopy(duplicate["metrics"][0]))
        self.assertIn("result metrics contain duplicate metric keys", self.check_result(duplicate))
        extra = copy.deepcopy(self.result); extra["metrics"].append(copy.deepcopy(extra["metrics"][0])); extra["metrics"][-1]["metric_id"]="unknown"
        self.assertIn("result metrics must exactly equal the Run selected_metrics ordered set", self.check_result(extra))

    def test_categorical_shape_rejects_bad_arithmetic_bins_and_wilson(self):
        result = copy.deepcopy(self.result); categorical=next(m for m in result["metrics"] if m["metric_id"]=="distinct_commander_colors_by_turn")
        categorical["bins"].pop(); categorical["confidence_interval"]={"method":"wilson_score_interval"}
        errors=self.check_result(result)
        self.assertTrue(any("bins" in error for error in errors)); self.assertIn("categorical metric must not define a Wilson interval", errors)

    def test_comparison_rejects_empty_missing_duplicate_and_asymmetric_optional(self):
        empty=copy.deepcopy(self.comparison); empty["metric_deltas"]=[]
        self.assertIn("comparison metric_deltas must be non-empty", self.check_comparison(empty))
        missing=copy.deepcopy(self.comparison); missing["metric_deltas"].pop()
        self.assertIn("comparison metric_deltas must exactly equal the selected metric set in order", self.check_comparison(missing))
        duplicate=copy.deepcopy(self.comparison); duplicate["metric_deltas"].append(copy.deepcopy(duplicate["metric_deltas"][0]))
        self.assertIn("comparison metric_deltas contain duplicate metric keys", self.check_comparison(duplicate))
        optional=copy.deepcopy(self.result); optional["metrics"].append({"metric_id":"commander_castability_by_turn","target_turn":3,"raw_count":1,"sample_size":100000,"probability":0.00001,"confidence_interval":{"method":"wilson_score_interval","level":0.95,"lower":0.0,"upper":0.000057}})
        self.assertTrue(any("result metrics must exactly equal the Run selected_metrics ordered set" in error for error in self.check_comparison(candidate_result=optional)))

    def test_unregistered_quality_synonym_cannot_be_a_claim(self):
        result=copy.deepcopy(self.result); result["evidence_claims"][0]["subject"]="superior_consistency_and_reliability"
        self.assertIn("evidence claim subject is not permitted", self.check_result(result))

    def test_result_rejects_top_level_reasoning_interpretation(self):
        result = copy.deepcopy(self.result); result["reasoning_interpretation"] = {"claim": "forbidden"}
        self.assertIn("reserved lifecycle field is not permitted at $.reasoning_interpretation", self.check_result(result))

    def test_result_claim_rejects_arbitrary_extra_text_structurally(self):
        result = copy.deepcopy(self.result); result["evidence_claims"][0]["text"] = "v1.1 delivers superior consistency and reliability"
        self.assertIn("evidence claim has fields outside its exact registered shape", self.check_result(result))

    def test_result_rejects_nested_reasoning_interpretation(self):
        result = copy.deepcopy(self.result); result["metadata"] = {"nested": {"reasoning_interpretation": {}}}
        self.assertIn("reserved lifecycle field is not permitted at $.metadata.nested.reasoning_interpretation", self.check_result(result))

    def test_result_rejects_product_owner_decision(self):
        result = copy.deepcopy(self.result); result["product_owner_decision"] = {"decision_id": "not-permitted"}
        self.assertIn("reserved lifecycle field is not permitted at $.product_owner_decision", self.check_result(result))

    def test_comparison_rejects_reserved_lifecycle_fields(self):
        for key in ("reasoning_interpretation", "product_owner_decision"):
            with self.subTest(key=key):
                comparison = copy.deepcopy(self.comparison); comparison[key] = {"forbidden": True}
                self.assertIn(f"reserved lifecycle field is not permitted at $.{key}", self.check_comparison(comparison))

    def test_result_rejects_unknown_failure_pattern_category(self):
        result = copy.deepcopy(self.result); result["failure_patterns"][0]["category_id"] = "unknown-category"
        self.assertIn("failure pattern references undefined category", self.check_result(result))

    def test_run_rejects_deck_fingerprint_mismatch(self):
        run = copy.deepcopy(self.run); run["deck_content_fingerprint"] = "deck-content-sha256-canonical-v2:" + "0" * 64
        self.assertIn("run fingerprint does not match DeckVersion", self.check_run(run))

    def test_run_rejects_missing_seed(self):
        run = copy.deepcopy(self.run); del run["seed"]
        errors = self.check_run(run)
        self.assertIn("run is missing required field 'seed'", errors)
        self.assertIn("run seed must be unsigned 64-bit integer", errors)

    def test_run_rejects_boundary_seed_scenario_and_config_mutations(self):
        cases = (
            ("seed_type", lambda x: x.__setitem__("seed_type", "text"), "run seed_type must be unsigned_64_bit"),
            ("scenario_ref", lambda x: x.__setitem__("scenario_ref", "arbitrary"), "run scenario_ref does not match the resolved policy"),
            ("sequencing_levels_missing", lambda x: x["config"].pop("sequencing_levels"), "run config.sequencing_levels must equal the approved sequence"),
            ("sequencing_levels_bad", lambda x: x["config"].__setitem__("sequencing_levels", ["level_2"]), "run config.sequencing_levels must equal the approved sequence"),
            ("boundary", lambda x: x["explicit_boundary"].__setitem__("carries_interpretation", True), "run explicit_boundary flags must all be false"),
        )
        for _, mutate, expected in cases:
            with self.subTest(expected=expected):
                run = copy.deepcopy(self.run); mutate(run); self.assertIn(expected, self.check_run(run))

    def test_result_and_comparison_reject_true_boundary_flags(self):
        result = copy.deepcopy(self.result); result["explicit_boundary"]["is_gameplay_claim"] = True
        self.assertIn("result explicit_boundary flags must all be false", self.check_result(result))
        comparison = copy.deepcopy(self.comparison); comparison["explicit_boundary"]["is_gameplay_claim"] = True
        self.assertIn("comparison explicit_boundary flags are invalid", self.check_comparison(comparison))

    def test_relative_delta_and_malformed_items_are_validated(self):
        comparison = copy.deepcopy(self.comparison); comparison["metric_deltas"][0].pop("relative_delta")
        comparison["evidence_claims"][0]["comparison"] = comparison["metric_deltas"][0]
        self.assertEqual([], self.check_comparison(comparison))
        bad_relative = copy.deepcopy(self.comparison); bad_relative["metric_deltas"][0]["relative_delta"] = 99
        self.assertIn("comparison relative_delta is invalid", self.check_comparison(bad_relative))
        categorical = next(x for x in self.comparison["metric_deltas"] if x["metric_id"] == "distinct_commander_colors_by_turn")
        bad_categorical = copy.deepcopy(self.comparison); next(x for x in bad_categorical["metric_deltas"] if x["metric_id"] == categorical["metric_id"])["relative_delta"] = 1
        self.assertIn("categorical comparison must not define relative_delta", self.check_comparison(bad_categorical))
        malformed = copy.deepcopy(self.result); malformed["metrics"].append("not-an-object")
        self.assertIn("result metrics must contain only objects", self.check_result(malformed))

    def test_production_modules_do_not_import_validation_modules(self):
        for path in (
            REPO_ROOT / "workshop/shared/identity.py",
            REPO_ROOT / "workshop/shared/simulation_determinism.py",
            REPO_ROOT / "workshop/simulation/instance_validation.py",
            REPO_ROOT / "workshop/analysis/structural_analysis.py",
        ):
            self.assertNotIn("workshop.tests.validation", path.read_text(encoding="utf-8"))

    def test_mana_source_registry_covers_both_versions(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        self.assertEqual([], self.check_registry(registry))

    def test_registry_rejects_unknown_condition_and_missing_life_treatment(self):
        registry = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"])
        profile = next(record for record in registry["records"] if record["card_name"] == "Myr Convert")["activation_groups"][0]["profiles"][0]
        profile["conditions"] = [{"condition_id": "free_text", "params": {}}]
        errors = self.check_registry(registry)
        self.assertTrue(any("invalid structured condition" in error for error in errors))
        registry = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"])
        profile = next(record for record in registry["records"] if record["card_name"] == "Myr Convert")["activation_groups"][0]["profiles"][0]
        profile["payment"]["life"]["treatment"] = "not_applicable"
        errors = self.check_registry(registry)
        self.assertTrue(any("life-cost profile" in error for error in errors))

    def test_registry_rejects_free_text_or_unknown_output_selection(self):
        registry = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"])
        profile = next(record for record in registry["records"] if record["card_name"] == "Myr Convert")["activation_groups"][0]["profiles"][0]
        profile["conditions"] = ["a prose condition"]
        errors = self.check_registry(registry)
        self.assertTrue(any("must be an object" in error for error in errors))
        registry = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"])
        profile = next(record for record in registry["records"] if record["card_name"] == "Myr Convert")["activation_groups"][0]["profiles"][0]
        profile["output_selection"] = "arbitrary_runtime_choice"
        errors = self.check_registry(registry)
        self.assertTrue(any("unregistered execution value" in error for error in errors))

    def test_registry_preserves_supported_and_unsupported_profile_boundaries(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        records = {record["card_name"]: record for record in registry["records"]}
        self.assertTrue(records["Myr Convert"]["activation_groups"][0]["profiles"][0]["supported"])
        self.assertEqual(records["Myr Convert"]["activation_groups"][0]["profiles"][0]["payment"]["life"], {"amount": 2, "treatment": "ignored"})
        self.assertEqual(records["Basalt Monolith"]["activation_groups"][0]["profiles"][0]["natural_untap_model"], "does_not_naturally_untap")
        self.assertFalse(records["Moonsnare Prototype"]["activation_groups"][0]["profiles"][0]["supported"])
        self.assertFalse(records["Springleaf Drum"]["activation_groups"][0]["profiles"][0]["supported"])
        self.assertEqual(records["Three Tree City"]["activation_groups"][0]["profiles"][0]["supported"], True)
        self.assertEqual(records["Three Tree City"]["activation_groups"][0]["profiles"][1]["supported"], False)

    def test_glimmervoid_state_transition_is_closed_and_required(self):
        self.assertEqual(
            self.policy["level_2_sequencing"]["mana_source_resolution"]["state_transition_timing"],
            "registered end-step removal conditions execute after deterministic same-turn development actions and before the applicable end-of-turn observation",
        )
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        glimmervoid = next(record for record in registry["records"] if record["card_name"] == "Glimmervoid")
        self.assertEqual(glimmervoid["state_transitions"], [{
            "event_id": "end_step_remove_unless_condition",
            "condition": {"condition_id": "artifact_controlled", "params": {"minimum_count": 1}},
        }])
        missing = copy.deepcopy(registry)
        next(record for record in missing["records"] if record["card_name"] == "Glimmervoid").pop("state_transitions")
        self.assertIn("Glimmervoid must have exactly the approved end-step artifact-control transition", self.check_registry(missing))
        invalid = copy.deepcopy(registry)
        invalid_transition = next(record for record in invalid["records"] if record["card_name"] == "Glimmervoid")["state_transitions"][0]
        invalid_transition["event_id"] = "arbitrary_event"
        self.assertTrue(any("event_id is not registered" in error for error in self.check_registry(invalid)))

    def test_registry_condition_parameter_values_are_closed(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        cases = (
            ("artifact_zero", "Spire of Industry", "colored", lambda condition: condition["params"].__setitem__("minimum_count", 0)),
            ("generic_negative", "The Mycosynth Gardens", "filter", lambda condition: condition["params"].__setitem__("required_units", -1)),
            ("generic_text", "The Mycosynth Gardens", "filter", lambda condition: condition["params"].__setitem__("required_units", "5")),
            ("tron_wrong", "Urza's Tower", "enhanced", lambda condition: condition["params"]["oracle_ids"].__setitem__(0, "00000000-0000-0000-0000-000000000000")),
            ("tron_duplicate", "Urza's Tower", "enhanced", lambda condition: condition["params"]["oracle_ids"].__setitem__(1, condition["params"]["oracle_ids"][0])),
            ("commander_missing", "Command Tower", "commander-choice", lambda condition: condition["params"].__setitem__("colors", ["W", "U", "B", "R"])),
            ("commander_unknown", "Command Tower", "commander-choice", lambda condition: condition["params"].__setitem__("colors", ["W", "U", "B", "R", "G", "X"])),
            ("saga_end", "Urza's Saga", "bounded-c", lambda condition: condition["params"].__setitem__("end_offset", 3)),
            ("saga_event", "Urza's Saga", "bounded-c", lambda condition: condition["params"].__setitem__("removal_event", "arbitrary_event")),
        )
        for name, card_name, profile_id, mutate in cases:
            with self.subTest(name=name):
                changed = copy.deepcopy(registry)
                profile = next(profile for record in changed["records"] if record["card_name"] == card_name for group in record["activation_groups"] for profile in group["profiles"] if profile["profile_id"] == profile_id)
                mutate(profile["conditions"][0])
                self.assertTrue(self.check_registry(changed))

    def test_registry_rejects_unregistered_fields_at_every_executable_boundary(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        cases = (
            ("top", lambda value: value.__setitem__("engine_hint", "forbidden")),
            ("record_runtime", lambda value: value["records"][0].__setitem__("runtime_override", True)),
            ("record_arbitrary", lambda value: value["records"][0].__setitem__("arbitrary_unknown_field", True)),
            ("deployment", lambda value: value["records"][0]["deployment"].__setitem__("extra", True)),
            ("casting_cost", lambda value: value["records"][0]["deployment"]["casting_cost"].__setitem__("extra", True)),
            ("activation_group", lambda value: value["records"][0]["activation_groups"][0].__setitem__("extra", True)),
            ("profile_oracle", lambda value: value["records"][0]["activation_groups"][0]["profiles"][0].__setitem__("oracle_text_rule", "forbidden")),
            ("profile_runtime", lambda value: value["records"][0]["activation_groups"][0]["profiles"][0].__setitem__("runtime_script", "forbidden")),
            ("payment", lambda value: value["records"][0]["activation_groups"][0]["profiles"][0]["payment"].__setitem__("custom_cost", 1)),
            ("life", lambda value: value["records"][0]["activation_groups"][0]["profiles"][0]["payment"]["life"].__setitem__("extra", True)),
            ("condition", lambda value: next(record for record in value["records"] if record["card_name"] == "Spire of Industry")["activation_groups"][0]["profiles"][1]["conditions"][0].__setitem__("description", "forbidden")),
            ("condition_params", lambda value: next(record for record in value["records"] if record["card_name"] == "Spire of Industry")["activation_groups"][0]["profiles"][1]["conditions"][0]["params"].__setitem__("extra", True)),
            ("transition", lambda value: next(record for record in value["records"] if record["card_name"] == "Glimmervoid")["state_transitions"][0].__setitem__("extra", True)),
            ("transition_condition", lambda value: next(record for record in value["records"] if record["card_name"] == "Glimmervoid")["state_transitions"][0]["condition"].__setitem__("description", "forbidden")),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                changed = copy.deepcopy(registry)
                mutate(changed)
                self.assertTrue(any("unregistered fields" in error for error in self.check_registry(changed)))

    def test_registry_rejects_primitive_domains_and_cross_field_drift(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]

        def record(value, card_name):
            return next(item for item in value["records"] if item["card_name"] == card_name)

        def profile(value, card_name, profile_id):
            return next(
                item for group in record(value, card_name)["activation_groups"] for item in group["profiles"]
                if item["profile_id"] == profile_id
            )

        cases = (
            ("negative_casting_generic", lambda value: record(value, "Island")["deployment"]["casting_cost"].__setitem__("generic", -1)),
            ("negative_payment_generic", lambda value: profile(value, "Prismatic Lens", "filter")["payment"].__setitem__("generic", -1)),
            ("negative_life_amount", lambda value: profile(value, "Myr Convert", "any")["payment"]["life"].__setitem__("amount", -2)),
            ("boolean_numeric", lambda value: profile(value, "Prismatic Lens", "filter").__setitem__("priority", True)),
            ("unknown_cost_color", lambda value: record(value, "Island")["deployment"]["casting_cost"].__setitem__("colored", ["X"])),
            ("unknown_payment_color", lambda value: profile(value, "Prismatic Lens", "filter")["payment"].__setitem__("colored", ["X"])),
            ("output_string", lambda value: profile(value, "Cascading Cataracts", "c").__setitem__("output_capabilities", "C")),
            ("unknown_capability", lambda value: profile(value, "Cascading Cataracts", "c").__setitem__("output_capabilities", ["X"])),
            ("duplicate_capability", lambda value: profile(value, "Cascading Cataracts", "c").__setitem__("output_capabilities", ["C", "C"])),
            ("fixed_multiple_capabilities", lambda value: profile(value, "Cascading Cataracts", "c").__setitem__("output_capabilities", ["C", "W"])),
            ("land_not_land_drop", lambda value: record(value, "Cascading Cataracts")["deployment"].__setitem__("counts_as_land_drop", False)),
            ("nonland_is_land_drop", lambda value: record(value, "Sol Ring")["deployment"].__setitem__("counts_as_land_drop", True)),
            ("mana_creature_noncreature", lambda value: record(value, "Sol Ring").__setitem__("source_kind", "mana_creature")),
            ("filter_payment_mismatch", lambda value: profile(value, "Cascading Cataracts", "filter-five")["conditions"][0]["params"].__setitem__("required_units", 1)),
            ("filter_payment_condition_missing", lambda value: profile(value, "Prismatic Lens", "filter").__setitem__("conditions", [])),
            ("bounded_window_condition_missing", lambda value: profile(value, "Urza's Saga", "bounded-c").__setitem__("conditions", [])),
            ("bounded_condition_immediate", lambda value: profile(value, "Urza's Saga", "bounded-c").__setitem__("online_model", "immediate")),
            ("invalid_schema_version", lambda value: value.__setitem__("schema_version", "2.0")),
            ("invalid_unsupported_reasons", lambda value: value.__setitem__("unsupported_reason_ids", ["duplicate", "duplicate"])),
            ("empty_card_name", lambda value: record(value, "Island").__setitem__("card_name", "")),
            ("empty_profile_id", lambda value: profile(value, "Prismatic Lens", "filter").__setitem__("profile_id", "")),
            ("invalid_group_id", lambda value: record(value, "Island")["activation_groups"][0].__setitem__("group_id", "not-mana")),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                changed = copy.deepcopy(registry)
                mutate(changed)
                self.assertTrue(self.check_registry(changed))

    def test_tron_profiles_are_derived_only_from_canonical_controlled_land_identities(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        records = {record["card_name"]: record for record in registry["records"]}
        mine = records["Urza's Mine"]["oracle_id"]
        plant = records["Urza's Power Plant"]["oracle_id"]
        tower = records["Urza's Tower"]["oracle_id"]
        island = records["Island"]["oracle_id"]
        plains = records["Plains"]["oracle_id"]

        def project(card_name, controlled):
            result, errors = project_level_two_land(
                records[card_name],
                condition_state={"controlled_land_oracle_ids": controlled},
                current_turn=3,
                horizon_turn=6,
                runtime_authority=self.runtime_authority,
            )
            self.assertEqual([], errors)
            return result["mana_units"]

        self.assertEqual(1, project("Urza's Tower", []))
        self.assertEqual(1, project("Urza's Tower", [mine]))

        tower_group = records["Urza's Tower"]["activation_groups"][0]
        selected, errors = resolve_activation_profiles(
            tower_group,
            {"controlled_land_oracle_ids": [mine, tower]},
            runtime_authority=self.runtime_authority,
        )
        self.assertEqual([], errors); self.assertEqual("base", selected[0]["profile_id"])

        complete = [mine, plant, tower]
        expected_units = {"Urza's Mine": 2, "Urza's Power Plant": 2, "Urza's Tower": 3}
        for card_name, mana_units in expected_units.items():
            with self.subTest(complete_current=card_name):
                group = records[card_name]["activation_groups"][0]
                selected, errors = resolve_activation_profiles(
                    group,
                    {"controlled_land_oracle_ids": complete},
                    runtime_authority=self.runtime_authority,
                )
                self.assertEqual([], errors); self.assertEqual(mana_units, selected[0]["mana_units"])

        self.assertEqual(3, project("Urza's Tower", [mine, plant]))
        self.assertEqual(2, project("Urza's Power Plant", [mine, tower]))
        self.assertEqual(1, project("Urza's Tower", [island, plains]))
        self.assertEqual(3, project("Urza's Tower", [mine, plant]))
        self.assertEqual(3, project("Urza's Tower", [plant, mine]))
        self.assertEqual(3, project("Urza's Tower", [mine, plant, tower]))
        self.assertEqual(3, project("Urza's Tower", [mine, mine, plant]))

        reversed_group = copy.deepcopy(tower_group); reversed_group["profiles"].reverse()
        selected, errors = resolve_activation_profiles(
            reversed_group,
            {"controlled_land_oracle_ids": [mine, plant], "candidate_land_oracle_id": tower},
            runtime_authority=self.runtime_authority,
        )
        self.assertEqual([], errors); self.assertEqual("enhanced", selected[0]["profile_id"])
        tied = copy.deepcopy(tower_group); tied["profiles"][1]["priority"] = 100
        _, errors = resolve_activation_profiles(
            tied,
            {"controlled_land_oracle_ids": [mine, plant], "candidate_land_oracle_id": tower},
            runtime_authority=self.runtime_authority,
        )
        self.assertIn("highest-priority activation group has tied matching profiles", errors)

    def test_legacy_tron_boolean_is_always_rejected(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        group = next(record for record in registry["records"] if record["card_name"] == "Urza's Tower")["activation_groups"][0]
        for value in (True, False, None, 1, "true"):
            with self.subTest(value=value):
                selected, errors = resolve_activation_profiles(
                    group,
                    {"complete_tron_set_controlled": value},
                    runtime_authority=self.runtime_authority,
                )
                self.assertEqual([], selected)
                self.assertIn("activation condition state complete_tron_set_controlled is forbidden", errors)

    def test_condition_state_containers_fail_closed_at_every_public_boundary(self):
        class DictSubclass(dict):
            pass

        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        records = {record["card_name"]: record for record in registry["records"]}
        tower = records["Urza's Tower"]
        glimmervoid = records["Glimmervoid"]
        lens = records["Prismatic Lens"]
        tower_condition = tower["activation_groups"][0]["profiles"][0]["conditions"][0]
        source_records = {records["Command Tower"]["oracle_id"]: records["Command Tower"]}
        source = {
            "source_id": "tower",
            "oracle_id": records["Command Tower"]["oracle_id"],
            "online": True,
            "tapped": False,
        }
        invalid_states = (
            [("commander_colors", ["W", "U", "B", "R", "G"])],
            (("commander_colors", ["W", "U", "B", "R", "G"]),),
            "condition-state",
            42,
            [],
            [()],
            object(),
            DictSubclass(),
            UserDict(),
            {"unknown_key": 1},
        )
        for invalid in invalid_states:
            with self.subTest(boundary="condition_is_satisfied", value=repr(invalid)):
                with self.assertRaises(ValueError):
                    condition_is_satisfied(tower_condition, invalid, runtime_authority=self.runtime_authority)
            with self.subTest(boundary="resolve_activation_profiles", value=repr(invalid)):
                selected, errors = resolve_activation_profiles(
                    tower["activation_groups"][0], invalid, runtime_authority=self.runtime_authority,
                )
                self.assertEqual([], selected); self.assertTrue(errors)
            with self.subTest(boundary="evaluate_end_step_state_transitions", value=repr(invalid)):
                result, errors = evaluate_end_step_state_transitions(glimmervoid, post_development_state=invalid)
                self.assertIsNone(result); self.assertTrue(errors)
            with self.subTest(boundary="project_level_two_land", value=repr(invalid)):
                result, errors = project_level_two_land(
                    tower,
                    condition_state=invalid,
                    current_turn=3,
                    horizon_turn=6,
                    runtime_authority=self.runtime_authority,
                )
                self.assertIsNone(result); self.assertTrue(errors)
            with self.subTest(boundary="project_level_two_ramp", value=repr(invalid)):
                result, errors = project_level_two_ramp(
                    lens, condition_state=invalid, available_generic_mana=2, available_colors=[],
                )
                self.assertIsNone(result); self.assertTrue(errors)
            with self.subTest(boundary="observe_source_capability_shared", value=repr(invalid)):
                with self.assertRaises(ValueError):
                    observe_source_capability(
                        source_records=source_records,
                        source_states=[source],
                        candidate_source_id="tower",
                        condition_state=invalid,
                        runtime_authority=self.runtime_authority,
                    )
            with self.subTest(boundary="observe_source_capability_per_source", value=repr(invalid)):
                with self.assertRaises(ValueError):
                    observe_source_capability(
                        source_records=source_records,
                        source_states=[{**source, "condition_state": invalid}],
                        candidate_source_id="tower",
                        condition_state={"commander_colors": ["W", "U", "B", "R", "G"]},
                        runtime_authority=self.runtime_authority,
                    )

    def test_condition_state_values_are_strict_and_canonically_bound(self):
        records = {
            record["card_name"]: record
            for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]
        }
        tron_condition = records["Urza's Tower"]["activation_groups"][0]["profiles"][0]["conditions"][0]
        commander_condition = records["Command Tower"]["activation_groups"][0]["profiles"][0]["conditions"][0]
        payment_condition = records["Prismatic Lens"]["activation_groups"][0]["profiles"][1]["conditions"][0]
        saga_condition = records["Urza's Saga"]["activation_groups"][0]["profiles"][0]["conditions"][0]
        artifact_condition = records["Glimmervoid"]["state_transitions"][0]["condition"]
        mine = records["Urza's Mine"]["oracle_id"]
        plant = records["Urza's Power Plant"]["oracle_id"]
        nonland = records["Sol Ring"]["oracle_id"]
        unknown = "00000000-0000-0000-0000-000000000000"

        for invalid in ("not-an-array", (mine,), [1], [""], [unknown], [nonland], None):
            with self.subTest(key="controlled_land_oracle_ids", value=invalid):
                with self.assertRaises(ValueError):
                    condition_is_satisfied(
                        tron_condition,
                        {"controlled_land_oracle_ids": invalid},
                        runtime_authority=self.runtime_authority,
                    )
        for invalid in (1, "", unknown, nonland, None):
            with self.subTest(key="candidate_land_oracle_id", value=invalid):
                with self.assertRaises(ValueError):
                    condition_is_satisfied(
                        tron_condition,
                        {"controlled_land_oracle_ids": [mine, plant], "candidate_land_oracle_id": invalid},
                        runtime_authority=self.runtime_authority,
                    )
        for invalid in (
            ("W", "U", "B", "R", "G"), "WUBRG", {"W", "U", "B", "R", "G"},
            [1], ["W", "W", "U", "B", "R", "G"], ["C"], ["X"], ["W"],
        ):
            with self.subTest(key="commander_colors", value=invalid):
                with self.assertRaises(ValueError):
                    condition_is_satisfied(
                        commander_condition,
                        {"commander_colors": invalid},
                        runtime_authority=self.runtime_authority,
                    )
        for condition, key in (
            (payment_condition, "generic_payment_available_from_other_sources"),
            (saga_condition, "controller_turn_offset"),
            (artifact_condition, "artifact_controlled_count"),
        ):
            for invalid in (True, -1, 1.5, "1", [], {}, None):
                with self.subTest(key=key, value=invalid):
                    with self.assertRaises(ValueError):
                        condition_is_satisfied(condition, {key: invalid})

    def test_runtime_state_authority_requires_validated_project_inputs(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        authority, errors = build_runtime_state_authority(
            registry, policy=self.policy, cards=self.cards["cards"], versions=self.versions,
        )
        self.assertEqual([], errors)
        self.assertEqual(self.runtime_authority, authority)

        changed_registry = copy.deepcopy(registry)
        next(record for record in changed_registry["records"] if record["card_name"] == "Sol Ring")["source_kind"] = "land"
        authority, errors = build_runtime_state_authority(
            changed_registry, policy=self.policy, cards=self.cards["cards"], versions=self.versions,
        )
        self.assertIsNone(authority); self.assertTrue(errors)

        changed_cards = copy.deepcopy(self.cards["cards"])
        next(card for card in changed_cards if card["name"] == "Island")["type_line"] = "Artifact"
        authority, errors = build_runtime_state_authority(
            registry, policy=self.policy, cards=changed_cards, versions=self.versions,
        )
        self.assertIsNone(authority); self.assertTrue(errors)

    def test_helper_owned_state_and_source_state_shape_cannot_be_injected(self):
        records = {
            record["card_name"]: record
            for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]
        }
        tower_id = records["Urza's Tower"]["oracle_id"]
        projected, errors = project_level_two_land(
            records["Urza's Tower"],
            condition_state={"candidate_land_oracle_id": tower_id},
            current_turn=3,
            horizon_turn=6,
            runtime_authority=self.runtime_authority,
        )
        self.assertIsNone(projected); self.assertTrue(errors)

        source_records = {records["Island"]["oracle_id"]: records["Island"]}
        source = {"source_id": "island", "oracle_id": records["Island"]["oracle_id"], "online": True, "tapped": False}
        observed = observe_source_capability(
            source_records=source_records,
            source_states=[source],
            candidate_source_id="island",
            condition_state=None,
        )
        self.assertTrue(observed["survives"])
        for malformed_source in (
            {**source, "unknown": True},
            {key: value for key, value in source.items() if key != "online"},
            {**source, "condition_state": None},
        ):
            with self.subTest(source=malformed_source):
                with self.assertRaises(ValueError):
                    observe_source_capability(
                        source_records=source_records,
                        source_states=[malformed_source],
                        candidate_source_id="island",
                    )

        tower_group = records["Urza's Tower"]["activation_groups"][0]
        selected, errors = resolve_activation_profiles(
            tower_group,
            {"controlled_land_oracle_ids": []},
        )
        self.assertEqual([], selected); self.assertTrue(errors)

    def test_malformed_state_cannot_change_registered_runtime_results(self):
        records = {
            record["card_name"]: record
            for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]
        }
        pair_state = [("commander_colors", ["W", "U", "B", "R", "G"])]
        command_tower = records["Command Tower"]
        source = {"source_id": "tower", "oracle_id": command_tower["oracle_id"], "online": True, "tapped": False}
        with self.assertRaises(ValueError):
            observe_source_capability(
                source_records={command_tower["oracle_id"]: command_tower},
                source_states=[source],
                candidate_source_id="tower",
                condition_state=pair_state,
                runtime_authority=self.runtime_authority,
            )

        selected, errors = resolve_activation_profiles(
            records["Urza's Tower"]["activation_groups"][0],
            {"complete_tron_set_controlled": True},
            runtime_authority=self.runtime_authority,
        )
        self.assertEqual([], selected); self.assertTrue(errors)

        transition, errors = evaluate_end_step_state_transitions(
            records["Glimmervoid"],
            post_development_state=[("artifact_controlled_count", 1)],
        )
        self.assertIsNone(transition); self.assertTrue(errors)

        projected, errors = project_level_two_land(
            records["Cascading Cataracts"],
            condition_state=[("generic_payment_available_from_other_sources", 5)],
            current_turn=2,
            horizon_turn=6,
            runtime_authority=self.runtime_authority,
        )
        self.assertIsNone(projected); self.assertTrue(errors)

        projected, errors = project_level_two_ramp(
            records["Prismatic Lens"],
            condition_state={"generic_payment_available_from_other_sources": 99},
            available_generic_mana=2,
            available_colors=[],
        )
        self.assertIsNone(projected); self.assertTrue(errors)

        saga = {"source_id": "saga", "oracle_id": records["Urza's Saga"]["oracle_id"], "online": True, "tapped": False}
        with self.assertRaises(ValueError):
            observe_source_capability(
                source_records={records["Urza's Saga"]["oracle_id"]: records["Urza's Saga"]},
                source_states=[saga],
                candidate_source_id="saga",
                condition_state={"controller_turn_offset": 0},
            )

    def test_failure_patterns_require_exact_emitting_set_and_question_target(self):
        result = copy.deepcopy(self.result); result["failure_patterns"] = []
        self.assertIn("failure_patterns must contain every emitting category exactly once and no non-emitting category", self.check_result(result))
        result = copy.deepcopy(self.result)
        result["failure_patterns"].append({"category_id": "insufficient_mana_by_turn", "raw_count": 0, "sample_size": 100000, "frequency": 0.0})
        self.assertIn("failure_patterns must contain every emitting category exactly once and no non-emitting category", self.check_result(result))

    def test_failure_patterns_enforce_quantities_and_exact_question_metric_resolution(self):
        result = copy.deepcopy(self.result)
        result["failure_patterns"][0]["raw_count"] = 100001
        self.assertIn("failure pattern raw_count must be within 0..sample_size", self.check_result(result))
        result = copy.deepcopy(self.result)
        result["failure_patterns"][0]["sample_size"] = 99999
        self.assertIn("failure pattern sample_size does not match run iteration_count", self.check_result(result))
        result = copy.deepcopy(self.result)
        result["failure_patterns"][0]["frequency"] = 0.5
        self.assertIn("failure pattern frequency does not equal raw_count/sample_size", self.check_result(result))
        reference = {"source": "simulation_question.required_metrics", "metric_id": "ramp_access_by_turn", "field": "target_turn"}
        missing = copy.deepcopy(self.question); missing["required_metrics"] = [item for item in missing["required_metrics"] if item["metric_id"] != "ramp_access_by_turn"]
        _, errors = resolve_question_metric_target(missing, reference)
        self.assertIn("question required_metrics must contain exactly one 'ramp_access_by_turn' target", errors)
        duplicate = copy.deepcopy(self.question); duplicate["required_metrics"].append(copy.deepcopy(next(item for item in duplicate["required_metrics"] if item["metric_id"] == "ramp_access_by_turn")))
        _, errors = resolve_question_metric_target(duplicate, reference)
        self.assertIn("question required_metrics must contain exactly one 'ramp_access_by_turn' target", errors)

    def test_failure_patterns_match_derivable_metric_events(self):
        def pattern(result, category_id):
            return next(item for item in result["failure_patterns"] if item["category_id"] == category_id)

        def set_pattern_count(result, category_id, raw_count):
            item = pattern(result, category_id)
            item["raw_count"] = raw_count
            item["frequency"] = raw_count / item["sample_size"]

        def metric(result, metric_id):
            return next(item for item in result["metrics"] if item["metric_id"] == metric_id)

        def refresh_metric_claim(result, changed_metric):
            claim = next(item for item in result["evidence_claims"] if item.get("metric_id") == changed_metric["metric_id"])
            claim["estimate"] = copy.deepcopy(changed_metric)

        self.assertEqual([], self.check_result())
        self.assertEqual(pattern(self.result, "one_land_hand_unkept")["raw_count"], 17000)
        self.assertEqual(pattern(self.result, "mulligan_to_low_hand")["raw_count"], 0)

        cases = (
            ("missed_land_drop", "failure pattern missed_land_drop raw_count must equal the complement of land_drop_success_by_turn", lambda result: set_pattern_count(result, "missed_land_drop", pattern(result, "missed_land_drop")["raw_count"] + 1)),
            ("ramp_not_available", "failure pattern ramp_not_available_by_turn raw_count must equal the complement of ramp_access_by_turn", lambda result: set_pattern_count(result, "ramp_not_available_by_turn", pattern(result, "ramp_not_available_by_turn")["raw_count"] + 1)),
            ("single_color_missing", "failure pattern single_color_missing_by_turn raw_count must equal distinct_commander_colors_by_turn bin 4", lambda result: set_pattern_count(result, "single_color_missing_by_turn", pattern(result, "single_color_missing_by_turn")["raw_count"] + 1)),
            ("multiple_colors_missing", "failure pattern multiple_colors_missing_by_turn raw_count must equal distinct_commander_colors_by_turn bins 0 through 3", lambda result: set_pattern_count(result, "multiple_colors_missing_by_turn", pattern(result, "multiple_colors_missing_by_turn")["raw_count"] + 1)),
            ("five_color_not_complete", "failure pattern five_color_not_complete_by_turn raw_count must equal the complement of five_color_availability_by_turn", lambda result: set_pattern_count(result, "five_color_not_complete_by_turn", pattern(result, "five_color_not_complete_by_turn")["raw_count"] + 1)),
            ("zero_land_lower_bound", "failure pattern zero_land_hand raw_count must be at least zero_land_hand_rate raw_count", lambda result: set_pattern_count(result, "zero_land_hand", metric(result, "zero_land_hand_rate")["raw_count"] - 1)),
            ("excessive_land_lower_bound", "failure pattern excessive_land_hand raw_count must be at least excessive_land_hand_rate raw_count", lambda result: set_pattern_count(result, "excessive_land_hand", metric(result, "excessive_land_hand_rate")["raw_count"] - 1)),
        )
        for name, diagnostic, mutate in cases:
            with self.subTest(name=name):
                result = copy.deepcopy(self.result)
                mutate(result)
                self.assertIn(diagnostic, self.check_result(result))

        result = copy.deepcopy(self.result)
        colors = metric(result, "distinct_commander_colors_by_turn")
        bin_four, bin_five = colors["bins"][4], colors["bins"][5]
        bin_four["raw_count"] -= 1
        bin_five["raw_count"] += 1
        for item in colors["bins"]:
            item["proportion"] = item["raw_count"] / colors["sample_size"]
        colors["mean"] = sum(item["value"] * item["raw_count"] for item in colors["bins"]) / colors["sample_size"]
        refresh_metric_claim(result, colors)
        set_pattern_count(result, "single_color_missing_by_turn", bin_four["raw_count"])
        self.assertIn(
            "five_color_availability_by_turn raw_count must equal distinct_commander_colors_by_turn bin 5",
            self.check_result(result),
        )

    def test_opening_hand_keep_aggregates_are_coherent(self):
        def metric(result, metric_id):
            return next(item for item in result["metrics"] if item["metric_id"] == metric_id)

        result = copy.deepcopy(self.result)
        n = self.run["iteration_count"]
        z = metric(result, "zero_land_hand_rate")["raw_count"]
        o = metric(result, "one_land_hand_rate")["raw_count"]
        e = metric(result, "excessive_land_hand_rate")["raw_count"]
        natural_two_to_five = n - z - o - e
        metric(result, "keepable_opening_hand_rate")["raw_count"] = natural_two_to_five - 1
        self.assertIn("keepable_opening_hand_rate raw_count is incompatible with the frozen natural-opening keep rule", self.check_result(result))

        result = copy.deepcopy(self.result)
        metric(result, "keepable_opening_hand_rate")["raw_count"] = natural_two_to_five + o + 1
        self.assertIn("keepable_opening_hand_rate raw_count is incompatible with the frozen natural-opening keep rule", self.check_result(result))

        result = copy.deepcopy(self.result)
        natural_one_land_rejected = o - (metric(result, "keepable_opening_hand_rate")["raw_count"] - natural_two_to_five)
        one_land_pattern = next(item for item in result["failure_patterns"] if item["category_id"] == "one_land_hand_unkept")
        one_land_pattern["raw_count"] = natural_one_land_rejected - 1
        one_land_pattern["frequency"] = one_land_pattern["raw_count"] / one_land_pattern["sample_size"]
        self.assertIn("failure pattern one_land_hand_unkept raw_count is below derived natural one-land rejections", self.check_result(result))

    def test_level_two_projection_is_registry_derived_and_support_bounded(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        records = {record["card_name"]: record for record in registry["records"]}
        state = {"generic_payment_available_from_other_sources": 0, "controller_turn_offset": 0}
        cataracts, errors = project_level_two_land(records["Cascading Cataracts"], condition_state=state, current_turn=1, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual([], cataracts["colors"]); self.assertEqual(1, cataracts["mana_units"])
        gardens, errors = project_level_two_land(records["The Mycosynth Gardens"], condition_state=state, current_turn=1, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual([], gardens["colors"])
        lens, errors = project_level_two_ramp(records["Prismatic Lens"], condition_state={}, available_generic_mana=2, available_colors=[])
        self.assertEqual([], errors); self.assertTrue(lens["payable"]); self.assertEqual(1, lens["output_units"])
        state["generic_payment_available_from_other_sources"] = 5
        cataracts, errors = project_level_two_land(records["Cascading Cataracts"], condition_state=state, current_turn=1, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(set("WUBRG"), set(cataracts["colors"])); self.assertEqual(5, cataracts["mana_units"])
        unsupported, errors = project_level_two_ramp(records["Moonsnare Prototype"], condition_state={}, available_generic_mana=9, available_colors=[])
        self.assertEqual([], errors); self.assertFalse(unsupported["payable"]); self.assertEqual(0, unsupported["output_units"])
        saga, errors = project_level_two_land(records["Urza's Saga"], condition_state={"controller_turn_offset": 2}, current_turn=3, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual([], saga["colors"]); self.assertFalse(saga["permanent"]); self.assertEqual(1, saga["remaining_availability"])

    def test_support_boundary_parity_and_recording_context_are_closed(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        semantics = self.documents["workshop/projects/the-myr-singularity/simulation/card_semantics.json"]
        self.assertEqual([], validate_card_semantics_registry_parity(semantics, registry))
        changed = copy.deepcopy(semantics)
        next(item for item in changed["entries"] if item["card_identity"]["name"] == "City of Brass")["modeled_behavior"]["produces_colors"].pop()
        self.assertTrue(validate_card_semantics_registry_parity(changed, registry))
        for name, identifier, timestamp in (
            ("simulation_run.contract.json", "run_id", False),
            ("simulation_result.contract.json", "result_id", "created_at"),
            ("comparison_result.contract.json", "comparison_id", "created_at"),
        ):
            with self.subTest(contract=name):
                context = self.contracts[name]["recording_context"]
                self.assertEqual(identifier, context["record_fields"]["id_field"])
                self.assertFalse(context["engine_boundary"]["wall_clock_read_permitted"])
                self.assertFalse(context["engine_boundary"]["random_or_uuid_recording_id_permitted"])
                if timestamp is False:
                    self.assertFalse(context["record_fields"]["created_at_required"])
                else:
                    self.assertEqual(timestamp, context["record_fields"]["created_at_field"])

    def test_registry_and_taxonomy_are_complete_approved_semantics(self):
        registry = self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]
        self.assertEqual([], self.check_registry(registry))
        mutations = (
            ("Sol Ring", "cc", lambda profile: profile.__setitem__("mana_units", 1)),
            ("Island", "u", lambda profile: profile.__setitem__("natural_untap_model", "does_not_naturally_untap")),
            ("Command Tower", "commander-choice", lambda profile: profile["output_capabilities"].pop()),
            ("Basalt Monolith", "ccc", lambda profile: profile.__setitem__("natural_untap_model", "normal")),
            ("Urza's Tower", "enhanced", lambda profile: profile.__setitem__("mana_units", 2)),
            ("Myr Convert", "any", lambda profile: profile["payment"]["life"].__setitem__("amount", 1)),
            ("Moonsnare Prototype", "secondary-tap", lambda profile: profile.__setitem__("supported", True)),
            ("Sol Ring", "cc", lambda profile: profile.__setitem__("supported", False)),
        )
        for card_name, profile_id, mutate in mutations:
            with self.subTest(card=card_name, profile=profile_id):
                changed = copy.deepcopy(registry)
                profile = next(profile for record in changed["records"] if record["card_name"] == card_name for group in record["activation_groups"] for profile in group["profiles"] if profile["profile_id"] == profile_id)
                mutate(profile)
                self.assertIn("mana source semantics does not match the approved v1 executable-semantics fingerprint", self.check_registry(changed))
        changed = copy.deepcopy(registry)
        next(record for record in changed["records"] if record["card_name"] == "Island")["state_transitions"] = [{
            "event_id": "end_step_remove_unless_condition",
            "condition": {"condition_id": "artifact_controlled", "params": {"minimum_count": 1}},
        }]
        self.assertIn("mana source semantics does not match the approved v1 executable-semantics fingerprint", self.check_registry(changed))
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["emission_contract"]["categories"]["zero_land_hand"]["predicate"] = "arbitrary"
        self.assertIn("failure taxonomy does not match the approved v4 emission-semantics fingerprint", validate_failure_pattern_taxonomy(taxonomy, policy=self.policy, question=self.question))
        self.assertIn("result validation requires the resolved failure taxonomy artifact", validate_simulation_result(self.result, run=self.run, policy=self.policy, question=self.question, question_contract=self.contracts["simulation_question.contract.json"], result_contract=self.contracts["simulation_result.contract.json"], taxonomy_ids=self.taxonomy_ids, load_reference=self.loader, project_id="the-myr-singularity", fingerprint_for_version=self.fingerprint, lifecycle_mode="creation"))

    def test_final_closure_has_no_legacy_level_two_authority(self):
        legacy = self.policy["sequencing_semantics"]["level_2_mana_development"]
        serialized = json.dumps(legacy, sort_keys=True)
        self.assertIn("mana_source_semantics.json", serialized)
        self.assertNotIn("canonical produced_mana, or explicitly modeled", serialized)
        self.assertNotIn("Conditional, activated-cost-dependent", serialized)

    def test_unsupported_only_exotic_orchard_is_a_legal_zero_output_land(self):
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        projected, errors = project_level_two_land(records["Exotic Orchard"], condition_state={}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority, ordinal=4)
        self.assertEqual([], errors)
        self.assertEqual({"colors": [], "five_color_source": False, "permanent": True, "remaining_availability": 5, "mana_units": 0, "oracle_id": records["Exotic Orchard"]["oracle_id"], "ordinal": 4}, projected)

    def test_cataracts_selector_uses_gross_legal_output_only_when_prepaid(self):
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        base, errors = project_level_two_land(records["Cascading Cataracts"], condition_state={"generic_payment_available_from_other_sources": 0}, current_turn=1, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual([], base["colors"]); self.assertEqual(1, base["mana_units"])
        prepaid, errors = project_level_two_land(records["Cascading Cataracts"], condition_state={"generic_payment_available_from_other_sources": 5}, current_turn=1, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(set("WUBRG"), set(prepaid["colors"])); self.assertEqual(5, prepaid["mana_units"])

    def test_land_selector_colors_are_wubrg_only_and_drive_selection(self):
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        island, errors = project_level_two_land(records["Island"], condition_state={}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(["U"], island["colors"])
        colorless, errors = project_level_two_land(records["Cascading Cataracts"], condition_state={"generic_payment_available_from_other_sources": 0}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual([], colorless["colors"])
        self.assertEqual(0, len(set(colorless["colors"]) - {"U"}))
        self.assertEqual(island["oracle_id"], select_land([island, colorless], {"U"}, 6, 2)["oracle_id"])
        plains, errors = project_level_two_land(records["Plains"], condition_state={}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(["W"], plains["colors"])
        self.assertEqual(plains["oracle_id"], select_land([colorless, plains], {"U"}, 6, 2)["oracle_id"])

    def test_projection_condition_phases_cover_tron_and_ramp_payment_reservation(self):
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        mine = records["Urza's Mine"]["oracle_id"]
        plant = records["Urza's Power Plant"]["oracle_id"]
        first, errors = project_level_two_land(records["Urza's Tower"], condition_state={"controlled_land_oracle_ids": []}, current_turn=3, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(1, first["mana_units"])
        tower, errors = project_level_two_land(records["Urza's Tower"], condition_state={"controlled_land_oracle_ids": [mine, plant]}, current_turn=3, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(3, tower["mana_units"])
        incomplete, errors = project_level_two_land(records["Urza's Tower"], condition_state={"controlled_land_oracle_ids": [mine]}, current_turn=3, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(1, incomplete["mana_units"])
        reversed_profiles = copy.deepcopy(records["Urza's Tower"])
        reversed_profiles["activation_groups"][0]["profiles"].reverse()
        unchanged, errors = project_level_two_land(reversed_profiles, condition_state={"controlled_land_oracle_ids": [mine, plant]}, current_turn=3, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(3, unchanged["mana_units"])
        lens_two, errors = project_level_two_ramp(records["Prismatic Lens"], condition_state={}, available_generic_mana=2, available_colors=[])
        self.assertEqual([], errors); self.assertTrue(lens_two["payable"]); self.assertEqual(1, lens_two["color_flexibility"])
        lens_three, errors = project_level_two_ramp(records["Prismatic Lens"], condition_state={}, available_generic_mana=3, available_colors=[])
        self.assertEqual([], errors); self.assertTrue(lens_three["payable"]); self.assertEqual(5, lens_three["color_flexibility"])
        new_saga, errors = project_level_two_land(records["Urza's Saga"], condition_state={}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertEqual(3, new_saga["remaining_availability"])

    def test_glimmervoid_selection_and_end_step_transition_are_distinct(self):
        records = {record["card_name"]: record for record in self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"]["records"]}
        glimmervoid = records["Glimmervoid"]
        absent, errors = project_level_two_land(glimmervoid, condition_state={"artifact_controlled_count": 0}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertFalse(absent["permanent"]); self.assertEqual(1, absent["remaining_availability"])
        present, errors = project_level_two_land(glimmervoid, condition_state={"artifact_controlled_count": 1}, current_turn=2, horizon_turn=6, runtime_authority=self.runtime_authority)
        self.assertEqual([], errors); self.assertTrue(present["permanent"]); self.assertEqual(5, present["remaining_availability"])
        end_step, errors = evaluate_end_step_state_transitions(glimmervoid, post_development_state={"artifact_controlled_count": 1})
        self.assertEqual([], errors); self.assertTrue(end_step["remains_available"])
        removed, errors = evaluate_end_step_state_transitions(glimmervoid, post_development_state={"artifact_controlled_count": 0})
        self.assertEqual([], errors); self.assertTrue(removed["removed"])

    def test_run_recording_and_nested_boundaries_are_exact_closed(self):
        for field in ("execution_digest", "engine_generated_at", "wall_clock_timestamp", "created_at", "runtime_override", "arbitrary_unknown_field"):
            with self.subTest(top_level=field):
                run = copy.deepcopy(self.run); run[field] = "forbidden"
                self.assertTrue(any("run has unregistered top-level fields" in error for error in self.check_run(run)))
        for label, mutate, diagnostic in (
            ("config", lambda run: run["config"].__setitem__("runtime_override", True), "run configuration does not match"),
            ("config-unknown", lambda run: run["config"].__setitem__("arbitrary_unknown_field", True), "run configuration does not match"),
            ("boundary", lambda run: run["explicit_boundary"].__setitem__("arbitrary_unknown_field", False), "run explicit_boundary flags"),
            ("id", lambda run: run.__setitem__("run_id", ""), "run run_id must be a non-empty string"),
        ):
            with self.subTest(label=label):
                run = copy.deepcopy(self.run); mutate(run)
                self.assertTrue(any(diagnostic in error for error in self.check_run(run)))
        result = copy.deepcopy(self.result); result["created_at"] = "not-a-recording-time"
        self.assertTrue(any("result created_at" in error for error in self.check_result(result)))
        result = copy.deepcopy(self.result); result["result_id"] = ""
        self.assertTrue(any("result result_id" in error for error in self.check_result(result)))
        comparison = copy.deepcopy(self.comparison); comparison["comparison_id"] = ""
        self.assertTrue(any("comparison comparison_id" in error for error in self.check_comparison(comparison)))
        comparison = copy.deepcopy(self.comparison); comparison["created_at"] = "not-a-recording-time"
        self.assertTrue(any("comparison created_at" in error for error in self.check_comparison(comparison)))

    def test_unsupported_limitations_city_and_recording_taxonomy_boundaries(self):
        required = {item for item in self.run["limitations"] if item.startswith("unsupported_mana_profile:")}
        self.assertEqual(4, len(required))
        run = copy.deepcopy(self.run); run["limitations"].remove(next(iter(required)))
        self.assertTrue(any("omit required unsupported behavior IDs" in error for error in self.check_run(run)))
        result = copy.deepcopy(self.result); result["limitations"].remove(next(iter(required)))
        self.assertTrue(any("omit required unsupported behavior IDs" in error for error in self.check_result(result)))
        registry = copy.deepcopy(self.documents["workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json"])
        city = next(record for record in registry["records"] if record["card_name"] == "City of Brass")
        city["activation_groups"][0]["profiles"][0]["payment"]["life"] = {"amount": 1, "treatment": "ignored"}
        self.assertIn("City of Brass card semantics/registry must not model a life-payment activation cost", validate_card_semantics_registry_parity(self.documents["workshop/projects/the-myr-singularity/simulation/card_semantics.json"], registry))
        for label, mutate in (
            ("contract-id", lambda context: context.__setitem__("contract_id", "other")),
            ("metadata-owner", lambda context: context["engine_boundary"].__setitem__("recording_metadata_owner", "engine")),
            ("wall-clock", lambda context: context["engine_boundary"].__setitem__("wall_clock_read_permitted", True)),
            ("random-id", lambda context: context["engine_boundary"].__setitem__("random_or_uuid_recording_id_permitted", True)),
            ("artifact-algorithm", lambda context: context["artifact_identity"].__setitem__("algorithm_id", "other")),
            ("replay-boundary", lambda context: context["artifact_identity"].__setitem__("replay_equivalence", "artifact identity")),
            ("id-owner", lambda context: context["record_fields"].__setitem__("id_owner", "engine")),
            ("timestamp-owner", lambda context: context["record_fields"].__setitem__("created_at_owner", "engine")),
        ):
            with self.subTest(recording_context=label):
                context = copy.deepcopy(self.contracts["simulation_result.contract.json"]["recording_context"]); mutate(context)
                self.assertTrue(validate_recording_context(context, id_field="result_id", created_at_required=True))
        self.assertEqual(["failure patterns require the resolved failure taxonomy artifact"], validate_result_failure_patterns([], 100000, {"bare-category"}, self.question))
        self.assertIn("result validation requires the resolved failure taxonomy artifact", validate_simulation_result(self.result, run=self.run, policy=self.policy, question=self.question, question_contract=self.contracts["simulation_question.contract.json"], result_contract=self.contracts["simulation_result.contract.json"], taxonomy_ids={"bare-category"}, load_reference=self.loader, project_id="the-myr-singularity", fingerprint_for_version=self.fingerprint, lifecycle_mode="creation"))
        self.assertTrue(any("resolved failure taxonomy artifact" in error for error in validate_comparison_result(self.comparison, baseline_run=self.baseline_run, candidate_run=self.run, baseline_result=self.baseline_result, candidate_result=self.result, policy=self.policy, question=self.question, question_contract=self.contracts["simulation_question.contract.json"], comparison_contract=self.contracts["comparison_result.contract.json"], run_contract=self.contracts["simulation_run.contract.json"], result_contract=self.contracts["simulation_result.contract.json"], project_id="the-myr-singularity", taxonomy_ids={"bare-category"}, load_reference=self.loader, fingerprint_for_version=self.fingerprint, lifecycle_mode="creation")))


if __name__ == "__main__":
    unittest.main()
