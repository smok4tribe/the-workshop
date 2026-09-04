"""Reusable validation for future simulation evidence instances.

This module is production-neutral: callers inject repository resolution and it
does not discover or create evidence artifacts itself.
"""

from __future__ import annotations

import math
import json
import re
from collections.abc import Mapping
from datetime import datetime

from workshop.shared.identity import artifact_content_fingerprint, deck_content_fingerprint
from workshop.shared.simulation_determinism import (
    APPROVED_RUNTIME_MANA_SOURCE_SEMANTICS_FINGERPRINT,
    SimulationRuntimeContext,
    _authenticate_runtime_context,
    _condition_state_for_conditions,
    _condition_is_satisfied,
    _resolve_activation_profiles,
    _resolve_runtime_record,
    _validate_condition_state,
    derive_run_seed,
)


DEPENDENCY_KEYS = (
    "policy", "question", "card_semantics", "mana_source_semantics", "canonical_card_facts",
    "failure_pattern_taxonomy", "simulation_question_contract",
    "simulation_run_contract", "simulation_result_contract",
    "comparison_result_contract",
)
SOURCE_KINDS = {"land", "mana_rock", "mana_creature"}
MANA_SYMBOLS = {"W", "U", "B", "R", "G", "C"}
GROUP_SELECTIONS = {"highest_priority_matching_profile", "independent_modes"}
OUTPUT_SELECTIONS = {"fixed", "one_choice", "any_combination"}
ONLINE_MODELS = {"immediate", "next_controller_turn", "bounded_window"}
UNTAP_MODELS = {"normal", "does_not_naturally_untap"}
CONDITION_PARAMS = {
    "artifact_controlled": {"minimum_count"},
    "complete_tron_set_controlled": {"oracle_ids"},
    "generic_payment_available_from_other_sources": {"required_units"},
    "commander_color_identity": {"colors"},
    "bounded_controller_turn_window": {"start_offset", "end_offset", "removal_event"},
}
STATE_TRANSITION_EVENTS = {"end_step_remove_unless_condition"}
REGISTRY_FIELDS = {
    "schema_version", "artifact_type", "artifact_id", "project_id", "policy_version",
    "condition_vocabulary", "unsupported_reason_ids", "records",
}
RECORD_FIELDS = {"card_name", "oracle_id", "source_kind", "deployment", "activation_groups", "state_transitions"}
DEPLOYMENT_FIELDS = {"casting_cost", "counts_as_land_drop"}
CASTING_COST_FIELDS = {"generic", "colored"}
ACTIVATION_GROUP_FIELDS = {"group_id", "selection", "profiles"}
PROFILE_FIELDS = {
    "profile_id", "priority", "mana_units", "output_capabilities", "output_selection",
    "tap_model", "payment", "conditions", "online_model", "natural_untap_model",
    "supported", "unsupported_reason_id",
}
PAYMENT_FIELDS = {"generic", "colored", "life"}
LIFE_FIELDS = {"amount", "treatment"}
CONDITION_FIELDS = {"condition_id", "params"}
STATE_TRANSITION_FIELDS = {"event_id", "condition"}
ALLOWED_SUBJECTS = {
    "hand_composition", "land_development", "ramp_access", "mana_development",
    "color_availability", "limitations",
}
RESERVED_LIFECYCLE_KEYS = {"reasoning_interpretation", "product_owner_decision"}
QUESTION_INSTANCE_FIELDS = {
    "schema_version", "artifact_type", "question_id", "project_id", "policy_id",
    "policy_version", "generated_at", "generated_by", "hypothesis", "question_text",
    "compared_versions", "success_interpretation", "limitations", "explicit_boundary",
    "policy_reference", "required_metrics", "optional_metrics", "comparison_sides",
}
QUESTION_LIFECYCLE_FIELDS = {
    "schema_version", "artifact_type", "lifecycle_id", "project_id", "question_id",
    "question_path", "question_content_fingerprint", "state", "recorded_evidence",
    "invalidation",
}
LIFECYCLE_STATES = {
    "preregistered", "runs_recorded", "results_recorded", "comparison_recorded", "invalidated",
}
LIFECYCLE_MODES = {"creation", "persistence"}
LIFECYCLE_INVALIDATION_REASON_IDS = {
    "operator_cancelled", "source_artifact_invalidated", "evidence_integrity_failure",
    "execution_environment_invalidated",
}
CANONICAL_POLICY_PATH = "workshop/projects/the-myr-singularity/simulation/simulation_policy.json"
CANONICAL_QUESTION_DIRECTORY = "workshop/projects/the-myr-singularity/simulation/questions"
CANONICAL_LIFECYCLE_DIRECTORY = "workshop/projects/the-myr-singularity/simulation/lifecycle"
CANONICAL_QUESTION_CONTRACT_PATH = "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question.contract.json"
CANONICAL_LIFECYCLE_CONTRACT_PATH = "workshop/projects/the-myr-singularity/simulation/contracts/simulation_question_lifecycle.contract.json"
QUESTION_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARTIFACT_FINGERPRINT_RE = re.compile(r"^artifact-content-sha256-v1:[0-9a-f]{64}$")
POLICY_CONTRACT_REGISTRY = {
    "simulation_question_contract": {
        "path": CANONICAL_QUESTION_CONTRACT_PATH,
        "artifact_type": "simulation_question_contract",
        "contract_id": "simulation-question-contract-v4",
        "schema_version": "4.0",
        "argument_name": "question_contract",
    },
    "simulation_run_contract": {
        "path": "workshop/projects/the-myr-singularity/simulation/contracts/simulation_run.contract.json",
        "artifact_type": "simulation_run_contract",
        "contract_id": "simulation-run-contract-v5",
        "schema_version": "5.0",
        "argument_name": "run_contract",
    },
    "simulation_result_contract": {
        "path": "workshop/projects/the-myr-singularity/simulation/contracts/simulation_result.contract.json",
        "artifact_type": "simulation_result_contract",
        "contract_id": "simulation-result-contract-v5",
        "schema_version": "5.0",
        "argument_name": "result_contract",
    },
    "comparison_result_contract": {
        "path": "workshop/projects/the-myr-singularity/simulation/contracts/comparison_result.contract.json",
        "artifact_type": "comparison_result_contract",
        "contract_id": "comparison-result-contract-v5",
        "schema_version": "5.0",
        "argument_name": "comparison_contract",
    },
}
APPROVED_LIFECYCLE_CONTRACT_FINGERPRINT = "artifact-content-sha256-v1:d8e85971e266ae51a781d69a24fa8006a24d05c5096feeb1e30d47d68619f9bc"
APPROVED_MANA_SOURCE_SEMANTICS_FINGERPRINT = APPROVED_RUNTIME_MANA_SOURCE_SEMANTICS_FINGERPRINT
APPROVED_SIMULATION_POLICY_FINGERPRINT = "artifact-content-sha256-v1:ea26388ed56b9e8145bc70a98320227c9d04fefd51cc6ee6a3b09200a888495f"
APPROVED_FAILURE_PATTERN_TAXONOMY_FINGERPRINT = "artifact-content-sha256-v1:7e2413fbca56dddfea2a16491548b95138191f0badfd80c5cecb0c9bf51b8742"
RECORDING_CONTEXT_ID = "simulation-recording-context-v1"
RECORDING_ARTIFACT_ALGORITHM = "artifact-content-sha256-v1"
RECORDING_ARTIFACT_COVERAGE = "The complete persisted artifact, including caller-supplied recording metadata."
RECORDING_REPLAY_EQUIVALENCE = "Deterministic semantic/execution equivalence; it does not require identical artifact-content identity when recording metadata differs."


def _measurement_contract(*, level, target_turn, shape, observation_point, event=None, value=None):
    """Build the Policy-owned complete contract for one registered metric."""
    contract = {
        "contract_id": "metric-measurement-v1",
        "population": {
            "id": "all_preregistered_run_iterations",
            "iteration_index_range": {
                "first": 1,
                "last": "simulation_run.iteration_count",
                "inclusive": True,
            },
            "conditional_exclusion_permitted": False,
            "observation_failure": "invalidates_run_and_result",
        },
        "sample_size_rule": {
            "id": "equals_run_iteration_count",
            "source": "simulation_run.iteration_count",
        },
        "sequencing_level": level,
        "target_turn": target_turn,
        "target_turn_semantics": "metric.target_turn",
        "observation_point": observation_point,
        "unsupported_behavior": {
            "iteration_remains_in_population": True,
            "cannot_contribute_to_success": True,
            "supported_behavior_may_independently_succeed": True,
        },
        "result_shape": shape,
    }
    if event is not None:
        contract["event"] = event
    if value is not None:
        contract["value"] = value
    return contract


METRIC_MEASUREMENT_CONTRACTS = {
    "keepable_opening_hand_rate": _measurement_contract(
        level="level_1", target_turn=0, shape="bernoulli_probability",
        observation_point={"id": "first_natural_opening_hand", "hand_size": 7, "before_mulligan": True},
        event={"id": "initial_hand_satisfies_registered_keep_rule", "keep_rule_id": "myr-singularity-keep-v1", "one_land_exception_source": "keep_rule.base_rule.one_land_exception"},
    ),
    "zero_land_hand_rate": _measurement_contract(
        level="level_1", target_turn=0, shape="bernoulli_probability",
        observation_point={"id": "first_natural_opening_hand", "hand_size": 7, "before_mulligan": True},
        event={"id": "initial_hand_land_count_equals", "land_count": 0},
    ),
    "one_land_hand_rate": _measurement_contract(
        level="level_1", target_turn=0, shape="bernoulli_probability",
        observation_point={"id": "first_natural_opening_hand", "hand_size": 7, "before_mulligan": True},
        event={"id": "initial_hand_land_count_equals", "land_count": 1},
    ),
    "excessive_land_hand_rate": _measurement_contract(
        level="level_1", target_turn=0, shape="bernoulli_probability",
        observation_point={"id": "first_natural_opening_hand", "hand_size": 7, "before_mulligan": True},
        event={"id": "initial_hand_land_count_inclusive_range", "minimum_land_count": 6, "maximum_land_count": 7},
    ),
    "land_drop_success_by_turn": _measurement_contract(
        level="level_2", target_turn=6, shape="bernoulli_probability",
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True},
        event={"id": "legal_land_drop_on_every_turn", "first_required_turn": 1, "last_required_turn": "metric.target_turn", "inclusive": True, "later_removal_erases_historical_success": False},
    ),
    "ramp_access_by_turn": _measurement_contract(
        level="level_1", target_turn=3, shape="bernoulli_probability",
        observation_point={"id": "final_kept_hand_plus_normal_draws_through_target_turn", "hand_state": "final_kept_hand", "draw_window": "normal_draws_through_target_turn"},
        event={"id": "registered_ramp_identity_seen", "registry_ref": "ramp_access_registry.oracle_ids", "access_only": True, "requires_castability": False, "requires_deployment": False, "requires_online": False, "requires_mana_production": False},
    ),
    "distinct_commander_colors_by_turn": _measurement_contract(
        level="level_2", target_turn=6, shape="categorical_count",
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True, "source_capability_observation_contract_id": "source-capability-observation-v1"},
        value={"id": "surviving_online_source_capability_color_cardinality", "projection": "source_capability", "domain": [0, 1, 2, 3, 4, 5], "colors": ["W", "U", "B", "R", "G"], "excluded_colors": ["C"], "source_state": "surviving_and_online", "earlier_tapping_removes_capability": False},
    ),
    "five_color_availability_by_turn": _measurement_contract(
        level="level_2", target_turn=6, shape="bernoulli_probability",
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True, "source_capability_observation_contract_id": "source-capability-observation-v1"},
        event={"id": "all_required_source_capability_colors_available", "projection": "source_capability", "required_colors": ["W", "U", "B", "R", "G"], "excluded_colors": ["C"], "source_state": "surviving_and_online", "earlier_tapping_removes_capability": False, "requires_simultaneous_spendable_mana": False, "requires_commander_castability": False},
    ),
    "commander_castability_by_turn": _measurement_contract(
        level="level_2", target_turn=3, shape="bernoulli_probability",
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True},
        event={"id": "legal_commander_payment_exists", "projection": "spendable_mana", "resources": "remaining_untapped_after_development", "cost_source": "current_modeled_command_zone_cost", "commander_card_reference": {"path": "workshop/card-data/cards.json", "oracle_id": "6222fccf-fc08-4190-8d40-a56d6d1423df", "mana_cost": "{3}"}, "base_cost": {"generic": 3, "colored": []}, "previous_commander_casts": 0, "commander_tax_generic": 0, "alternate_or_unmodeled_resources_allowed": False, "commander_actually_cast": False},
    ),
}


def validate_policy_metric_contracts(policy):
    """Validate that the resolved Policy completely owns all metric semantics."""
    metrics = (policy.get("metric_catalog") or {}).get("metrics")
    if not isinstance(metrics, list):
        return ["policy metric_catalog.metrics must be an array"]
    by_id = {metric.get("metric_id"): metric for metric in metrics if isinstance(metric, dict)}
    errors = []
    if len(by_id) != len(metrics) or set(by_id) != set(METRIC_MEASUREMENT_CONTRACTS):
        errors.append("policy metric catalog must contain each registered metric exactly once")
        return errors
    for metric_id, expected in METRIC_MEASUREMENT_CONTRACTS.items():
        metric = by_id[metric_id]
        for field in ("level", "target_turn", "shape"):
            if metric.get(field) != expected["%s" % {"level": "sequencing_level", "target_turn": "target_turn", "shape": "result_shape"}[field]]:
                errors.append(f"policy metric {metric_id} {field} does not match its measurement_contract")
        if metric.get("measurement_contract") != expected:
            errors.append(f"policy metric {metric_id} measurement_contract is incomplete or does not match the preregistered semantics")
    return errors


def _required(value, fields, label):
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    return [f"{label} is missing required field {field!r}" for field in fields if field not in value]


def _unregistered_top_level_field_errors(value, contract, label):
    if not isinstance(value, dict):
        return []
    allowed = set((contract.get("required_fields") or {}).keys())
    extras = sorted(set(value) - allowed)
    if extras:
        return [f"{label} has unregistered top-level fields: {', '.join(extras)}"]
    return []


def _reserved_lifecycle_key_errors(value, path="$"):
    """Return structural lifecycle-key violations at every evidence depth."""
    errors = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in RESERVED_LIFECYCLE_KEYS:
                errors.append(f"reserved lifecycle field is not permitted at {child}")
            errors.extend(_reserved_lifecycle_key_errors(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_reserved_lifecycle_key_errors(item, f"{path}[{index}]"))
    return errors


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _rounded_matches(actual, expected):
    if not _number(actual):
        return False
    text = format(actual, "f").rstrip("0").rstrip(".")
    places = len(text.partition(".")[2])
    return round(expected, places) == actual


def wilson_interval(raw_count, sample_size):
    z = 1.959963984540054
    probability = raw_count / sample_size
    denominator = 1 + z * z / sample_size
    center = (probability + z * z / (2 * sample_size)) / denominator
    margin = z * math.sqrt(probability * (1 - probability) / sample_size + z * z / (4 * sample_size * sample_size)) / denominator
    return center - margin, center + margin


def render_evidence_claims(claims):
    """The sole permitted persisted readable-summary representation."""
    return " | ".join(
        f"{claim['claim_type']}:{claim.get('metric_id', 'limitation')}@{claim.get('target_turn', '-') }"
        for claim in claims
    )


def _resolve_reference(reference, label, errors, load_reference, expected=None):
    if not isinstance(reference, dict):
        errors.append(f"{label} must be an immutable reference object")
        return None
    path = reference.get("path")
    fingerprint = reference.get("content_fingerprint")
    if not isinstance(path, str) or not path:
        errors.append(f"{label}.path must be a non-empty repo-relative path")
        return None
    try:
        resolved = load_reference(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"{label} does not resolve: {exc}")
        return None
    if artifact_content_fingerprint(resolved) != fingerprint:
        errors.append(f"{label} content fingerprint does not match resolved artifact")
    if expected is not None and resolved != expected:
        errors.append(f"{label} does not resolve to the expected artifact")
    return resolved


def resolve_policy_pinned_contract(policy, supplied_contract, *, reference_key, load_reference):
    """Resolve one trusted Policy-pinned contract without caller-data fallback."""
    errors = []
    trusted = POLICY_CONTRACT_REGISTRY.get(reference_key)
    if trusted is None:
        return None, [f"unsupported Policy contract reference {reference_key!r}"]
    reference = (policy.get("references") or {}).get(reference_key) if isinstance(policy, dict) else None
    if not isinstance(reference, dict) or set(reference) != {"path", "content_fingerprint"}:
        return None, [f"policy {reference_key} reference has an invalid field set"]
    if reference.get("path") != trusted["path"]:
        errors.append(f"policy {reference_key} reference path is not canonical")
    fingerprint = reference.get("content_fingerprint")
    if not isinstance(fingerprint, str) or not ARTIFACT_FINGERPRINT_RE.fullmatch(fingerprint):
        errors.append(f"policy {reference_key} reference has an invalid content fingerprint")
    resolved = _resolve_reference(reference, f"policy {reference_key} reference", errors, load_reference)
    if not isinstance(resolved, dict):
        return None, errors
    if resolved.get("artifact_type") != trusted["artifact_type"]:
        errors.append(f"policy {reference_key} does not resolve to the trusted artifact_type")
    if resolved.get("contract_id") != trusted["contract_id"]:
        errors.append(f"policy {reference_key} does not resolve to the trusted contract_id")
    if resolved.get("schema_version") != trusted["schema_version"]:
        errors.append(f"policy {reference_key} does not resolve to the trusted schema_version")
    if resolved.get("policy_version") != policy.get("policy_version"):
        errors.append(f"policy {reference_key} contract policy_version does not match the Policy")
    if supplied_contract != resolved:
        errors.append(
            f"supplied {trusted['argument_name']} does not match the Policy-resolved immutable "
            f"{trusted['artifact_type'].replace('_', ' ')}"
        )
    if errors:
        return None, errors
    return resolved, []


def _resolve_policy_question_contract(policy, supplied_contract, load_reference):
    return resolve_policy_pinned_contract(
        policy, supplied_contract,
        reference_key="simulation_question_contract",
        load_reference=load_reference,
    )


def _resolve_canonical_lifecycle_contract(supplied_contract, load_reference):
    """Resolve and freeze the v1 lifecycle contract before validating evidence."""
    errors = []
    try:
        canonical = load_reference(CANONICAL_LIFECYCLE_CONTRACT_PATH)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return supplied_contract, [f"canonical lifecycle contract does not resolve: {exc}"]
    if artifact_content_fingerprint(canonical) != APPROVED_LIFECYCLE_CONTRACT_FINGERPRINT:
        errors.append("canonical lifecycle contract does not match the approved v1 identity")
    if supplied_contract != canonical:
        errors.append("supplied lifecycle_contract does not match the canonical v1 lifecycle contract")
    required_fields = canonical.get("required_fields") if isinstance(canonical, dict) else None
    expected_top_level = {
        "schema_version", "artifact_type", "contract_id", "project_id", "purpose", "required_fields",
        "canonical_path_rule", "transitions", "recording_identity_rules", "persistence_boundary", "seed_boundary",
    }
    if (
        not isinstance(canonical, dict)
        or set(canonical) != expected_top_level
        or canonical.get("schema_version") != "1.0"
        or canonical.get("artifact_type") != "simulation_question_lifecycle_contract"
        or canonical.get("contract_id") != "simulation-question-lifecycle-contract-v1"
        or canonical.get("project_id") != "the-myr-singularity"
        or not isinstance(required_fields, dict)
        or set(required_fields) != QUESTION_LIFECYCLE_FIELDS
    ):
        errors.append("canonical lifecycle contract has invalid v1 structural requirements")
    return canonical if isinstance(canonical, dict) else supplied_contract, errors


def validate_question_role_bindings(compared_versions):
    if not isinstance(compared_versions, list):
        return ["question compared_versions must be an array"]
    errors, versions, roles = [], [], []
    for index, item in enumerate(compared_versions):
        if not isinstance(item, dict):
            errors.append(f"question compared_versions[{index}] must be an object")
            continue
        version_id, role = item.get("deck_version_id"), item.get("run_role")
        if not isinstance(version_id, str) or not version_id:
            errors.append(f"question compared_versions[{index}] is missing deck_version_id")
        else:
            versions.append(version_id)
        if not isinstance(role, str) or not role:
            errors.append(f"question compared_versions[{index}] is missing run_role")
        else:
            roles.append(role)
    if len(versions) != len(set(versions)):
        errors.append("question compared_versions must contain each DeckVersion once")
    if len(roles) != len(set(roles)):
        errors.append("question compared_versions must use unique run_role values")
    return errors


def validate_question_comparison_sides(comparison_sides, compared_versions):
    errors = []
    fields = {"baseline_run_role", "candidate_run_role"}
    if not isinstance(comparison_sides, dict) or set(comparison_sides) != fields:
        return ["question comparison_sides must contain exactly baseline_run_role and candidate_run_role"]
    roles = []
    for field in ("baseline_run_role", "candidate_run_role"):
        role = comparison_sides.get(field)
        if not isinstance(role, str) or not role:
            errors.append(f"question comparison_sides.{field} must be a non-empty string")
        else:
            roles.append(role)
    if len(roles) == 2 and roles[0] == roles[1]:
        errors.append("question comparison_sides roles must be distinct")
    compared_roles = [
        item.get("run_role") for item in compared_versions
        if isinstance(item, dict) and isinstance(item.get("run_role"), str) and item.get("run_role")
    ]
    for role in roles:
        if compared_roles.count(role) != 1:
            errors.append(f"question comparison_sides role {role!r} must resolve exactly one compared version")
    if len(roles) == 2 and set(roles) != set(compared_roles):
        errors.append("question comparison_sides must exactly cover both compared version roles")
    return errors


def canonical_question_path(question_id):
    """Return the canonical path for a validated Question identity."""
    if (
        not isinstance(question_id, str)
        or not 1 <= len(question_id) <= 64
        or not QUESTION_ID_RE.fullmatch(question_id)
    ):
        raise ValueError("question_id must be a 1..64 character lowercase kebab-case identity")
    return f"{CANONICAL_QUESTION_DIRECTORY}/{question_id}.json"


def lifecycle_path_for_question(question_id):
    """Return the single canonical mutable lifecycle path for a Question."""
    return f"{CANONICAL_LIFECYCLE_DIRECTORY}/{question_id}.json"


def _question_metric_entries(question, policy):
    """Validate generic Question metric subsets against the resolved Policy."""
    errors = []
    catalog = _metric_catalog(policy)
    catalog_by_id = {metric.get("metric_id"): metric for metric in catalog.values() if isinstance(metric, dict)}
    required = question.get("required_metrics")
    optional = question.get("optional_metrics")
    if not isinstance(required, list) or not required:
        errors.append("question required_metrics must be a non-empty array")
        required = []
    if not isinstance(optional, list):
        errors.append("question optional_metrics must be an array")
        optional = []

    def validate(entries, label, permitted_kinds):
        keys = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != {"metric_id", "target_turn"}:
                errors.append(f"question {label}[{index}] must contain exactly metric_id and target_turn")
                continue
            key = _metric_key(entry)
            metric = catalog.get(key)
            if metric is None:
                if entry.get("metric_id") in catalog_by_id:
                    errors.append(f"question {label}[{index}] target_turn does not match the Policy metric definition")
                else:
                    errors.append(f"question {label}[{index}] does not resolve to a Policy metric definition")
                continue
            if metric.get("kind") not in permitted_kinds:
                errors.append(f"question {label}[{index}] is not permitted for that metric kind")
            if metric.get("target_turn") != entry.get("target_turn"):
                errors.append(f"question {label}[{index}] target_turn does not match the Policy metric definition")
            keys.append(key)
        if len(keys) != len(set(keys)):
            errors.append(f"question {label} must be duplicate-free")
        return keys

    required_keys = validate(required, "required_metrics", {"primary"})
    optional_keys = validate(optional, "optional_metrics", {"optional_sanity"})
    if set(required_keys) & set(optional_keys):
        errors.append("question required_metrics and optional_metrics must be disjoint")
    return errors


def validate_simulation_question(question, *, policy, question_contract, project_id, load_reference, fingerprint_for_version, question_path=None):
    """Fail closed on an immutable preregistered SimulationQuestion."""
    effective_contract, errors = _resolve_policy_question_contract(policy, question_contract, load_reference)
    if effective_contract is None:
        return errors
    errors.extend(_required(question, (effective_contract.get("required_fields") or {}).keys(), "question"))
    if not isinstance(question, dict):
        return errors
    extras = sorted(set(question) - QUESTION_INSTANCE_FIELDS)
    if extras:
        errors.append(f"question has unregistered top-level fields: {', '.join(extras)}")
    if question.get("schema_version") != "4.0":
        errors.append("question schema_version must be 4.0")
    if question.get("artifact_type") != "simulation_question":
        errors.append("question artifact_type must be 'simulation_question'")
    if question.get("project_id") != project_id:
        errors.append("question project_id does not match the project")
    try:
        derived_question_path = canonical_question_path(question.get("question_id"))
    except ValueError as exc:
        derived_question_path = None
        errors.append(str(exc))
    if not isinstance(question_path, str) or not question_path:
        errors.append("question source path must be a non-empty caller-supplied string")
    if derived_question_path is not None:
        if isinstance(question_path, str) and question_path and question_path != derived_question_path:
            errors.append("question source path does not match the canonical path derived from question_id")
        try:
            canonical_question = load_reference(derived_question_path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"canonical Question does not resolve: {exc}")
        else:
            if canonical_question != question:
                errors.append("supplied Question does not match the canonical Question resolved from question_id")
    if question.get("policy_id") != policy.get("policy_id") or question.get("policy_version") != policy.get("policy_version"):
        errors.append("question policy binding does not match the resolved policy")
    reference = question.get("policy_reference")
    if not isinstance(reference, dict) or reference.get("path") != CANONICAL_POLICY_PATH:
        errors.append("question policy_reference.path is not the canonical SimulationPolicy path")
    if not isinstance(reference, dict) or set(reference) != {"path", "content_fingerprint"}:
        errors.append("question policy_reference has an invalid field set")
    _resolve_reference(reference, "question policy_reference", errors, load_reference, policy)

    compared = question.get("compared_versions")
    expected_compared_count = ((effective_contract.get("required_fields") or {}).get("compared_versions") or {}).get("exact_item_count")
    if not isinstance(compared, list) or not _integer(expected_compared_count):
        errors.append("question compared_versions contract must declare an exact item count")
        compared = []
    elif len(compared) != expected_compared_count:
        errors.append(f"question compared_versions must contain exactly {expected_compared_count} DeckVersions")
    errors.extend(validate_question_role_bindings(compared))
    errors.extend(validate_question_comparison_sides(question.get("comparison_sides"), compared))
    paths = []
    for index, item in enumerate(compared):
        if not isinstance(item, dict) or set(item) != {"deck_version_id", "path", "run_role", "deck_content_fingerprint"}:
            errors.append(f"question compared_versions[{index}] has an invalid field set")
            continue
        path = item.get("path")
        paths.append(path)
        try:
            version = load_reference(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"question compared_versions[{index}] DeckVersion does not resolve: {exc}")
            continue
        if item.get("deck_version_id") != version.get("version_id"):
            errors.append(f"question compared_versions[{index}] deck_version_id does not match DeckVersion")
        if item.get("deck_content_fingerprint") != fingerprint_for_version(version):
            errors.append(f"question compared_versions[{index}] fingerprint does not match DeckVersion")
    if len(paths) != len(set(paths)):
        errors.append("question compared_versions must contain distinct DeckVersion paths")
    errors.extend(_question_metric_entries(question, policy))

    boundary = question.get("explicit_boundary")
    if not isinstance(boundary, dict) or set(boundary) != {"statement", "carries_results", "authorizes_deck_change", "is_gameplay_claim"} or any(boundary.get(key) is not False for key in ("carries_results", "authorizes_deck_change", "is_gameplay_claim")):
        errors.append("question explicit_boundary flags must all be false")
    interpretation = question.get("success_interpretation")
    if not isinstance(interpretation, dict) or set(interpretation) != {"directional_expectation", "notes"}:
        errors.append("question success_interpretation has an invalid field set")
    text = json.dumps({key: question.get(key) for key in ("hypothesis", "question_text", "success_interpretation")}, sort_keys=True)
    forbidden = ((policy.get("evidence_language_boundary") or {}).get("forbidden_claims") or [])
    if any(isinstance(claim, str) and claim.casefold() in text.casefold() for claim in forbidden):
        errors.append("question contains forbidden evidence-language claim")
    return errors


def _lifecycle_reference_errors(entries, label, load_reference):
    errors = []
    if not isinstance(entries, list):
        return [f"lifecycle recorded_evidence.{label} must be an array"]
    seen = set()
    for index, reference in enumerate(entries):
        if not isinstance(reference, dict) or set(reference) != {"id", "path", "content_fingerprint"}:
            errors.append(f"lifecycle recorded_evidence.{label}[{index}] has an invalid field set")
            continue
        identity = reference.get("id")
        if not isinstance(identity, str) or identity in seen:
            errors.append(f"lifecycle recorded_evidence.{label} identities must be unique non-empty strings")
        seen.add(identity)
        _resolve_reference(reference, f"lifecycle recorded_evidence.{label}[{index}]", errors, load_reference)
    return errors


def validate_simulation_question_lifecycle(
    lifecycle, *, question, lifecycle_contract, project_id, load_reference,
    policy=None, question_contract=None, fingerprint_for_version=None,
):
    """Validate the canonical persisted lifecycle without making it semantic RNG input."""
    effective_contract, errors = _resolve_canonical_lifecycle_contract(lifecycle_contract, load_reference)
    errors.extend(_required(lifecycle, (effective_contract.get("required_fields") or {}).keys(), "lifecycle"))
    if not isinstance(lifecycle, dict):
        return errors
    extras = sorted(set(lifecycle) - QUESTION_LIFECYCLE_FIELDS)
    if extras:
        errors.append(f"lifecycle has unregistered top-level fields: {', '.join(extras)}")
    if lifecycle.get("artifact_type") != "simulation_question_lifecycle":
        errors.append("lifecycle artifact_type is invalid")
    if lifecycle.get("schema_version") != "1.0":
        errors.append("lifecycle schema_version must be 1.0")
    invalidation_contract = (effective_contract.get("required_fields") or {}).get("invalidation") or {}
    if (
        invalidation_contract.get("reason_contract_id") != "simulation-lifecycle-invalidation-v1"
        or set(invalidation_contract.get("allowed_reason_ids") or []) != LIFECYCLE_INVALIDATION_REASON_IDS
    ):
        errors.append("lifecycle contract invalidation reason vocabulary is not frozen")
    if lifecycle.get("project_id") != project_id:
        errors.append("lifecycle project_id does not match the project")
    if lifecycle.get("question_id") != question.get("question_id"):
        errors.append("lifecycle question_id does not match the immutable Question")
    if lifecycle.get("lifecycle_id") != f"{question.get('question_id')}-lifecycle":
        errors.append("lifecycle_id is not derived from question_id")
    expected_question_path = f"workshop/projects/the-myr-singularity/simulation/questions/{question.get('question_id')}.json"
    if lifecycle.get("question_path") != expected_question_path:
        errors.append("lifecycle question_path is not canonical")
    if lifecycle.get("question_content_fingerprint") != artifact_content_fingerprint(question):
        errors.append("lifecycle question_content_fingerprint does not match immutable Question")
    state = lifecycle.get("state")
    if state not in LIFECYCLE_STATES:
        errors.append("lifecycle state is not allowed")
    evidence = lifecycle.get("recorded_evidence")
    if not isinstance(evidence, dict) or set(evidence) != {"runs", "results", "comparison"}:
        return [*errors, "lifecycle recorded_evidence has an invalid field set"]
    runs, results, comparison = evidence.get("runs"), evidence.get("results"), evidence.get("comparison")
    errors.extend(_lifecycle_reference_errors(runs, "runs", load_reference))
    errors.extend(_lifecycle_reference_errors(results, "results", load_reference))
    if comparison is not None:
        errors.extend(_lifecycle_reference_errors([comparison], "comparison", load_reference))
    invalidation = lifecycle.get("invalidation")
    expected_counts = {
        "preregistered": (0, 0, False), "runs_recorded": (2, 0, False),
        "results_recorded": (2, 2, False), "comparison_recorded": (2, 2, True),
    }
    if state in expected_counts:
        run_count, result_count, has_comparison = expected_counts[state]
        if len(runs or []) != run_count or len(results or []) != result_count or (comparison is not None) != has_comparison:
            errors.append("lifecycle recorded evidence cardinality does not match state")
        if invalidation is not None:
            errors.append("non-invalidated lifecycle must set invalidation to null")
    elif state == "invalidated":
        if not isinstance(invalidation, dict) or set(invalidation) != {"from_state", "reason_id"}:
            errors.append("invalidated lifecycle requires exact invalidation metadata")
        elif (
            invalidation.get("from_state") not in {"preregistered", "runs_recorded", "results_recorded"}
            or invalidation.get("reason_id") not in set(invalidation_contract.get("allowed_reason_ids") or [])
        ):
            errors.append("lifecycle invalidation metadata is invalid")
        else:
            run_count, result_count, has_comparison = expected_counts[invalidation["from_state"]]
            if len(runs or []) != run_count or len(results or []) != result_count or (comparison is not None) != has_comparison:
                errors.append("invalidated lifecycle evidence must preserve its declared prior-state prefix")
    expected_versions = {
        item.get("run_role"): item
        for item in question.get("compared_versions", [])
        if isinstance(item, dict) and isinstance(item.get("run_role"), str)
    }
    resolved_runs = []
    for reference in runs or []:
        document = _resolve_reference(reference, "lifecycle run evidence", errors, load_reference)
        if isinstance(document, dict):
            resolved_runs.append(document)
            if document.get("artifact_type") != "simulation_run" or document.get("run_id") != reference.get("id"):
                errors.append("lifecycle run evidence identity is invalid")
            if document.get("question_id") != question.get("question_id") or document.get("status") != "executed":
                errors.append("lifecycle run evidence must be an executed Run for the immutable Question")
            expected_version = expected_versions.get(document.get("run_role"))
            if expected_version is None:
                errors.append("lifecycle Run has an unregistered question-bound run_role")
            elif (
                document.get("deck_version_id") != expected_version.get("deck_version_id")
                or document.get("deck_version_path") != expected_version.get("path")
                or document.get("deck_content_fingerprint") != expected_version.get("deck_content_fingerprint")
            ):
                errors.append("lifecycle Run does not match its preregistered DeckVersion and run_role")
    if runs and (
        {item.get("run_role") for item in resolved_runs} != set(expected_versions)
        or {item.get("deck_version_id") for item in resolved_runs}
        != {item.get("deck_version_id") for item in expected_versions.values()}
    ):
        errors.append("lifecycle runs must contain exactly one executed Run for each preregistered DeckVersion and run_role")
    run_ids = {item.get("run_id") for item in resolved_runs}
    resolved_results = []
    for reference in results or []:
        document = _resolve_reference(reference, "lifecycle result evidence", errors, load_reference)
        if isinstance(document, dict):
            resolved_results.append(document)
            if document.get("artifact_type") != "simulation_result" or document.get("result_id") != reference.get("id"):
                errors.append("lifecycle result evidence identity is invalid")
            if document.get("run_id") not in run_ids:
                errors.append("lifecycle Result is not bound to a recorded Run")
    result_run_ids = [item.get("run_id") for item in resolved_results]
    if results and (len(result_run_ids) != len(set(result_run_ids)) or set(result_run_ids) != run_ids):
        errors.append("lifecycle results must contain exactly one Result for each recorded Run")
    if comparison is not None:
        document = _resolve_reference(comparison, "lifecycle comparison evidence", errors, load_reference)
        if isinstance(document, dict):
            result_ids = {item.get("result_id") for item in resolved_results}
            sides = (document.get("baseline") or {}, document.get("candidate") or {})
            if document.get("artifact_type") != "comparison_result" or document.get("comparison_id") != comparison.get("id") or document.get("question_id") != question.get("question_id"):
                errors.append("lifecycle Comparison evidence identity is invalid")
            if {side.get("run_id") for side in sides} != run_ids or {side.get("result_id") for side in sides} != result_ids:
                errors.append("lifecycle Comparison does not bind exactly the recorded Runs and Results")
    if resolved_runs or resolved_results or comparison is not None:
        if policy is None or question_contract is None or fingerprint_for_version is None:
            errors.append("lifecycle evidence validation requires policy, Question contract, and DeckVersion fingerprint dependencies")
            return errors
        try:
            references = policy.get("references") or {}
            run_contract = load_reference(references["simulation_run_contract"]["path"])
            result_contract = load_reference(references["simulation_result_contract"]["path"])
            comparison_contract = load_reference(references["comparison_result_contract"]["path"])
            taxonomy = load_reference(references["failure_pattern_taxonomy"]["path"])
        except (KeyError, OSError, ValueError, TypeError) as exc:
            errors.append(f"lifecycle evidence validation cannot resolve required contracts: {exc}")
            return errors
        for document in resolved_runs:
            for error in validate_simulation_run(
                document, question=question, policy=policy, question_contract=question_contract,
                run_contract=run_contract, project_id=project_id, load_reference=load_reference,
                fingerprint_for_version=fingerprint_for_version, lifecycle_mode="creation",
            ):
                errors.append(f"lifecycle Run is invalid: {error}")
        runs_by_id = {document.get("run_id"): document for document in resolved_runs}
        for document in resolved_results:
            run = runs_by_id.get(document.get("run_id"))
            if run is None:
                continue
            for error in validate_simulation_result(
                document, run=run, policy=policy, question=question,
                question_contract=question_contract, result_contract=result_contract,
                taxonomy_ids=taxonomy, load_reference=load_reference, project_id=project_id,
                fingerprint_for_version=fingerprint_for_version, lifecycle_mode="creation",
            ):
                errors.append(f"lifecycle Result is invalid: {error}")
        if comparison is not None:
            comparison_document = _resolve_reference(comparison, "lifecycle comparison evidence", errors, load_reference)
            if not isinstance(comparison_document, dict):
                return errors
            results_by_id = {item.get("result_id"): item for item in resolved_results}
            sides = comparison_document.get("baseline") or {}, comparison_document.get("candidate") or {}
            baseline_run = runs_by_id.get(sides[0].get("run_id"))
            candidate_run = runs_by_id.get(sides[1].get("run_id"))
            baseline_result = results_by_id.get(sides[0].get("result_id"))
            candidate_result = results_by_id.get(sides[1].get("result_id"))
            if all(isinstance(item, dict) for item in (baseline_run, candidate_run, baseline_result, candidate_result)):
                for error in validate_comparison_result(
                    comparison_document, baseline_run=baseline_run, candidate_run=candidate_run,
                    baseline_result=baseline_result, candidate_result=candidate_result,
                    policy=policy, question=question, question_contract=question_contract,
                    comparison_contract=comparison_contract, run_contract=run_contract,
                    result_contract=result_contract, project_id=project_id, taxonomy_ids=taxonomy,
                    load_reference=load_reference, fingerprint_for_version=fingerprint_for_version,
                    lifecycle_mode="creation",
                ):
                    errors.append(f"lifecycle Comparison is invalid: {error}")
    return errors


def validate_simulation_question_lifecycle_transition(
    previous, current, *, question, lifecycle_contract, project_id, load_reference,
    policy=None, question_contract=None, fingerprint_for_version=None,
):
    """Validate one caller-owned atomic transition and immutable evidence prefix."""
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return ["lifecycle transition requires previous and current lifecycle objects"]
    errors = []
    for label, lifecycle in (("previous", previous), ("current", current)):
        for error in validate_simulation_question_lifecycle(
            lifecycle, question=question, lifecycle_contract=lifecycle_contract,
            project_id=project_id, load_reference=load_reference, policy=policy,
            question_contract=question_contract, fingerprint_for_version=fingerprint_for_version,
        ):
            errors.append(f"{label} lifecycle is invalid: {error}")
    if errors:
        return errors
    previous_state, current_state = previous.get("state"), current.get("state")
    if previous.get("question_id") != current.get("question_id") or previous.get("question_content_fingerprint") != current.get("question_content_fingerprint"):
        return ["lifecycle transition must preserve immutable Question identity"]
    allowed = {
        ("preregistered", "runs_recorded"), ("runs_recorded", "results_recorded"),
        ("results_recorded", "comparison_recorded"), ("preregistered", "invalidated"),
        ("runs_recorded", "invalidated"), ("results_recorded", "invalidated"),
    }
    if (previous_state, current_state) not in allowed:
        return ["lifecycle transition is forbidden"]
    previous_evidence = previous.get("recorded_evidence")
    current_evidence = current.get("recorded_evidence")
    if current_state == "runs_recorded":
        if current_evidence.get("results") != [] or current_evidence.get("comparison") is not None:
            return ["preregistered to runs_recorded may add only the exact two Runs"]
    elif current_state == "results_recorded":
        if current_evidence.get("runs") != previous_evidence.get("runs"):
            return ["runs_recorded to results_recorded must preserve recorded Run references exactly"]
        if current_evidence.get("comparison") is not None:
            return ["runs_recorded to results_recorded may add only Results"]
    elif current_state == "comparison_recorded":
        if (
            current_evidence.get("runs") != previous_evidence.get("runs")
            or current_evidence.get("results") != previous_evidence.get("results")
        ):
            return ["results_recorded to comparison_recorded must preserve Run and Result references exactly"]
    elif current_state == "invalidated":
        if current.get("invalidation", {}).get("from_state") != previous_state:
            return ["invalidated lifecycle must declare the exact previous state"]
        if current_evidence != previous_evidence:
            return ["invalidated lifecycle must preserve the prior evidence prefix exactly"]
    return []


def _validate_lifecycle_mode(*, lifecycle_mode, lifecycle, lifecycle_path, lifecycle_contract, question, policy, question_contract, project_id, load_reference, fingerprint_for_version, artifact, artifact_kind):
    if lifecycle_mode not in LIFECYCLE_MODES:
        return ["lifecycle_mode must be explicitly 'creation' or 'persistence'"]
    if lifecycle_mode == "creation":
        if lifecycle is not None or lifecycle_path is not None or lifecycle_contract is not None:
            return ["creation lifecycle mode must not accept persisted lifecycle evidence"]
        return []
    if lifecycle is None or lifecycle_contract is None or lifecycle_path != lifecycle_path_for_question(question.get("question_id")):
        return ["persistence lifecycle mode requires the canonical lifecycle artifact and contract"]
    errors = validate_simulation_question_lifecycle(
        lifecycle, question=question, lifecycle_contract=lifecycle_contract,
        project_id=project_id, load_reference=load_reference, policy=policy,
        question_contract=question_contract, fingerprint_for_version=fingerprint_for_version,
    )
    if errors:
        return errors
    evidence = lifecycle.get("recorded_evidence") or {}
    entries = evidence.get({"run": "runs", "result": "results", "comparison": "comparison"}[artifact_kind])
    entries = [entries] if artifact_kind == "comparison" and entries is not None else entries
    expected_id = artifact.get({"run": "run_id", "result": "result_id", "comparison": "comparison_id"}[artifact_kind])
    if not any(isinstance(entry, dict) and entry.get("id") == expected_id and entry.get("content_fingerprint") == artifact_content_fingerprint(artifact) for entry in (entries or [])):
        errors.append(f"persisted {artifact_kind} is not recorded by the canonical lifecycle artifact")
    return errors


def resolve_question_metric_target(question, reference):
    """Resolve a taxonomy target reference without positional array semantics."""
    if not isinstance(reference, dict):
        return None, ["failure emission question metric reference must be an object"]
    if reference.get("source") != "simulation_question.required_metrics" or reference.get("field") != "target_turn":
        return None, ["failure emission question metric reference is structurally invalid"]
    metric_id = reference.get("metric_id")
    matches = [item for item in question.get("required_metrics", []) if isinstance(item, dict) and item.get("metric_id") == metric_id]
    if len(matches) != 1:
        return None, [f"question required_metrics must contain exactly one {metric_id!r} target"]
    target = matches[0].get("target_turn")
    if not _integer(target):
        return None, [f"question metric {metric_id!r} target_turn must be an integer"]
    return target, []


def project_level_two_land(*, runtime_context, oracle_id, condition_state, current_turn, horizon_turn, ordinal=1):
    """Project one registered land into the frozen Level 2 selector inputs.

    No Oracle text is parsed here. Generic external payments and artifact state
    remain pre-play, while Tron evaluates the hypothetical controlled-land set
    after this land enters and bounded sources start at controller-turn offset 0.
    """
    try:
        snapshot = _authenticate_runtime_context(runtime_context)
        record = _resolve_runtime_record(snapshot, oracle_id, required_source_kind={"land"})
    except ValueError as error:
        return None, [str(error)]
    if (record.get("deployment") or {}).get("counts_as_land_drop") is not True:
        return None, ["Level 2 land projection requires a legal registered land drop"]
    groups = record.get("activation_groups") or []
    if len(groups) != 1:
        return None, ["Level 2 land projection requires exactly one activation group"]
    try:
        _validate_condition_state(
            condition_state,
            allowed_keys={
                "generic_payment_available_from_other_sources", "controller_turn_offset",
                "artifact_controlled_count", "controlled_land_oracle_ids", "commander_colors",
            },
            runtime_snapshot=snapshot,
            label="Level 2 land condition state",
        )
    except ValueError as error:
        return None, [str(error)]
    if record.get("oracle_id") not in snapshot.canonical_land_oracle_ids:
        return None, ["Level 2 land projection requires a canonical registered-land identity"]
    selection_state = condition_state.copy()
    selection_state["candidate_land_oracle_id"] = record["oracle_id"]
    selection_state.setdefault("controller_turn_offset", 0)
    profile_conditions = [
        condition
        for profile in (groups[0].get("profiles") or []) if isinstance(profile, Mapping)
        for condition in (profile.get("conditions") or [])
    ]
    profiles, errors = _resolve_activation_profiles(
        groups[0],
        _condition_state_for_conditions(selection_state, profile_conditions),
        runtime_snapshot=snapshot,
    )
    if errors:
        return None, errors
    supported = [profile for profile in profiles if profile.get("supported")]
    colors = sorted({
        color
        for profile in supported
        for color in profile.get("output_capabilities", [])
        if color in set("WUBRG")
    })
    bounded = [
        condition for profile in supported for condition in profile.get("conditions", [])
        if isinstance(condition, Mapping) and condition.get("condition_id") == "bounded_controller_turn_window"
    ]
    transitions = record.get("state_transitions") or []
    transition_persists = all(
        _condition_is_satisfied(
            transition.get("condition"),
            _condition_state_for_conditions(selection_state, [transition.get("condition")]),
            runtime_snapshot=snapshot,
        )
        for transition in transitions if isinstance(transition, Mapping)
    )
    if bounded:
        end = bounded[0]["params"]["end_offset"]
        offset = selection_state.get("controller_turn_offset")
        remaining = max(0, end - offset + 1) if _integer(offset) else 0
    else:
        # Selection records only what the pre-selection state can guarantee. A
        # later same-turn deployment may alter the separate end-step outcome.
        remaining = max(0, horizon_turn - current_turn + 1) if transition_persists else 1
    return {
        "colors": colors,
        "five_color_source": set("WUBRG") <= set(colors),
        "permanent": not bounded and transition_persists,
        "remaining_availability": remaining,
        "mana_units": max((profile["mana_units"] for profile in supported), default=0),
        "oracle_id": record["oracle_id"],
        "ordinal": ordinal,
    }, []


def project_level_two_ramp(*, runtime_context, oracle_id, condition_state, available_generic_mana, available_colors, ordinal=1):
    """Project one registered nonland source into frozen ramp-selector inputs."""
    try:
        snapshot = _authenticate_runtime_context(runtime_context)
        record = _resolve_runtime_record(snapshot, oracle_id, required_source_kind={"mana_rock", "mana_creature"})
    except ValueError as error:
        return None, [str(error)]
    groups = record.get("activation_groups") or []
    if len(groups) != 1:
        return None, ["Level 2 ramp projection requires exactly one activation group"]
    try:
        _validate_condition_state(
            condition_state,
            allowed_keys=set(),
            label="Level 2 ramp condition state",
        )
    except ValueError as error:
        return None, [str(error)]
    cost = (record.get("deployment") or {}).get("casting_cost") or {}
    colored_cost = cost.get("colored") or []
    supplied_colors = list(available_colors) if isinstance(available_colors, list) else []
    can_pay_colored = all(supplied_colors.count(color) >= colored_cost.count(color) for color in set(colored_cost))
    can_deploy = _integer(available_generic_mana) and available_generic_mana >= cost.get("generic", 0) and can_pay_colored
    supported = []
    if can_deploy:
        post_deployment_state = {}
        post_deployment_state["generic_payment_available_from_other_sources"] = available_generic_mana - cost.get("generic", 0)
        profile_conditions = [
            condition
            for profile in (groups[0].get("profiles") or []) if isinstance(profile, Mapping)
            for condition in (profile.get("conditions") or [])
        ]
        profiles, errors = _resolve_activation_profiles(
            groups[0],
            _condition_state_for_conditions(post_deployment_state, profile_conditions),
        )
        if errors:
            return None, errors
        supported = [profile for profile in profiles if profile.get("supported")]
    payable = bool(supported) and bool(can_deploy)
    return {
        "payable": payable,
        "same_turn_online_noncreature": record.get("source_kind") == "mana_rock" and any(profile.get("online_model") == "immediate" for profile in supported),
        "output_units": max((profile["mana_units"] for profile in supported), default=0),
        "color_flexibility": max((len(profile["output_capabilities"]) for profile in supported), default=0),
        "mana_value": cost.get("generic", 0) + len(colored_cost),
        "oracle_id": record["oracle_id"],
        "ordinal": ordinal,
    }, []


def _unregistered_field_errors(value, allowed, label):
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    extras = sorted(set(value) - allowed)
    return [f"{label} has unregistered fields: {', '.join(extras)}"] if extras else []


def _controlled_mana_symbols(value):
    return isinstance(value, list) and all(isinstance(symbol, str) and symbol in MANA_SYMBOLS for symbol in value)


def _validate_registry_condition(condition, *, expected_commander_colors, expected_tron_ids, label):
    errors = _unregistered_field_errors(condition, CONDITION_FIELDS, label)
    if not isinstance(condition, dict):
        return errors
    errors.extend(_required(condition, CONDITION_FIELDS, label))
    condition_id = condition.get("condition_id")
    params = condition.get("params")
    if condition_id not in CONDITION_PARAMS:
        return errors + [f"{label} has invalid structured condition"]
    if isinstance(params, dict):
        extras = sorted(set(params) - CONDITION_PARAMS[condition_id])
        if extras:
            errors.append(f"{label} params has unregistered fields: {', '.join(extras)}")
    if not isinstance(params, dict) or set(params) != CONDITION_PARAMS[condition_id]:
        return errors + [f"{label} has invalid structured condition"]
    if condition_id == "artifact_controlled":
        if not _integer(params["minimum_count"]) or params["minimum_count"] < 1:
            errors.append(f"{label} artifact_controlled.minimum_count must be an integer at least 1")
    elif condition_id == "complete_tron_set_controlled":
        oracle_ids = params["oracle_ids"]
        if not isinstance(oracle_ids, list) or len(oracle_ids) != 3 or len(set(oracle_ids)) != 3 or set(oracle_ids) != expected_tron_ids:
            errors.append(f"{label} complete_tron_set_controlled.oracle_ids must be the three canonical Tron Oracle IDs")
    elif condition_id == "generic_payment_available_from_other_sources":
        if not _integer(params["required_units"]) or params["required_units"] not in {1, 5}:
            errors.append(f"{label} generic_payment_available_from_other_sources.required_units must be approved positive integer 1 or 5")
    elif condition_id == "commander_color_identity":
        colors = params["colors"]
        if not isinstance(colors, list) or len(colors) != len(set(colors)) or set(colors) != expected_commander_colors:
            errors.append(f"{label} commander_color_identity.colors must exactly match the canonical Commander color identity")
    elif condition_id == "bounded_controller_turn_window":
        start, end, removal = params["start_offset"], params["end_offset"], params["removal_event"]
        if not _integer(start) or not _integer(end) or start < 0 or end < 0 or start > end:
            errors.append(f"{label} bounded_controller_turn_window offsets are invalid")
        if start != 0 or end != 2 or removal != "final_chapter_ability_leaves_stack":
            errors.append(f"{label} bounded_controller_turn_window must use the approved Urza's Saga bounds and removal event")
    return errors


def validate_mana_source_semantics(registry, *, policy, cards, versions):
    """Validate the complete, machine-executable project source registry."""
    errors = _required(registry, ("schema_version", "artifact_type", "artifact_id", "project_id", "policy_version", "condition_vocabulary", "unsupported_reason_ids", "records"), "mana source semantics")
    if not isinstance(registry, dict):
        return errors
    errors.extend(_unregistered_field_errors(registry, REGISTRY_FIELDS, "mana source semantics"))
    if registry.get("schema_version") != "1.0": errors.append("mana source semantics schema_version must be 1.0")
    if registry.get("artifact_type") != "project_scoped_mana_source_semantics": errors.append("mana source semantics artifact_type is invalid")
    if registry.get("artifact_id") != "the-myr-singularity-mana-source-semantics-v1": errors.append("mana source semantics artifact_id is invalid")
    if registry.get("project_id") != policy.get("project_id") or registry.get("policy_version") != policy.get("policy_version"):
        errors.append("mana source semantics does not bind the active policy/project")
    if artifact_content_fingerprint(registry) != APPROVED_MANA_SOURCE_SEMANTICS_FINGERPRINT:
        errors.append("mana source semantics does not match the approved v1 executable-semantics fingerprint")
    vocabulary = registry.get("condition_vocabulary")
    if not isinstance(vocabulary, dict) or set(vocabulary) != set(CONDITION_PARAMS):
        errors.append("mana source semantics condition vocabulary is not the closed required set")
    elif any(
        _unregistered_field_errors(vocabulary[key], {"required_params"}, f"condition vocabulary {key}")
        or set((vocabulary[key] or {}).get("required_params", [])) != params
        for key, params in CONDITION_PARAMS.items()
    ):
        errors.append("mana source semantics condition vocabulary parameters are invalid")
    unsupported_reason_ids = registry.get("unsupported_reason_ids")
    if not isinstance(unsupported_reason_ids, list) or any(not isinstance(reason, str) or not reason for reason in unsupported_reason_ids) or len(unsupported_reason_ids) != len(set(unsupported_reason_ids or [])):
        errors.append("mana source semantics unsupported_reason_ids must be unique non-empty strings")
    records = registry.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["mana source semantics records must be a non-empty array"]
    card_by_name = {card.get("name"): card for card in cards if isinstance(card, dict)}
    expected_tron_ids = {
        card_by_name[name]["oracle_id"] for name in ("Urza's Mine", "Urza's Power Plant", "Urza's Tower")
        if name in card_by_name
    }
    commander_names = {version.get("commander", {}).get("name") for version in versions if isinstance(version, dict)}
    commander_records = [card_by_name.get(name) for name in commander_names]
    expected_commander_colors = set(commander_records[0].get("color_identity", [])) if len(commander_records) == 1 and commander_records[0] else set()
    if len(expected_tron_ids) != 3:
        errors.append("canonical Card Facts do not resolve the three Tron identities")
    if expected_commander_colors != {"W", "U", "B", "R", "G"}:
        errors.append("canonical Card Facts do not resolve the required Commander color identity")
    expected = set()
    for version in versions:
        for item in version.get("main_deck", []):
            card = card_by_name.get(item.get("name"))
            if card and "Land" in card.get("type_line", ""):
                expected.add(card.get("oracle_id"))
    expected.update((policy.get("ramp_access_registry") or {}).get("oracle_ids", []))
    seen = set()
    reasons = set(unsupported_reason_ids) if isinstance(unsupported_reason_ids, list) else set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("mana source record must be an object"); continue
        errors.extend(_unregistered_field_errors(record, RECORD_FIELDS, "mana source record"))
        oracle_id = record.get("oracle_id")
        if not isinstance(oracle_id, str) or not oracle_id: errors.append("mana source record is missing oracle_id"); continue
        if oracle_id in seen: errors.append("mana source semantics has duplicate oracle_id record")
        seen.add(oracle_id)
        if not isinstance(record.get("card_name"), str) or not record["card_name"]:
            errors.append(f"mana source record {oracle_id} card_name must be a non-empty string")
        card = next((item for item in cards if item.get("oracle_id") == oracle_id), None)
        if card is None or record.get("card_name") != card.get("name"): errors.append(f"mana source record {oracle_id} does not resolve to canonical Card Facts")
        if record.get("source_kind") not in SOURCE_KINDS: errors.append(f"mana source record {oracle_id} has invalid source_kind")
        deployment = record.get("deployment")
        if not isinstance(deployment, dict):
            errors.append(f"mana source record {oracle_id} deployment must be an object")
            deployment = {}
        cost = deployment.get("casting_cost")
        if not isinstance(cost, dict):
            errors.append(f"mana source record {oracle_id} casting_cost must be an object")
            cost = {}
        errors.extend(_unregistered_field_errors(deployment, DEPLOYMENT_FIELDS, f"mana source record {oracle_id} deployment"))
        errors.extend(_unregistered_field_errors(cost, CASTING_COST_FIELDS, f"mana source record {oracle_id} casting_cost"))
        if not _integer(cost.get("generic")) or cost.get("generic") < 0 or not _controlled_mana_symbols(cost.get("colored")) or not isinstance(deployment.get("counts_as_land_drop"), bool): errors.append(f"mana source record {oracle_id} has invalid deployment")
        if card is not None:
            is_land = "Land" in card.get("type_line", "")
            is_creature = "Creature" in card.get("type_line", "")
            if record.get("source_kind") == "land" and (not is_land or deployment.get("counts_as_land_drop") is not True):
                errors.append(f"mana source record {oracle_id} land source_kind must match a canonical Land and count as a land drop")
            if record.get("source_kind") in {"mana_rock", "mana_creature"} and deployment.get("counts_as_land_drop") is not False:
                errors.append(f"mana source record {oracle_id} nonland source_kind must not count as a land drop")
            if record.get("source_kind") == "mana_creature" and not is_creature:
                errors.append(f"mana source record {oracle_id} mana_creature source_kind must match a canonical Creature")
            if record.get("source_kind") == "mana_rock" and is_land:
                errors.append(f"mana source record {oracle_id} mana_rock source_kind must not treat a canonical Land as a rock")
        groups = record.get("activation_groups")
        if not isinstance(groups, list) or len(groups) != 1: errors.append(f"mana source record {oracle_id} must have exactly one activation group"); continue
        group = groups[0]
        errors.extend(_unregistered_field_errors(group, ACTIVATION_GROUP_FIELDS, f"mana source record {oracle_id} activation group"))
        if group.get("group_id") != "mana" or group.get("selection") not in GROUP_SELECTIONS: errors.append(f"mana source record {oracle_id} has invalid activation-group selection")
        profiles = group.get("profiles")
        if not isinstance(profiles, list) or not profiles: errors.append(f"mana source record {oracle_id} has no profiles"); continue
        ids, priorities = set(), set()
        for profile in profiles:
            required = ("profile_id", "priority", "mana_units", "output_capabilities", "output_selection", "tap_model", "payment", "conditions", "online_model", "natural_untap_model", "supported", "unsupported_reason_id")
            if not isinstance(profile, dict) or _required(profile, required, "activation profile"):
                errors.append(f"mana source record {oracle_id} has incomplete profile"); continue
            errors.extend(_unregistered_field_errors(profile, PROFILE_FIELDS, f"mana source record {oracle_id} profile"))
            profile_id = profile["profile_id"]
            if not isinstance(profile_id, str) or not profile_id:
                errors.append(f"mana source record {oracle_id} profile_id must be a non-empty string")
            elif profile_id in ids: errors.append(f"mana source record {oracle_id} has duplicate profile_id")
            else: ids.add(profile_id)
            if not _integer(profile["priority"]) or not _integer(profile["mana_units"]) or profile["mana_units"] < 0: errors.append(f"mana source record {oracle_id} profile has invalid numeric fields")
            if profile["output_selection"] not in OUTPUT_SELECTIONS or profile["tap_model"] != "tap_self_once" or profile["online_model"] not in ONLINE_MODELS or profile["natural_untap_model"] not in UNTAP_MODELS: errors.append(f"mana source record {oracle_id} profile uses an unregistered execution value")
            payment = profile["payment"]
            life = payment.get("life") if isinstance(payment, dict) else None
            errors.extend(_unregistered_field_errors(payment, PAYMENT_FIELDS, f"mana source record {oracle_id} payment"))
            errors.extend(_unregistered_field_errors(life, LIFE_FIELDS, f"mana source record {oracle_id} payment.life"))
            if not isinstance(payment, dict) or not _integer(payment.get("generic")) or payment.get("generic") < 0 or not _controlled_mana_symbols(payment.get("colored")) or not isinstance(life, dict) or not _integer(life.get("amount")) or life.get("amount") < 0 or life.get("treatment") not in {"not_applicable", "ignored"}: errors.append(f"mana source record {oracle_id} profile has invalid payment")
            elif life["amount"] > 0 and life["treatment"] != "ignored": errors.append(f"mana source record {oracle_id} life-cost profile must explicitly ignore life")
            outputs = profile["output_capabilities"]
            if not isinstance(outputs, list) or not _controlled_mana_symbols(outputs) or len(outputs) != len(set(outputs)):
                errors.append(f"mana source record {oracle_id} profile output_capabilities must be unique controlled mana symbols")
            elif profile["supported"] is True:
                if profile["output_selection"] == "fixed" and len(outputs) != 1:
                    errors.append(f"mana source record {oracle_id} fixed profile must have exactly one output capability")
                if profile["output_selection"] in {"one_choice", "any_combination"} and not outputs:
                    errors.append(f"mana source record {oracle_id} selectable profile must have output capabilities")
            conditions = profile["conditions"]
            if not isinstance(conditions, list): errors.append(f"mana source record {oracle_id} profile conditions must be an array")
            else:
                for index, condition in enumerate(conditions):
                    errors.extend(_validate_registry_condition(condition, expected_commander_colors=expected_commander_colors, expected_tron_ids=expected_tron_ids, label=f"mana source record {oracle_id} profile condition[{index}]"))
                generic_payment_conditions = [condition for condition in conditions if isinstance(condition, dict) and condition.get("condition_id") == "generic_payment_available_from_other_sources"]
                if generic_payment_conditions:
                    if len(generic_payment_conditions) != 1 or not _integer(payment.get("generic") if isinstance(payment, dict) else None) or payment.get("generic") <= 0 or generic_payment_conditions[0].get("params", {}).get("required_units") != payment.get("generic"):
                        errors.append(f"mana source record {oracle_id} generic external-payment condition must exactly match positive payment.generic")
                elif profile["supported"] is True and isinstance(payment, dict) and payment.get("generic", 0) > 0:
                    errors.append(f"mana source record {oracle_id} positive generic external payment requires exactly one matching condition")
                bounded_conditions = [condition for condition in conditions if isinstance(condition, dict) and condition.get("condition_id") == "bounded_controller_turn_window"]
                if profile["online_model"] == "bounded_window" and len(bounded_conditions) != 1:
                    errors.append(f"mana source record {oracle_id} bounded_window profile requires exactly one bounded_controller_turn_window condition")
                if profile["online_model"] != "bounded_window" and bounded_conditions:
                    errors.append(f"mana source record {oracle_id} bounded_controller_turn_window condition requires online_model bounded_window")
            if profile["supported"] is True:
                if profile["mana_units"] <= 0 or not profile["output_capabilities"] or profile["unsupported_reason_id"] is not None: errors.append(f"mana source record {oracle_id} supported profile is malformed")
            elif profile["supported"] is False:
                if profile["mana_units"] != 0 or profile["output_capabilities"] or profile["unsupported_reason_id"] not in reasons: errors.append(f"mana source record {oracle_id} unsupported profile is malformed")
            else: errors.append(f"mana source record {oracle_id} profile supported must be boolean")
            if group.get("selection") == "highest_priority_matching_profile":
                if profile.get("priority") in priorities: errors.append(f"mana source record {oracle_id} has tied replacement profile priority")
                priorities.add(profile.get("priority"))
        transitions = record.get("state_transitions")
        if transitions is not None and not isinstance(transitions, list):
            errors.append(f"mana source record {oracle_id} state_transitions must be an array")
        elif isinstance(transitions, list):
            for index, transition in enumerate(transitions):
                label = f"mana source record {oracle_id} state_transition[{index}]"
                errors.extend(_unregistered_field_errors(transition, STATE_TRANSITION_FIELDS, label))
                errors.extend(_required(transition, STATE_TRANSITION_FIELDS, label))
                if isinstance(transition, dict):
                    if transition.get("event_id") not in STATE_TRANSITION_EVENTS:
                        errors.append(f"{label} event_id is not registered")
                    errors.extend(_validate_registry_condition(transition.get("condition"), expected_commander_colors=expected_commander_colors, expected_tron_ids=expected_tron_ids, label=f"{label} condition"))
        if record.get("card_name") == "Glimmervoid":
            expected_transition = [{
                "event_id": "end_step_remove_unless_condition",
                "condition": {"condition_id": "artifact_controlled", "params": {"minimum_count": 1}},
            }]
            if transitions != expected_transition:
                errors.append("Glimmervoid must have exactly the approved end-step artifact-control transition")
    if seen != expected:
        errors.append("mana source semantics does not cover exactly the v1.0/v1.1 executable-source union")
    return errors


def build_simulation_runtime_context(registry, *, policy, card_facts, versions):
    """Seal the approved executable registry after canonical-input validation."""
    errors = []
    if artifact_content_fingerprint(policy) != APPROVED_SIMULATION_POLICY_FINGERPRINT:
        errors.append("runtime context requires the approved active SimulationPolicy")
    if not isinstance(card_facts, dict) or artifact_content_fingerprint(card_facts) != (policy.get("references") or {}).get("canonical_card_facts", {}).get("content_fingerprint"):
        errors.append("runtime context requires Policy-pinned canonical Card Facts")
        cards = []
    else:
        cards = card_facts.get("cards")
    expected_versions = (policy.get("deck_fingerprint_policy") or {}).get("reference_fingerprints", {})
    if not isinstance(versions, list) or {version.get("version_id") for version in versions if isinstance(version, dict)} != {"v1.0", "v1.1"}:
        errors.append("runtime context requires exactly the preregistered DeckVersions")
    else:
        try:
            version_fingerprints_match = all(
                deck_content_fingerprint(version, cards) == expected_versions.get(version.get("version_id"))
                for version in versions
            )
        except ValueError as error:
            errors.append(f"runtime context cannot resolve preregistered DeckVersions: {error}")
        else:
            if not version_fingerprints_match:
                errors.append("runtime context DeckVersions do not match Policy-pinned canonical fingerprints")
    errors.extend(validate_mana_source_semantics(registry, policy=policy, cards=cards, versions=versions))
    if errors:
        return None, errors
    return SimulationRuntimeContext._from_validated_registry(registry), []


def validate_card_semantics_registry_parity(card_semantics, registry):
    """Require one result-changing interpretation for shared special mana sources."""
    entries = {
        item.get("card_identity", {}).get("name"): item
        for item in (card_semantics.get("entries") or []) if isinstance(item, dict)
    } if isinstance(card_semantics, dict) else {}
    records = {
        item.get("card_name"): item
        for item in (registry.get("records") or []) if isinstance(item, dict)
    } if isinstance(registry, dict) else {}
    errors = []
    for name in ("City of Brass", "Mana Confluence", "Urza's Saga"):
        if name not in entries or name not in records:
            errors.append(f"card semantics/registry parity is missing {name}")
    if errors:
        return errors

    def profiles(name):
        return [
            profile for group in records[name].get("activation_groups", [])
            for profile in group.get("profiles", []) if isinstance(profile, dict) and profile.get("supported")
        ]

    for name in ("City of Brass", "Mana Confluence"):
        behavior = entries[name].get("modeled_behavior") or {}
        record = records[name]
        capabilities = set().union(*(set(profile.get("output_capabilities", [])) for profile in profiles(name)))
        if record.get("deployment", {}).get("counts_as_land_drop") is not True or behavior.get("counts_as_land_drop") is not True:
            errors.append(f"{name} card semantics/registry land-drop parity fails")
        if capabilities != set("WUBRG") or set(behavior.get("produces_colors", [])) != set("WUBRG"):
            errors.append(f"{name} card semantics/registry WUBRG capability parity fails")
        if "C" in capabilities or behavior.get("produces_colorless") is not False or behavior.get("counts_as_five_color_source") is not True:
            errors.append(f"{name} card semantics/registry five-color parity fails")
    mana_confluence_life = [profile.get("payment", {}).get("life") for profile in profiles("Mana Confluence")]
    if mana_confluence_life != [{"amount": 1, "treatment": "ignored"}]:
        errors.append("Mana Confluence card semantics/registry life-payment parity fails")
    city_life = [profile.get("payment", {}).get("life") for profile in profiles("City of Brass")]
    if city_life != [{"amount": 0, "treatment": "not_applicable"}]:
        errors.append("City of Brass card semantics/registry must not model a life-payment activation cost")

    saga_behavior = entries["Urza's Saga"].get("modeled_behavior") or {}
    saga_time = entries["Urza's Saga"].get("time_dependent_availability") or {}
    saga_profiles = profiles("Urza's Saga")
    saga_conditions = [
        condition for profile in saga_profiles for condition in profile.get("conditions", [])
        if isinstance(condition, dict) and condition.get("condition_id") == "bounded_controller_turn_window"
    ]
    if records["Urza's Saga"].get("deployment", {}).get("counts_as_land_drop") is not True or saga_behavior.get("counts_as_land_drop") is not True:
        errors.append("Urza's Saga card semantics/registry land-drop parity fails")
    if len(saga_profiles) != 1 or saga_profiles[0].get("output_capabilities") != ["C"] or saga_behavior.get("produces_colors") != [] or saga_behavior.get("produces_colorless") is not True or saga_behavior.get("counts_as_five_color_source") is not False:
        errors.append("Urza's Saga card semantics/registry color capability parity fails")
    expected_window = {"start_offset": 0, "end_offset": 2, "removal_event": "final_chapter_ability_leaves_stack"}
    if len(saga_conditions) != 1 or saga_conditions[0].get("params") != expected_window:
        errors.append("Urza's Saga card semantics/registry bounded window parity fails")
    removal = saga_time.get("removal_event") or {}
    availability = saga_time.get("availability_window") or {}
    if availability.get("start_offset") != 0 or availability.get("end_offset") != 2 or removal.get("trigger") != "final_chapter_ability_leaves_stack" or saga_time.get("persists_as_permanent_land") is not False:
        errors.append("Urza's Saga card semantics/registry nonpermanent removal parity fails")
    return errors


def validate_failure_pattern_taxonomy(taxonomy, *, policy, question):
    """Fail closed on the complete approved v3 taxonomy, not merely its IDs."""
    if not isinstance(taxonomy, dict):
        return ["failure taxonomy must be the resolved taxonomy artifact"]
    errors = []
    if taxonomy.get("taxonomy_id") != "sim-failure-taxonomy-v4" or taxonomy.get("taxonomy_version") != "v4" or taxonomy.get("policy_version") != policy.get("policy_version"):
        errors.append("failure taxonomy identity does not match the active policy")
    if artifact_content_fingerprint(taxonomy) != APPROVED_FAILURE_PATTERN_TAXONOMY_FINGERPRINT:
        errors.append("failure taxonomy does not match the approved v4 emission-semantics fingerprint")
    categories = taxonomy.get("categories")
    emission = taxonomy.get("emission_contract") or {}
    category_contracts = emission.get("categories") or {}
    category_ids = [item.get("category_id") for item in categories if isinstance(item, dict)] if isinstance(categories, list) else []
    if len(category_ids) != 12 or len(category_ids) != len(set(category_ids)) or set(category_ids) != set(category_contracts):
        errors.append("failure taxonomy categories and emission metadata must be an exact one-to-one set")
    if emission.get("boolean_once_per_iteration") is not True or emission.get("overlap") != "permitted" or emission.get("result_inclusion") != "all_emitting_categories_exactly_once_including_zero_counts":
        errors.append("failure taxonomy emission behavior is incomplete")
    for category_id, metadata in category_contracts.items():
        if not isinstance(metadata, dict) or metadata.get("emitting") not in {True, False}:
            errors.append(f"failure taxonomy {category_id} emitting behavior is invalid")
            continue
        if metadata.get("emitting") is True:
            if not isinstance(metadata.get("state_ref"), str) or not isinstance(metadata.get("predicate"), str):
                errors.append(f"failure taxonomy {category_id} emitting metadata is incomplete")
            reference = metadata.get("question_metric_ref")
            if reference is not None:
                _, target_errors = resolve_question_metric_target(question, reference)
                errors.extend(target_errors)
        elif not isinstance(metadata.get("non_emitting_reason_id"), str):
            errors.append(f"failure taxonomy {category_id} non-emitting metadata is incomplete")
    return errors


def validate_run_role_binding(run, question):
    errors = []
    if run.get("question_id") != question.get("question_id"):
        errors.append("run question_id does not match the referenced question")
    bindings = {item.get("deck_version_id"): item.get("run_role") for item in question.get("compared_versions", []) if isinstance(item, dict)}
    expected = bindings.get(run.get("deck_version_id"))
    if expected is None:
        errors.append("run DeckVersion is not bound by the question")
    elif run.get("run_role") != expected:
        errors.append("run role is not bound to the question DeckVersion")
    return errors


def _validate_bundle(bundle, *, policy, question, deck_path, deck_fingerprint, load_reference, include_deck=True):
    errors = _required(bundle, DEPENDENCY_KEYS + (("deck_version",) if include_deck else ()), "semantic_dependencies")
    if not isinstance(bundle, dict):
        return errors
    expected = {"policy": policy, "question": question}
    policy_refs = policy.get("references") or {}
    map_names = {
        "card_semantics": "card_semantics", "mana_source_semantics": "mana_source_semantics", "canonical_card_facts": "canonical_card_facts",
        "failure_pattern_taxonomy": "failure_pattern_taxonomy",
        "simulation_question_contract": "simulation_question_contract",
        "simulation_run_contract": "simulation_run_contract",
        "simulation_result_contract": "simulation_result_contract",
        "comparison_result_contract": "comparison_result_contract",
    }
    for key in DEPENDENCY_KEYS:
        resolved = _resolve_reference(bundle.get(key), f"semantic_dependencies.{key}", errors, load_reference, expected.get(key))
        policy_reference = policy_refs.get(map_names.get(key, ""))
        if key not in ("policy", "question") and bundle.get(key) != policy_reference:
            errors.append(f"semantic_dependencies.{key} does not match the policy dependency")
    if include_deck:
        deck = bundle.get("deck_version")
        if not isinstance(deck, dict) or deck.get("path") != deck_path:
            errors.append("semantic_dependencies.deck_version path does not match the run DeckVersion")
        elif deck.get("deck_content_fingerprint") != deck_fingerprint:
            errors.append("semantic_dependencies.deck_version fingerprint does not match the run")
    return errors


def validate_failure_pattern(pattern, run_iteration_count, taxonomy_ids):
    errors = _required(pattern, ("category_id", "raw_count", "sample_size", "frequency"), "failure pattern")
    if pattern.get("category_id") not in taxonomy_ids:
        errors.append("failure pattern references undefined category")
    raw, size, frequency = pattern.get("raw_count"), pattern.get("sample_size"), pattern.get("frequency")
    if not _integer(raw): errors.append("failure pattern raw_count must be an integer")
    if not _integer(size) or size <= 0: errors.append("failure pattern sample_size must be positive integer")
    elif size != run_iteration_count: errors.append("failure pattern sample_size does not match run iteration_count")
    if _integer(raw) and _integer(size) and not 0 <= raw <= size: errors.append("failure pattern raw_count must be within 0..sample_size")
    if not _number(frequency) or not 0 <= frequency <= 1: errors.append("failure pattern frequency must be within 0..1")
    elif _integer(raw) and _integer(size) and size and not math.isclose(frequency, raw / size, abs_tol=1e-12): errors.append("failure pattern frequency does not equal raw_count/sample_size")
    return errors


def validate_result_failure_patterns(patterns, run_iteration_count, taxonomy, question):
    """Enforce the v3 emitting/non-emitting taxonomy boundary."""
    if not isinstance(taxonomy, dict):
        return ["failure patterns require the resolved failure taxonomy artifact"]
    taxonomy_errors = validate_failure_pattern_taxonomy(taxonomy, policy={"policy_version": taxonomy.get("policy_version")}, question=question)
    if taxonomy_errors:
        return ["failure patterns require a valid resolved failure taxonomy artifact", *taxonomy_errors]
    contract = taxonomy.get("emission_contract") or {}
    categories = contract.get("categories") or {}
    errors = []
    emitting = {key for key, value in categories.items() if isinstance(value, dict) and value.get("emitting") is True}
    non_emitting = {key for key, value in categories.items() if isinstance(value, dict) and value.get("emitting") is False}
    actual = [item.get("category_id") for item in patterns if isinstance(item, dict)] if isinstance(patterns, list) else []
    if len(actual) != len(set(actual)): errors.append("failure_patterns contains duplicate category_id")
    if set(actual) != emitting: errors.append("failure_patterns must contain every emitting category exactly once and no non-emitting category")
    for category_id, metadata in categories.items():
        reference = metadata.get("question_metric_ref") if isinstance(metadata, dict) else None
        if reference is not None:
            _, target_errors = resolve_question_metric_target(question, reference)
            errors.extend(target_errors)
    for pattern in patterns if isinstance(patterns, list) else []:
        errors.extend(validate_failure_pattern(pattern, run_iteration_count, set(categories)))
    return errors


def validate_failure_pattern_aggregate_consistency(metrics, patterns, iteration_count):
    """Bind emitted failure counts to the aggregate metric events that define them."""
    if not isinstance(metrics, list) or not isinstance(patterns, list):
        return []
    metric_by_id = {metric.get("metric_id"): metric for metric in metrics if isinstance(metric, dict)}
    pattern_by_id = {pattern.get("category_id"): pattern for pattern in patterns if isinstance(pattern, dict)}

    def pattern_count(category_id):
        value = pattern_by_id.get(category_id, {}).get("raw_count")
        return value if _integer(value) else None

    def bernoulli_count(metric_id):
        value = metric_by_id.get(metric_id, {}).get("raw_count")
        return value if _integer(value) else None

    colors = metric_by_id.get("distinct_commander_colors_by_turn")
    bins = colors.get("bins") if isinstance(colors, dict) else None
    bin_counts = {}
    if isinstance(bins, list):
        bin_counts = {
            item.get("value"): item.get("raw_count")
            for item in bins if isinstance(item, dict) and _integer(item.get("raw_count"))
        }
    errors = []

    def require_exact(category_id, expected, diagnostic):
        actual = pattern_count(category_id)
        if actual is not None and expected is not None and actual != expected:
            errors.append(diagnostic)

    land_success = bernoulli_count("land_drop_success_by_turn")
    ramp_success = bernoulli_count("ramp_access_by_turn")
    five_color_success = bernoulli_count("five_color_availability_by_turn")
    if _integer(iteration_count):
        require_exact(
            "missed_land_drop",
            iteration_count - land_success if land_success is not None else None,
            "failure pattern missed_land_drop raw_count must equal the complement of land_drop_success_by_turn",
        )
        require_exact(
            "ramp_not_available_by_turn",
            iteration_count - ramp_success if ramp_success is not None else None,
            "failure pattern ramp_not_available_by_turn raw_count must equal the complement of ramp_access_by_turn",
        )
        require_exact(
            "five_color_not_complete_by_turn",
            iteration_count - five_color_success if five_color_success is not None else None,
            "failure pattern five_color_not_complete_by_turn raw_count must equal the complement of five_color_availability_by_turn",
        )
    require_exact(
        "single_color_missing_by_turn",
        bin_counts.get(4),
        "failure pattern single_color_missing_by_turn raw_count must equal distinct_commander_colors_by_turn bin 4",
    )
    required_color_bins = (0, 1, 2, 3)
    if all(value in bin_counts for value in required_color_bins):
        require_exact(
            "multiple_colors_missing_by_turn",
            sum(bin_counts[value] for value in required_color_bins),
            "failure pattern multiple_colors_missing_by_turn raw_count must equal distinct_commander_colors_by_turn bins 0 through 3",
        )
    if five_color_success is not None and bin_counts.get(5) is not None:
        if five_color_success != bin_counts[5]:
            errors.append("five_color_availability_by_turn raw_count must equal distinct_commander_colors_by_turn bin 5")
        five_probability = metric_by_id["five_color_availability_by_turn"].get("probability")
        color_proportion = next((item.get("proportion") for item in bins if item.get("value") == 5), None)
        if _number(five_probability) and _number(color_proportion) and not math.isclose(five_probability, color_proportion, abs_tol=1e-12):
            errors.append("five_color_availability_by_turn probability must equal distinct_commander_colors_by_turn bin 5 proportion")
    zero_land = bernoulli_count("zero_land_hand_rate")
    one_land = bernoulli_count("one_land_hand_rate")
    keepable = bernoulli_count("keepable_opening_hand_rate")
    excessive_land = bernoulli_count("excessive_land_hand_rate")
    zero_land_pattern = pattern_count("zero_land_hand")
    one_land_unkept_pattern = pattern_count("one_land_hand_unkept")
    excessive_land_pattern = pattern_count("excessive_land_hand")
    if zero_land is not None and zero_land_pattern is not None and zero_land_pattern < zero_land:
        errors.append("failure pattern zero_land_hand raw_count must be at least zero_land_hand_rate raw_count")
    if excessive_land is not None and excessive_land_pattern is not None and excessive_land_pattern < excessive_land:
        errors.append("failure pattern excessive_land_hand raw_count must be at least excessive_land_hand_rate raw_count")
    if all(value is not None for value in (iteration_count, zero_land, one_land, excessive_land, keepable)):
        two_to_five = iteration_count - zero_land - one_land - excessive_land
        if not two_to_five <= keepable <= two_to_five + one_land:
            errors.append("keepable_opening_hand_rate raw_count is incompatible with the frozen natural-opening keep rule")
        natural_one_land_rejected = one_land - (keepable - two_to_five)
        if one_land_unkept_pattern is not None and one_land_unkept_pattern < natural_one_land_rejected:
            errors.append("failure pattern one_land_hand_unkept raw_count is below derived natural one-land rejections")
    return errors


def _metric_key(metric):
    return (metric.get("metric_id"), metric.get("target_turn")) if isinstance(metric, dict) else None


def _metric_catalog(policy):
    return {_metric_key(metric): metric for metric in (policy.get("metric_catalog") or {}).get("metrics", [])}


def _validate_bernoulli(metric, iteration_count, errors):
    allowed = {"metric_id", "target_turn", "raw_count", "sample_size", "probability", "confidence_interval"}
    if set(metric) != allowed:
        errors.append("result Bernoulli metric must not redefine Policy measurement semantics")
    for field in ("raw_count", "sample_size", "probability", "confidence_interval"):
        if field not in metric: errors.append(f"result Bernoulli metric is missing {field}")
    raw, size, probability = metric.get("raw_count"), metric.get("sample_size"), metric.get("probability")
    if not _integer(raw) or not _integer(size) or not 0 <= raw <= size or size != iteration_count:
        errors.append("result Bernoulli metric raw_count/sample_size is invalid")
        return
    if not _number(probability) or not math.isclose(probability, raw / size, abs_tol=1e-12): errors.append("result Bernoulli metric probability does not equal raw_count/sample_size")
    interval = metric.get("confidence_interval") or {}
    if interval.get("method") != "wilson_score_interval" or interval.get("level") != 0.95:
        errors.append("result Bernoulli metric confidence interval must be Wilson 95%")
    else:
        lower, upper = wilson_interval(raw, size)
        if not _rounded_matches(interval.get("lower"), lower) or not _rounded_matches(interval.get("upper"), upper): errors.append("result Bernoulli metric confidence interval does not match Wilson 95%")


def _validate_categorical(metric, iteration_count, errors):
    allowed = {"metric_id", "target_turn", "sample_size", "bins", "mean"}
    if set(metric) != allowed:
        errors.append("result categorical metric must not redefine Policy measurement semantics")
    if "confidence_interval" in metric: errors.append("categorical metric must not define a Wilson interval")
    if metric.get("sample_size") != iteration_count: errors.append("categorical metric sample_size does not match run iteration_count")
    bins = metric.get("bins")
    if not isinstance(bins, list) or [item.get("value") for item in bins if isinstance(item, dict)] != list(range(6)):
        errors.append("categorical metric bins must contain values 0..5 exactly once")
        return
    total = sum(item.get("raw_count", -1) for item in bins if _integer(item.get("raw_count")))
    if total != iteration_count: errors.append("categorical metric bin raw counts must sum to sample_size")
    proportions = 0.0
    weighted = 0
    for item in bins:
        raw, proportion = item.get("raw_count"), item.get("proportion")
        if not _integer(raw) or raw < 0: errors.append("categorical metric bin raw_count must be non-negative integer")
        elif not _number(proportion) or not math.isclose(proportion, raw / iteration_count, abs_tol=1e-12): errors.append("categorical metric bin proportion does not equal raw_count/sample_size")
        proportions += proportion if _number(proportion) else 0
        weighted += item["value"] * raw if _integer(raw) else 0
    if not math.isclose(proportions, 1.0, abs_tol=1e-12): errors.append("categorical metric bin proportions must sum to one")
    if not _number(metric.get("mean")) or not math.isclose(metric["mean"], weighted / iteration_count, abs_tol=1e-12): errors.append("categorical metric mean does not match bins")


def _validate_claims(claims, resolved, expected_type, readable_summary, errors):
    if not isinstance(claims, list) or not claims:
        errors.append("evidence_claims must be a non-empty array")
        return
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("claim_type") not in {expected_type, "limitation"}:
            errors.append("evidence claim type is not permitted")
            continue
        if claim.get("subject") not in ALLOWED_SUBJECTS:
            errors.append("evidence claim subject is not permitted")
        kind = claim.get("claim_type")
        if kind == "limitation":
            if set(claim) != {"claim_type", "subject", "limitation"} or claim.get("subject") != "limitations" or claim.get("limitation") not in resolved:
                errors.append("limitation evidence claim must exactly bind a recorded limitation")
        else:
            value_key = "estimate" if kind == "metric_estimate" else "comparison"
            expected_keys = {"claim_type", "subject", "metric_id", "target_turn", value_key}
            key = _metric_key(claim)
            if set(claim) != expected_keys:
                errors.append("evidence claim has fields outside its exact registered shape")
            elif key not in resolved or claim.get(value_key) != resolved[key]:
                errors.append("evidence claim does not exactly bind resolved evidence")
    if readable_summary != render_evidence_claims(claims): errors.append("readable_summary must be the deterministic rendering of evidence_claims")


def validate_recording_context(context, *, id_field, created_at_required):
    """Fail closed on the persisted caller-owned recording boundary."""
    if not isinstance(context, dict):
        return ["recording_context must be an object"]
    errors = []
    if context.get("contract_id") != RECORDING_CONTEXT_ID:
        errors.append("recording_context contract_id is invalid")
    boundary = context.get("engine_boundary")
    expected_boundary = {
        "wall_clock_read_permitted": False,
        "random_or_uuid_recording_id_permitted": False,
        "recording_metadata_owner": "caller",
    }
    if boundary != expected_boundary:
        errors.append("recording_context engine boundary must be caller-owned and prohibit clock/random IDs")
    identity = context.get("artifact_identity")
    expected_identity = {
        "algorithm_id": RECORDING_ARTIFACT_ALGORITHM,
        "coverage": RECORDING_ARTIFACT_COVERAGE,
        "replay_equivalence": RECORDING_REPLAY_EQUIVALENCE,
    }
    if identity != expected_identity:
        errors.append("recording_context artifact identity boundary is invalid")
    expected_fields = {"id_field": id_field, "id_owner": "caller"}
    if created_at_required:
        expected_fields.update({"created_at_field": "created_at", "created_at_owner": "caller"})
    else:
        expected_fields["created_at_required"] = False
    if context.get("record_fields") != expected_fields:
        errors.append("recording_context record fields are not caller-owned exact fields")
    return errors


def _valid_recording_timestamp(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except ValueError:
        return False


def _required_unsupported_limitation_ids(run, *, load_reference):
    """Derive limitation identifiers from unsupported executable profiles in deck."""
    dependencies = run.get("semantic_dependencies") if isinstance(run, dict) else None
    registry_reference = dependencies.get("mana_source_semantics") if isinstance(dependencies, dict) else None
    try:
        registry = load_reference((registry_reference or {}).get("path"))
        version = load_reference(run.get("deck_version_path"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return set(), ["unable to resolve evidence for unsupported-behavior limitations"]
    records = {record.get("card_name"): record for record in registry.get("records", []) if isinstance(record, dict)}
    cards = [version.get("commander")] + list(version.get("main_deck") or []) if isinstance(version, dict) else []
    ids = set()
    for card in cards:
        record = records.get(card.get("name")) if isinstance(card, dict) else None
        if not isinstance(record, dict):
            continue
        for group in record.get("activation_groups", []):
            for profile in group.get("profiles", []) if isinstance(group, dict) else []:
                if isinstance(profile, dict) and profile.get("supported") is False:
                    ids.add(f"unsupported_mana_profile:{record.get('oracle_id')}:{profile.get('unsupported_reason_id')}")
    return ids, []


def _validate_unsupported_limitations(value, required_ids, label, errors):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{label} limitations must be an array of strings")
        return
    missing = sorted(required_ids - set(value))
    if missing:
        errors.append(f"{label} limitations omit required unsupported behavior IDs: {', '.join(missing)}")


def _validate_selected_metrics(selection, question):
    """Validate the immutable, ordered execution metric plan."""
    errors = []
    if not isinstance(selection, list):
        return ["run selected_metrics must be an ordered array"]
    required = question.get("required_metrics") or []
    optional = question.get("optional_metrics") or []
    if selection[:len(required)] != required:
        errors.append("run selected_metrics must begin with every required Question metric in Question order")
    tail = selection[len(required):]
    if any(not isinstance(entry, dict) or set(entry) != {"metric_id", "target_turn"} for entry in selection):
        errors.append("run selected_metrics entries must contain exactly metric_id and target_turn")
        return errors
    keys = [_metric_key(entry) for entry in selection]
    if len(keys) != len(set(keys)):
        errors.append("run selected_metrics must be duplicate-free")
    optional_keys = {_metric_key(entry) for entry in optional if isinstance(entry, dict)}
    if any(_metric_key(entry) not in optional_keys for entry in tail):
        errors.append("run selected_metrics contains an unregistered optional metric")
    expected_tail = [entry for entry in optional if isinstance(entry, dict) and _metric_key(entry) in {_metric_key(item) for item in tail if isinstance(item, dict)}]
    if tail != expected_tail:
        errors.append("run selected optional metrics must follow Question optional_metrics order")
    return errors


def validate_simulation_run(run, *, question, policy, question_contract, run_contract, project_id, load_reference, fingerprint_for_version, lifecycle_mode, lifecycle=None, lifecycle_path=None, lifecycle_contract=None):
    run_contract, errors = resolve_policy_pinned_contract(
        policy, run_contract, reference_key="simulation_run_contract", load_reference=load_reference,
    )
    if run_contract is None:
        return errors
    errors.extend(_required(run, (run_contract.get("required_fields") or {}).keys(), "run"))
    if not isinstance(run, dict): return errors
    question_path = ((run.get("semantic_dependencies") or {}).get("question") or {}).get("path")
    errors.extend(validate_simulation_question(question, policy=policy, question_contract=question_contract, project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version, question_path=question_path))
    errors.extend(_unregistered_top_level_field_errors(run, run_contract, "run"))
    errors.extend(validate_recording_context(run_contract.get("recording_context"), id_field="run_id", created_at_required=False))
    if not isinstance(run.get("run_id"), str) or not run.get("run_id"):
        errors.append("run run_id must be a non-empty string")
    if run.get("artifact_type") != "simulation_run": errors.append("run artifact_type must be 'simulation_run'")
    if run.get("project_id") != project_id: errors.append("run project_id does not match the project")
    if run.get("policy_id") != policy.get("policy_id") or run.get("policy_version") != policy.get("policy_version"): errors.append("run policy binding does not match policy")
    errors.extend(validate_run_role_binding(run, question))
    path = run.get("deck_version_path")
    try: version = load_reference(path)
    except (OSError, ValueError, KeyError, TypeError) as exc: version = None; errors.append(f"run deck_version_path does not resolve: {exc}")
    if isinstance(version, dict):
        if run.get("deck_version_id") != version.get("version_id"): errors.append("run deck_version_id does not match DeckVersion")
        if run.get("deck_content_fingerprint") != fingerprint_for_version(version): errors.append("run fingerprint does not match DeckVersion")
    errors.extend(_validate_bundle(run.get("semantic_dependencies"), policy=policy, question=question, deck_path=path, deck_fingerprint=run.get("deck_content_fingerprint"), load_reference=load_reference))
    seed = run.get("seed")
    if not _integer(seed) or not 0 <= seed < 2 ** 64: errors.append("run seed must be unsigned 64-bit integer")
    else:
        question_ref = (run.get("semantic_dependencies") or {}).get("question", {})
        policy_ref = (run.get("semantic_dependencies") or {}).get("policy", {})
        expected = derive_run_seed(question_ref.get("content_fingerprint", ""), policy_ref.get("content_fingerprint", ""), run.get("deck_content_fingerprint", ""), run.get("run_role", ""))
        if seed != expected: errors.append("run seed is not immutable-semantics-derived")
    if run.get("seed_derivation_algorithm_id") != "sim-seed-sha256-v2": errors.append("run must use sim-seed-sha256-v2")
    if not _integer(run.get("iteration_count")) or run["iteration_count"] < (policy.get("iteration_policy") or {}).get("minimum_saved_iterations", 0): errors.append("run iteration_count is below policy minimum")
    if run.get("rng_id") != "pcg32-v1": errors.append("run rng_id must be pcg32-v1")
    if run.get("seed_type") != "unsigned_64_bit": errors.append("run seed_type must be unsigned_64_bit")
    if run.get("scenario_ref") != f"{policy.get('policy_version')}:commander_scenario": errors.append("run scenario_ref does not match the resolved policy")
    if run.get("status") not in (run_contract.get("required_fields", {}).get("status", {}).get("allowed_values") or []): errors.append("run status is not allowed by the contract")
    errors.extend(_validate_selected_metrics(run.get("selected_metrics"), question))
    expected_config = {
        "mulligan_policy_ref": f"{policy.get('policy_version')}:mulligan_policy",
        "keep_rule_ref": f"{policy.get('policy_version')}:keep_rule",
        "bottoming_rule_ref": f"{policy.get('policy_version')}:bottoming_rule",
        "observation_horizon_turn": (policy.get("turn_semantics") or {}).get("observation_horizon_turn"),
        "card_semantics_ref": (policy.get("references") or {}).get("card_semantics", {}).get("path"),
        "mana_source_semantics_ref": (policy.get("references") or {}).get("mana_source_semantics", {}).get("path"),
    }
    config = run.get("config")
    expected_config_fields = set((run_contract.get("required_fields", {}).get("config", {}).get("required_fields") or []))
    if not isinstance(config, dict) or set(config) != expected_config_fields or any(config.get(field) != expected for field, expected in expected_config.items()):
        errors.append("run configuration does not match the resolved policy")
    if not isinstance(config, dict) or config.get("sequencing_levels") != ["level_1", "level_2"]:
        errors.append("run config.sequencing_levels must equal the approved sequence")
    boundary = run.get("explicit_boundary")
    expected_boundary_fields = set((run_contract.get("required_fields", {}).get("explicit_boundary", {}).get("required_fields") or []))
    if not isinstance(boundary, dict) or set(boundary) != expected_boundary_fields or any(boundary.get(key) is not False for key in expected_boundary_fields):
        errors.append("run explicit_boundary flags must all be false")
    required_limitations, limitation_errors = _required_unsupported_limitation_ids(run, load_reference=load_reference)
    errors.extend(limitation_errors)
    _validate_unsupported_limitations(run.get("limitations"), required_limitations, "run", errors)
    errors.extend(_reserved_lifecycle_key_errors(run))
    for key in ("metrics", "probability", "metric_deltas", "result_id", "comparison_id"):
        if key in run: errors.append(f"run must not carry {key}")
    errors.extend(_validate_lifecycle_mode(
        lifecycle_mode=lifecycle_mode, lifecycle=lifecycle, lifecycle_path=lifecycle_path, lifecycle_contract=lifecycle_contract,
        question=question, policy=policy, question_contract=question_contract,
        project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version,
        artifact=run, artifact_kind="run",
    ))
    return errors


def validate_simulation_result(result, *, run, policy, question, question_contract, result_contract, taxonomy_ids, load_reference, project_id, fingerprint_for_version, lifecycle_mode, lifecycle=None, lifecycle_path=None, lifecycle_contract=None):
    result_contract, errors = resolve_policy_pinned_contract(
        policy, result_contract, reference_key="simulation_result_contract", load_reference=load_reference,
    )
    if result_contract is None:
        return errors
    errors.extend(_required(result, (result_contract.get("required_fields") or {}).keys(), "result"))
    if not isinstance(result, dict): return errors
    question_path = ((run.get("semantic_dependencies") or {}).get("question") or {}).get("path")
    errors.extend(validate_simulation_question(question, policy=policy, question_contract=question_contract, project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version, question_path=question_path))
    errors.extend(_unregistered_top_level_field_errors(result, result_contract, "result"))
    errors.extend(_reserved_lifecycle_key_errors(result))
    errors.extend(validate_recording_context(result_contract.get("recording_context"), id_field="result_id", created_at_required=True))
    if not isinstance(result.get("result_id"), str) or not result.get("result_id"):
        errors.append("result result_id must be a non-empty string")
    if not _valid_recording_timestamp(result.get("created_at")):
        errors.append("result created_at must be a non-empty ISO-8601 UTC recording string")
    if result.get("artifact_type") != "simulation_result": errors.append("result artifact_type must be 'simulation_result'")
    for field in ("project_id", "run_id", "deck_version_id", "deck_content_fingerprint", "policy_version", "iteration_count"):
        if result.get(field) != run.get(field): errors.append(f"result {field} does not match run")
    refs = result.get("source_references") or {}; _resolve_reference(refs.get("run"), "result source_references.run", errors, load_reference, run)
    if result.get("semantic_dependencies") != run.get("semantic_dependencies"): errors.append("result semantic_dependencies do not match run semantic lineage")
    errors.extend(_validate_bundle(
        result.get("semantic_dependencies"), policy=policy, question=question,
        deck_path=run.get("deck_version_path"), deck_fingerprint=run.get("deck_content_fingerprint"),
        load_reference=load_reference,
    ))
    catalog = _metric_catalog(policy); metrics = result.get("metrics")
    if not isinstance(metrics, list) or not metrics: errors.append("result metrics must be non-empty") ; return errors
    if any(not isinstance(m, dict) for m in metrics): errors.append("result metrics must contain only objects")
    keys = [_metric_key(m) for m in metrics if isinstance(m, dict)]
    if len(keys) != len(set(keys)): errors.append("result metrics contain duplicate metric keys")
    selected = run.get("selected_metrics")
    if not isinstance(selected, list) or keys != [_metric_key(m) for m in selected if isinstance(m, dict)]:
        errors.append("result metrics must exactly equal the Run selected_metrics ordered set")
    for metric in metrics:
        definition = catalog.get(_metric_key(metric))
        if definition is None:
            errors.append("result metric does not resolve to a Policy metric definition")
        elif definition.get("shape") == "categorical_count": _validate_categorical(metric, run.get("iteration_count"), errors)
        else: _validate_bernoulli(metric, run.get("iteration_count"), errors)
    if not isinstance(taxonomy_ids, dict):
        errors.append("result validation requires the resolved failure taxonomy artifact")
    else:
        errors.extend(validate_failure_pattern_taxonomy(taxonomy_ids, policy=policy, question=question))
        errors.extend(validate_result_failure_patterns(result.get("failure_patterns"), run.get("iteration_count"), taxonomy_ids, question))
    errors.extend(validate_failure_pattern_aggregate_consistency(metrics, result.get("failure_patterns"), run.get("iteration_count")))
    required_limitations, limitation_errors = _required_unsupported_limitation_ids(run, load_reference=load_reference)
    errors.extend(limitation_errors)
    _validate_unsupported_limitations(result.get("limitations"), required_limitations, "result", errors)
    if "observations" in result: errors.append("result must not carry free-form observations")
    boundary = result.get("explicit_boundary")
    if not isinstance(boundary, dict) or any(boundary.get(key) is not False for key in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version")):
        errors.append("result explicit_boundary flags must all be false")
    _validate_claims(result.get("evidence_claims"), {_metric_key(m): m for m in metrics if isinstance(m, dict)}, "metric_estimate", result.get("readable_summary"), errors)
    errors.extend(_validate_lifecycle_mode(
        lifecycle_mode=lifecycle_mode, lifecycle=lifecycle, lifecycle_path=lifecycle_path, lifecycle_contract=lifecycle_contract,
        question=question, policy=policy, question_contract=question_contract,
        project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version,
        artifact=result, artifact_kind="result",
    ))
    return errors


def validate_comparison_result(comparison, *, baseline_run, candidate_run, baseline_result, candidate_result, policy, question, question_contract, comparison_contract, run_contract, result_contract, project_id, taxonomy_ids, load_reference, fingerprint_for_version, lifecycle_mode, lifecycle=None, lifecycle_path=None, lifecycle_contract=None):
    errors = []
    resolved_contracts = {}
    for reference_key, supplied in (
        ("comparison_result_contract", comparison_contract),
        ("simulation_run_contract", run_contract),
        ("simulation_result_contract", result_contract),
    ):
        resolved, resolution_errors = resolve_policy_pinned_contract(
            policy, supplied, reference_key=reference_key, load_reference=load_reference,
        )
        errors.extend(resolution_errors)
        resolved_contracts[reference_key] = resolved
    if any(contract is None for contract in resolved_contracts.values()):
        return errors
    comparison_contract = resolved_contracts["comparison_result_contract"]
    run_contract = resolved_contracts["simulation_run_contract"]
    result_contract = resolved_contracts["simulation_result_contract"]
    errors.extend(_required(comparison, (comparison_contract.get("required_fields") or {}).keys(), "comparison"))
    if not isinstance(comparison, dict): return errors
    errors.extend(_unregistered_top_level_field_errors(comparison, comparison_contract, "comparison"))
    errors.extend(_reserved_lifecycle_key_errors(comparison))
    errors.extend(validate_recording_context(comparison_contract.get("recording_context"), id_field="comparison_id", created_at_required=True))
    if not isinstance(comparison.get("comparison_id"), str) or not comparison.get("comparison_id"):
        errors.append("comparison comparison_id must be a non-empty string")
    if not _valid_recording_timestamp(comparison.get("created_at")):
        errors.append("comparison created_at must be a non-empty ISO-8601 UTC recording string")
    if comparison.get("artifact_type") != "comparison_result": errors.append("comparison artifact_type must be 'comparison_result'")
    if comparison.get("project_id") != project_id: errors.append("comparison project_id does not match the project")
    if comparison.get("question_id") != question.get("question_id"): errors.append("comparison question_id does not match the question")
    if comparison.get("policy_version") != policy.get("policy_version"): errors.append("comparison policy_version does not match the policy")
    comparison_sides = question.get("comparison_sides") if isinstance(question, dict) else None
    if not isinstance(comparison_sides, dict):
        errors.append("comparison requires Question-owned comparison_sides")
    else:
        if baseline_run.get("run_role") != comparison_sides.get("baseline_run_role"):
            errors.append("comparison baseline Run role does not match Question comparison_sides")
        if candidate_run.get("run_role") != comparison_sides.get("candidate_run_role"):
            errors.append("comparison candidate Run role does not match Question comparison_sides")
    if comparison.get("iteration_count") != baseline_run.get("iteration_count") or comparison.get("iteration_count") != candidate_run.get("iteration_count"):
        errors.append("comparison iteration_count does not match both runs")
    for label, run in (("baseline", baseline_run), ("candidate", candidate_run)):
        for error in validate_simulation_run(run, question=question, policy=policy, question_contract=question_contract, run_contract=run_contract, project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version, lifecycle_mode=lifecycle_mode, lifecycle=lifecycle, lifecycle_path=lifecycle_path, lifecycle_contract=lifecycle_contract): errors.append(f"comparison {label} SimulationRun is invalid: {error}")
    for label, result, run in (("baseline", baseline_result, baseline_run), ("candidate", candidate_result, candidate_run)):
        for error in validate_simulation_result(result, run=run, policy=policy, question=question, question_contract=question_contract, result_contract=result_contract, taxonomy_ids=taxonomy_ids, load_reference=load_reference, project_id=project_id, fingerprint_for_version=fingerprint_for_version, lifecycle_mode=lifecycle_mode, lifecycle=lifecycle, lifecycle_path=lifecycle_path, lifecycle_contract=lifecycle_contract): errors.append(f"comparison {label} SimulationResult is invalid: {error}")
    expected_bundle = {key: value for key, value in (baseline_run.get("semantic_dependencies") or {}).items() if key != "deck_version"}
    if comparison.get("semantic_dependencies") != expected_bundle:
        errors.append("comparison semantic dependencies do not match resolved run lineage")
    errors.extend(_validate_bundle(
        comparison.get("semantic_dependencies"), policy=policy, question=question,
        deck_path=baseline_run.get("deck_version_path"), deck_fingerprint=baseline_run.get("deck_content_fingerprint"),
        load_reference=load_reference, include_deck=False,
    ))
    refs = comparison.get("source_references") or {}
    for key, expected in (("baseline_run", baseline_run), ("candidate_run", candidate_run), ("baseline_result", baseline_result), ("candidate_result", candidate_result)):
        _resolve_reference(refs.get(key), f"comparison source_references.{key}", errors, load_reference, expected)
    for label, side, run, result in (("baseline", comparison.get("baseline"), baseline_run, baseline_result), ("candidate", comparison.get("candidate"), candidate_run, candidate_result)):
        if not isinstance(side, dict):
            errors.append(f"comparison {label} side must be an object")
            continue
        for field, expected in (
            ("deck_version_id", run.get("deck_version_id")), ("run_id", run.get("run_id")),
            ("result_id", result.get("result_id")), ("deck_content_fingerprint", run.get("deck_content_fingerprint")),
            ("run_role", run.get("run_role")),
        ):
            if side.get(field) != expected:
                errors.append(f"comparison {label}.{field} does not match resolved evidence")
    if baseline_run.get("deck_version_id") == candidate_run.get("deck_version_id"):
        errors.append("comparison baseline and candidate must reference distinct DeckVersions")
    for field in ("question_id", "policy_id", "policy_version", "iteration_count", "scenario_ref", "config", "rng_id", "seed_derivation_algorithm_id"):
        if baseline_run.get(field) != candidate_run.get(field):
            errors.append(f"comparison semantic parity fails for {field}")
    if baseline_run.get("selected_metrics") != candidate_run.get("selected_metrics"):
        errors.append("comparison selected_metrics must be identical across both Runs")
    bmetrics={_metric_key(m):m for m in baseline_result.get("metrics", []) if isinstance(m, dict)}; cmetrics={_metric_key(m):m for m in candidate_result.get("metrics", []) if isinstance(m, dict)}
    if set(bmetrics) != set(cmetrics): errors.append("comparison optional metric selection is asymmetric")
    deltas=comparison.get("metric_deltas")
    if not isinstance(deltas,list) or not deltas: errors.append("comparison metric_deltas must be non-empty"); return errors
    if any(not isinstance(d, dict) for d in deltas): errors.append("comparison metric_deltas must contain only objects")
    keys=[_metric_key(d) for d in deltas if isinstance(d,dict)]
    if len(keys)!=len(set(keys)): errors.append("comparison metric_deltas contain duplicate metric keys")
    selected_keys = [_metric_key(m) for m in baseline_run.get("selected_metrics", []) if isinstance(m, dict)]
    if keys != selected_keys: errors.append("comparison metric_deltas must exactly equal the selected metric set in order")
    for delta in deltas:
        key=_metric_key(delta); bm,cm=bmetrics.get(key),cmetrics.get(key)
        if not bm or not cm: continue
        allowed = ({"metric_id", "target_turn", "baseline_estimate", "candidate_estimate", "mean_absolute_delta", "bin_proportion_deltas"}
                   if "bins" in bm else {"metric_id", "target_turn", "baseline_estimate", "candidate_estimate", "absolute_delta", "relative_delta", "relative_delta_applicable"})
        if not set(delta) <= allowed:
            errors.append("comparison metric delta must not redefine Policy measurement semantics")
        if delta.get("baseline_estimate")!=bm or delta.get("candidate_estimate")!=cm: errors.append("comparison estimate does not match resolved result metric"); continue
        if "bins" in bm:
            if not math.isclose(delta.get("mean_absolute_delta", float("nan")), cm["mean"]-bm["mean"], abs_tol=1e-12): errors.append("comparison categorical mean delta is invalid")
            bins=delta.get("bin_proportion_deltas")
            if not isinstance(bins,list) or [item.get("value") for item in bins if isinstance(item, dict)] != list(range(6)):
                errors.append("comparison categorical metric requires exactly six ordered bin deltas")
            else:
                for item, baseline_bin, candidate_bin in zip(bins, bm["bins"], cm["bins"]):
                    expected = candidate_bin["proportion"] - baseline_bin["proportion"]
                    if not math.isclose(item.get("absolute_delta", float("nan")), expected, abs_tol=1e-12):
                        errors.append("comparison categorical bin delta is invalid")
        else:
            expected=cm["probability"]-bm["probability"]
            if not math.isclose(delta.get("absolute_delta", float("nan")), expected, abs_tol=1e-12): errors.append("comparison absolute_delta does not equal candidate minus baseline")
            baseline_probability = bm["probability"]
            if baseline_probability == 0:
                if delta.get("relative_delta") is not None or delta.get("relative_delta_applicable") is not False:
                    errors.append("comparison relative_delta must be unavailable when baseline probability is zero")
            elif delta.get("relative_delta") is not None and (not math.isclose(delta.get("relative_delta"), expected / baseline_probability, abs_tol=1e-12) or delta.get("relative_delta_applicable") is not True):
                errors.append("comparison relative_delta is invalid")
        if "delta_confidence_interval" in delta: errors.append("comparison must not define a delta confidence interval")
        if "bins" in bm and ("relative_delta" in delta or "relative_delta_applicable" in delta): errors.append("categorical comparison must not define relative_delta")
    boundary = comparison.get("explicit_boundary")
    if not isinstance(boundary, dict) or any(boundary.get(key) is not False for key in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version")) or not isinstance(boundary.get("attributes_deck_content_effect"), bool):
        errors.append("comparison explicit_boundary flags are invalid")
    _validate_claims(comparison.get("evidence_claims"), {_metric_key(d): d for d in deltas if isinstance(d, dict)}, "comparison_delta", comparison.get("readable_summary"), errors)
    if baseline_run.get("deck_content_fingerprint")==candidate_run.get("deck_content_fingerprint") and (comparison.get("explicit_boundary") or {}).get("attributes_deck_content_effect") is not False: errors.append("equal-content comparison must not attribute a deck-content effect")
    errors.extend(_validate_lifecycle_mode(
        lifecycle_mode=lifecycle_mode, lifecycle=lifecycle, lifecycle_path=lifecycle_path, lifecycle_contract=lifecycle_contract,
        question=question, policy=policy, question_contract=question_contract,
        project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version,
        artifact=comparison, artifact_kind="comparison",
    ))
    return errors
