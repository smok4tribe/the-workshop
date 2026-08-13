#!/usr/bin/env python3
"""Validate the active Sprint 2 simulation-policy-v3 contract layer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from workshop.shared.identity import (  # noqa: E402
    artifact_content_fingerprint,
    deck_content_fingerprint,
    load_strict_json,
)
from workshop.shared.simulation_determinism import derive_iteration_seed, derive_run_seed  # noqa: E402
from workshop.simulation.instance_validation import (  # noqa: E402
    validate_policy_metric_contracts,
    validate_question_role_bindings,
)

PROJECT_ID = "the-myr-singularity"
PROJECT = REPO_ROOT / "workshop" / "projects" / PROJECT_ID
SIM = PROJECT / "simulation"
CONTRACTS = SIM / "contracts"
CARDS = REPO_ROOT / "workshop" / "card-data" / "cards.json"
EXPECTED_METRICS = {
    "keepable_opening_hand_rate", "zero_land_hand_rate", "one_land_hand_rate",
    "excessive_land_hand_rate", "land_drop_success_by_turn", "ramp_access_by_turn",
    "distinct_commander_colors_by_turn", "five_color_availability_by_turn",
    "commander_castability_by_turn",
}
INSTANCE_TYPES = {"simulation_run", "simulation_result", "comparison_result"}


def load_json(path):
    return load_strict_json(Path(path))


def report(checks):
    failed = 0
    for name, errors in checks:
        if errors:
            failed += 1
            print(f"[FAIL] {name}")
            for error in errors:
                print(f"       - {error}")
        else:
            print(f"[PASS] {name}")
    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} simulation-contract checks failed.")
        return 1
    print(f"PASS: all {len(checks)} simulation-contract checks passed.")
    return 0


def _required(obj, fields, label):
    if not isinstance(obj, dict):
        return [f"{label} must be an object"]
    return [f"{label} is missing required field {field!r}" for field in fields if field not in obj]


def _check_reference(reference, expected_path, expected_document, label):
    errors = []
    if not isinstance(reference, dict):
        return [f"{label} must be an immutable reference object"]
    if reference.get("path") != expected_path:
        errors.append(f"{label}.path must be {expected_path!r}")
    if reference.get("content_fingerprint") != artifact_content_fingerprint(expected_document):
        errors.append(f"{label} content fingerprint does not match resolved artifact")
    return errors


def main():
    files = {
        "policy": SIM / "simulation_policy.json", "semantics": SIM / "card_semantics.json",
        "question": SIM / "questions" / "question-001-mana-color.json",
        "taxonomy": CONTRACTS / "failure_pattern_taxonomy.json",
        "question_contract": CONTRACTS / "simulation_question.contract.json",
        "run_contract": CONTRACTS / "simulation_run.contract.json",
        "result_contract": CONTRACTS / "simulation_result.contract.json",
        "comparison_contract": CONTRACTS / "comparison_result.contract.json",
        "cards": CARDS,
    }
    docs, errors = {}, []
    for name, path in files.items():
        try:
            docs[name] = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{name} does not strictly parse: {exc}")
    checks = [("all v3 artifacts exist and strictly parse", errors)]
    if errors:
        return report(checks)
    policy, semantics, question, taxonomy = (docs[k] for k in ("policy", "semantics", "question", "taxonomy"))

    errors = _required(policy, ("policy_id", "policy_version", "references", "randomness_policy", "deck_fingerprint_policy", "metric_catalog", "level_2_sequencing"), "policy")
    if policy.get("policy_version") != "sim-policy-v3": errors.append("policy_version must be sim-policy-v3")
    if policy.get("bottoming_rule", {}).get("rule_id") != "deterministic-bottoming-v2": errors.append("policy must use deterministic-bottoming-v2")
    checks.append(("policy has versioned v3 ownership", errors))

    errors = []
    expected_refs = {
        "card_semantics": ("workshop/projects/the-myr-singularity/simulation/card_semantics.json", semantics),
        "canonical_card_facts": ("workshop/card-data/cards.json", docs["cards"]),
        "failure_pattern_taxonomy": ("workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json", taxonomy),
        "simulation_question_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json", docs["question_contract"]),
        "simulation_run_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_run.contract.json", docs["run_contract"]),
        "simulation_result_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_result.contract.json", docs["result_contract"]),
        "comparison_result_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/comparison_result.contract.json", docs["comparison_contract"]),
    }
    for key, (path, document) in expected_refs.items(): errors.extend(_check_reference((policy.get("references") or {}).get(key), path, document, f"policy.references.{key}"))
    checks.append(("policy pins every immutable semantic dependency without self-hashing", errors))

    errors = []
    fp = policy.get("deck_fingerprint_policy", {})
    if fp.get("algorithm_id") != "deck-content-sha256-canonical-v2": errors.append("deck fingerprint algorithm must be deck-content-sha256-canonical-v2")
    for version_id in ("v1.0", "v1.1"):
        version = load_json(PROJECT / "versions" / f"{version_id}.json")
        try: computed = deck_content_fingerprint(version, docs["cards"]["cards"])
        except ValueError as exc: errors.append(str(exc)); continue
        if fp.get("reference_fingerprints", {}).get(version_id) != computed: errors.append(f"{version_id} v2 fingerprint does not recompute")
    checks.append(("canonical oracle-id deck fingerprints recompute", errors))

    errors = []
    rng = policy.get("randomness_policy", {})
    if rng.get("rng_id") != "pcg32-v1": errors.append("pcg32-v1 must remain the RNG")
    if (rng.get("canonical_seed_derivation") or {}).get("algorithm_id") != "sim-seed-sha256-v2": errors.append("run seed derivation must be sim-seed-sha256-v2")
    if (rng.get("iteration_seed_derivation") or {}).get("algorithm_id") != "sim-iteration-seed-sha256-v1": errors.append("iteration seed derivation must be sim-iteration-seed-sha256-v1")
    if rng.get("trace_contract_id") != "simulation-iteration-trace-v1": errors.append("trace contract id is missing")
    checks.append(("seed and iteration determinism are versioned", errors))

    errors = []
    errors.extend(validate_policy_metric_contracts(policy))
    by_id = {m.get("metric_id"): m for m in (policy.get("metric_catalog") or {}).get("metrics", [])}
    if set(by_id) != EXPECTED_METRICS: errors.append("metric catalog must contain exactly the nine registered metrics")
    if by_id.get("distinct_commander_colors_by_turn", {}).get("domain") != [0, 1, 2, 3, 4, 5]: errors.append("distinct commander colors must use categorical_count 0..5")
    checks.append(("metric registry has complete v3 measurement contracts", errors))

    errors = []
    if semantics.get("policy_version") != "sim-policy-v3": errors.append("card semantics must bind sim-policy-v3")
    saga = next((e for e in semantics.get("entries", []) if e.get("card_identity", {}).get("name") == "Urza's Saga"), {})
    if saga.get("source", {}).get("oracle_basis") != "Saga land with a Chapter I {T}: Add {C} ability and a Chapter III ability.": errors.append("Urza's Saga must use the approved narrow oracle basis")
    if "upkeep" in saga.get("source", {}).get("oracle_basis", "").casefold(): errors.append("Urza's Saga source basis must not contain upkeep")
    if saga.get("time_dependent_availability", {}).get("removal_event", {}).get("trigger") != "final_chapter_ability_leaves_stack": errors.append("Urza's Saga removal trigger is incorrect")
    checks.append(("Urza's Saga source prose and bounded removal are consistent", errors))

    errors = []
    if question.get("policy_version") != "sim-policy-v3": errors.append("question must bind sim-policy-v3")
    errors.extend(_check_reference(question.get("policy_reference"), "workshop/projects/the-myr-singularity/simulation/simulation_policy.json", policy, "question.policy_reference"))
    required = {(m.get("metric_id"), m.get("target_turn")) for m in question.get("required_metrics", [])}
    optional = {(m.get("metric_id"), m.get("target_turn")) for m in question.get("optional_metrics", [])}
    if {mid for mid, _ in required} != EXPECTED_METRICS - {"commander_castability_by_turn"}: errors.append("question required_metrics must contain first eight metrics")
    if {mid for mid, _ in optional} != {"commander_castability_by_turn"}: errors.append("question optional_metrics must contain commander castability")
    errors.extend(validate_question_role_bindings(question.get("compared_versions")))
    for entry in question.get("compared_versions", []):
        version = load_json(REPO_ROOT / entry.get("path", "missing"))
        if entry.get("deck_content_fingerprint") != deck_content_fingerprint(version, docs["cards"]["cards"]): errors.append(f"question DeckVersion fingerprint does not recompute for {entry.get('deck_version_id')}")
    checks.append(("question structurally separates required and optional metrics", errors))

    errors = []
    for name, expected_id in (("question_contract", "simulation-question-contract-v2"), ("run_contract", "simulation-run-contract-v2"), ("result_contract", "simulation-result-contract-v2"), ("comparison_contract", "comparison-result-contract-v2")):
        if docs[name].get("contract_id") != expected_id: errors.append(f"{name} must have v2 contract identity")
    checks.append(("materially changed schemas use v2 contract identities", errors))

    errors = []
    level2 = policy.get("level_2_sequencing", {})
    if level2.get("turn_order") != ['untap_and_clear_floating_mana','draw','advance_time_dependent_state','select_and_play_one_land','repeatedly_deploy_payable_registered_ramp','resolve_pending_time_dependent_removals','record_end_of_turn_observations']:
        errors.append("Level 2 turn order is not frozen")
    if not level2.get("land_selection_priority") or not level2.get("ramp_deployment_priority") or not level2.get("payment_priority"):
        errors.append("Level 2 selection and payment priorities are incomplete")
    checks.append(("Level 2 trace sequencing is explicit and deterministic", errors))

    errors = []
    for path in SIM.rglob("*.json"):
        try: document = load_json(path)
        except ValueError: continue
        if document.get("artifact_type") in INSTANCE_TYPES: errors.append(f"production simulation evidence is present: {path.relative_to(REPO_ROOT)}")
    checks.append(("no production Run, Result, or Comparison is created", errors))
    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
