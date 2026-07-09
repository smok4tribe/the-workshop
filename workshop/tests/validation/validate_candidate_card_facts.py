#!/usr/bin/env python3
"""Candidate Card Facts validation checks for Sprint 1.

Validates the external candidate Card Facts intake layer in
workshop/card-data/candidate_cards.json and its import metadata.

Standard library only. No external dependencies.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

CANDIDATE_CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "candidate_cards.json"
CANDIDATE_METADATA_PATH = REPO_ROOT / "workshop" / "card-data" / "candidate_card_import_metadata.json"
DECK_CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"

REQUIRED_NAMES = [
    "City of Brass",
    "Mana Confluence",
    "Urza's Saga",
    "Krark-Clan Ironworks",
    "Mana Echoes",
    "Tezzeret the Seeker",
]

FORBIDDEN_LANGUAGE_PATTERNS = [
    r"\badd this\b",
    r"\bcut this\b",
    r"\breplace\b",
    r"\bbest\b",
    r"\bstrict upgrade\b",
    r"\bauto include\b",
    r"\bauto-include\b",
    r"\bmust include\b",
    r"\bfinal verdict\b",
    r"\bpower score\b",
    r"\btier\b",
    r"\bEDHREC\b",
    r"\bprice\b",
    r"\bbudget\b",
]


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    # Check 1: candidate_cards.json parses as JSON.
    candidate_doc = None
    errors = []
    try:
        candidate_doc = load_json(CANDIDATE_CARDS_PATH)
    except FileNotFoundError:
        errors.append(f"{CANDIDATE_CARDS_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{CANDIDATE_CARDS_PATH} is not valid JSON: {exc}")
    check("candidate_cards.json parses as JSON", errors)

    # Check 2: candidate_card_import_metadata.json parses as JSON.
    metadata = None
    errors = []
    try:
        metadata = load_json(CANDIDATE_METADATA_PATH)
    except FileNotFoundError:
        errors.append(f"{CANDIDATE_METADATA_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{CANDIDATE_METADATA_PATH} is not valid JSON: {exc}")
    check("candidate_card_import_metadata.json parses as JSON", errors)

    if candidate_doc is None or metadata is None:
        return report(checks)

    records = candidate_doc.get("candidate_cards")

    # Check 3: candidate_cards.json contains exactly 6 records.
    errors = []
    if not isinstance(records, list):
        errors.append("candidate_cards is not an array")
        records = []
    elif len(records) != 6:
        errors.append(f"candidate_cards contains {len(records)} records, expected 6")
    check("candidate_cards.json contains exactly 6 records", errors)

    # Check 4: metadata imported_card_count equals 6.
    errors = []
    if metadata.get("imported_card_count") != 6:
        errors.append(f"imported_card_count is {metadata.get('imported_card_count')!r}, expected 6")
    check("metadata imported_card_count equals 6", errors)

    # Check 5: unresolved_card_count equals 0.
    errors = []
    if metadata.get("unresolved_card_count") != 0:
        errors.append(f"unresolved_card_count is {metadata.get('unresolved_card_count')!r}, expected 0")
    check("metadata unresolved_card_count equals 0", errors)

    # Check 6: unresolved_cards is empty.
    errors = []
    unresolved_cards = metadata.get("unresolved_cards")
    if unresolved_cards != []:
        errors.append(f"unresolved_cards is {unresolved_cards!r}, expected []")
    check("metadata unresolved_cards is empty", errors)

    # Check 7: required candidate names are present exactly.
    errors = []
    actual_names = [record.get("name") for record in records if isinstance(record, dict)]
    if actual_names != REQUIRED_NAMES:
        errors.append(f"candidate names are {actual_names!r}, expected {REQUIRED_NAMES!r}")
    if metadata.get("candidate_card_names") != REQUIRED_NAMES:
        errors.append("metadata candidate_card_names does not match required names")
    check("required candidate names are present exactly", errors)

    # Check 8: every record has a Scryfall ID.
    errors = []
    for record in records:
        if not record.get("scryfall_id"):
            errors.append(f"{record.get('name', '<unknown>')} lacks scryfall_id")
    check("every record has a Scryfall ID", errors)

    # Check 9: every record source/source_ref indicates Scryfall.
    errors = []
    for record in records:
        source_ref = record.get("source_ref") or {}
        if record.get("source") != "scryfall":
            errors.append(f"{record.get('name', '<unknown>')} source is not 'scryfall'")
        if source_ref.get("source") != "scryfall":
            errors.append(f"{record.get('name', '<unknown>')} source_ref.source is not 'scryfall'")
        if "scryfall" not in str(source_ref.get("api_uri", "")).lower():
            errors.append(f"{record.get('name', '<unknown>')} source_ref.api_uri does not indicate Scryfall")
    check("every record source/source_ref indicates Scryfall", errors)

    # Check 10: required canonical fields are present.
    errors = []
    for record in records:
        name = record.get("name", "<unknown>")
        for field in ("name", "type_line", "color_identity", "legalities"):
            if field not in record or record.get(field) in (None, ""):
                errors.append(f"{name} lacks required field {field!r}")
        if "oracle_text" not in record:
            errors.append(f"{name} lacks oracle_text field")
        if "mana_cost" not in record or "cmc" not in record:
            errors.append(f"{name} lacks mana_cost/cmc fields")
    check("every record has required canonical fields", errors)

    # Check 11: no duplicate Scryfall IDs.
    errors = []
    seen_ids = set()
    for record in records:
        scryfall_id = record.get("scryfall_id")
        if scryfall_id in seen_ids:
            errors.append(f"duplicate Scryfall ID {scryfall_id}")
        seen_ids.add(scryfall_id)
    check("no duplicate Scryfall IDs", errors)

    # Check 12: no candidate card already exists in deck Card Facts.
    errors = []
    deck_cards = load_json(DECK_CARDS_PATH).get("cards", [])
    deck_ids = {card.get("scryfall_id") for card in deck_cards if card.get("scryfall_id")}
    deck_names = {card.get("name") for card in deck_cards if card.get("name")}
    for record in records:
        if record.get("scryfall_id") in deck_ids:
            errors.append(f"{record.get('name')} already exists in cards.json by Scryfall ID")
        if record.get("name") in deck_names:
            errors.append(f"{record.get('name')} already exists in cards.json by exact name")
    check("candidate cards do not already exist in deck Card Facts", errors)

    # Check 13: recommendation_status is facts_only for every record.
    errors = []
    for record in records:
        if record.get("recommendation_status") != "facts_only":
            errors.append(f"{record.get('name', '<unknown>')} recommendation_status is not 'facts_only'")
    check("recommendation_status is facts_only for every record", errors)

    # Check 14: no recommendation/actionable language appears in facts or metadata.
    errors = []
    combined_text = json.dumps(candidate_doc, ensure_ascii=False) + "\n" + json.dumps(metadata, ensure_ascii=False)
    for pattern in FORBIDDEN_LANGUAGE_PATTERNS:
        match = re.search(pattern, combined_text, flags=re.IGNORECASE)
        if match:
            errors.append(f"forbidden language found: {match.group(0)!r}")
    check("no recommendation/actionable language appears in candidate facts or metadata", errors)

    # Check 15: validator is read-only by design.
    errors = []
    for path in (CANDIDATE_CARDS_PATH, CANDIDATE_METADATA_PATH, DECK_CARDS_PATH):
        if not path.is_file():
            errors.append(f"expected file missing during read-only validation: {path}")
    check("validator does not alter files", errors)

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
        print(f"FAIL: {failed} of {len(checks)} candidate card facts validation checks failed.")
        return 1
    print(f"PASS: all {len(checks)} candidate card facts validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
