"""Derive the current-state structural snapshot for a DeckVersion.

This module deliberately reports only repository-backed deck composition and
functional-role facts. It does not model draws, games, outcomes, or quality.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from .validate_simulation_contracts import deck_content_fingerprint
except ImportError:
    from validate_simulation_contracts import deck_content_fingerprint


PROJECT_ID = "the-myr-singularity"
ANALYSIS_METHOD_ID = "structural-analysis-v1"
ANALYSIS_METHOD_VERSION = "1.0"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).split()).casefold()


def project_paths(root: Path):
    project = root / "workshop" / "projects" / PROJECT_ID
    return {
        "project": project / "project.json",
        "brief": project / "brief" / "brief.json",
        "deck_version": project / "versions" / "v1.1.json",
        "parent_deck_version": project / "versions" / "v1.0.json",
        "card_facts": root / "workshop" / "card-data" / "cards.json",
        "functional_roles": root / "workshop" / "knowledge" / "functional_roles.json",
        "role_taxonomy": root / "workshop" / "knowledge" / "role_taxonomy.json",
    }


def _fact_index(records):
    index = {}
    for card in records:
        if not isinstance(card, dict):
            continue
        for field in ("name", "normalized_name", "original_decklist_name", "display_name"):
            value = card.get(field)
            if value:
                index[normalize_name(value)] = card
    return index


def _role_index(assignments):
    index = {}
    for assignment in assignments:
        if not isinstance(assignment, dict):
            continue
        for field in ("canonical_card_name", "card_name", "original_decklist_name"):
            value = assignment.get(field)
            if value:
                index[normalize_name(value)] = assignment
    return index


def _version_entries(version):
    commander = version.get("commander")
    main_deck = version.get("main_deck")
    entries = []
    if isinstance(commander, dict):
        entries.append(commander)
    if isinstance(main_deck, list):
        entries.extend(main_deck)
    return entries


def _contains_type(card, type_name):
    return bool(re.search(rf"\b{re.escape(type_name)}\b", str(card.get("type_line", ""))))


def _counter_to_object(counter):
    return {key: counter[key] for key in sorted(counter)}


def derive_structural_facts(root: Path):
    """Return the exact v1.1 facts derived from immutable repository sources."""
    paths = project_paths(root)
    project = load_json(paths["project"])
    version = load_json(paths["deck_version"])
    facts = load_json(paths["card_facts"]).get("cards", [])
    assignments = load_json(paths["functional_roles"]).get("assignments", [])
    taxonomy = load_json(paths["role_taxonomy"])
    facts_by_name = _fact_index(facts)
    roles_by_name = _role_index(assignments)
    role_to_category = {
        role["role_id"]: role["category"]
        for role in taxonomy.get("roles", [])
        if isinstance(role, dict) and role.get("role_id") and role.get("category")
    }
    category_labels = {
        category["category_id"]: category["label"]
        for category in taxonomy.get("categories", [])
        if isinstance(category, dict) and category.get("category_id") and category.get("label")
    }

    resolved = []
    errors = []
    for entry in _version_entries(version):
        name = entry.get("name") if isinstance(entry, dict) else None
        quantity = entry.get("quantity") if isinstance(entry, dict) else None
        if not name or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            errors.append(f"DeckVersion entry is invalid: {entry!r}")
            continue
        key = normalize_name(name)
        fact = facts_by_name.get(key)
        assignment = roles_by_name.get(key)
        if not fact:
            errors.append(f"DeckVersion card {name!r} has no canonical Card Facts record")
        if not assignment:
            errors.append(f"DeckVersion card {name!r} has no Functional Knowledge assignment")
        if fact and assignment:
            resolved.append((entry, fact, assignment))
    if errors:
        raise ValueError("; ".join(errors))

    total_cards = sum(entry["quantity"] for entry, _, _ in resolved)
    lands = sum(entry["quantity"] for entry, fact, _ in resolved if _contains_type(fact, "Land"))
    nonlands = [item for item in resolved if not _contains_type(item[1], "Land")]
    curve = Counter()
    color_pips = Counter({color: 0 for color in "WUBRG"})
    colored_nonlands = 0
    for entry, fact, _ in nonlands:
        mana_cost = str(fact.get("mana_cost", ""))
        cmc = fact.get("cmc")
        bucket = "6_plus" if isinstance(cmc, (int, float)) and cmc >= 6 else str(int(cmc))
        curve[bucket] += entry["quantity"]
        has_colored_symbol = False
        for color in "WUBRG":
            amount = mana_cost.count("{" + color + "}") * entry["quantity"]
            color_pips[color] += amount
            has_colored_symbol = has_colored_symbol or amount > 0
        if has_colored_symbol:
            colored_nonlands += entry["quantity"]

    role_counts = Counter()
    primary_counts = Counter()
    category_records = {
        category_id: {"any": 0, "primary": 0, "assignments": 0}
        for category_id in category_labels
    }
    confidence_counts = Counter()
    land_role_counts = Counter()
    for entry, fact, assignment in resolved:
        quantity = entry["quantity"]
        confidence_counts[assignment.get("confidence", "unknown")] += quantity
        role_categories = set()
        for role_id in assignment.get("roles", []):
            category_id = role_to_category.get(role_id)
            if category_id is None:
                raise ValueError(f"Functional role {role_id!r} has no taxonomy category")
            role_counts[role_id] += quantity
            role_categories.add(category_id)
            category_records[category_id]["assignments"] += quantity
        for category_id in role_categories:
            category_records[category_id]["any"] += quantity
        primary_categories = set()
        for role_id in assignment.get("primary_roles", []):
            category_id = role_to_category.get(role_id)
            if category_id is None:
                raise ValueError(f"Primary Functional role {role_id!r} has no taxonomy category")
            primary_counts[role_id] += quantity
            primary_categories.add(category_id)
        for category_id in primary_categories:
            category_records[category_id]["primary"] += quantity
        if _contains_type(fact, "Land"):
            for role_id in set(assignment.get("roles", [])):
                if role_id in {"colored_source", "fixing_land"}:
                    land_role_counts[role_id] += quantity

    category_distribution = {
        category_id: {
            "label": category_labels[category_id],
            "cards_with_any_role": record["any"],
            "cards_with_primary_role": record["primary"],
            "role_assignments_in_category": record["assignments"],
        }
        for category_id, record in category_records.items()
    }
    sideboard = version.get("sideboard", [])
    sideboard_roles = {}
    for entry in sideboard:
        assignment = roles_by_name.get(normalize_name(entry.get("name", "")))
        if assignment:
            sideboard_roles[entry["name"]] = assignment.get("roles", [])

    return {
        "project_id": project.get("id"),
        "deck_version_id": version.get("version_id"),
        "deck_content_fingerprint": deck_content_fingerprint(version),
        "deck_identity_summary": {
            "commander": version.get("commander", {}).get("name"),
            "format": project.get("format"),
            "stated_identity": project.get("identity", {}).get("summary"),
            "stated_resource_model": project.get("identity", {}).get("resource_model"),
            "color_identity": ["W", "U", "B", "R", "G"],
            "composition": {
                "playable_cards": total_cards,
                "lands": lands,
                "nonland_cards": total_cards - lands,
                "artifact_cards": sum(entry["quantity"] for entry, fact, _ in resolved if _contains_type(fact, "Artifact")),
                "creature_cards": sum(entry["quantity"] for entry, fact, _ in resolved if _contains_type(fact, "Creature")),
                "myr_typal_cards": sum(entry["quantity"] for entry, fact, _ in resolved if _contains_type(fact, "Myr")),
                "colored_nonland_cards": colored_nonlands,
                "average_mana_value_nonland": round(sum(entry["quantity"] * fact["cmc"] for entry, fact, _ in nonlands) / sum(entry["quantity"] for entry, _, _ in nonlands), 2),
                "mana_value_curve_nonland": {bucket: curve[bucket] for bucket in ("0", "1", "2", "3", "4", "5", "6_plus")},
                "sideboard_cards": sum(entry.get("quantity", 0) for entry in sideboard if isinstance(entry, dict)),
            },
        },
        "color_requirements": {
            "counting_basis": "colored mana symbols in canonical mana_cost fields for playable nonland cards",
            "colored_nonland_cards": colored_nonlands,
            "mana_symbol_counts": _counter_to_object(color_pips),
            "colored_land_sources_by_role": land_role_counts["colored_source"],
            "fixing_lands_by_role": land_role_counts["fixing_land"],
        },
        "role_distribution": {
            "counting_basis": "cards_in_playable_100_carrying_role",
            "roles": {
                role_id: {
                    "cards_with_role": role_counts[role_id],
                    "cards_with_primary_role": primary_counts[role_id],
                }
                for role_id in sorted(role_counts)
            },
            "taxonomy_roles_unused_in_deck": sorted(set(role_to_category) - set(role_counts)),
            "assignment_confidence": _counter_to_object(confidence_counts),
        },
        "category_distribution": {
            "counting_basis": "cards_with_any_role and cards_with_primary_role count distinct cards in the playable 100; role_assignments_in_category counts role assignments",
            "categories": category_distribution,
        },
        "sideboard_roles": sideboard_roles,
    }


def derive_v1_delta(root: Path):
    paths = project_paths(root)
    parent = load_json(paths["parent_deck_version"])
    current = load_json(paths["deck_version"])

    def counter(version):
        values = Counter()
        for entry in _version_entries(version):
            values[normalize_name(entry["name"])] += entry["quantity"]
        return values

    parent_names = counter(parent)
    current_names = counter(current)
    current_spelling = {normalize_name(entry["name"]): entry["name"] for entry in _version_entries(current)}
    parent_spelling = {normalize_name(entry["name"]): entry["name"] for entry in _version_entries(parent)}
    return {
        "from_deck_version_id": parent.get("version_id"),
        "added": [current_spelling[key] for key in sorted(current_names - parent_names)],
        "removed": [parent_spelling[key] for key in sorted(parent_names - current_names)],
    }


def analysis_snapshot(root: Path):
    """Select the current-state facts recorded by the analysis artifact."""
    facts = derive_structural_facts(root)
    return {
        "deck_content_fingerprint": facts["deck_content_fingerprint"],
        "deck_identity_summary": facts["deck_identity_summary"],
        "color_requirements": facts["color_requirements"],
        "functional_role_density": {
            role_id: values["cards_with_role"]
            for role_id, values in facts["role_distribution"]["roles"].items()
        },
        "category_distribution": facts["category_distribution"],
        "functional_assignment_confidence": facts["role_distribution"]["assignment_confidence"],
        "sideboard_roles": facts["sideboard_roles"],
    }
