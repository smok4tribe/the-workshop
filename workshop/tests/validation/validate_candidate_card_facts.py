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


def promoted_record_mapping(records, label):
    mapping = {}
    errors = []
    if not isinstance(records, list):
        return mapping, [f"{label} must be an array"]
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        scryfall_id = record.get("scryfall_id")
        card_name = record.get("card_name")
        if not isinstance(scryfall_id, str) or not scryfall_id:
            errors.append(f"{label}[{index}] is missing scryfall_id")
            continue
        if not isinstance(card_name, str) or not card_name:
            errors.append(f"{label}[{index}] is missing card_name")
            continue
        if record.get("status") != "promoted":
            errors.append(f"{label}[{index}] status must be 'promoted'")
        if scryfall_id in mapping:
            errors.append(f"duplicate promoted Scryfall ID {scryfall_id!r}")
            continue
        if card_name in mapping.values():
            errors.append(f"duplicate promoted card name {card_name!r}")
            continue
        mapping[scryfall_id] = card_name
    return mapping, errors


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

    # Check 3: active candidate count matches lifecycle metadata.
    errors = []
    active_count = metadata.get("active_candidate_card_count")
    if not isinstance(records, list):
        errors.append("candidate_cards is not an array")
        records = []
    if not isinstance(active_count, int) or isinstance(active_count, bool):
        errors.append("active_candidate_card_count must be an integer")
    elif len(records) != active_count:
        errors.append(f"candidate_cards contains {len(records)} records, expected {active_count}")
    check("candidate_cards.json count matches active candidate lifecycle metadata", errors)

    # Check 4: initial intake count matches the stable manifest.
    errors = []
    intake_ids = metadata.get("candidate_intake_scryfall_ids")
    if not isinstance(intake_ids, list) or not all(isinstance(value, str) and value for value in intake_ids):
        errors.append("candidate_intake_scryfall_ids must be an array of non-empty strings")
        intake_ids = []
    elif len(intake_ids) != len(set(intake_ids)):
        errors.append("candidate_intake_scryfall_ids contains duplicate Scryfall IDs")
    if metadata.get("imported_card_count") != len(intake_ids):
        errors.append(
            f"imported_card_count is {metadata.get('imported_card_count')!r}, "
            f"expected {len(intake_ids)} from candidate_intake_scryfall_ids"
        )
    check("metadata imported_card_count matches the stable intake manifest", errors)

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

    # Check 7: active candidate records expose unique name-to-ID identities.
    errors = []
    active_names = []
    for index, record in enumerate(records):
        name = record.get("name") if isinstance(record, dict) else None
        if not name:
            errors.append(f"candidate_cards[{index}] is missing name")
            continue
        if name in active_names:
            errors.append(f"duplicate active candidate card name {name!r}")
        active_names.append(name)
    check("active candidate records expose unique names", errors)

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

    # Check 12: active and promoted identities partition the stable intake manifest.
    errors = []
    active_ids = {record.get("scryfall_id") for record in records if record.get("scryfall_id")}
    promoted_records = metadata.get("promoted_candidate_records")
    promoted_by_id, mapping_errors = promoted_record_mapping(
        promoted_records, "promoted_candidate_records"
    )
    errors.extend(mapping_errors)
    promoted_ids = set(promoted_by_id)
    if metadata.get("promoted_candidate_card_count") != len(promoted_records or []):
        errors.append("promoted_candidate_card_count does not match promoted_candidate_records")
    if active_ids & promoted_ids:
        errors.append("active and promoted candidate identities overlap")
    if active_ids | promoted_ids != set(intake_ids):
        errors.append("active and promoted candidate identities do not partition the intake manifest")
    check("candidate intake manifest preserves active and promoted identity mappings", errors)

    # Check 13: promoted metadata maps exactly to canonical Card Facts.
    errors = []
    deck_cards = load_json(DECK_CARDS_PATH).get("cards", [])
    deck_cards_by_id = {
        card.get("scryfall_id"): card for card in deck_cards if card.get("scryfall_id")
    }
    deck_ids = set(deck_cards_by_id)
    deck_names = {card.get("name") for card in deck_cards if card.get("name")}
    missing_promoted_ids = sorted(promoted_ids - deck_ids)
    if missing_promoted_ids:
        errors.append(f"promoted candidate IDs are missing from cards.json: {missing_promoted_ids}")
    for scryfall_id, card_name in promoted_by_id.items():
        canonical = deck_cards_by_id.get(scryfall_id)
        if canonical and canonical.get("name") != card_name:
            errors.append(
                "promoted candidate metadata name does not match canonical Card Facts "
                f"for Scryfall ID {scryfall_id!r}"
            )
    check("promoted candidate metadata maps exactly to canonical Card Facts", errors)

    # Check 14: no active candidate card already exists in deck Card Facts.
    errors = []
    for record in records:
        if record.get("scryfall_id") in deck_ids:
            errors.append(f"{record.get('name')} already exists in cards.json by Scryfall ID")
        if record.get("name") in deck_names:
            errors.append(f"{record.get('name')} already exists in cards.json by exact name")
    check("active candidate cards do not already exist in canonical Card Facts", errors)

    # Check 15: recommendation_status is facts_only for every active record.
    errors = []
    for record in records:
        if record.get("recommendation_status") != "facts_only":
            errors.append(f"{record.get('name', '<unknown>')} recommendation_status is not 'facts_only'")
    check("recommendation_status is facts_only for every record", errors)

    # Check 16: no recommendation/actionable language appears in facts or metadata.
    errors = []
    combined_text = json.dumps(candidate_doc, ensure_ascii=False) + "\n" + json.dumps(metadata, ensure_ascii=False)
    for pattern in FORBIDDEN_LANGUAGE_PATTERNS:
        match = re.search(pattern, combined_text, flags=re.IGNORECASE)
        if match:
            errors.append(f"forbidden language found: {match.group(0)!r}")
    check("no recommendation/actionable language appears in candidate facts or metadata", errors)

    # Check 17: validator is read-only by design.
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
