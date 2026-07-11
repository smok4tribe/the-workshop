#!/usr/bin/env python3
"""Validate structured project reports against their referenced Workshop data."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECTS_DIR = REPO_ROOT / "workshop" / "projects"
RENDERER_PATH = REPO_ROOT / "workshop" / "scripts" / "render_project_report.py"
DECK_VALIDATOR_PATH = REPO_ROOT / "workshop" / "tests" / "validation" / "validate_deck_versions.py"
REQUIRED_SOURCES = {
    "project", "brief", "baseline_deck_version", "resulting_deck_version",
    "current_decklist", "baseline_analysis", "recommendation", "product_owner_review",
    "decisions", "deck_change_design", "card_facts", "functional_knowledge",
    "candidate_lifecycle_metadata", "active_candidate_facts",
}
DECK_ZONES = ("commander", "main_deck", "sideboard")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report(checks):
    failed = 0
    for description, errors in checks:
        print(f"[{'PASS' if not errors else 'FAIL'}] {description}")
        for error in errors:
            print(f"       - {error}")
        failed += bool(errors)
    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} project report checks failed.")
        return 1
    print(f"PASS: all {len(checks)} project report validation checks passed.")
    return 0


def source_path(reference):
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        return None
    path = (REPO_ROOT / reference["path"]).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        return None
    return path


def load_source(reference, label, errors):
    path = source_path(reference)
    if not path or not path.is_file():
        errors.append(f"source {label!r} does not exist: {reference!r}")
        return None, None
    try:
        return path, load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"source {label!r} is invalid JSON: {exc}")
        return path, None


def source_list(value):
    return value if isinstance(value, list) else [value]


def report_delta_counter(items, deck):
    result = {zone: Counter() for zone in DECK_ZONES}
    indexed = {}
    errors = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict):
            errors.append(f"delta item {index} must be an object")
            continue
        zone = item.get("zone")
        quantity = item.get("quantity")
        name = item.get("card_name")
        if zone not in result or not deck.valid_quantity(quantity) or not name:
            errors.append(f"delta item {index} has invalid card_name, quantity, or zone")
            continue
        key = (zone, deck.normalize_name(name))
        if key in indexed:
            errors.append(f"duplicate report delta item for {name!r} in {zone}")
        indexed[key] = item
        result[zone][key[1]] += quantity
    return result, indexed, errors


def card_indexes(canonical_card_facts, active_candidate_facts):
    canonical = canonical_card_facts.get("cards", [])
    active = active_candidate_facts.get("candidate_cards", [])
    by_id = {card.get("scryfall_id"): card for card in canonical + active if card.get("scryfall_id")}
    return canonical, active, by_id


def candidate_card_names(candidate, by_id):
    names = []
    for reference in candidate.get("incoming_cards", []):
        match = re.fullmatch(r"candidate:scryfall:([0-9a-f-]+)", str(reference))
        card = by_id.get(match.group(1)) if match else None
        if card:
            names.append(card.get("name"))
    return names


def validate_evidence(value, label, project_id, version_id, errors):
    if not isinstance(value, dict) or "status" not in value:
        errors.append(f"evidence {label!r} must be an object with status")
        return
    status = value["status"]
    refs = value.get("sources") if label == "performance_claim" else [value.get("source")]
    refs = [] if refs is None else [reference for reference in refs if reference is not None]
    if status in {"not_run", "not_recorded", "not_measured"}:
        if refs:
            errors.append(f"unmeasured evidence {label!r} must not reference sources")
        return
    if status not in {"completed", "validated", "measured"}:
        errors.append(f"evidence {label!r} has unsupported status {status!r}")
        return
    if not isinstance(refs, list) or not refs:
        errors.append(f"measured evidence {label!r} requires a structured source")
        return
    for reference in refs:
        path, evidence = load_source(reference, f"evidence:{label}", errors)
        if not evidence:
            continue
        if evidence.get("project_id") != project_id or evidence.get("deck_version_id") != version_id:
            errors.append(f"evidence {label!r} does not match report project and resulting DeckVersion")
        if evidence.get("artifact_type") != "post_implementation_evidence":
            errors.append(f"evidence {label!r} has wrong artifact type")
        if label == "performance_claim" and evidence.get("evidence_kind") != "performance_measurement":
            errors.append("measured performance claim lacks performance-measurement evidence")


def main():
    checks = []
    def check(description, errors):
        checks.append((description, errors))

    project_filter = os.environ.get("WORKSHOP_PROJECT_ID")
    projects = {}
    for project_path in PROJECTS_DIR.iterdir():
        metadata_path = project_path / "project.json"
        if project_path.is_dir() and metadata_path.is_file():
            metadata = load_json(metadata_path)
            if metadata.get("id"):
                projects[metadata["id"]] = (project_path, metadata)
    report_paths = []
    for project_id, (project_path, _) in projects.items():
        if not project_filter or project_filter == project_id:
            report_paths.extend(sorted((project_path / "reports").glob("project_report_v*.json")))
    check("structured project reports are discovered from project metadata", [] if report_paths else ["no structured project reports found"])

    deck = load_module("deck_version_helpers", DECK_VALIDATOR_PATH)
    renderer = load_module("project_report_renderer", RENDERER_PATH)
    for report_path in report_paths:
        errors = []
        try:
            doc = load_json(report_path)
        except json.JSONDecodeError as exc:
            check(f"{report_path.name} parses", [str(exc)])
            continue
        label = doc.get("report_id", report_path.stem)
        project_id = doc.get("project_id")
        project_info = projects.get(project_id)
        if not project_info:
            check(f"{label} resolves its project", [f"project_id {project_id!r} does not resolve"])
            continue
        project_dir, project = project_info
        if report_path.parent != project_dir / "reports":
            errors.append("report path does not belong to its resolved project")
        baseline_id = doc.get("baseline_deck_version_id")
        resulting_id = doc.get("resulting_deck_version_id")
        if not baseline_id or not resulting_id or baseline_id == resulting_id:
            errors.append("report baseline and resulting DeckVersions must be distinct")
        if not (project_dir / "versions" / f"{baseline_id}.json").is_file():
            errors.append(f"baseline DeckVersion {baseline_id!r} does not resolve")
        if not (project_dir / "versions" / f"{resulting_id}.json").is_file():
            errors.append(f"resulting DeckVersion {resulting_id!r} does not resolve")
        if doc.get("resulting_version_is_current") is not (resulting_id == project.get("current_version_id")):
            errors.append("report resulting_version_is_current claim does not match project metadata")
        check(f"{label} resolves its project and version claims", errors)
        if errors:
            continue

        sources = doc.get("source_references", {})
        errors = []
        if not isinstance(sources, dict):
            errors.append("source_references must be an object")
        else:
            missing = sorted(REQUIRED_SOURCES - set(sources))
            if missing:
                errors.append(f"missing required structured sources: {missing}")
        check(f"{label} declares the complete structured source contract", errors)
        if errors:
            continue

        errors = []
        project_path, source_project = load_source(sources["project"], "project", errors)
        brief_path, brief = load_source(sources["brief"], "brief", errors)
        baseline_path, baseline = load_source(sources["baseline_deck_version"], "baseline_deck_version", errors)
        resulting_path, resulting = load_source(sources["resulting_deck_version"], "resulting_deck_version", errors)
        analysis_path, analysis = load_source(sources["baseline_analysis"], "baseline_analysis", errors)
        recommendation_path, recommendation = load_source(sources["recommendation"], "recommendation", errors)
        review_path, review = load_source(sources["product_owner_review"], "product_owner_review", errors)
        design_path, design = load_source(sources["deck_change_design"], "deck_change_design", errors)
        card_facts_path, card_facts = load_source(sources["card_facts"], "card_facts", errors)
        active_facts_path, active_facts = load_source(sources["active_candidate_facts"], "active_candidate_facts", errors)
        roles_path, roles = load_source(sources["functional_knowledge"], "functional_knowledge", errors)
        lifecycle_path, lifecycle = load_source(sources["candidate_lifecycle_metadata"], "candidate_lifecycle_metadata", errors)
        current_path = source_path(sources["current_decklist"])
        if not current_path or not current_path.is_file():
            errors.append("source 'current_decklist' does not exist")
        decisions = {}
        for reference in source_list(sources["decisions"]):
            path, decision = load_source(reference, "decisions", errors)
            if decision:
                decision_id = reference.get("id")
                if decision.get("decision_id") != decision_id:
                    errors.append(f"decision source identity mismatch for {decision_id!r}")
                decisions[decision_id] = decision
        if source_project and (source_project.get("id") != project_id or sources["project"].get("id") != project_id):
            errors.append("project source identity does not match report project")
        if brief and (brief.get("project_id") != project_id or brief.get("commander") != project.get("commander")):
            errors.append("brief source identity does not match project")
        for version, expected, source_name in ((baseline, baseline_id, "baseline"), (resulting, resulting_id, "resulting")):
            if version and (version.get("version_id") != expected or version.get("project_id") != project_id):
                errors.append(f"{source_name} DeckVersion source identity does not match report")
        if resulting and resulting.get("parent_version_id") != baseline_id:
            errors.append("resulting DeckVersion parent does not match report baseline")
        if analysis and (analysis.get("analysis_id") != sources["baseline_analysis"].get("id") or analysis.get("project_id") != project_id or analysis.get("deck_version_id") != baseline_id):
            errors.append("baseline analysis source identity does not match report")
        if recommendation and (recommendation.get("recommendation_set_id") != sources["recommendation"].get("id") or recommendation.get("project_id") != project_id):
            errors.append("recommendation source identity does not match report")
        if review and (review.get("artifact_type") != "product_owner_candidate_review" or review.get("project_id") != project_id or review.get("recommendation_set_id") != recommendation.get("recommendation_set_id")):
            errors.append("Product Owner review source identity does not match recommendation")
        if design and (design.get("design_id") != sources["deck_change_design"].get("id") or design.get("project_id") != project_id or design.get("implemented_version_id") != resulting_id or design.get("product_owner_approved") is not True):
            errors.append("deck-change design source identity or approval does not match report")
        if card_facts and not isinstance(card_facts.get("cards"), list):
            errors.append("card facts source has wrong artifact shape")
        if active_facts and not isinstance(active_facts.get("candidate_cards"), list):
            errors.append("active candidate facts source has wrong artifact shape")
        if roles and (roles.get("name") != "Functional Role Assignments" or not isinstance(roles.get("assignments"), list)):
            errors.append("functional knowledge source has wrong artifact shape")
        if lifecycle and (not isinstance(lifecycle.get("candidate_intake_scryfall_ids"), list) or not isinstance(lifecycle.get("promoted_candidate_records"), list)):
            errors.append("candidate lifecycle source has wrong artifact shape")
        identity = doc.get("project_identity", {})
        if source_project and identity.get("name") != source_project.get("name"):
            errors.append("report project name does not match project metadata")
        if source_project and identity.get("format") != source_project.get("format"):
            errors.append("report project format does not match project metadata")
        if source_project and identity.get("commander") != source_project.get("commander"):
            errors.append("report project commander does not match project metadata")
        if not isinstance(identity.get("curated_summary"), dict):
            errors.append("report project narrative must be explicitly marked curated")
        if source_project and doc.get("brief_summary", {}).get("goals") != source_project.get("goals"):
            errors.append("report brief goals do not match authoritative project goals")
        baseline_summary = doc.get("baseline_summary", {})
        if analysis and baseline_summary.get("analysis_id") != analysis.get("analysis_id"):
            errors.append("report baseline analysis ID does not match source analysis")
        if analysis and baseline_summary.get("deck_version_id") != analysis.get("deck_version_id"):
            errors.append("report baseline DeckVersion summary does not match source analysis")
        implementation = doc.get("implementation_summary", {})
        if design and resulting and (implementation.get("design_id") != design.get("design_id") or implementation.get("design_id") not in {resulting.get("approved_design_id"), resulting.get("implementation_source")}):
            errors.append("implementation summary design_id does not match approved design")
        if design and implementation.get("product_owner_approved") is not design.get("product_owner_approved"):
            errors.append("implementation summary approval state does not match design")
        if design and implementation.get("approval_by") != design.get("approved_by"):
            errors.append("implementation summary approver does not match design")
        if resulting and (implementation.get("parent_version_id") != resulting.get("parent_version_id") or implementation.get("parent_version_id") != baseline_id):
            errors.append("implementation summary parent version does not match resulting DeckVersion")
        if design and (implementation.get("resulting_version_id") != resulting_id or implementation.get("resulting_version_id") != design.get("implemented_version_id")):
            errors.append("implementation summary resulting version does not match sources")
        if implementation.get("validation_status") not in {"implementation_verified", "implementation_not_verified"}:
            errors.append("implementation summary validation_status is unsupported")
        check(f"{label} validates every structured source by identity and relationship", errors)
        if errors:
            continue

        errors = []
        baseline_counters = {zone: deck.section_counter(baseline, zone)[0] for zone in DECK_ZONES}
        resulting_counters = {zone: deck.section_counter(resulting, zone)[0] for zone in DECK_ZONES}
        actual_added = {zone: resulting_counters[zone] - baseline_counters[zone] for zone in DECK_ZONES}
        actual_removed = {zone: baseline_counters[zone] - resulting_counters[zone] for zone in DECK_ZONES}
        report_added, added_items, item_errors = report_delta_counter(doc.get("version_delta", {}).get("added"), deck)
        report_removed, removed_items, removed_errors = report_delta_counter(doc.get("version_delta", {}).get("removed"), deck)
        errors.extend(item_errors + removed_errors)
        if report_added != actual_added or report_removed != actual_removed:
            errors.append("report version delta does not match the derived parent-child DeckVersion diff")
        delta = doc.get("version_delta", {})
        if delta.get("commander_unchanged") is not (not actual_added["commander"] and not actual_removed["commander"]):
            errors.append("report commander unchanged claim does not match versions")
        if delta.get("sideboard_unchanged") is not (not actual_added["sideboard"] and not actual_removed["sideboard"]):
            errors.append("report sideboard unchanged claim does not match versions")
        playable_total = sum(resulting_counters["commander"].values()) + sum(resulting_counters["main_deck"].values())
        if delta.get("playable_total") != playable_total:
            errors.append("report playable_total does not match resulting DeckVersion")
        facts_by_name = {}
        singleton_errors = []
        for card in card_facts.get("cards", []) + active_facts.get("candidate_cards", []):
            for field in ("name", "original_decklist_name", "display_name", "normalized_name"):
                if card.get(field):
                    key = deck.normalize_name(card[field])
                    existing = facts_by_name.get(key)
                    if existing and existing.get("scryfall_id") != card.get("scryfall_id"):
                        singleton_errors.append(f"duplicate Card Facts identity for {card[field]!r}")
                    facts_by_name[key] = card
        playable = resulting_counters["commander"] + resulting_counters["main_deck"]
        for name, quantity in playable.items():
            if quantity > 1 and not re.search(r"\bBasic\b", str(facts_by_name.get(name, {}).get("type_line", ""))):
                singleton_errors.append(f"non-basic card {name!r} has quantity {quantity}")
        if delta.get("singleton_state") != ("valid" if not singleton_errors else "invalid"):
            errors.append("report singleton_state does not match resulting DeckVersion")
        baseline_immutable = baseline_path.is_file() and resulting.get("parent_version_id") == baseline_id
        if delta.get("baseline_version_unchanged") is not baseline_immutable:
            errors.append("report baseline_version_unchanged claim is not supported by retained parent state")
        parsed_current, parse_errors = deck.parse_current_deck(current_path)
        errors.extend(parse_errors)
        for zone in DECK_ZONES:
            if parsed_current[zone] != resulting_counters[zone]:
                errors.append(f"current deck {zone} differs from report resulting DeckVersion {resulting_id}")
        if delta.get("current_decklist_matches_resulting_version") is not (not parse_errors and parsed_current == resulting_counters):
            errors.append("report current decklist alignment claim does not match exact parsed deck content")
        if doc.get("implementation_summary", {}).get("current_decklist_matches_resulting_version") is not (not parse_errors and parsed_current == resulting_counters):
            errors.append("implementation summary current-deck alignment does not match exact parsed deck content")
        check(f"{label} derives version, singleton, and exact current-deck claims", errors)

        errors = []
        for direction, items, decision_field in (("added", added_items, "incoming_cards"), ("removed", removed_items, "outgoing_cards")):
            for (_, name), item in items.items():
                decision_id = item.get("source_decision_id")
                decision = decisions.get(decision_id)
                if not decision:
                    errors.append(f"report delta {direction} {item.get('card_name')!r} has unresolved source decision")
                    continue
                if decision.get("implemented_in_version") != resulting_id:
                    errors.append(f"decision {decision_id!r} does not identify resulting DeckVersion")
                if name not in Counter(deck.normalize_name(value) for value in decision.get(decision_field, [])):
                    errors.append(f"report delta {direction} {item.get('card_name')!r} has wrong decision attribution")
        summaries = {item.get("decision_id"): item for item in doc.get("decision_summary", []) if isinstance(item, dict)}
        if set(summaries) != set(decisions):
            errors.append("decision summary IDs do not match referenced decisions")
        for decision_id, decision in decisions.items():
            summary = summaries.get(decision_id, {})
            if (summary.get("candidate_id") != decision.get("source_candidate_id")
                    or summary.get("incoming_cards") != decision.get("incoming_cards")
                    or summary.get("outgoing_cards") != decision.get("outgoing_cards")
                    or summary.get("source_rationale") != decision.get("implementation_rationale")):
                errors.append(f"decision summary for {decision_id!r} does not match source decision")
        design_added, design_added_errors = deck.zoned_item_counters(design.get("incoming_cards"), "incoming")
        design_removed, design_removed_errors = deck.zoned_item_counters(design.get("proposed_outgoing_cards"), "outgoing")
        errors.extend(design_added_errors + design_removed_errors)
        if design_added != actual_added or design_removed != actual_removed:
            errors.append("deck-change design does not match report resulting delta")
        check(f"{label} validates decision provenance and summaries for every delta item", errors)

        errors = []
        _, active_cards, cards_by_id = card_indexes(card_facts, active_facts)
        candidates = {item.get("candidate_id"): item for item in recommendation.get("candidates", []) if isinstance(item, dict)}
        review_statuses = {item.get("candidate_id"): item.get("review_status") for item in review.get("review_entries", []) if isinstance(item, dict)}
        dispositions = {item.get("candidate_id"): item for item in doc.get("candidate_dispositions", []) if isinstance(item, dict)}
        if set(dispositions) != set(candidates):
            errors.append("candidate dispositions do not exactly cover recommendation candidates")
        decision_by_candidate = {decision.get("source_candidate_id"): decision for decision in decisions.values()}
        actual_added_names = Counter()
        for zone in DECK_ZONES:
            actual_added_names += actual_added[zone]
        for candidate_id, candidate in candidates.items():
            disposition = dispositions.get(candidate_id, {})
            incoming_names = candidate_card_names(candidate, cards_by_id)
            expected_name = " and ".join(incoming_names) or candidate_id
            if disposition.get("candidate_name") != expected_name or disposition.get("review_status") != review_statuses.get(candidate_id):
                errors.append(f"candidate disposition for {candidate_id!r} does not match recommendation/review")
                continue
            decision = decision_by_candidate.get(candidate_id)
            implemented = bool(decision and review_statuses.get(candidate_id) == "accepted_for_decision" and decision.get("implemented_in_version") == resulting_id and all(actual_added_names[deck.normalize_name(name)] for name in decision.get("incoming_cards", [])))
            expected_status = "implemented" if implemented else "not_implemented"
            if disposition.get("implementation_status") != expected_status:
                errors.append(f"candidate disposition for {candidate_id!r} does not match derived implementation state")
            expected_ids = [decision.get("decision_id")] if implemented else []
            if disposition.get("source_decision_ids") != expected_ids:
                errors.append(f"candidate disposition for {candidate_id!r} has incorrect decision provenance")
        implemented_names = sorted(name for zone in DECK_ZONES for name in actual_added[zone])
        reported_names = sorted(deck.normalize_name(name) for name in doc.get("knowledge_alignment", {}).get("implemented_cards_in_canonical_facts", []))
        if reported_names != implemented_names:
            errors.append("implemented-card Knowledge set does not match derived additions")
        canonical, active_cards, cards_by_id = card_indexes(card_facts, active_facts)
        canonical_ids = [card.get("scryfall_id") for card in canonical]
        canonical_names = [deck.normalize_name(card.get("name")) for card in canonical if card.get("name")]
        active_ids_list = [card.get("scryfall_id") for card in active_cards]
        if len(canonical_ids) != len(set(canonical_ids)) or len(canonical_names) != len(set(canonical_names)):
            errors.append("referenced canonical Card Facts have duplicate Scryfall IDs or names")
        if len(active_ids_list) != len(set(active_ids_list)):
            errors.append("referenced active candidate facts have duplicate Scryfall IDs")
        canonical_by_name = {deck.normalize_name(card.get("name")): card for card in canonical}
        assignments = {item.get("card_source_ref", {}).get("id"): item for item in roles.get("assignments", []) if isinstance(item, dict)}
        promoted_ids = {item.get("scryfall_id") for item in lifecycle.get("promoted_candidate_records", [])}
        active_ids = {item.get("scryfall_id") for item in active_cards}
        if active_ids & promoted_ids:
            errors.append("active candidate facts overlap promoted lifecycle records")
        for name in implemented_names:
            card = canonical_by_name.get(name)
            if not card or not card.get("scryfall_id") or card["scryfall_id"] not in assignments:
                errors.append(f"implemented card {name!r} lacks canonical facts or Functional Knowledge")
            elif card["scryfall_id"] not in promoted_ids or card["scryfall_id"] in active_ids:
                errors.append(f"implemented card {name!r} lacks promoted historical candidate provenance")
            expected_reference = next(
                (item.get("reference") for item in design.get("incoming_cards", [])
                 if deck.normalize_name(item.get("name")) == name),
                None,
            )
            expected_match = re.fullmatch(r"candidate:scryfall:([0-9a-f-]+)", str(expected_reference))
            if expected_match and card and card.get("scryfall_id") != expected_match.group(1):
                errors.append(f"implemented card {card.get('name')!r} has wrong referenced Card Facts identity")
        for candidate_id, candidate in candidates.items():
            if review_statuses.get(candidate_id) == "needs_testing":
                for reference in candidate.get("incoming_cards", []):
                    candidate_id_match = re.fullmatch(r"candidate:scryfall:([0-9a-f-]+)", str(reference))
                    if not candidate_id_match or candidate_id_match.group(1) not in active_ids:
                        errors.append(f"needs-testing candidate {candidate_id!r} is not an active candidate fact")
        if doc.get("knowledge_alignment", {}).get("historical_candidate_provenance") != "resolvable":
            errors.append("historical candidate provenance claim does not match lifecycle state")
        check(f"{label} derives candidate states, Knowledge alignment, and provenance", errors)

        errors = []
        evidence = doc.get("evidence_status", {})
        if evidence.get("implementation_result") not in {"verified", "not_verified"}:
            errors.append("implementation_result has unsupported status")
        implementation_status = doc.get("implementation_summary", {}).get("validation_status")
        expected_implementation_result = {
            "implementation_verified": "verified",
            "implementation_not_verified": "not_verified",
        }.get(implementation_status)
        if (expected_implementation_result is not None
                and evidence.get("implementation_result") in {"verified", "not_verified"}
                and evidence.get("implementation_result") != expected_implementation_result):
            errors.append(
                "implementation summary validation_status does not agree with evidence implementation_result"
            )
        for evidence_label in ("post_implementation_analysis", "post_implementation_simulation", "gameplay_validation", "performance_claim"):
            validate_evidence(evidence.get(evidence_label), evidence_label, project_id, resulting_id, errors)
        measured = evidence.get("performance_claim", {}).get("status") == "measured"
        expected_report_status = "implementation_verified_outcomes_measured" if measured else "implementation_verified_outcomes_not_measured"
        if evidence.get("implementation_result") == "verified" and doc.get("report_status") != expected_report_status:
            errors.append("report status does not agree with evidence state")
        check(f"{label} validates generic evidence references and report status", errors)

        errors = []
        markdown_path = report_path.with_suffix(".md")
        if not markdown_path.is_file():
            errors.append(f"{markdown_path.name} does not exist")
        elif markdown_path.read_text(encoding="utf-8") != renderer.render_report(doc):
            errors.append("committed Markdown differs from deterministic renderer output")
        check(f"{label} Markdown is deterministic and complete", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
