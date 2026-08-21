#!/usr/bin/env python3
"""Validate the active Sprint 2 simulation-policy-v4 contract layer."""

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
    validate_card_semantics_registry_parity,
    validate_failure_pattern_taxonomy,
    validate_mana_source_semantics,
    validate_policy_metric_contracts,
    validate_question_role_bindings,
    validate_recording_context,
    validate_simulation_question,
    validate_simulation_question_lifecycle,
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
        "mana_source_semantics": SIM / "mana_source_semantics.json",
        "question": SIM / "questions" / "question-001-mana-color.json",
        "taxonomy": CONTRACTS / "failure_pattern_taxonomy.json",
        "question_contract": CONTRACTS / "simulation_question.contract.json",
        "run_contract": CONTRACTS / "simulation_run.contract.json",
        "result_contract": CONTRACTS / "simulation_result.contract.json",
        "comparison_contract": CONTRACTS / "comparison_result.contract.json",
        "lifecycle_contract": CONTRACTS / "simulation_question_lifecycle.contract.json",
        "lifecycle": SIM / "lifecycle" / "question-001-mana-color.json",
        "cards": CARDS,
    }
    docs, errors = {}, []
    for name, path in files.items():
        try:
            docs[name] = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{name} does not strictly parse: {exc}")
    checks = [("all v5 executable-semantics artifacts exist and strictly parse", errors)]
    if errors:
        return report(checks)
    policy, semantics, question, taxonomy = (docs[k] for k in ("policy", "semantics", "question", "taxonomy"))

    errors = _required(policy, ("policy_id", "policy_version", "references", "randomness_policy", "deck_fingerprint_policy", "metric_catalog", "level_2_sequencing"), "policy")
    if policy.get("policy_version") != "sim-policy-v5": errors.append("policy_version must be sim-policy-v5")
    if policy.get("bottoming_rule", {}).get("rule_id") != "deterministic-bottoming-v2": errors.append("policy must use deterministic-bottoming-v2")
    transition = policy.get("mulligan_policy", {}).get("executable_state_transition", {})
    expected_transition = {
        "canonical_library": "99 physical card-instance tokens in canonical token order",
        "initial_shuffle": "fisher_yates_full_library_with_iteration_pcg32",
        "rejected_hand_transition": [
            "return_all_physical_tokens_to_eligibility",
            "reconstruct_full_library_in_canonical_instance_token_order",
            "increment_mulligans_taken_before_recording_next_attempt",
            "fisher_yates_full_library_with_same_continuous_iteration_pcg32",
            "draw_opening_hand_size",
        ],
        "rng_reset_permitted": False,
        "rng_consumption": "fisher_yates_and_registered_bounded_rejection_sampling_only",
        "force_keep_when_mulligans_taken_equals": 6,
        "bottom_count": "max(0, mulligans_taken - free_mulligans)",
        "bottoming_consumes_rng": False,
        "bottom_placement": "append_selected_cards_to_current_post_draw_library_in_selection_order",
    }
    if transition != expected_transition:
        errors.append("policy executable mulligan transition is incomplete")
    checks.append(("policy has versioned v5 executable ownership", errors))

    errors = []
    expected_refs = {
        "card_semantics": ("workshop/projects/the-myr-singularity/simulation/card_semantics.json", semantics),
        "mana_source_semantics": ("workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json", docs["mana_source_semantics"]),
        "canonical_card_facts": ("workshop/card-data/cards.json", docs["cards"]),
        "failure_pattern_taxonomy": ("workshop/projects/the-myr-singularity/simulation/contracts/failure_pattern_taxonomy.json", taxonomy),
        "simulation_question_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json", docs["question_contract"]),
        "simulation_run_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_run.contract.json", docs["run_contract"]),
        "simulation_result_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/simulation_result.contract.json", docs["result_contract"]),
        "comparison_result_contract": ("workshop/projects/the-myr-singularity/simulation/contracts/comparison_result.contract.json", docs["comparison_contract"]),
    }
    for key, (path, document) in expected_refs.items(): errors.extend(_check_reference((policy.get("references") or {}).get(key), path, document, f"policy.references.{key}"))
    checks.append(("policy pins every immutable semantic dependency without self-hashing", errors))

    errors = validate_mana_source_semantics(
        docs["mana_source_semantics"], policy=policy, cards=docs["cards"]["cards"],
        versions=[load_json(PROJECT / "versions" / "v1.0.json"), load_json(PROJECT / "versions" / "v1.1.json")],
    )
    checks.append(("normalized source registry covers v1.0/v1.1 with controlled executable semantics", errors))

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
    if semantics.get("policy_version") != "sim-policy-v5": errors.append("card semantics must bind sim-policy-v5")
    saga = next((e for e in semantics.get("entries", []) if e.get("card_identity", {}).get("name") == "Urza's Saga"), {})
    if saga.get("source", {}).get("oracle_basis") != "Saga land with a Chapter I {T}: Add {C} ability and a Chapter III ability.": errors.append("Urza's Saga must use the approved narrow oracle basis")
    if "upkeep" in saga.get("source", {}).get("oracle_basis", "").casefold(): errors.append("Urza's Saga source basis must not contain upkeep")
    if saga.get("time_dependent_availability", {}).get("removal_event", {}).get("trigger") != "final_chapter_ability_leaves_stack": errors.append("Urza's Saga removal trigger is incorrect")
    checks.append(("Urza's Saga source prose and bounded removal are consistent", errors))

    errors = validate_failure_pattern_taxonomy(taxonomy, policy=policy, question=question)
    checks.append(("failure taxonomy v4 is a complete fail-closed emission contract", errors))

    errors = validate_card_semantics_registry_parity(semantics, docs["mana_source_semantics"])
    checks.append(("card semantics and executable registry have one result-changing interpretation", errors))

    errors = validate_simulation_question(
        question, policy=policy, question_contract=docs["question_contract"], project_id=PROJECT_ID,
        load_reference=lambda path: load_json(REPO_ROOT / path),
        fingerprint_for_version=lambda version: deck_content_fingerprint(version, docs["cards"]["cards"]),
    )
    required = {(m.get("metric_id"), m.get("target_turn")) for m in question.get("required_metrics", [])}
    optional = {(m.get("metric_id"), m.get("target_turn")) for m in question.get("optional_metrics", [])}
    if {mid for mid, _ in required} != EXPECTED_METRICS - {"commander_castability_by_turn"}: errors.append("question required_metrics must contain first eight metrics")
    if {mid for mid, _ in optional} != {"commander_castability_by_turn"}: errors.append("question optional_metrics must contain commander castability")
    checks.append(("question structurally separates required and optional metrics", errors))

    errors = []
    for name, expected_id in (("question_contract", "simulation-question-contract-v3"), ("run_contract", "simulation-run-contract-v4"), ("result_contract", "simulation-result-contract-v4"), ("comparison_contract", "comparison-result-contract-v4"), ("lifecycle_contract", "simulation-question-lifecycle-contract-v1")):
        if docs[name].get("contract_id") != expected_id: errors.append(f"{name} has an unexpected contract identity")
    if docs["question_contract"].get("required_fields", {}).get("compared_versions", {}).get("exact_item_count") != 2:
        errors.append("Question contract must require exactly two compared DeckVersions")
    if docs["run_contract"].get("required_fields", {}).get("selected_metrics", {}).get("item_required_fields") != ["metric_id", "target_turn"]:
        errors.append("Run contract must declare exact selected_metrics item fields")
    if "exactly equal source SimulationRun.selected_metrics in the same order" not in docs["result_contract"].get("required_fields", {}).get("metrics", {}).get("description", ""):
        errors.append("Result contract must bind metrics to ordered Run selected_metrics")
    if "shared ordered SimulationRun.selected_metrics" not in docs["comparison_contract"].get("required_fields", {}).get("metric_deltas", {}).get("description", ""):
        errors.append("Comparison contract must bind deltas to shared ordered selected_metrics")
    lifecycle_evidence = docs["lifecycle_contract"].get("required_fields", {}).get("recorded_evidence", {})
    invalidation = docs["lifecycle_contract"].get("required_fields", {}).get("invalidation", {})
    if set(lifecycle_evidence.get("reference_shape", {})) != {"id", "path", "content_fingerprint"} or lifecycle_evidence.get("state_cardinality", {}).get("runs_recorded") != {"runs": 2, "results": 0, "comparison": False}:
        errors.append("Lifecycle contract must declare exact reference shape and cardinality")
    if invalidation.get("reason_contract_id") != "simulation-lifecycle-invalidation-v1" or not invalidation.get("allowed_reason_ids"):
        errors.append("Lifecycle contract must freeze a versioned invalidation reason vocabulary")
    checks.append(("materially changed contracts use v4 identities and lifecycle v1", errors))

    errors = []
    legacy_level2 = (policy.get("sequencing_semantics") or {}).get("level_2_mana_development") or {}
    legacy_text = json.dumps(legacy_level2, sort_keys=True)
    if "canonical produced_mana, or explicitly modeled" in legacy_text or "Conditional, activated-cost-dependent" in legacy_text or "canonical produced_mana list" in legacy_text:
        errors.append("legacy Level 2 source authority contradicts the executable mana-source registry")
    if "mana_source_semantics.json" not in legacy_text:
        errors.append("legacy Level 2 section does not delegate executable behavior to the registry")
    limitations = ((policy.get("card_behavior_boundary") or {}).get("unsupported_behavior_handling") or {}).get("limitation_representation")
    if limitations != {
        "format": "unsupported_mana_profile:<oracle_id>:<unsupported_reason_id>",
        "derivation": "For every unsupported executable profile on a source present in the run DeckVersion, derive exactly one limitation ID. The SimulationRun and its SimulationResult must both carry the complete applicable set.",
        "metric_boundary": "Unsupported behavior contributes zero modeled mana/colors and cannot improve a success metric.",
    }:
        errors.append("unsupported behavior limitation representation is incomplete")
    checks.append(("Level 2 has one registry authority and deterministic unsupported limitations", errors))

    errors = []
    level2 = policy.get("level_2_sequencing", {})
    if level2.get("turn_order") != ['untap_and_clear_floating_mana','draw','advance_time_dependent_state','select_and_play_one_land','repeatedly_deploy_payable_registered_ramp','resolve_pending_time_dependent_removals','record_end_of_turn_observations']:
        errors.append("Level 2 turn order is not frozen")
    if not level2.get("land_selection_priority") or not level2.get("ramp_deployment_priority") or not level2.get("payment_priority"):
        errors.append("Level 2 selection and payment priorities are incomplete")
    if level2.get("mana_source_resolution", {}).get("state_transition_timing") != "registered end-step removal conditions execute after deterministic same-turn development actions and before the applicable end-of-turn observation":
        errors.append("Level 2 source state-transition timing is not frozen")
    projection = level2.get("mana_source_projection") or {}
    if projection.get("contract_id") != "mana-source-projection-v1" or set((projection.get("land_selector_fields") or {})) != {"colors", "five_color_source", "permanent", "remaining_availability", "mana_units", "identity"} or set((projection.get("ramp_selector_fields") or {})) != {"payable", "same_turn_online_noncreature", "output_units", "color_flexibility", "mana_value", "identity"}:
        errors.append("Level 2 mana-source selector projection is incomplete")
    phases = projection.get("condition_evaluation_phases") or {}
    if phases != {
        "land_candidate": {
            "generic_payment_available_from_other_sources": "pre_play_resources_excluding_candidate",
            "complete_tron_set_controlled": "hypothetical_post_play_controlled_lands_including_candidate",
            "bounded_controller_turn_window": "candidate_controller_turn_offset_default_zero",
            "commander_color_identity": "static_scenario_state",
            "artifact_controlled": "pre_selection_state_for_selector_persistence",
            "end_step_remove_unless_condition": "post_development_state",
        },
        "ramp_candidate": {
            "deployment_payment": "pre_deployment_resources",
            "activation_profiles": "post_deployment_residual_resources_after_reserved_payment",
            "self_funding": "forbidden",
        },
        "end_of_turn_source_capability_observation": {
            "evaluation_phase": "after_deterministic_development_and_pending_removals_before_end_of_turn_observation",
            "source_snapshot": "surviving_online_sources_after_post_development_removals",
            "earlier_tapping_and_spending": "do_not_remove_gross_source_capability",
            "generic_payment_available_from_other_sources": "gross_nonrecursive_base_capacity_from_other_surviving_online_sources",
            "self_funding": "forbidden",
            "conditional_profiles_feed_base_capacity": False,
            "spendable_mana_relation": "remaining_untapped_payable_resources_only",
        },
    }:
        errors.append("Level 2 condition evaluation phases are not frozen")
    if "W, U, B, R, and G" not in (projection.get("land_selector_fields") or {}).get("colors", "") or "C never contributes" not in (projection.get("land_selector_fields") or {}).get("colors", ""):
        errors.append("Level 2 land selector colors are not restricted to commander colors")
    observation = projection.get("source_capability_observation") or {}
    if observation.get("contract_id") != "source-capability-observation-v1" or observation.get("projection") != "gross_surviving_online_capability":
        errors.append("EOT source-capability observation contract is incomplete")
    checks.append(("Level 2 trace sequencing and EOT source capability are explicit and deterministic", errors))

    errors = validate_simulation_question_lifecycle(
        docs["lifecycle"], question=question, lifecycle_contract=docs["lifecycle_contract"], project_id=PROJECT_ID,
        load_reference=lambda path: load_json(REPO_ROOT / path),
    )
    if docs["lifecycle"].get("state") != "preregistered":
        errors.append("question-001 lifecycle must remain preregistered without production evidence")
    checks.append(("immutable Question has canonical preregistered lifecycle state", errors))

    errors = []
    expected_recording = {
        "simulation_run.contract.json": ("run_id", False),
        "simulation_result.contract.json": ("result_id", "created_at"),
        "comparison_result.contract.json": ("comparison_id", "created_at"),
    }
    for name, (identifier, timestamp) in expected_recording.items():
        context = docs[{"simulation_run.contract.json": "run_contract", "simulation_result.contract.json": "result_contract", "comparison_result.contract.json": "comparison_contract"}[name]].get("recording_context") or {}
        errors.extend(f"{name} {error}" for error in validate_recording_context(context, id_field=identifier, created_at_required=timestamp is not False))
    checks.append(("persisted RecordingContext keeps identity and time outside the engine", errors))

    errors = []
    for path in SIM.rglob("*.json"):
        try: document = load_json(path)
        except ValueError: continue
        if document.get("artifact_type") in INSTANCE_TYPES: errors.append(f"production simulation evidence is present: {path.relative_to(REPO_ROOT)}")
    checks.append(("no production Run, Result, or Comparison is created", errors))
    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
