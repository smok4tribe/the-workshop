#!/usr/bin/env python3
"""Validate recommendation -> review -> decision -> approved design traceability."""

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
DECISIONS_DIR = PROJECT_DIR / "decisions"
RECOMMENDATIONS_DIR = PROJECT_DIR / "recommendations"
CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"
CANDIDATE_CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "candidate_cards.json"

ALLOWED_REVIEW_STATUSES = {
    "under_review",
    "needs_testing",
    "deferred",
    "accepted_for_decision",
    "rejected",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_name(value):
    value = unicodedata.normalize("NFKC", str(value))
    return " ".join(value.split()).casefold()


def name_counter(values):
    return Counter(normalize_name(value) for value in values)


def card_signature(card):
    fields = ("name", "type_line", "oracle_text", "mana_cost", "color_identity", "legalities")
    return {field: card.get(field) for field in fields}


def load_card_identity_index():
    canonical = load_json(CARDS_PATH).get("cards", [])
    staged = load_json(CANDIDATE_CARDS_PATH).get("candidate_cards", [])
    by_id = {}
    errors = []
    for store_name, records in (("cards.json", canonical), ("candidate_cards.json", staged)):
        for card in records:
            scryfall_id = card.get("scryfall_id")
            if not scryfall_id:
                continue
            previous = by_id.get(scryfall_id)
            if previous and card_signature(previous) != card_signature(card):
                errors.append(
                    f"Scryfall ID {scryfall_id!r} has conflicting facts across Card Facts stores"
                )
            elif previous and previous.get("_store") == store_name:
                errors.append(f"duplicate Scryfall ID {scryfall_id!r} in {store_name}")
            else:
                indexed = dict(card)
                indexed["_store"] = store_name
                by_id[scryfall_id] = indexed
    return by_id, errors


def resolve_card_reference(card_ref, cards_by_id):
    match = re.fullmatch(r"(?:candidate|deck):scryfall:([0-9a-f-]+)", str(card_ref))
    if not match:
        return None
    return cards_by_id.get(match.group(1))


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
        print(f"FAIL: {failed} of {len(checks)} decision pipeline checks failed.")
        return 1
    print(f"PASS: all {len(checks)} decision pipeline validation checks passed.")
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
    if project.get("id") != PROJECT_ID:
        errors.append(f"project id must be {PROJECT_ID!r}")
    check("project metadata resolves", errors)

    designs = []
    decisions = {}
    errors = []
    for path in sorted(DECISIONS_DIR.glob("*.json")):
        try:
            doc = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name} is invalid JSON: {exc}")
            continue
        if not doc:
            continue
        if doc.get("design_type") == "pre_version_deck_change_design":
            designs.append((path, doc))
        else:
            decision_id = doc.get("decision_id")
            if not decision_id or decision_id in decisions:
                errors.append(f"{path.name} has a missing or duplicate decision_id")
            else:
                decisions[decision_id] = doc
    if not designs:
        errors.append("no deck-change design artifact exists")
    check("decision and design artifacts parse with unique IDs", errors)

    cards_by_id, card_errors = load_card_identity_index()
    check("Card Facts identities used by the pipeline are unambiguous", card_errors)

    for design_path, design in designs:
        label = design.get("design_id") or design_path.stem
        target_version = design.get("target_future_version") or design.get("implemented_version_id")

        errors = []
        if not target_version:
            errors.append(f"{label} has no target version")
        recommendation_id = design.get("source_recommendation_id")
        rec_path = RECOMMENDATIONS_DIR / f"{recommendation_id}.json"
        try:
            recommendation = load_json(rec_path)
        except (OSError, json.JSONDecodeError) as exc:
            recommendation = {}
            errors.append(f"{label} referenced recommendation cannot be loaded: {exc}")
        if recommendation.get("recommendation_set_id") != recommendation_id:
            errors.append(f"{label} recommendation ID does not match its source artifact")

        review_ref = design.get("source_review_file")
        review_path = REPO_ROOT / review_ref if review_ref else None
        try:
            review = load_json(review_path) if review_path else {}
        except (OSError, json.JSONDecodeError) as exc:
            review = {}
            errors.append(f"{label} referenced review cannot be loaded: {exc}")
        if review.get("recommendation_set_id") != recommendation_id:
            errors.append(f"{label} review does not reference {recommendation_id!r}")
        check(f"{label} recommendation and review references resolve", errors)

        candidates = {
            item.get("candidate_id"): item
            for item in recommendation.get("candidates", [])
            if isinstance(item, dict) and item.get("candidate_id")
        }
        review_entries = {
            item.get("candidate_id"): item
            for item in review.get("review_entries", [])
            if isinstance(item, dict) and item.get("candidate_id")
        }

        errors = []
        for candidate_id, entry in review_entries.items():
            status = entry.get("review_status")
            if status not in ALLOWED_REVIEW_STATUSES:
                errors.append(f"{candidate_id} has unsupported review status {status!r}")
            if candidate_id not in candidates:
                errors.append(f"{candidate_id} does not exist in {recommendation_id}")
        if set(review_entries) != set(candidates):
            errors.append("recommendation candidates and review entries are not one-to-one")
        check(f"{label} preserves distinct candidate review outcomes", errors)

        source_decision_ids = design.get("source_decision_ids") or []
        source_decisions = {}
        errors = []
        for decision_id in source_decision_ids:
            decision = decisions.get(decision_id)
            if not decision:
                errors.append(f"{label} references missing decision {decision_id!r}")
                continue
            source_decisions[decision_id] = decision
            candidate_id = decision.get("source_candidate_id")
            review_entry = review_entries.get(candidate_id)
            if not review_entry:
                errors.append(f"{decision_id} references unknown reviewed candidate {candidate_id!r}")
                continue
            if review_entry.get("review_status") != "accepted_for_decision":
                errors.append(
                    f"{decision_id} references {candidate_id!r} with unapproved review status "
                    f"{review_entry.get('review_status')!r}"
                )
            if decision.get("candidate_status_at_review") != review_entry.get("review_status"):
                errors.append(f"{decision_id} does not preserve the Product Owner review outcome")
        accepted_ids = {
            candidate_id
            for candidate_id, entry in review_entries.items()
            if entry.get("review_status") == "accepted_for_decision"
        }
        relevant_decisions = {
            decision_id: doc
            for decision_id, doc in decisions.items()
            if doc.get("source_recommendation_id") == recommendation_id
        }
        decided_candidate_ids = {
            doc.get("source_candidate_id") for doc in relevant_decisions.values()
        }
        unapproved_decisions = decided_candidate_ids - accepted_ids
        if unapproved_decisions:
            errors.append(f"unapproved candidates have decision records: {sorted(unapproved_decisions)}")
        check(f"{label} decisions map only to accepted Product Owner reviews", errors)

        errors = []
        implemented_status = f"implemented_as_{target_version}" if target_version else None
        for decision_id, decision in source_decisions.items():
            status = decision.get("decision_status")
            if status == "pending_deck_change_design":
                for field in ("deck_change_authorized", "deck_change_implemented", "creates_new_deck_version"):
                    if decision.get(field) is not False:
                        errors.append(f"{decision_id} pending state requires {field}=false")
            elif status == implemented_status:
                for field in ("deck_change_authorized", "deck_change_implemented", "creates_new_deck_version"):
                    if decision.get(field) is not True:
                        errors.append(f"{decision_id} implemented state requires {field}=true")
                if decision.get("target_deck_version") != target_version:
                    errors.append(f"{decision_id} target version does not match {target_version!r}")
                if decision.get("implemented_in_version") != target_version:
                    errors.append(f"{decision_id} implemented version does not match {target_version!r}")
                if decision.get("implementation_source") != label:
                    errors.append(f"{decision_id} implementation source does not match {label!r}")
            else:
                errors.append(f"{decision_id} has incoherent decision_status {status!r}")
        check(f"{label} decision states are coherent for their target version", errors)

        design_incoming = [item.get("name") for item in design.get("incoming_cards", [])]
        design_outgoing = [item.get("name") for item in design.get("proposed_outgoing_cards", [])]
        decision_incoming = [name for doc in source_decisions.values() for name in doc.get("incoming_cards", [])]
        decision_outgoing = [name for doc in source_decisions.values() for name in doc.get("outgoing_cards", [])]
        errors = []
        if name_counter(design_incoming) != name_counter(decision_incoming):
            errors.append("approved design incoming cards do not exactly match source decisions")
        if name_counter(design_outgoing) != name_counter(decision_outgoing):
            errors.append("approved design outgoing cards do not exactly match source decisions")
        for item in design.get("incoming_cards", []):
            decision_id = item.get("source_decision_id")
            decision = source_decisions.get(decision_id)
            if not decision or normalize_name(item.get("name")) not in name_counter(decision.get("incoming_cards", [])):
                errors.append(f"design incoming card {item.get('name')!r} is mapped to the wrong decision")
        for item in design.get("proposed_outgoing_cards", []):
            matching = [
                decision_id
                for decision_id, decision in source_decisions.items()
                if normalize_name(item.get("name")) in name_counter(decision.get("outgoing_cards", []))
            ]
            if len(matching) != 1:
                errors.append(f"design outgoing card {item.get('name')!r} does not map to exactly one decision")
        check(f"{label} approved card changes exactly match and map to decisions", errors)

        errors = []
        for item in design.get("incoming_cards", []):
            decision = source_decisions.get(item.get("source_decision_id"))
            candidate_id = decision.get("source_candidate_id") if decision else None
            review_status = (review_entries.get(candidate_id) or {}).get("review_status")
            if review_status != "accepted_for_decision":
                errors.append(
                    f"unapproved candidate {candidate_id!r} appears in design incoming cards "
                    f"with review status {review_status!r}"
                )
                continue
            candidate = candidates.get(candidate_id) or {}
            candidate_names = []
            for card_ref in candidate.get("incoming_cards", []):
                card = resolve_card_reference(card_ref, cards_by_id)
                if not card:
                    errors.append(f"{candidate_id} incoming reference cannot be resolved: {card_ref!r}")
                else:
                    candidate_names.append(card.get("name"))
            if normalize_name(item.get("name")) not in name_counter(candidate_names):
                errors.append(
                    f"design incoming card {item.get('name')!r} is not authorized by {candidate_id!r}"
                )
        check(f"{label} excludes rejected, deferred, and needs-testing candidates", errors)

        errors = []
        status = design.get("design_status")
        implemented_status = f"implemented_as_{target_version}" if target_version else None
        approved = design.get("product_owner_approved") is True
        implementation_ready = status in {"product_owner_approved", implemented_status}
        if implementation_ready:
            for field in ("approved_by", "approved_at", "approval_rationale"):
                if not design.get(field):
                    errors.append(f"{label} approved state is missing {field}")
            if not approved:
                errors.append(f"{label} cannot be implementation-ready without Product Owner approval")
        elif approved or design.get("deck_change_authorized") or design.get("deck_change_implemented"):
            errors.append(f"{label} has approval or implementation flags in a non-approved state")
        if status == implemented_status:
            if design.get("implemented_version_id") != target_version:
                errors.append(f"{label} implemented_version_id does not match its target")
            if not design.get("implemented_at"):
                errors.append(f"{label} implemented state is missing implemented_at")
            for field in ("deck_change_authorized", "deck_change_implemented", "creates_new_deck_version"):
                if design.get(field) is not True:
                    errors.append(f"{label} implemented state requires {field}=true")
        elif status not in {"proposed_for_product_owner_review", "product_owner_approved"}:
            errors.append(f"{label} has unsupported design_status {status!r}")
        check(f"{label} design and Product Owner approval states are coherent", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
