#!/usr/bin/env python3
"""Validate the post-v1.1 current-state structural analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from workshop.analysis.structural_analysis import (
    ANALYSIS_METHOD_ID,
    ANALYSIS_METHOD_VERSION,
    PROJECT_ID,
    analysis_snapshot,
    derive_structural_facts,
    derive_v1_delta,
    load_json,
    project_paths,
)


ANALYSIS_PATH = REPO_ROOT / "workshop" / "projects" / PROJECT_ID / "analysis" / "current_v1.1.json"
FORBIDDEN_KEYS = {
    "simulation_run",
    "simulation_result",
    "comparison_result",
    "recommendation_id",
    "product_owner_decision",
}
FORBIDDEN_LANGUAGE = (
    "better mana",
    "fixed color consistency",
    "is stronger",
    "more reliable in games",
    "performs better",
    "improves mana",
    "improved mana",
    "improves consistency",
    "improved consistency",
    "win rate",
    "gameplay performance",
)


def check(name, errors, checks):
    checks.append((name, errors))


def report(checks):
    failed = 0
    for name, errors in checks:
        if errors:
            failed += 1
            print(f"FAIL: {name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS: {name}")
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed")
    return 1 if failed else 0


def flatten_text(value):
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def forbidden_key_paths(value, path=""):
    paths = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}" if path else str(key)
            if key in FORBIDDEN_KEYS:
                paths.append(item_path)
            paths.extend(forbidden_key_paths(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(forbidden_key_paths(item, f"{path}[{index}]"))
    return paths


def main():
    checks = []
    try:
        analysis = load_json(ANALYSIS_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: current v1.1 structural analysis parses\n  - {exc}")
        return 1

    errors = []
    required = {
        "schema_version", "artifact_type", "analysis_id", "analysis_type", "project_id",
        "deck_version_id", "analysis_method", "generated_from", "scope", "computed",
        "historical_context", "structural_observations", "structural_pressure_points",
        "unsupported_or_uncertain_classifications", "assumptions", "limitations",
        "suggested_evidence_questions", "explicit_boundary",
    }
    errors.extend(f"analysis is missing required field {field!r}" for field in sorted(required - set(analysis)))
    if analysis.get("artifact_type") != "structural_analysis":
        errors.append("artifact_type must be 'structural_analysis'")
    if analysis.get("analysis_id") != "current_v1.1":
        errors.append("analysis_id must be 'current_v1.1'")
    if analysis.get("analysis_type") != "post_implementation_current_state_structural_analysis":
        errors.append("analysis_type must identify a post-implementation current-state structural analysis")
    if analysis.get("project_id") != PROJECT_ID:
        errors.append("analysis project_id must be 'the-myr-singularity'")
    if analysis.get("deck_version_id") != "v1.1":
        errors.append("analysis must bind to DeckVersion v1.1")
    if analysis.get("analysis_method") != {"id": ANALYSIS_METHOD_ID, "version": ANALYSIS_METHOD_VERSION}:
        errors.append("analysis method identity is not the registered structural-analysis-v1 method")
    check("analysis identity and model are explicit", errors, checks)

    paths = project_paths(REPO_ROOT)
    errors = []
    expected_sources = {
        "project": ("workshop/projects/the-myr-singularity/project.json", "project_id", PROJECT_ID),
        "deck_version": ("workshop/projects/the-myr-singularity/versions/v1.1.json", "version_id", "v1.1"),
        "card_facts": ("workshop/card-data/cards.json", None, None),
        "functional_roles": ("workshop/knowledge/functional_roles.json", None, None),
        "role_taxonomy": ("workshop/knowledge/role_taxonomy.json", None, None),
    }
    sources = analysis.get("generated_from", {})
    for source_id, (expected_path, identity_key, identity_value) in expected_sources.items():
        source = sources.get(source_id)
        if not isinstance(source, dict):
            errors.append(f"analysis source reference {source_id!r} is missing")
            continue
        if source.get("path") != expected_path:
            errors.append(f"analysis source reference {source_id!r} must use {expected_path!r}")
            continue
        path = REPO_ROOT / source["path"]
        try:
            document = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"analysis source reference {source_id!r} does not resolve: {exc}")
            continue
        if identity_key and source.get(identity_key) != identity_value:
            errors.append(f"analysis source reference {source_id!r} does not record {identity_key}={identity_value!r}")
        document_identity_key = "id" if source_id == "project" else identity_key
        if document_identity_key and document.get(document_identity_key) != identity_value:
            errors.append(
                f"analysis source {source_id!r} does not resolve to "
                f"{document_identity_key}={identity_value!r}"
            )
    check("analysis source references resolve to the authoritative v1.1 inputs", errors, checks)

    errors = []
    try:
        derived = derive_structural_facts(REPO_ROOT)
        snapshot = analysis_snapshot(REPO_ROOT)
    except ValueError as exc:
        derived = None
        snapshot = None
        errors.append(str(exc))
    if snapshot and analysis.get("computed") != snapshot:
        errors.append("analysis computed structural facts do not match recomputation from DeckVersion v1.1")
    if derived and sources.get("deck_version", {}).get("deck_content_fingerprint") != derived["deck_content_fingerprint"]:
        errors.append("analysis DeckVersion fingerprint does not match v1.1 recomputation")
    check("all recorded structural counts and the v1.1 fingerprint recompute exactly", errors, checks)

    errors = []
    expected_delta = derive_v1_delta(REPO_ROOT)
    if analysis.get("historical_context", {}).get("exact_deck_content_delta_from_v1.0") != expected_delta:
        errors.append("historical v1.0 to v1.1 context does not match the exact DeckVersion diff")
    observation = analysis.get("historical_context", {}).get("observation", "")
    if "structural" not in observation.casefold() or "unmeasured" not in observation.casefold():
        errors.append("historical context must distinguish structural observation from unmeasured performance")
    check("v1.0 relationship is exact provenance context, not a current-state derivation", errors, checks)

    errors = []
    text = flatten_text(analysis).casefold()
    for path in forbidden_key_paths(analysis):
        key = path.rsplit(".", 1)[-1]
        errors.append(f"analysis must not contain forbidden artifact key {key!r} at {path}")
    for phrase in FORBIDDEN_LANGUAGE:
        if phrase in text:
            errors.append(f"analysis contains prohibited performance language {phrase!r}")
    boundary = analysis.get("explicit_boundary", {})
    if boundary.get("simulation_execution") != "not_executed":
        errors.append("analysis must state that simulation execution is not_executed")
    if boundary.get("recommendations_created") is not False:
        errors.append("analysis must state that no Recommendation was created")
    if boundary.get("decisions_created") is not False:
        errors.append("analysis must state that no Product Owner Decision was created")
    check("analysis preserves simulation, performance, recommendation, and decision boundaries", errors, checks)

    errors = []
    questions = analysis.get("suggested_evidence_questions")
    if not isinstance(questions, list) or not questions:
        errors.append("analysis must record an evidence question rather than a recommendation")
    else:
        question = questions[0]
        if question.get("question_id") != "question-001-mana-color":
            errors.append("suggested evidence question must reference question-001-mana-color")
        if question.get("execution_status") != "not_executed":
            errors.append("suggested evidence question must remain not_executed")
        if not str(question.get("purpose", "")).casefold().startswith("test"):
            errors.append("suggested evidence question must describe testing, not a deck action")
    check("next evidence step is the preregistered simulation question without a card action", errors, checks)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
