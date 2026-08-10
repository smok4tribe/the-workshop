"""Reusable standard-library validation for simulation evidence instances.

The Task 30 validator has no production Run, Result, or Comparison instances to
load. Future production writers and the committed fixture tests call these
functions so their instance rules stay identical.
"""

from __future__ import annotations

import math


def _required_fields(document, fields, label):
    if not isinstance(document, dict):
        return [f"{label} must be an object"]
    return [f"{label} is missing required field {field!r}" for field in fields if field not in document]


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _decimal_places(value):
    text = format(value, "f").rstrip("0").rstrip(".")
    return len(text.partition(".")[2])


def _rounded_matches(actual, expected):
    if not _is_number(actual):
        return False
    return round(expected, _decimal_places(actual)) == actual


def wilson_interval(raw_count, sample_size, confidence_level=0.95):
    """Return the two-sided Wilson interval for the frozen 95% policy."""
    if not _is_int(raw_count) or not _is_int(sample_size) or sample_size <= 0:
        raise ValueError("raw_count and sample_size must be valid positive-count inputs")
    if confidence_level != 0.95:
        raise ValueError("only the frozen 95% confidence level is supported")
    z = 1.959963984540054
    probability = raw_count / sample_size
    denominator = 1 + (z * z / sample_size)
    center = (probability + (z * z / (2 * sample_size))) / denominator
    margin = z * math.sqrt((probability * (1 - probability) / sample_size) + (z * z / (4 * sample_size * sample_size))) / denominator
    return center - margin, center + margin


def validate_question_role_bindings(compared_versions):
    """Validate the generic one-DeckVersion/one-unique-role invariant."""
    if not isinstance(compared_versions, list):
        return ["question compared_versions must be an array"]
    errors = []
    version_ids = []
    roles = []
    for index, version in enumerate(compared_versions):
        if not isinstance(version, dict):
            errors.append(f"question compared_versions[{index}] must be an object")
            continue
        version_id = version.get("deck_version_id")
        run_role = version.get("run_role")
        if not isinstance(version_id, str) or not version_id:
            errors.append(f"question compared_versions[{index}] is missing deck_version_id")
        else:
            version_ids.append(version_id)
        if not isinstance(run_role, str) or not run_role:
            errors.append(f"question compared_versions[{index}] is missing run_role")
        else:
            roles.append(run_role)
    if len(version_ids) != len(set(version_ids)):
        errors.append("question compared_versions must contain each DeckVersion once")
    if len(roles) != len(set(roles)):
        errors.append("question compared_versions must use unique run_role values")
    return errors


def validate_run_role_binding(run, question):
    """Validate that a Run uses the role bound by its referenced Question."""
    if not isinstance(run, dict):
        return ["run must be an object"]
    if not isinstance(question, dict):
        return ["question must be an object"]
    errors = []
    if run.get("question_id") != question.get("question_id"):
        errors.append("run question_id does not match the referenced question")
    roles_by_version = {
        entry.get("deck_version_id"): entry.get("run_role")
        for entry in question.get("compared_versions", [])
        if isinstance(entry, dict)
    }
    version_id = run.get("deck_version_id")
    expected_role = roles_by_version.get(version_id)
    if expected_role is None:
        errors.append("run DeckVersion is not bound by the question")
    elif run.get("run_role") != expected_role:
        errors.append("run role is not bound to the question DeckVersion")
    return errors


def validate_failure_pattern(pattern, run_iteration_count, taxonomy_ids):
    """Validate a quantitative failure pattern against its source Run."""
    if not isinstance(pattern, dict):
        return ["failure pattern must be an object"]
    errors = _required_fields(pattern, ("category_id", "raw_count", "sample_size", "frequency"), "failure pattern")
    if pattern.get("category_id") not in taxonomy_ids:
        errors.append("failure pattern references undefined category")
    raw_count = pattern.get("raw_count")
    sample_size = pattern.get("sample_size")
    frequency = pattern.get("frequency")
    if not _is_int(raw_count):
        errors.append("failure pattern raw_count must be an integer")
    if not _is_int(sample_size):
        errors.append("failure pattern sample_size must be an integer")
    elif sample_size <= 0:
        errors.append("failure pattern sample_size must be positive")
    elif sample_size != run_iteration_count:
        errors.append("failure pattern sample_size does not match run iteration_count")
    if _is_int(raw_count) and _is_int(sample_size) and (raw_count < 0 or raw_count > sample_size):
        errors.append("failure pattern raw_count must be within 0..sample_size")
    if not _is_number(frequency):
        errors.append("failure pattern frequency must be numeric")
    elif frequency < 0 or frequency > 1:
        errors.append("failure pattern frequency must be within 0..1")
    elif _is_int(raw_count) and _is_int(sample_size) and sample_size > 0:
        if not math.isclose(frequency, raw_count / sample_size, rel_tol=0.0, abs_tol=1e-12):
            errors.append("failure pattern frequency does not equal raw_count/sample_size")
    return errors


def validate_simulation_run(run, *, question, policy, run_contract, project_id, load_reference, fingerprint_for_version, derive_seed):
    """Validate a saved SimulationRun against its Question, Policy, and deck."""
    required = (run_contract.get("required_fields") or {}).keys()
    errors = _required_fields(run, required, "run")
    if not isinstance(run, dict):
        return errors
    if run.get("artifact_type") != "simulation_run":
        errors.append("run artifact_type must be 'simulation_run'")
    if run.get("project_id") != project_id:
        errors.append("run project_id does not match the project")
    if run.get("policy_id") != policy.get("policy_id") or run.get("policy_version") != policy.get("policy_version"):
        errors.append("run policy binding does not match the referenced policy")
    errors.extend(validate_run_role_binding(run, question))

    version = None
    path = run.get("deck_version_path")
    if not isinstance(path, str):
        errors.append("run deck_version_path must be a repo-relative string")
    else:
        try:
            version = load_reference(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"run deck_version_path does not resolve: {exc}")
    if isinstance(version, dict):
        if run.get("deck_version_id") != version.get("version_id"):
            errors.append("run deck_version_id does not match the referenced DeckVersion")
        expected_fingerprint = fingerprint_for_version(version)
        if run.get("deck_content_fingerprint") != expected_fingerprint:
            errors.append("run fingerprint does not match DeckVersion")

    seed = run.get("seed")
    if not _is_int(seed) or seed < 0 or seed >= 2 ** 64:
        errors.append("run seed must be an unsigned 64-bit integer")
    else:
        expected_seed = derive_seed(
            run.get("question_id", ""), run.get("policy_version", ""),
            run.get("deck_content_fingerprint", ""), run.get("run_role", ""),
        )
        if seed != expected_seed:
            errors.append("run seed is not policy-derived")
    minimum = (policy.get("iteration_policy") or {}).get("minimum_saved_iterations")
    if not _is_int(run.get("iteration_count")) or run.get("iteration_count") < minimum:
        errors.append("run iteration_count is below the policy minimum")
    if run.get("rng_id") != (policy.get("randomness_policy") or {}).get("rng_id"):
        errors.append("run rng_id does not match policy")
    if run.get("seed_type") != (policy.get("randomness_policy") or {}).get("seed_type"):
        errors.append("run seed_type does not match policy")
    if run.get("seed_derivation_algorithm_id") != ((policy.get("randomness_policy") or {}).get("canonical_seed_derivation") or {}).get("algorithm_id"):
        errors.append("run seed_derivation_algorithm_id does not match policy")
    expected_scenario_ref = f"{policy.get('policy_version')}:commander_scenario"
    if run.get("scenario_ref") != expected_scenario_ref:
        errors.append("run scenario_ref does not match the policy scenario")
    flags = run.get("explicit_boundary") or {}
    for field in ("carries_metrics", "carries_interpretation", "creates_deck_version"):
        if flags.get(field) is not False:
            errors.append(f"run explicit_boundary.{field} must be false")
    for forbidden in ("metrics", "probability", "reasoning_interpretation", "product_owner_decision"):
        if forbidden in run:
            errors.append(f"run must not carry {forbidden!r}")
    return errors


def validate_simulation_result(result, *, run, policy, result_contract, taxonomy_ids, forbidden_claims):
    """Validate a Result against exactly one resolved SimulationRun."""
    required = (result_contract.get("required_fields") or {}).keys()
    errors = _required_fields(result, required, "result")
    if not isinstance(result, dict):
        return errors
    if result.get("artifact_type") != "simulation_result":
        errors.append("result artifact_type must be 'simulation_result'")
    for field in ("project_id", "run_id", "deck_version_id", "deck_content_fingerprint", "policy_version", "iteration_count"):
        if result.get(field) != run.get(field):
            errors.append(f"result {field} does not match run")
    catalog = {
        (metric.get("metric_id"), metric.get("target_turn"))
        for metric in (policy.get("metric_catalog") or {}).get("metrics", [])
    }
    for metric in result.get("metrics", []):
        if not isinstance(metric, dict):
            errors.append("result metric must be an object")
            continue
        if (metric.get("metric_id"), metric.get("target_turn")) not in catalog:
            errors.append("result metric definition is not in the policy catalog")
        raw_count = metric.get("raw_count")
        sample_size = metric.get("sample_size")
        probability = metric.get("probability")
        if not _is_int(raw_count) or not _is_int(sample_size):
            errors.append("result metric raw_count and sample_size must be integers")
            continue
        if sample_size != run.get("iteration_count"):
            errors.append("result metric sample_size does not match run iteration_count")
        if raw_count < 0 or raw_count > sample_size:
            errors.append("result metric raw_count must be within 0..sample_size")
        if not _is_number(probability) or not math.isclose(probability, raw_count / sample_size, rel_tol=0.0, abs_tol=1e-12):
            errors.append("result metric probability does not equal raw_count/sample_size")
        interval = metric.get("confidence_interval") or {}
        if interval.get("method") != "wilson_score_interval" or interval.get("level") != 0.95:
            errors.append("result metric confidence interval must be Wilson 95%")
        elif sample_size > 0 and 0 <= raw_count <= sample_size:
            lower, upper = wilson_interval(raw_count, sample_size)
            if not _rounded_matches(interval.get("lower"), lower) or not _rounded_matches(interval.get("upper"), upper):
                errors.append("result metric confidence interval does not match Wilson 95%")
    for pattern in result.get("failure_patterns", []):
        errors.extend(validate_failure_pattern(pattern, run.get("iteration_count"), taxonomy_ids))
    for forbidden in ("reasoning_interpretation", "product_owner_decision"):
        if forbidden in result:
            errors.append("result carries interpretation or decision")
    for text in [result.get("readable_summary", "")] + list(result.get("observations", [])):
        if forbidden_claims(text):
            errors.append("result contains forbidden evidence-language claim")
    flags = result.get("explicit_boundary") or {}
    for field in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version"):
        if flags.get(field) is not False:
            errors.append(f"result explicit_boundary.{field} must be false")
    return errors


def validate_comparison_result(comparison, *, baseline_run, candidate_run, baseline_result, candidate_result, policy, question, comparison_contract, forbidden_claims, load_reference=None):
    """Validate a ComparisonResult from resolved Runs and Results, not parity flags."""
    required = (comparison_contract.get("required_fields") or {}).keys()
    errors = _required_fields(comparison, required, "comparison")
    if not isinstance(comparison, dict):
        return errors
    if comparison.get("artifact_type") != "comparison_result":
        errors.append("comparison artifact_type must be 'comparison_result'")
    if comparison.get("project_id") != policy.get("project_id"):
        errors.append("comparison project_id does not match policy")
    if comparison.get("question_id") != question.get("question_id"):
        errors.append("comparison question_id does not match question")
    if comparison.get("policy_version") != policy.get("policy_version"):
        errors.append("comparison policy_version does not match policy")
    if comparison.get("iteration_count") != baseline_run.get("iteration_count") or comparison.get("iteration_count") != candidate_run.get("iteration_count"):
        errors.append("comparison iteration_count does not match both runs")
    if baseline_run.get("deck_version_id") == candidate_run.get("deck_version_id"):
        errors.append("comparison must reference distinct DeckVersions")

    for label, side, run, result in (
        ("baseline", comparison.get("baseline") or {}, baseline_run, baseline_result),
        ("candidate", comparison.get("candidate") or {}, candidate_run, candidate_result),
    ):
        for field, expected in (
            ("deck_version_id", run.get("deck_version_id")), ("run_id", run.get("run_id")),
            ("result_id", result.get("result_id")), ("deck_content_fingerprint", run.get("deck_content_fingerprint")),
            ("run_role", run.get("run_role")),
        ):
            if side.get(field) != expected:
                errors.append(f"comparison {label}.{field} does not match resolved evidence")

    if load_reference is not None:
        for reference_key, expected in (
            ("baseline_run", baseline_run), ("candidate_run", candidate_run),
            ("baseline_result", baseline_result), ("candidate_result", candidate_result),
        ):
            path = (comparison.get("source_references") or {}).get(reference_key)
            try:
                resolved = load_reference(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f"comparison {reference_key} does not resolve: {exc}")
                continue
            if resolved != expected:
                errors.append(f"comparison {reference_key} does not resolve to supplied evidence")

    if baseline_run.get("policy_version") != candidate_run.get("policy_version"):
        errors.append("comparison semantic parity failed: policy differs")
    if baseline_run.get("question_id") != candidate_run.get("question_id"):
        errors.append("comparison semantic parity failed: question differs")
    if baseline_run.get("iteration_count") != candidate_run.get("iteration_count"):
        errors.append("comparison semantic parity failed: iteration count differs")
    if baseline_run.get("config") != candidate_run.get("config"):
        errors.append("comparison semantic parity failed: config differs")
    if baseline_run.get("scenario_ref") != candidate_run.get("scenario_ref"):
        errors.append("comparison semantic parity failed: scenario differs")
    rng_fields = ("rng_id", "seed_type", "seed_derivation_algorithm_id")
    if any(baseline_run.get(field) != candidate_run.get(field) for field in rng_fields):
        errors.append("comparison semantic parity failed: RNG strategy differs")
    if (policy.get("randomness_policy") or {}).get("comparison_stream_mode") != "independent_deterministic_streams":
        errors.append("comparison policy must use independent_deterministic_streams")
    baseline_metrics = {(metric.get("metric_id"), metric.get("target_turn")): metric for metric in baseline_result.get("metrics", [])}
    candidate_metrics = {(metric.get("metric_id"), metric.get("target_turn")): metric for metric in candidate_result.get("metrics", [])}
    if set(baseline_metrics) != set(candidate_metrics):
        errors.append("comparison semantic parity failed: metric definitions differ")

    for delta in comparison.get("metric_deltas", []):
        key = (delta.get("metric_id"), delta.get("target_turn"))
        baseline_metric = baseline_metrics.get(key)
        candidate_metric = candidate_metrics.get(key)
        if baseline_metric is None or candidate_metric is None:
            errors.append("comparison metric_delta does not resolve to both result metrics")
            continue
        for side_label, estimate, metric in (
            ("baseline", delta.get("baseline_estimate") or {}, baseline_metric),
            ("candidate", delta.get("candidate_estimate") or {}, candidate_metric),
        ):
            for field in ("raw_count", "sample_size", "probability", "confidence_interval"):
                if estimate.get(field) != metric.get(field):
                    errors.append(f"comparison {side_label}_estimate does not match resolved result metric")
                    break
        baseline_probability = baseline_metric.get("probability")
        candidate_probability = candidate_metric.get("probability")
        expected_delta = candidate_probability - baseline_probability
        if not _is_number(delta.get("absolute_delta")) or not math.isclose(delta["absolute_delta"], expected_delta, rel_tol=0.0, abs_tol=1e-12):
            errors.append("comparison absolute_delta does not equal candidate minus baseline")
        relative_delta = delta.get("relative_delta")
        if baseline_probability == 0:
            if relative_delta is not None or delta.get("relative_delta_applicable") not in (False, None):
                errors.append("comparison relative_delta is invalid with zero baseline")
        elif relative_delta is not None:
            expected_relative = expected_delta / baseline_probability
            if not _is_number(relative_delta) or not _rounded_matches(relative_delta, expected_relative):
                errors.append("comparison relative_delta does not match resolved estimates")
    flags = comparison.get("explicit_boundary") or {}
    for field in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version"):
        if flags.get(field) is not False:
            errors.append(f"comparison explicit_boundary.{field} must be false")
    if not isinstance(flags.get("attributes_deck_content_effect"), bool):
        errors.append("comparison explicit_boundary.attributes_deck_content_effect must be boolean")
    if baseline_run.get("deck_content_fingerprint") == candidate_run.get("deck_content_fingerprint") and flags.get("attributes_deck_content_effect") is not False:
        errors.append("equal-content comparison must not attribute a deck-content effect")
    if forbidden_claims(comparison.get("readable_summary", "")):
        errors.append("comparison contains forbidden evidence-language claim")
    return errors
