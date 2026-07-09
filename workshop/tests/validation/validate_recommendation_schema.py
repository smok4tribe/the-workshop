#!/usr/bin/env python3
"""Recommendation Candidate Schema validation checks for Sprint 1.

Validates the recommendation candidate schema in
workshop/projects/the-myr-singularity/recommendations/rec-001.json and its
companion rec-001.md, in their current schema-only state.

This validator confirms schema structure and boundaries only. It does not
generate recommendations, evaluate cards, or alter deck files. Words like
add/cut/swap are allowed in schema field descriptions and boundary
statements; the validator fails only if actual candidate entries exist
while the set is schema-only, or if recommendation files contain actionable
recommendation content rather than schema documentation.

Run from the repository root:

    python workshop/tests/validation/validate_recommendation_schema.py

Exits 0 with a PASS summary when all checks pass.
Exits 1 with per-check failure messages when any check fails.

Standard library only. No external dependencies.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
REC_JSON_PATH = PROJECT_DIR / "recommendations" / "rec-001.json"
REC_MD_PATH = PROJECT_DIR / "recommendations" / "rec-001.md"
CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"

REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "project_id",
    "deck_version_id",
    "recommendation_set_id",
    "recommendation_type",
    "status",
    "generated_from",
    "scope",
    "explicit_no_recommendations_boundary",
    "reference_conventions",
    "candidate_schema",
    "candidate_lifecycle",
    "validation_expectations",
    "candidates",
]

REQUIRED_GENERATED_FROM_KEYS = [
    "baseline_analysis",
    "brief",
    "deck_version",
    "card_facts",
    "functional_roles",
    "role_taxonomy",
]

REQUIRED_FIELD_GROUPS = [
    "identity_fields",
    "traceability_fields",
    "evidence_fields",
    "content_fields",
    "boundary_fields",
    "review_fields",
]

REQUIRED_CANDIDATE_TYPES = [
    "add_candidate",
    "cut_candidate",
    "swap_candidate",
    "package_candidate",
    "mana_base_adjustment_candidate",
    "role_coverage_candidate",
    "knowledge_review_candidate",
]

REQUIRED_STATUS_VALUES = [
    "proposed",
    "under_review",
    "accepted",
    "rejected",
    "deferred",
    "needs_testing",
]

REQUIRED_EVIDENCE_TYPES = [
    "baseline_analysis",
    "card_facts",
    "functional_roles",
    "project_brief",
    "playtest_note",
    "simulation_result",
    "user_preference",
]

REQUIRED_CONFIDENCE_VALUES = ["low", "medium", "high"]

# Actionable-language patterns for check 18. Schema vocabulary such as
# "add_candidate", "cut_candidate", or descriptions of what candidates MAY
# describe is allowed; these patterns target direct instructions to change
# the deck now.
ACTIONABLE_LANGUAGE_PATTERNS = [
    r"\byou (should|must) (add|cut|swap|remove|replace)\b",
    r"\bwe (should|must) (add|cut|swap|remove|replace)\b",
    r"\bimmediately (add|cut|swap|remove|replace)\b",
    r"\bfinal verdict\b",
    r"\bauto.?include\b",
    r"\bpower level\b",
    r"\bpower score\b",
    r"\btier list\b",
]


def load_real_card_names():
    """All canonical and decklist card names from Card Facts."""
    names = set()
    cards = json.load(open(CARDS_PATH, encoding="utf-8")).get("cards", [])
    for card in cards:
        for key in ("name", "original_decklist_name", "display_name"):
            value = card.get(key)
            if value:
                names.add(value)
    return names


def find_real_card_names(text, names):
    return sorted(n for n in names if n in text)


def validate_candidate(candidate, index, context):
    """Helper for future candidate validation.

    Validates a single candidate record against the field contract. Not
    exercised in the schema-only state (candidates is empty); kept here so
    the future task that populates candidates can extend this validator
    without redesigning it. `context` carries allowed-value sets and real
    card names.
    """
    errors = []
    label = f"candidates[{index}]"
    if not isinstance(candidate, dict):
        return [f"{label} is not an object"]

    required_fields = [
        "candidate_id", "candidate_type", "status",
        "source_analysis_id", "source_pressure_point_ids",
        "related_project_goals",
        "evidence_summary", "evidence_items", "confidence",
        "proposed_change", "affected_cards", "expected_impact",
        "tradeoffs", "risks", "constraints_checked",
        "is_actionable", "requires_user_decision", "requires_testing",
        "creates_new_deck_version", "decision_log_required",
    ]
    for field in required_fields:
        if field not in candidate:
            errors.append(f"{label} missing required field {field!r}")

    if candidate.get("candidate_type") not in context["candidate_types"]:
        errors.append(f"{label} has invalid candidate_type {candidate.get('candidate_type')!r}")
    if candidate.get("status") not in context["status_values"]:
        errors.append(f"{label} has invalid status {candidate.get('status')!r}")
    if candidate.get("confidence") not in context["confidence_values"]:
        errors.append(f"{label} has invalid confidence {candidate.get('confidence')!r}")
    for i, item in enumerate(candidate.get("evidence_items") or []):
        if not isinstance(item, dict) or item.get("evidence_type") not in context["evidence_types"]:
            errors.append(f"{label} evidence_items[{i}] has invalid evidence_type")
    if candidate.get("status") in ("accepted", "rejected"):
        if not candidate.get("user_decision") or not candidate.get("decision_id"):
            errors.append(f"{label} is terminal but lacks user_decision/decision_id")
    if candidate.get("is_actionable") and not candidate.get("decision_id"):
        errors.append(f"{label} is_actionable without a recorded decision_id")
    return errors


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    # Check 1: rec-001.json parses as JSON.
    errors = []
    doc = None
    try:
        doc = json.load(open(REC_JSON_PATH, encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{REC_JSON_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{REC_JSON_PATH} is not valid JSON: {exc}")
    check("rec-001.json parses as JSON", errors)
    if doc is None:
        return report(checks)

    # Check 2: required top-level fields.
    errors = [f"missing top-level field {f!r}" for f in REQUIRED_TOP_LEVEL_FIELDS if f not in doc]
    check("required top-level fields exist", errors)

    # Check 3: recommendation_type.
    errors = []
    if doc.get("recommendation_type") != "candidate_schema":
        errors.append(f"recommendation_type is {doc.get('recommendation_type')!r}, expected 'candidate_schema'")
    check("recommendation_type equals 'candidate_schema'", errors)

    # Check 4: status.
    errors = []
    if doc.get("status") != "schema_only":
        errors.append(f"status is {doc.get('status')!r}, expected 'schema_only'")
    check("status equals 'schema_only'", errors)

    # Check 5: candidates empty while schema_only.
    errors = []
    candidates = doc.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates is not an array")
    elif doc.get("status") == "schema_only" and candidates:
        errors.append(f"candidates must be empty while status is 'schema_only', found {len(candidates)}")
    check("candidates is an empty array while status is 'schema_only'", errors)

    # Check 6: generated_from references existing files.
    errors = []
    generated_from = doc.get("generated_from") or {}
    for key in REQUIRED_GENERATED_FROM_KEYS:
        rel = generated_from.get(key)
        if not rel:
            errors.append(f"generated_from missing key {key!r}")
        elif not (REPO_ROOT / rel).is_file():
            errors.append(f"generated_from[{key!r}] references missing file {rel!r}")
    check("generated_from references expected existing files", errors)

    schema = doc.get("candidate_schema") or {}

    # Check 7: required field groups.
    errors = [f"candidate_schema missing group {g!r}" for g in REQUIRED_FIELD_GROUPS if g not in schema]
    check("candidate_schema contains the required field groups", errors)

    def allowed_values(group, field):
        return ((schema.get(group) or {}).get(field) or {}).get("allowed_values") or []

    # Check 8: candidate_type allowed values.
    got = allowed_values("identity_fields", "candidate_type")
    errors = [f"candidate_type allowed_values missing {v!r}" for v in REQUIRED_CANDIDATE_TYPES if v not in got]
    check("candidate_type allowed values include all required types", errors)

    # Check 9: status allowed values.
    got = allowed_values("identity_fields", "status")
    errors = [f"status allowed_values missing {v!r}" for v in REQUIRED_STATUS_VALUES if v not in got]
    check("status allowed values include all required statuses", errors)

    # Check 10: evidence_type allowed values.
    evidence_items = (schema.get("evidence_fields") or {}).get("evidence_items") or {}
    got = ((evidence_items.get("item_fields") or {}).get("evidence_type") or {}).get("allowed_values") or []
    errors = [f"evidence_type allowed_values missing {v!r}" for v in REQUIRED_EVIDENCE_TYPES if v not in got]
    check("evidence_type allowed values include all required types", errors)

    # Check 11: confidence allowed values.
    got = allowed_values("evidence_fields", "confidence")
    errors = [f"confidence allowed_values missing {v!r}" for v in REQUIRED_CONFIDENCE_VALUES if v not in got]
    check("confidence allowed values include low, medium, high", errors)

    lifecycle = doc.get("candidate_lifecycle") or {}
    transitions = lifecycle.get("transitions") or []
    rules_text = " ".join(lifecycle.get("rules") or []).lower()

    # Check 12: terminal accepted/rejected states.
    errors = []
    for terminal in ("accepted", "rejected"):
        entry = next((t for t in transitions if isinstance(t, dict) and t.get("from") == terminal), None)
        if entry is None:
            errors.append(f"candidate_lifecycle has no transition entry for {terminal!r}")
        elif entry.get("to"):
            errors.append(f"{terminal!r} must be terminal but transitions to {entry.get('to')!r}")
    check("candidate_lifecycle includes terminal accepted/rejected states", errors)

    # Check 13: accepted/rejected require user_decision and decision_id.
    errors = []
    if not (re.search(r"accepted.*rejected|rejected.*accepted", rules_text)
            and "user_decision" in rules_text and "decision_id" in rules_text):
        errors.append("lifecycle rules do not state that accepted/rejected require user_decision and decision_id")
    check("lifecycle rules require user_decision and decision_id for terminal states", errors)

    # Check 14: acceptance does not change the deck by itself.
    errors = []
    if not re.search(r"accepted.*does not change the deck by itself", rules_text):
        errors.append("lifecycle rules do not state that acceptance does not change the deck by itself")
    check("lifecycle rules state acceptance does not change the deck by itself", errors)

    # Check 15: boundary states no deck change is authorized.
    errors = []
    boundary = doc.get("explicit_no_recommendations_boundary") or {}
    boundary_text = json.dumps(boundary).lower()
    if "no deck change is authorized" not in boundary_text:
        errors.append("explicit_no_recommendations_boundary does not state that no deck change is authorized")
    check("explicit_no_recommendations_boundary states no deck change is authorized", errors)

    # Check 16: no real recommendation candidate exists.
    errors = []
    if isinstance(candidates, list) and candidates:
        errors.append(f"{len(candidates)} candidate record(s) exist; expected none in schema-only state")
    check("no real recommendation candidate exists", errors)

    real_names = load_real_card_names()

    # Check 17: no candidate text names real cards as proposed recommendations.
    errors = []
    for i, candidate in enumerate(candidates if isinstance(candidates, list) else []):
        hits = find_real_card_names(json.dumps(candidate), real_names)
        if hits:
            errors.append(f"candidates[{i}] names real cards: {hits}")
    check("no candidate text names real cards as proposed recommendations", errors)

    # Check 18: no actionable deck-change language outside boundary/schema
    # descriptions. In the schema-only state, no real card name may appear
    # anywhere in the recommendation files, and no direct instruction to
    # change the deck may appear. Schema vocabulary (add/cut/swap as field
    # names or descriptions of what future candidates may describe) is
    # allowed by design.
    errors = []
    rec_json_text = REC_JSON_PATH.read_text(encoding="utf-8")
    rec_md_text = REC_MD_PATH.read_text(encoding="utf-8") if REC_MD_PATH.is_file() else ""
    combined = rec_json_text + "\n" + rec_md_text
    if doc.get("status") == "schema_only":
        hits = find_real_card_names(combined, real_names)
        if hits:
            errors.append(f"real card names appear in schema-only recommendation files: {hits}")
    for pattern in ACTIONABLE_LANGUAGE_PATTERNS:
        match = re.search(pattern, combined, flags=re.IGNORECASE)
        if match:
            errors.append(f"actionable/evaluative language found: {match.group(0)!r}")
    check("no actionable deck-change language in recommendation files", errors)

    # Check 19: rec-001.md exists.
    errors = [] if REC_MD_PATH.is_file() else [f"{REC_MD_PATH} not found"]
    check("rec-001.md exists", errors)

    # Check 20: rec-001.md states the schema-only boundaries.
    errors = []
    md_lower = rec_md_text.lower()
    md_requirements = {
        "states it is a schema, not a recommendation": r"is not a recommendation|not a recommendation\b",
        "states the candidates array is empty": r"candidates.*(array|list).*(is|remains?) empty|zero candidates",
        "states no deck change is authorized": r"no deck changes? (is|are) authorized|authorizes no deck change",
    }
    for requirement, pattern in md_requirements.items():
        if not re.search(pattern, md_lower):
            errors.append(f"rec-001.md does not clearly state: {requirement}")
    check("rec-001.md states schema-only / not a recommendation / empty candidates / no deck change", errors)

    # Future candidate records (none today) are validated per-record.
    errors = []
    context = {
        "candidate_types": REQUIRED_CANDIDATE_TYPES,
        "status_values": REQUIRED_STATUS_VALUES,
        "evidence_types": REQUIRED_EVIDENCE_TYPES,
        "confidence_values": REQUIRED_CONFIDENCE_VALUES,
        "real_card_names": real_names,
    }
    for i, candidate in enumerate(candidates if isinstance(candidates, list) else []):
        errors.extend(validate_candidate(candidate, i, context))
    check("all candidate records conform to the candidate schema (vacuous while empty)", errors)

    return report(checks)


def report(checks):
    failed = 0
    for description, errors in checks:
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {description}")
        for error in errors:
            print(f"       - {error}")
        if errors:
            failed += 1

    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} recommendation schema checks failed.")
        return 1
    print(f"PASS: all {len(checks)} recommendation schema validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
