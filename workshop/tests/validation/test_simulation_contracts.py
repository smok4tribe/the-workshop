"""Positive and adversarial coverage for the active simulation-policy-v2 contract."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from workshop.shared.identity import (  # noqa: E402
    artifact_content_fingerprint, deck_content_fingerprint, load_strict_json_bytes,
    resolve_card_fact,
)
from workshop.shared.simulation_determinism import (  # noqa: E402
    PCG32, choose_payment, derive_iteration_seed, derive_run_seed,
    select_bottom_tokens, select_land, select_payable_ramp,
)
from workshop.simulation.instance_validation import (  # noqa: E402
    validate_comparison_result, validate_simulation_result, validate_simulation_run,
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


class SimulationContractV2Tests(unittest.TestCase):
    def setUp(self):
        self.policy = load(SIM / "simulation_policy.json")
        self.question = load(SIM / "questions" / "question-001-mana-color.json")
        self.cards = load(REPO_ROOT / "workshop" / "card-data" / "cards.json")
        self.contracts = {name: load(CONTRACTS / name) for name in (
            "simulation_run.contract.json", "simulation_result.contract.json", "comparison_result.contract.json",
        )}
        self.run = load(FIXTURES / "simulation_run.valid.json")
        self.baseline_run = load(FIXTURES / "simulation_run.baseline.valid.json")
        self.result = load(FIXTURES / "simulation_result.valid.json")
        self.baseline_result = load(FIXTURES / "simulation_result.baseline.valid.json")
        self.comparison = load(FIXTURES / "comparison_result.valid.json")
        self.documents = {
            "workshop/projects/the-myr-singularity/simulation/simulation_policy.json": self.policy,
            "workshop/projects/the-myr-singularity/simulation/questions/question-001-mana-color.json": self.question,
            "workshop/projects/the-myr-singularity/simulation/card_semantics.json": load(SIM / "card_semantics.json"),
            "workshop/card-data/cards.json": self.cards,
            "workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json": load(CONTRACTS / "failure_pattern_taxonomy.json"),
            "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json": load(CONTRACTS / "simulation_question.contract.json"),
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
        self.taxonomy_ids = {x["category_id"] for x in self.documents["workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json"]["categories"]}

    def loader(self, path):
        return self.documents[path]

    def fingerprint(self, version):
        return deck_content_fingerprint(version, self.cards["cards"])

    def check_run(self, run=None):
        return validate_simulation_run(run or self.run, question=self.question, policy=self.policy, run_contract=self.contracts["simulation_run.contract.json"], project_id="the-myr-singularity", load_reference=self.loader, fingerprint_for_version=self.fingerprint)

    def check_result(self, result=None, run=None):
        return validate_simulation_result(result or self.result, run=run or self.run, policy=self.policy, question=self.question, result_contract=self.contracts["simulation_result.contract.json"], taxonomy_ids=self.taxonomy_ids, load_reference=self.loader)

    def check_comparison(self, comparison=None, baseline_result=None, candidate_result=None):
        return validate_comparison_result(comparison or self.comparison, baseline_run=self.baseline_run, candidate_run=self.run, baseline_result=baseline_result or self.baseline_result, candidate_result=candidate_result or self.result, policy=self.policy, question=self.question, comparison_contract=self.contracts["comparison_result.contract.json"], run_contract=self.contracts["simulation_run.contract.json"], result_contract=self.contracts["simulation_result.contract.json"], project_id="the-myr-singularity", taxonomy_ids=self.taxonomy_ids, load_reference=self.loader, fingerprint_for_version=self.fingerprint)

    def test_committed_validator_passes(self):
        result = subprocess.run([sys.executable, "workshop/tests/validation/validate_simulation_contracts.py"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_valid_v2_fixtures_validate(self):
        self.assertEqual([], self.check_run())
        self.assertEqual([], self.check_result())
        self.assertEqual([], self.check_comparison())

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

    def test_v2_seed_and_iteration_vectors(self):
        seed = derive_run_seed(self.run["semantic_dependencies"]["question"]["content_fingerprint"], self.run["semantic_dependencies"]["policy"]["content_fingerprint"], self.run["deck_content_fingerprint"], self.run["run_role"])
        self.assertEqual(seed, self.run["seed"])
        self.assertEqual(derive_iteration_seed(seed, 1), 2077295790868176945)
        self.assertEqual(derive_iteration_seed(seed, 2), 9341791923079031219)

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
        self.assertIn("result metrics are missing required question metrics", self.check_result(missing))
        duplicate = copy.deepcopy(self.result); duplicate["metrics"].append(copy.deepcopy(duplicate["metrics"][0]))
        self.assertIn("result metrics contain duplicate metric keys", self.check_result(duplicate))
        extra = copy.deepcopy(self.result); extra["metrics"].append(copy.deepcopy(extra["metrics"][0])); extra["metrics"][-1]["metric_id"]="unknown"
        self.assertIn("result metrics contain unregistered metric", self.check_result(extra))

    def test_categorical_shape_rejects_bad_arithmetic_bins_and_wilson(self):
        result = copy.deepcopy(self.result); categorical=next(m for m in result["metrics"] if m["metric_id"]=="distinct_commander_colors_by_turn")
        categorical["bins"].pop(); categorical["confidence_interval"]={"method":"wilson_score_interval"}
        errors=self.check_result(result)
        self.assertTrue(any("bins" in error for error in errors)); self.assertIn("categorical metric must not define a Wilson interval", errors)

    def test_comparison_rejects_empty_missing_duplicate_and_asymmetric_optional(self):
        empty=copy.deepcopy(self.comparison); empty["metric_deltas"]=[]
        self.assertIn("comparison metric_deltas must be non-empty", self.check_comparison(empty))
        missing=copy.deepcopy(self.comparison); missing["metric_deltas"].pop()
        self.assertIn("comparison metric_deltas must exactly cover reported metrics", self.check_comparison(missing))
        duplicate=copy.deepcopy(self.comparison); duplicate["metric_deltas"].append(copy.deepcopy(duplicate["metric_deltas"][0]))
        self.assertIn("comparison metric_deltas contain duplicate metric keys", self.check_comparison(duplicate))
        optional=copy.deepcopy(self.result); optional["metrics"].append({"metric_id":"commander_castability_by_turn","target_turn":3,"raw_count":1,"sample_size":100000,"probability":0.00001,"confidence_interval":{"method":"wilson_score_interval","level":0.95,"lower":0.0,"upper":0.000057}})
        self.assertIn("comparison optional metric selection is asymmetric", self.check_comparison(candidate_result=optional))

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


if __name__ == "__main__":
    unittest.main()
