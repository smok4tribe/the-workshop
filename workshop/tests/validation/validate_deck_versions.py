#!/usr/bin/env python3
"""Validate current deck and DeckVersion integrity independently of review."""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ID = os.environ.get("WORKSHOP_PROJECT_ID", "the-myr-singularity")
PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / PROJECT_ID
VERSIONS_DIR = PROJECT_DIR / "versions"
DECISIONS_DIR = PROJECT_DIR / "decisions"
RECOMMENDATIONS_DIR = PROJECT_DIR / "recommendations"
CURRENT_DECK_PATH = PROJECT_DIR / "deck" / "current.txt"
CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"
CANDIDATE_CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "candidate_cards.json"
DECK_ZONES = ("commander", "main_deck", "sideboard")
SLOT_TO_ZONE = {
    "commander": "commander",
    "main": "main_deck",
    "main_deck": "main_deck",
    "land": "main_deck",
    "nonland": "main_deck",
    "sideboard": "sideboard",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_name(value):
    value = unicodedata.normalize("NFKC", str(value))
    return " ".join(value.split()).casefold()


def valid_quantity(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def entries_for(version, section):
    if section == "commander":
        commander = version.get("commander")
        return [commander] if isinstance(commander, dict) else []
    entries = version.get(section)
    return entries if isinstance(entries, list) else []


def section_counter(version, section):
    errors = []
    counter = Counter()
    raw = version.get("commander") if section == "commander" else version.get(section)
    if section == "commander" and not isinstance(raw, dict):
        return counter, ["commander must be an object"]
    if section != "commander" and not isinstance(raw, list):
        return counter, [f"{section} must be an array"]
    for index, entry in enumerate(entries_for(version, section)):
        if not isinstance(entry, dict):
            errors.append(f"{section}[{index}] must be an object")
            continue
        name = entry.get("name")
        quantity = entry.get("quantity")
        if not name:
            errors.append(f"{section}[{index}] is missing name")
            continue
        if not valid_quantity(quantity):
            errors.append(f"{section}[{index}] quantity must be a positive integer")
            continue
        counter[normalize_name(name)] += quantity
    return counter, errors


def parse_current_deck(path):
    headers = {
        "commander": "commander",
        "main deck": "main_deck",
        "sideboard:": "sideboard",
        "sideboard": "sideboard",
    }
    counters = {section: Counter() for section in DECK_ZONES}
    errors = []
    section = None
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        header = headers.get(line.casefold())
        if header:
            section = header
            continue
        match = re.fullmatch(r"(\d+)\s+(.+)", line)
        if not match or not section:
            errors.append(f"current deck line {line_number} is not a valid section entry: {line!r}")
            continue
        quantity = int(match.group(1))
        if quantity <= 0:
            errors.append(f"current deck line {line_number} quantity must be positive")
            continue
        counters[section][normalize_name(match.group(2))] += quantity
    return counters, errors


def facts_index():
    records = load_json(CARDS_PATH).get("cards", [])
    records += load_json(CANDIDATE_CARDS_PATH).get("candidate_cards", [])
    by_name = {}
    errors = []
    for card in records:
        for field in ("name", "original_decklist_name", "display_name", "normalized_name"):
            value = card.get(field)
            if not value:
                continue
            key = normalize_name(value)
            previous = by_name.get(key)
            if previous and previous.get("scryfall_id") != card.get("scryfall_id"):
                errors.append(f"normalized card name {value!r} resolves to multiple Scryfall IDs")
            else:
                by_name[key] = card
    return by_name, errors


def item_counter(items):
    result = Counter()
    errors = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict) or not item.get("name"):
            errors.append(f"change item {index} is missing a card name")
            continue
        quantity = item.get("quantity", 1)
        if not valid_quantity(quantity):
            errors.append(f"change item {item.get('name')!r} has invalid quantity {quantity!r}")
            continue
        result[normalize_name(item["name"])] += quantity
    return result, errors


def design_change_zone(item, direction):
    zone_field = "target_zone" if direction == "incoming" else "source_zone"
    raw_zone = item.get(zone_field, item.get("slot"))
    zone = SLOT_TO_ZONE.get(raw_zone)
    if not zone:
        return None, (
            f"change item {item.get('name')!r} has unsupported {zone_field}/slot "
            f"value {raw_zone!r}"
        )
    return zone, None


def zoned_item_counters(items, direction):
    counters = {zone: Counter() for zone in DECK_ZONES}
    errors = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict) or not item.get("name"):
            errors.append(f"change item {index} is missing a card name")
            continue
        quantity = item.get("quantity", 1)
        if not valid_quantity(quantity):
            errors.append(f"change item {item.get('name')!r} has invalid quantity {quantity!r}")
            continue
        zone, zone_error = design_change_zone(item, direction)
        if zone_error:
            errors.append(zone_error)
            continue
        counters[zone][normalize_name(item["name"])] += quantity
    return counters, errors


def flatten_zone_counters(counters):
    flattened = Counter()
    for counter in counters.values():
        flattened += counter
    return flattened


def report(checks):
    failed = 0
    for description, errors in checks:
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {description}")
        for error in errors:
            print(f"       - {error}")
        failed += bool(errors)
    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} DeckVersion checks failed.")
        return 1
    print(f"PASS: all {len(checks)} DeckVersion validation checks passed.")
    return 0


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    errors = []
    try:
        project = load_json(PROJECT_DIR / "project.json")
    except (OSError, json.JSONDecodeError) as exc:
        project = {}
        errors.append(f"project metadata cannot be loaded: {exc}")
    current_version_id = project.get("current_version_id")
    if not current_version_id:
        errors.append("project metadata is missing current_version_id")
    current_version_path = VERSIONS_DIR / f"{current_version_id}.json" if current_version_id else None
    if current_version_path and not current_version_path.is_file():
        errors.append(f"current_version_id {current_version_id!r} does not resolve")
    check("project current version reference resolves", errors)
    if errors:
        return report(checks)

    try:
        current_version = load_json(current_version_path)
    except json.JSONDecodeError as exc:
        check("resolved current DeckVersion parses", [str(exc)])
        return report(checks)
    errors = []
    if current_version.get("version_id") != current_version_id:
        errors.append("current DeckVersion version_id does not match project.current_version_id")
    if current_version.get("version_status") != "implemented":
        errors.append("current DeckVersion must have version_status 'implemented'")
    check("resolved current DeckVersion identity is coherent", errors)

    parent_id = current_version.get("parent_version_id")
    parent_path = VERSIONS_DIR / f"{parent_id}.json" if parent_id else None
    errors = []
    if not parent_id:
        errors.append("current DeckVersion is missing parent_version_id")
    elif not parent_path.is_file():
        errors.append(f"parent DeckVersion {parent_id!r} does not exist")
    check("parent DeckVersion exists", errors)
    if errors:
        return report(checks)
    parent_version = load_json(parent_path)

    current_counters = {}
    errors = []
    for section in ("commander", "main_deck", "sideboard"):
        current_counters[section], section_errors = section_counter(current_version, section)
        errors.extend(section_errors)
    commander_total = sum(current_counters["commander"].values())
    main_total = sum(current_counters["main_deck"].values())
    if commander_total != 1:
        errors.append(f"commander quantity total is {commander_total}, expected 1")
    if main_total != 99:
        errors.append(f"main-deck quantity total is {main_total}, expected 99")
    if commander_total + main_total != 100:
        errors.append(
            f"Commander deck quantity total is {commander_total + main_total}, expected 100"
        )
    check("Commander and main-deck quantity totals are valid", errors)

    facts_by_name, fact_errors = facts_index()
    errors = list(fact_errors)
    playable = current_counters["commander"] + current_counters["main_deck"]
    commander_names = set(current_counters["commander"])
    duplicated_commander = commander_names & set(current_counters["main_deck"])
    if duplicated_commander:
        errors.append(f"commander is duplicated in main deck: {sorted(duplicated_commander)}")
    for name, quantity in playable.items():
        if quantity <= 1:
            continue
        card = facts_by_name.get(name)
        if not card:
            errors.append(f"cannot verify singleton exception for unresolved card {name!r}")
            continue
        type_prefix = str(card.get("type_line", "")).split("—", 1)[0]
        if not re.search(r"\bBasic\b", type_prefix):
            errors.append(f"non-basic card {card.get('name')!r} has quantity {quantity}")
    check("singleton rules are quantity-aware", errors)

    parsed_current, errors = parse_current_deck(CURRENT_DECK_PATH)
    for section in ("commander", "main_deck", "sideboard"):
        if parsed_current[section] != current_counters[section]:
            errors.append(f"current deck {section} differs from resolved DeckVersion {current_version_id}")
    check("current deck text exactly matches the resolved current DeckVersion", errors)

    parent_counters = {}
    errors = []
    for section in ("commander", "main_deck", "sideboard"):
        parent_counters[section], section_errors = section_counter(parent_version, section)
        errors.extend(section_errors)
    check("parent DeckVersion quantities parse", errors)

    design_id = current_version.get("approved_design_id") or current_version.get("implementation_source")
    design_path = DECISIONS_DIR / f"{design_id}.json" if design_id else None
    errors = []
    try:
        design = load_json(design_path) if design_path else {}
    except (OSError, json.JSONDecodeError) as exc:
        design = {}
        errors.append(f"approved design cannot be loaded: {exc}")
    if design.get("design_id") != design_id:
        errors.append("DeckVersion approved_design_id does not resolve to the matching design")
    if design.get("implemented_version_id") != current_version_id:
        errors.append("approved design does not identify the resolved current version as implemented")
    expected_design_status = f"implemented_as_{current_version_id}"
    if design.get("design_status") != expected_design_status:
        errors.append(
            f"approved design status must be {expected_design_status!r} for the current version"
        )
    if design.get("product_owner_approved") is not True:
        errors.append("approved design lacks Product Owner approval")
    check("current DeckVersion resolves to an approved implemented design", errors)

    expected_added_by_zone, errors = zoned_item_counters(design.get("incoming_cards"), "incoming")
    expected_removed_by_zone, item_errors = zoned_item_counters(
        design.get("proposed_outgoing_cards"), "outgoing"
    )
    errors.extend(item_errors)
    actual_added_by_zone = {
        zone: current_counters[zone] - parent_counters[zone] for zone in DECK_ZONES
    }
    actual_removed_by_zone = {
        zone: parent_counters[zone] - current_counters[zone] for zone in DECK_ZONES
    }
    for zone in DECK_ZONES:
        if actual_added_by_zone[zone] != expected_added_by_zone[zone]:
            errors.append(
                f"{zone} additions do not exactly match approved incoming changes: "
                f"actual={dict(actual_added_by_zone[zone])}, "
                f"expected={dict(expected_added_by_zone[zone])}"
            )
        if actual_removed_by_zone[zone] != expected_removed_by_zone[zone]:
            errors.append(
                f"{zone} removals do not exactly match approved outgoing changes: "
                f"actual={dict(actual_removed_by_zone[zone])}, "
                f"expected={dict(expected_removed_by_zone[zone])}"
            )
    actual_added = flatten_zone_counters(actual_added_by_zone)
    actual_removed = flatten_zone_counters(actual_removed_by_zone)
    check("parent-child diffs are exact, zone-aware, and quantity-aware", errors)

    errors = []
    if not expected_added_by_zone["sideboard"] and not expected_removed_by_zone["sideboard"]:
        if actual_added_by_zone["sideboard"] or actual_removed_by_zone["sideboard"]:
            errors.append("sideboard differs from parent despite no approved sideboard change")
    parent_sideboard_total = sum(parent_counters["sideboard"].values())
    current_sideboard_total = sum(current_counters["sideboard"].values())
    if current_sideboard_total != parent_sideboard_total:
        errors.append(
            f"sideboard quantity total is {current_sideboard_total}, expected {parent_sideboard_total}"
        )
    check("sideboard diff matches approved changes and preserves its quantity invariant", errors)

    change_field = f"changes_from_{parent_id}"
    recorded_changes = current_version.get(change_field)
    errors = []
    if not isinstance(recorded_changes, dict):
        errors.append(f"current DeckVersion is missing {change_field!r}")
    else:
        recorded_added, record_errors = item_counter(recorded_changes.get("added"))
        errors.extend(record_errors)
        recorded_removed, record_errors = item_counter(recorded_changes.get("removed"))
        errors.extend(record_errors)
        if recorded_added != actual_added:
            errors.append("recorded added changes do not match the calculated parent-child diff")
        if recorded_removed != actual_removed:
            errors.append("recorded removed changes do not match the calculated parent-child diff")
    check("DeckVersion change metadata matches its calculated diff", errors)

    source_decision_ids = current_version.get("source_decision_ids") or []
    decision_added = []
    decision_removed = []
    errors = []
    for decision_id in source_decision_ids:
        path = DECISIONS_DIR / f"{decision_id}.json"
        try:
            decision = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"source decision {decision_id!r} cannot be loaded: {exc}")
            continue
        if decision.get("implemented_in_version") != current_version_id:
            errors.append(f"{decision_id} does not identify {current_version_id!r} as implemented")
        decision_added.extend(decision.get("incoming_cards", []))
        decision_removed.extend(decision.get("outgoing_cards", []))
    if Counter(normalize_name(name) for name in decision_added) != actual_added:
        errors.append("source decision incoming cards do not match the implemented additions")
    if Counter(normalize_name(name) for name in decision_removed) != actual_removed:
        errors.append("source decision outgoing cards do not match the implemented removals")
    check("decisions, design, parent, and child agree on the exact change", errors)

    errors = []
    recommendation_id = current_version.get("source_recommendation_id")
    review_ref = current_version.get("source_review_file")
    try:
        recommendation = load_json(RECOMMENDATIONS_DIR / f"{recommendation_id}.json")
        review = load_json(REPO_ROOT / review_ref)
    except (OSError, json.JSONDecodeError) as exc:
        recommendation = {}
        review = {}
        errors.append(f"recommendation/review implementation sources cannot be loaded: {exc}")
    review_statuses = {
        item.get("candidate_id"): item.get("review_status")
        for item in review.get("review_entries", [])
        if isinstance(item, dict)
    }
    ref_names = {}
    for card in list(load_json(CARDS_PATH).get("cards", [])) + list(
        load_json(CANDIDATE_CARDS_PATH).get("candidate_cards", [])
    ):
        if card.get("scryfall_id"):
            ref_names[card["scryfall_id"]] = normalize_name(card.get("name"))
    for candidate in recommendation.get("candidates", []):
        candidate_id = candidate.get("candidate_id")
        if review_statuses.get(candidate_id) == "accepted_for_decision":
            continue
        for ref in candidate.get("incoming_cards", []):
            match = re.fullmatch(r"candidate:scryfall:([0-9a-f-]+)", str(ref))
            name = ref_names.get(match.group(1)) if match else None
            if name and name in actual_added:
                errors.append(
                    f"unapproved candidate {candidate_id!r} with status "
                    f"{review_statuses.get(candidate_id)!r} appears in implemented additions"
                )
    check("unapproved candidate changes are absent from the implemented version", errors)

    errors = []
    for zone in DECK_ZONES:
        changed_names = set(actual_added_by_zone[zone]) | set(actual_removed_by_zone[zone])
        for name in set(parent_counters[zone]) | set(current_counters[zone]):
            if name in changed_names:
                continue
            if parent_counters[zone][name] != current_counters[zone][name]:
                errors.append(
                    f"unchanged {zone} card {name!r} changed quantity from "
                    f"{parent_counters[zone][name]} to {current_counters[zone][name]}"
                )
    check("cards outside the approved diff remain unchanged", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
