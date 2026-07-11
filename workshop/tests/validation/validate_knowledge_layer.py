#!/usr/bin/env python3
"""Knowledge Layer validation checks for Sprint 1.

Validates consistency between Card Facts (workshop/card-data/cards.json)
and Card Knowledge (workshop/knowledge/role_taxonomy.json and
workshop/knowledge/functional_roles.json).

This validator checks structural and boundary rules only. It does not
perform deck analysis, produce recommendations, or evaluate card quality.

Run from the repository root:

    python workshop/tests/validation/validate_knowledge_layer.py

Exits 0 with a PASS summary when all checks pass.
Exits 1 with per-check failure messages when any check fails.

Standard library only. No external dependencies.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"
CARD_IMPORT_METADATA_PATH = REPO_ROOT / "workshop" / "card-data" / "card_import_metadata.json"
TAXONOMY_PATH = REPO_ROOT / "workshop" / "knowledge" / "role_taxonomy.json"
ASSIGNMENTS_PATH = REPO_ROOT / "workshop" / "knowledge" / "functional_roles.json"

ALLOWED_CONFIDENCE_VALUES = {"low", "medium", "high"}
ALLOWED_SOURCE_TYPES = {"human_curated", "taxonomy_inference", "project_override"}
EXPECTED_CARD_SOURCE = "scryfall"

# Word-boundary patterns chosen to avoid false positives on legitimate
# oracle-text evidence (for example "adds colorless mana" or the card
# name "Urza's Power Plant" must not trip these checks).
RECOMMENDATION_LANGUAGE_PATTERNS = [
    r"\brecommend(s|ed|ation|ations)?\b",
    r"\bcut\b",
    r"\bcuts\b",
    r"\bshould (be )?(add|added|include|included|remove|removed|replace|replaced)\b",
    r"\bconsider (adding|cutting|removing|replacing|including)\b",
    r"\bswap (in|out)\b",
    r"\bupgrade\b",
    r"\bstaple\b",
    r"\bauto.?include\b",
]

ANALYSIS_LANGUAGE_PATTERNS = [
    r"\banalysis\b",
    r"\banalyz(e|es|ed|ing)\b",
    r"\bpower level\b",
    r"\brank(s|ed|ing|ings)?\b",
    r"\bimportance\b",
    r"\bscore(s|d)?\b",
    r"\btier\b",
    r"\bbest\b",
    r"\bworst\b",
    r"\boverpowered\b",
    r"\bunderpowered\b",
]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def assignment_label(assignment, index):
    name = assignment.get("card_name") if isinstance(assignment, dict) else None
    return f"assignment[{index}] ({name})" if name else f"assignment[{index}]"


def assignment_text_fields(assignment):
    """Yield (field_name, text) pairs for evidence and source_note."""
    source_note = assignment.get("source_note")
    if isinstance(source_note, str):
        yield "source_note", source_note
    evidence = assignment.get("evidence")
    if isinstance(evidence, list):
        for i, entry in enumerate(evidence):
            if isinstance(entry, str):
                yield f"evidence[{i}]", entry


def find_language(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def main():
    checks = []  # list of (description, list_of_error_strings)

    def check(description, errors):
        checks.append((description, errors))

    # Checks 1-4: files parse as JSON.
    parsed = {}
    for label, path in (
        ("cards.json", CARDS_PATH),
        ("card_import_metadata.json", CARD_IMPORT_METADATA_PATH),
        ("role_taxonomy.json", TAXONOMY_PATH),
        ("functional_roles.json", ASSIGNMENTS_PATH),
    ):
        errors = []
        try:
            parsed[label] = load_json(path)
        except FileNotFoundError:
            errors.append(f"{path} not found")
        except json.JSONDecodeError as exc:
            errors.append(f"{path} is not valid JSON: {exc}")
        check(f"{label} parses as JSON", errors)

    if any(errors for _, errors in checks):
        return report(checks)

    cards_doc = parsed["cards.json"]
    card_import_metadata = parsed["card_import_metadata.json"]
    taxonomy_doc = parsed["role_taxonomy.json"]
    assignments_doc = parsed["functional_roles.json"]

    cards = cards_doc.get("cards", [])
    assignments = assignments_doc.get("assignments", [])
    taxonomy_role_ids = {
        role.get("role_id") for role in taxonomy_doc.get("roles", [])
    }

    # Check 5: canonical facts count is metadata-driven.
    errors = []
    expected_card_count = card_import_metadata.get("canonical_card_facts_count")
    if not isinstance(expected_card_count, int) or isinstance(expected_card_count, bool):
        errors.append("card_import_metadata.json is missing integer canonical_card_facts_count")
    elif len(cards) != expected_card_count:
        errors.append(f"expected {expected_card_count} card records, found {len(cards)}")
    check("cards.json count matches canonical Card Facts metadata", errors)

    # Check 6: every canonical fact has one assignment record.
    errors = []
    if len(assignments) != len(cards):
        errors.append(f"expected {len(cards)} assignment records, found {len(assignments)}")
    check("functional-role assignment count matches canonical Card Facts", errors)

    card_ids = {card.get("scryfall_id") for card in cards}

    assignment_ids = []
    for assignment in assignments:
        ref = assignment.get("card_source_ref")
        assignment_ids.append(ref.get("id") if isinstance(ref, dict) else None)

    # Check 6: every card has exactly one assignment by Scryfall ID.
    errors = []
    for card in cards:
        card_id = card.get("scryfall_id")
        count = assignment_ids.count(card_id)
        if count != 1:
            errors.append(
                f"card '{card.get('name')}' ({card_id}) has {count} assignments, expected exactly 1"
            )
    check("every cards.json record has exactly one assignment by Scryfall ID", errors)

    # Check 7: no assignments for cards outside cards.json.
    errors = []
    for index, assignment in enumerate(assignments):
        if assignment_ids[index] not in card_ids:
            errors.append(
                f"{assignment_label(assignment, index)} references Scryfall ID "
                f"{assignment_ids[index]!r} not present in cards.json"
            )
    check("no assignments exist for cards outside cards.json", errors)

    # Checks 8-12: role list integrity.
    unknown_role_errors = []
    primary_subset_errors = []
    secondary_subset_errors = []
    overlap_errors = []
    union_errors = []
    for index, assignment in enumerate(assignments):
        label = assignment_label(assignment, index)
        roles = set(assignment.get("roles", []))
        primary = set(assignment.get("primary_roles", []))
        secondary = set(assignment.get("secondary_roles", []))

        unknown = (roles | primary | secondary) - taxonomy_role_ids
        if unknown:
            unknown_role_errors.append(
                f"{label} uses role IDs not in role_taxonomy.json: {sorted(unknown)}"
            )
        if not primary <= roles:
            primary_subset_errors.append(
                f"{label} primary_roles not a subset of roles: {sorted(primary - roles)}"
            )
        if not secondary <= roles:
            secondary_subset_errors.append(
                f"{label} secondary_roles not a subset of roles: {sorted(secondary - roles)}"
            )
        overlap = primary & secondary
        if overlap:
            overlap_errors.append(
                f"{label} primary_roles and secondary_roles overlap: {sorted(overlap)}"
            )
        if roles != (primary | secondary):
            union_errors.append(
                f"{label} roles does not equal union of primary_roles and secondary_roles"
            )
    check("every role ID used exists in role_taxonomy.json", unknown_role_errors)
    check("primary_roles is a subset of roles", primary_subset_errors)
    check("secondary_roles is a subset of roles", secondary_subset_errors)
    check("primary_roles and secondary_roles do not overlap", overlap_errors)
    check("roles equals the union of primary_roles and secondary_roles", union_errors)

    # Check 13: confidence values.
    errors = []
    for index, assignment in enumerate(assignments):
        confidence = assignment.get("confidence")
        if confidence not in ALLOWED_CONFIDENCE_VALUES:
            errors.append(
                f"{assignment_label(assignment, index)} has invalid confidence {confidence!r}"
            )
    check("confidence is one of: low, medium, high", errors)

    # Check 14: source types.
    errors = []
    for index, assignment in enumerate(assignments):
        source_type = assignment.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(
                f"{assignment_label(assignment, index)} has invalid source_type {source_type!r}"
            )
    check(
        "source_type is one of: human_curated, taxonomy_inference, project_override",
        errors,
    )

    # Check 15: card_source_ref.source is scryfall.
    errors = []
    for index, assignment in enumerate(assignments):
        ref = assignment.get("card_source_ref")
        source = ref.get("source") if isinstance(ref, dict) else None
        if source != EXPECTED_CARD_SOURCE:
            errors.append(
                f"{assignment_label(assignment, index)} has card_source_ref.source "
                f"{source!r}, expected {EXPECTED_CARD_SOURCE!r}"
            )
    check("card_source_ref.source is scryfall for all assignments", errors)

    # Check 16: evidence present and non-empty.
    errors = []
    for index, assignment in enumerate(assignments):
        evidence = assignment.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(
                f"{assignment_label(assignment, index)} has missing or empty evidence"
            )
        elif not all(isinstance(e, str) and e.strip() for e in evidence):
            errors.append(
                f"{assignment_label(assignment, index)} has blank or non-string evidence entries"
            )
    check("evidence is present and non-empty for every assignment", errors)

    # Check 17: no recommendation/cut/add language.
    errors = []
    for index, assignment in enumerate(assignments):
        for field, text in assignment_text_fields(assignment):
            found = find_language(RECOMMENDATION_LANGUAGE_PATTERNS, text)
            if found:
                errors.append(
                    f"{assignment_label(assignment, index)} {field} contains "
                    f"recommendation language {found!r}: {text!r}"
                )
    check("no recommendation/cut/add language in evidence or source_note", errors)

    # Check 18: no analysis/power/ranking/importance-score language.
    errors = []
    for index, assignment in enumerate(assignments):
        for field, text in assignment_text_fields(assignment):
            found = find_language(ANALYSIS_LANGUAGE_PATTERNS, text)
            if found:
                errors.append(
                    f"{assignment_label(assignment, index)} {field} contains "
                    f"analysis language {found!r}: {text!r}"
                )
    check(
        "no analysis/power/ranking/importance-score language in evidence or source_note",
        errors,
    )

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
        print(f"FAIL: {failed} of {len(checks)} checks failed.")
        return 1
    print(f"PASS: all {len(checks)} Knowledge Layer validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
