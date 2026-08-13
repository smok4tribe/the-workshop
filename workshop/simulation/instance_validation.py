"""Reusable validation for future simulation evidence instances.

This module is production-neutral: callers inject repository resolution and it
does not discover or create evidence artifacts itself.
"""

from __future__ import annotations

import math

from workshop.shared.identity import artifact_content_fingerprint
from workshop.shared.simulation_determinism import derive_run_seed


DEPENDENCY_KEYS = (
    "policy", "question", "card_semantics", "canonical_card_facts",
    "failure_pattern_taxonomy", "simulation_question_contract",
    "simulation_run_contract", "simulation_result_contract",
    "comparison_result_contract",
)
ALLOWED_SUBJECTS = {
    "hand_composition", "land_development", "ramp_access", "mana_development",
    "color_availability", "limitations",
}
RESERVED_LIFECYCLE_KEYS = {"reasoning_interpretation", "product_owner_decision"}


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
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True},
        value={"id": "surviving_online_source_capability_color_cardinality", "projection": "source_capability", "domain": [0, 1, 2, 3, 4, 5], "colors": ["W", "U", "B", "R", "G"], "excluded_colors": ["C"], "source_state": "surviving_and_online", "earlier_tapping_removes_capability": False},
    ),
    "five_color_availability_by_turn": _measurement_contract(
        level="level_2", target_turn=6, shape="bernoulli_probability",
        observation_point={"id": "end_of_target_turn_after_level_2_sequencing", "after_pending_time_dependent_removals": True},
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
        "card_semantics": "card_semantics", "canonical_card_facts": "canonical_card_facts",
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


def validate_simulation_run(run, *, question, policy, run_contract, project_id, load_reference, fingerprint_for_version):
    errors = _required(run, (run_contract.get("required_fields") or {}).keys(), "run")
    if not isinstance(run, dict): return errors
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
    expected_config = {
        "mulligan_policy_ref": f"{policy.get('policy_version')}:mulligan_policy",
        "keep_rule_ref": f"{policy.get('policy_version')}:keep_rule",
        "bottoming_rule_ref": f"{policy.get('policy_version')}:bottoming_rule",
        "observation_horizon_turn": (policy.get("turn_semantics") or {}).get("observation_horizon_turn"),
        "card_semantics_ref": (policy.get("references") or {}).get("card_semantics", {}).get("path"),
    }
    config = run.get("config")
    if not isinstance(config, dict) or any(config.get(field) != expected for field, expected in expected_config.items()):
        errors.append("run configuration does not match the resolved policy")
    if not isinstance(config, dict) or config.get("sequencing_levels") != ["level_1", "level_2"]:
        errors.append("run config.sequencing_levels must equal the approved sequence")
    boundary = run.get("explicit_boundary")
    if not isinstance(boundary, dict) or any(boundary.get(key) is not False for key in ("carries_metrics", "carries_interpretation", "creates_deck_version")):
        errors.append("run explicit_boundary flags must all be false")
    errors.extend(_reserved_lifecycle_key_errors(run))
    for key in ("metrics", "probability", "metric_deltas", "result_id", "comparison_id"):
        if key in run: errors.append(f"run must not carry {key}")
    return errors


def validate_simulation_result(result, *, run, policy, question, result_contract, taxonomy_ids, load_reference):
    errors = _required(result, (result_contract.get("required_fields") or {}).keys(), "result")
    if not isinstance(result, dict): return errors
    errors.extend(_reserved_lifecycle_key_errors(result))
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
    catalog = _metric_catalog(policy); required = {_metric_key(m) for m in question.get("required_metrics", [])}; optional = {_metric_key(m) for m in question.get("optional_metrics", [])}; metrics = result.get("metrics")
    if not isinstance(metrics, list) or not metrics: errors.append("result metrics must be non-empty") ; return errors
    if any(not isinstance(m, dict) for m in metrics): errors.append("result metrics must contain only objects")
    keys = [_metric_key(m) for m in metrics if isinstance(m, dict)]
    if len(keys) != len(set(keys)): errors.append("result metrics contain duplicate metric keys")
    if not required <= set(keys): errors.append("result metrics are missing required question metrics")
    if not set(keys) <= required | optional: errors.append("result metrics contain unregistered metric")
    for metric in metrics:
        definition = catalog.get(_metric_key(metric))
        if definition is None: continue
        if definition.get("shape") == "categorical_count": _validate_categorical(metric, run.get("iteration_count"), errors)
        else: _validate_bernoulli(metric, run.get("iteration_count"), errors)
    for pattern in result.get("failure_patterns", []): errors.extend(validate_failure_pattern(pattern, run.get("iteration_count"), taxonomy_ids))
    if "observations" in result: errors.append("result must not carry free-form observations")
    boundary = result.get("explicit_boundary")
    if not isinstance(boundary, dict) or any(boundary.get(key) is not False for key in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version")):
        errors.append("result explicit_boundary flags must all be false")
    _validate_claims(result.get("evidence_claims"), {_metric_key(m): m for m in metrics if isinstance(m, dict)}, "metric_estimate", result.get("readable_summary"), errors)
    return errors


def validate_comparison_result(comparison, *, baseline_run, candidate_run, baseline_result, candidate_result, policy, question, comparison_contract, run_contract, result_contract, project_id, taxonomy_ids, load_reference, fingerprint_for_version):
    errors = _required(comparison, (comparison_contract.get("required_fields") or {}).keys(), "comparison")
    if not isinstance(comparison, dict): return errors
    errors.extend(_reserved_lifecycle_key_errors(comparison))
    if comparison.get("artifact_type") != "comparison_result": errors.append("comparison artifact_type must be 'comparison_result'")
    if comparison.get("project_id") != project_id: errors.append("comparison project_id does not match the project")
    if comparison.get("question_id") != question.get("question_id"): errors.append("comparison question_id does not match the question")
    if comparison.get("policy_version") != policy.get("policy_version"): errors.append("comparison policy_version does not match the policy")
    if comparison.get("iteration_count") != baseline_run.get("iteration_count") or comparison.get("iteration_count") != candidate_run.get("iteration_count"):
        errors.append("comparison iteration_count does not match both runs")
    for label, run in (("baseline", baseline_run), ("candidate", candidate_run)):
        for error in validate_simulation_run(run, question=question, policy=policy, run_contract=run_contract, project_id=project_id, load_reference=load_reference, fingerprint_for_version=fingerprint_for_version): errors.append(f"comparison {label} SimulationRun is invalid: {error}")
    for label, result, run in (("baseline", baseline_result, baseline_run), ("candidate", candidate_result, candidate_run)):
        for error in validate_simulation_result(result, run=run, policy=policy, question=question, result_contract=result_contract, taxonomy_ids=taxonomy_ids, load_reference=load_reference): errors.append(f"comparison {label} SimulationResult is invalid: {error}")
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
    bmetrics={_metric_key(m):m for m in baseline_result.get("metrics", []) if isinstance(m, dict)}; cmetrics={_metric_key(m):m for m in candidate_result.get("metrics", []) if isinstance(m, dict)}
    if set(bmetrics) != set(cmetrics): errors.append("comparison optional metric selection is asymmetric")
    deltas=comparison.get("metric_deltas")
    if not isinstance(deltas,list) or not deltas: errors.append("comparison metric_deltas must be non-empty"); return errors
    if any(not isinstance(d, dict) for d in deltas): errors.append("comparison metric_deltas must contain only objects")
    keys=[_metric_key(d) for d in deltas if isinstance(d,dict)]
    if len(keys)!=len(set(keys)): errors.append("comparison metric_deltas contain duplicate metric keys")
    if set(keys)!=set(bmetrics): errors.append("comparison metric_deltas must exactly cover reported metrics")
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
    return errors
