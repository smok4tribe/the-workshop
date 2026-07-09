#!/usr/bin/env python3
"""Recommendation Candidate Schema validation checks for Sprint 1.

Validates recommendation candidate data in
workshop/projects/the-myr-singularity/recommendations/rec-001.json and its
companion rec-001.md.

The validator supports two modes:

* schema-only mode:
  recommendation_type == "candidate_schema", status == "schema_only",
  and candidates is empty.
* candidate-set mode:
  recommendation_type == "candidate_set", status == "candidates_proposed",
  and candidates contains proposed, non-actionable records.

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
ROLES_PATH = REPO_ROOT / "workshop" / "knowledge" / "role_taxonomy.json"
PROJECT_PATH = PROJECT_DIR / "project.json"
BRIEF_PATH = PROJECT_DIR / "brief" / "brief.json"

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

DECK_ALTERING_TYPES = {
    "add_candidate",
    "cut_candidate",
    "swap_candidate",
    "package_candidate",
    "mana_base_adjustment_candidate",
}

FORBIDDEN_CANDIDATE_LANGUAGE_PATTERNS = [
    r"\bbudget\b",
    r"\bprice\b",
    r"\bedhrec\b",
    r"\bpopularity\b",
    r"\bfinal verdict\b",
    r"\bpower score\b",
    r"\bpower level\b",
    r"\btier\b",
    r"\branking\b",
    r"\byou (should|must) (add|cut|swap|remove|replace|upgrade)\b",
    r"\bwe (should|must) (add|cut|swap|remove|replace|upgrade)\b",
    r"\bimmediately (add|cut|swap|remove|replace|upgrade)\b",
]


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_real_card_names():
    names = set()
    for card in load_json(CARDS_PATH).get("cards", []):
        for key in ("name", "original_decklist_name", "display_name"):
            value = card.get(key)
            if value:
                names.add(value)
    return names


def find_real_card_names(text, names):
    return sorted(name for name in names if name in text)


def allowed_values(schema, group, field):
    return ((schema.get(group) or {}).get(field) or {}).get("allowed_values") or []


def candidate_text(candidate):
    return json.dumps(candidate, ensure_ascii=False)


def resolve_analysis(doc):
    generated_from = doc.get("generated_from") or {}
    rel_path = generated_from.get("baseline_analysis")
    if not rel_path:
        return None
    path = REPO_ROOT / rel_path
    if not path.is_file():
        return None
    return load_json(path)


def load_reference_sets():
    cards = load_json(CARDS_PATH).get("cards", [])
    scryfall_ids = {card.get("scryfall_id") for card in cards if card.get("scryfall_id")}

    taxonomy = load_json(ROLES_PATH)
    role_ids = {role.get("role_id") for role in taxonomy.get("roles", []) if role.get("role_id")}
    category_ids = {
        category.get("category_id")
        for category in taxonomy.get("categories", [])
        if category.get("category_id")
    }

    goals = set(load_json(PROJECT_PATH).get("goals", []))
    brief = load_json(BRIEF_PATH)
    goals.update(brief.get("improvement_areas", []))

    return {
        "scryfall_ids": scryfall_ids,
        "role_ids": role_ids,
        "category_ids": category_ids,
        "goals": goals,
    }


def check_candidate_required_fields(candidate, index):
    label = f"candidates[{index}]"
    required_fields = [
        "candidate_id",
        "candidate_type",
        "status",
        "source_analysis_id",
        "source_pressure_point_ids",
        "related_project_goals",
        "evidence_summary",
        "evidence_items",
        "confidence",
        "proposed_change",
        "affected_cards",
        "expected_impact",
        "tradeoffs",
        "risks",
        "constraints_checked",
        "is_actionable",
        "requires_user_decision",
        "requires_testing",
        "creates_new_deck_version",
        "decision_log_required",
    ]
    return [f"{label} missing required field {field!r}" for field in required_fields if field not in candidate]


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    # Check 1: rec-001.json parses as JSON.
    errors = []
    doc = None
    try:
        doc = load_json(REC_JSON_PATH)
    except FileNotFoundError:
        errors.append(f"{REC_JSON_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{REC_JSON_PATH} is not valid JSON: {exc}")
    check("rec-001.json parses as JSON", errors)
    if doc is None:
        return report(checks)

    # Check 2: required top-level fields.
    errors = [f"missing top-level field {field!r}" for field in REQUIRED_TOP_LEVEL_FIELDS if field not in doc]
    check("required top-level fields exist", errors)

    recommendation_type = doc.get("recommendation_type")
    status = doc.get("status")
    candidates = doc.get("candidates")

    # Check 3: recommendation_type is a supported mode.
    errors = []
    if recommendation_type not in {"candidate_schema", "candidate_set"}:
        errors.append(f"unsupported recommendation_type {recommendation_type!r}")
    check("recommendation_type is a supported mode", errors)

    # Check 4: status is a supported mode.
    errors = []
    if status not in {"schema_only", "candidates_proposed"}:
        errors.append(f"unsupported status {status!r}")
    check("status is a supported mode", errors)

    # Check 5: recommendation_type/status/candidates cardinality are consistent.
    errors = []
    if not isinstance(candidates, list):
        errors.append("candidates is not an array")
    elif recommendation_type == "candidate_schema":
        if status != "schema_only":
            errors.append("candidate_schema mode must use status 'schema_only'")
        if candidates:
            errors.append(f"schema_only mode must have zero candidates, found {len(candidates)}")
    elif recommendation_type == "candidate_set":
        if status != "candidates_proposed":
            errors.append("candidate_set mode must use status 'candidates_proposed'")
        if not candidates:
            errors.append("candidate_set mode must contain at least one candidate")
    check("mode pairing and candidate cardinality are valid", errors)

    # Check 6: generated_from references existing files.
    errors = []
    generated_from = doc.get("generated_from") or {}
    for key in REQUIRED_GENERATED_FROM_KEYS:
        rel_path = generated_from.get(key)
        if not rel_path:
            errors.append(f"generated_from missing key {key!r}")
        elif not (REPO_ROOT / rel_path).is_file():
            errors.append(f"generated_from[{key!r}] references missing file {rel_path!r}")
    check("generated_from references expected existing files", errors)

    schema = doc.get("candidate_schema") or {}

    # Check 7: required field groups.
    errors = [f"candidate_schema missing group {group!r}" for group in REQUIRED_FIELD_GROUPS if group not in schema]
    check("candidate_schema contains the required field groups", errors)

    # Check 8: candidate_type allowed values.
    got = allowed_values(schema, "identity_fields", "candidate_type")
    errors = [f"candidate_type allowed_values missing {value!r}" for value in REQUIRED_CANDIDATE_TYPES if value not in got]
    check("candidate_type allowed values include all required types", errors)

    # Check 9: status allowed values.
    got = allowed_values(schema, "identity_fields", "status")
    errors = [f"status allowed_values missing {value!r}" for value in REQUIRED_STATUS_VALUES if value not in got]
    check("status allowed values include all required statuses", errors)

    # Check 10: evidence_type allowed values.
    evidence_items = (schema.get("evidence_fields") or {}).get("evidence_items") or {}
    got = ((evidence_items.get("item_fields") or {}).get("evidence_type") or {}).get("allowed_values") or []
    errors = [f"evidence_type allowed_values missing {value!r}" for value in REQUIRED_EVIDENCE_TYPES if value not in got]
    check("evidence_type allowed values include all required types", errors)

    # Check 11: confidence allowed values.
    got = allowed_values(schema, "evidence_fields", "confidence")
    errors = [f"confidence allowed_values missing {value!r}" for value in REQUIRED_CONFIDENCE_VALUES if value not in got]
    check("confidence allowed values include low, medium, high", errors)

    lifecycle = doc.get("candidate_lifecycle") or {}
    transitions = lifecycle.get("transitions") or []
    rules_text = " ".join(lifecycle.get("rules") or []).lower()

    # Check 12: terminal accepted/rejected states.
    errors = []
    for terminal in ("accepted", "rejected"):
        entry = next((item for item in transitions if isinstance(item, dict) and item.get("from") == terminal), None)
        if entry is None:
            errors.append(f"candidate_lifecycle has no transition entry for {terminal!r}")
        elif entry.get("to"):
            errors.append(f"{terminal!r} must be terminal but transitions to {entry.get('to')!r}")
    check("candidate_lifecycle includes terminal accepted/rejected states", errors)

    # Check 13: accepted/rejected require user_decision and decision_id.
    errors = []
    if not (
        re.search(r"accepted.*rejected|rejected.*accepted", rules_text)
        and "user_decision" in rules_text
        and "decision_id" in rules_text
    ):
        errors.append("lifecycle rules do not state that accepted/rejected require user_decision and decision_id")
    check("lifecycle rules require user_decision and decision_id for terminal states", errors)

    # Check 14: acceptance does not change the deck by itself.
    errors = []
    if not re.search(r"accepted.*does not change the deck by itself", rules_text):
        errors.append("lifecycle rules do not state that acceptance does not change the deck by itself")
    check("lifecycle rules state acceptance does not change the deck by itself", errors)

    # Check 15: boundary states no deck change is authorized.
    errors = []
    boundary_text = json.dumps(doc.get("explicit_no_recommendations_boundary") or {}, ensure_ascii=False).lower()
    if "no deck change is authorized" not in boundary_text:
        errors.append("explicit_no_recommendations_boundary does not state that no deck change is authorized")
    check("explicit boundary states no deck change is authorized", errors)

    candidates = candidates if isinstance(candidates, list) else []

    # Check 16: candidate IDs are unique and required fields are present.
    errors = []
    seen_ids = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            errors.append(f"candidates[{index}] is not an object")
            continue
        errors.extend(check_candidate_required_fields(candidate, index))
        candidate_id = candidate.get("candidate_id")
        if not re.fullmatch(r"cand-\d{3}", str(candidate_id)):
            errors.append(f"candidates[{index}] has invalid candidate_id {candidate_id!r}")
        if candidate_id in seen_ids:
            errors.append(f"duplicate candidate_id {candidate_id!r}")
        seen_ids.add(candidate_id)
        if candidate.get("candidate_type") not in REQUIRED_CANDIDATE_TYPES:
            errors.append(f"{candidate_id} has invalid candidate_type {candidate.get('candidate_type')!r}")
        if candidate.get("status") not in REQUIRED_STATUS_VALUES:
            errors.append(f"{candidate_id} has invalid status {candidate.get('status')!r}")
        if candidate.get("confidence") not in REQUIRED_CONFIDENCE_VALUES:
            errors.append(f"{candidate_id} has invalid confidence {candidate.get('confidence')!r}")
    check("candidate records have unique IDs and required schema fields", errors)

    # Check 17: candidate-set records are proposed and non-actionable.
    errors = []
    if recommendation_type == "candidate_set":
        for candidate in candidates:
            candidate_id = candidate.get("candidate_id")
            if candidate.get("status") != "proposed":
                errors.append(f"{candidate_id} status is not 'proposed'")
            if candidate.get("is_actionable") is not False:
                errors.append(f"{candidate_id} is_actionable must be false")
            if candidate.get("user_decision") is not None:
                errors.append(f"{candidate_id} user_decision must be null while proposed")
            if candidate.get("decision_id") is not None:
                errors.append(f"{candidate_id} decision_id must be null while proposed")
            if candidate.get("candidate_type") != "knowledge_review_candidate":
                if candidate.get("requires_user_decision") is not True:
                    errors.append(f"{candidate_id} requires_user_decision must be true")
            if candidate.get("candidate_type") in DECK_ALTERING_TYPES:
                if candidate.get("creates_new_deck_version") is not True:
                    errors.append(f"{candidate_id} deck-altering candidate must create a new version if accepted")
                if candidate.get("decision_log_required") is not True:
                    errors.append(f"{candidate_id} deck-altering candidate must require a decision log")
    check("candidate-set records are proposed, non-actionable, and undecided", errors)

    # Check 18: evidence and project goals are present for every candidate.
    errors = []
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        if not candidate.get("source_analysis_id"):
            errors.append(f"{candidate_id} lacks source_analysis_id")
        if not candidate.get("related_project_goals"):
            errors.append(f"{candidate_id} lacks related_project_goals")
        if not candidate.get("evidence_items"):
            errors.append(f"{candidate_id} lacks evidence_items")
        for item_index, item in enumerate(candidate.get("evidence_items") or []):
            if not isinstance(item, dict):
                errors.append(f"{candidate_id} evidence_items[{item_index}] is not an object")
                continue
            if item.get("evidence_type") not in REQUIRED_EVIDENCE_TYPES:
                errors.append(f"{candidate_id} evidence_items[{item_index}] has invalid evidence_type")
            if not item.get("reference"):
                errors.append(f"{candidate_id} evidence_items[{item_index}] lacks reference")
    check("every candidate has analysis, evidence, and project-goal traceability", errors)

    # Check 19: references resolve.
    errors = []
    references = load_reference_sets()
    analysis = resolve_analysis(doc)
    pressure_count = len((analysis or {}).get("structural_pressure_points", []))
    question_count = len((analysis or {}).get("open_questions", []))
    analysis_id = (analysis or {}).get("analysis_id")
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        if analysis_id and candidate.get("source_analysis_id") != analysis_id:
            errors.append(f"{candidate_id} source_analysis_id does not match {analysis_id!r}")
        for ref in candidate.get("source_pressure_point_ids") or []:
            match = re.fullmatch(r"baseline_v1\.0:pressure_point:(\d+)", str(ref))
            if not match or int(match.group(1)) >= pressure_count:
                errors.append(f"{candidate_id} has unresolved pressure point {ref!r}")
        for ref in candidate.get("related_open_question_ids") or []:
            match = re.fullmatch(r"baseline_v1\.0:open_question:(\d+)", str(ref))
            if not match or int(match.group(1)) >= question_count:
                errors.append(f"{candidate_id} has unresolved open question {ref!r}")
        for role_id in candidate.get("related_roles") or []:
            if role_id not in references["role_ids"]:
                errors.append(f"{candidate_id} has unknown role {role_id!r}")
        for category_id in candidate.get("related_categories") or []:
            if category_id not in references["category_ids"]:
                errors.append(f"{candidate_id} has unknown category {category_id!r}")
        for goal in candidate.get("related_project_goals") or []:
            if goal not in references["goals"]:
                errors.append(f"{candidate_id} has unknown project goal {goal!r}")
        for card_ref in candidate.get("affected_cards") or []:
            if not str(card_ref).startswith("scryfall:"):
                errors.append(f"{candidate_id} affected_cards entry is not a Scryfall ref: {card_ref!r}")
                continue
            scryfall_id = str(card_ref).split(":", 1)[1]
            if scryfall_id not in references["scryfall_ids"]:
                errors.append(f"{candidate_id} affected_cards ref not found in cards.json: {card_ref!r}")
    check("candidate references resolve to analysis, goals, cards, roles, and categories", errors)

    # Check 20: candidate text has no forbidden evaluative or external-data language.
    errors = []
    for candidate in candidates:
        text = candidate_text(candidate)
        for pattern in FORBIDDEN_CANDIDATE_LANGUAGE_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                errors.append(f"{candidate.get('candidate_id')} contains forbidden language {match.group(0)!r}")
    check("candidate text avoids forbidden recommendation language", errors)

    # Check 21: rec-001.md reflects the current mode.
    errors = []
    if not REC_MD_PATH.is_file():
        errors.append(f"{REC_MD_PATH} not found")
        rec_md_text = ""
    else:
        rec_md_text = REC_MD_PATH.read_text(encoding="utf-8")
    md_lower = rec_md_text.lower()
    if recommendation_type == "candidate_schema":
        real_name_hits = find_real_card_names(rec_md_text + REC_JSON_PATH.read_text(encoding="utf-8"), load_real_card_names())
        if real_name_hits:
            errors.append(f"real card names appear in schema-only mode: {real_name_hits}")
        for pattern in [
            r"schema[- ]only|schema only",
            r"not a recommendation",
            r"zero candidates|candidates.*empty",
            r"no deck changes? (is|are) authorized|authorizes no deck change",
        ]:
            if not re.search(pattern, md_lower):
                errors.append(f"rec-001.md missing schema-only boundary pattern {pattern!r}")
    elif recommendation_type == "candidate_set":
        for pattern in [
            r"candidate set",
            r"proposed",
            r"non-actionable|non actionable",
            r"no deck changes? (is|are) authorized|no deck change is authorized",
            r"product owner",
            r"decision log",
            r"new deck version",
        ]:
            if not re.search(pattern, md_lower):
                errors.append(f"rec-001.md missing candidate-set boundary pattern {pattern!r}")
    check("rec-001.md reflects the active recommendation mode", errors)

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
