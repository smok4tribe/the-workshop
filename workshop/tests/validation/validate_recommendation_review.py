#!/usr/bin/env python3
"""Product Owner Recommendation Review validation checks for Sprint 1.

Validates the Product Owner review layer:

- workshop/projects/the-myr-singularity/recommendations/review_schema.json
  (the review artifact contract)
- workshop/projects/the-myr-singularity/recommendations/review-rec-002.json
  and its companion review-rec-002.md (the first review artifact, scoped to
  rec-002)

The validator supports two artifact states:

* scaffold state: every review entry is 'under_review' and the top-level
  review_status is 'not_started' or 'pending_product_owner_review'.
* progressed state: the Product Owner has recorded non-neutral review
  states ('needs_testing', 'deferred', 'accepted_for_decision',
  'rejected') on some entries and the top-level review_status is
  'in_progress' or 'completed'.

In both states the validator guards the boundary between three layers:

* Recommendation candidates (rec-002.json) are generated, proposed,
  non-actionable artifacts. Review never modifies them.
* Product Owner review (review-rec-002.json) records human review intent.
  'accepted_for_decision' and 'needs_testing' do not change the deck.
* Decision logs and deck versions are separate, later artifacts. Review
  never creates a decision log entry or a new deck version (no v1.1).

Standard library only. No external dependencies.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
RECOMMENDATIONS_DIR = PROJECT_DIR / "recommendations"
DECISIONS_DIR = PROJECT_DIR / "decisions"
VERSIONS_DIR = PROJECT_DIR / "versions"

REVIEW_SCHEMA_PATH = RECOMMENDATIONS_DIR / "review_schema.json"
REVIEW_JSON_PATH = RECOMMENDATIONS_DIR / "review-rec-002.json"
REVIEW_MD_PATH = RECOMMENDATIONS_DIR / "review-rec-002.md"
DEFAULT_REC_JSON_PATH = RECOMMENDATIONS_DIR / "rec-002.json"

ALLOWED_ENTRY_STATUSES = {
    "under_review",
    "needs_testing",
    "deferred",
    "accepted_for_decision",
    "rejected",
}

NON_NEUTRAL_ENTRY_STATUSES = ALLOWED_ENTRY_STATUSES - {"under_review"}

# accepted_or_rejected_or_deferred mirrors exactly these entry states.
CONCLUSIVE_ENTRY_STATUSES = {"accepted_for_decision", "rejected", "deferred"}

ALLOWED_TOP_LEVEL_STATUSES = {
    "not_started",
    "pending_product_owner_review",
    "in_progress",
    "completed",
}

SCAFFOLD_TOP_LEVEL_STATUSES = {"not_started", "pending_product_owner_review"}

# Fields that belong to the decision layer and must never appear on a
# review entry: a review cannot create or reference a decision by itself.
DECISION_LAYER_ENTRY_FIELDS = {"decision_id", "user_decision"}

REQUIRED_REVIEW_ENTRY_FIELDS = [
    "candidate_id",
    "recommendation_set_id",
    "review_status",
    "reviewer_role",
    "reviewer_notes",
    "rationale",
    "testing_required",
    "testing_notes",
    "decision_log_required",
    "creates_new_deck_version_if_accepted",
    "reviewed_at",
]

ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}([T ].+)?")


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def entry_label(index, entry):
    candidate_id = entry.get("candidate_id") if isinstance(entry, dict) else None
    return f"review_entries[{index}] ({candidate_id!r})"


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    # Check 1: review_schema.json parses as JSON.
    errors = []
    schema_doc = None
    try:
        schema_doc = load_json(REVIEW_SCHEMA_PATH)
    except FileNotFoundError:
        errors.append(f"{REVIEW_SCHEMA_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{REVIEW_SCHEMA_PATH} is not valid JSON: {exc}")
    check("review_schema.json parses as JSON", errors)

    # Check 2: review-rec-002.json parses as JSON.
    errors = []
    review_doc = None
    review_mtime_before = REVIEW_JSON_PATH.stat().st_mtime if REVIEW_JSON_PATH.is_file() else None
    try:
        review_doc = load_json(REVIEW_JSON_PATH)
    except FileNotFoundError:
        errors.append(f"{REVIEW_JSON_PATH} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{REVIEW_JSON_PATH} is not valid JSON: {exc}")
    check("review-rec-002.json parses as JSON", errors)

    # Check 3: review-rec-002.md exists.
    errors = []
    review_md_text = ""
    if not REVIEW_MD_PATH.is_file():
        errors.append(f"{REVIEW_MD_PATH} not found")
    else:
        review_md_text = REVIEW_MD_PATH.read_text(encoding="utf-8")
    check("review-rec-002.md exists", errors)

    if schema_doc is None or review_doc is None:
        return report(checks)

    # Check 4: review artifact references rec-002.json.
    errors = []
    source_file = review_doc.get("source_recommendation_file")
    rec_json_path = DEFAULT_REC_JSON_PATH
    if not source_file:
        errors.append("review artifact is missing source_recommendation_file")
    else:
        rec_json_path = REPO_ROOT / source_file
        if rec_json_path.resolve() != DEFAULT_REC_JSON_PATH.resolve():
            errors.append(
                f"source_recommendation_file {source_file!r} does not point at "
                f"{DEFAULT_REC_JSON_PATH.relative_to(REPO_ROOT)}"
            )
    if review_doc.get("recommendation_set_id") != "rec-002":
        errors.append("review artifact recommendation_set_id must be 'rec-002'")
    check("review artifact references rec-002.json", errors)

    # Check 5: rec-002.json exists and parses.
    errors = []
    rec_doc = None
    try:
        rec_doc = load_json(rec_json_path)
    except FileNotFoundError:
        errors.append(f"{rec_json_path} not found")
    except json.JSONDecodeError as exc:
        errors.append(f"{rec_json_path} is not valid JSON: {exc}")
    check("rec-002.json exists and parses", errors)

    if rec_doc is None:
        return report(checks)

    rec_candidates = rec_doc.get("candidates") or []
    rec_candidates_by_id = {
        candidate.get("candidate_id"): candidate
        for candidate in rec_candidates
        if isinstance(candidate, dict) and candidate.get("candidate_id")
    }

    review_entries = review_doc.get("review_entries")
    if not isinstance(review_entries, list):
        review_entries = []
    entries = [entry for entry in review_entries if isinstance(entry, dict)]

    # Check 6: every review entry candidate_id exists in rec-002.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            errors.append(f"review_entries[{index}] is not an object")
            continue
        candidate_id = entry.get("candidate_id")
        if candidate_id not in rec_candidates_by_id:
            errors.append(f"review_entries[{index}] candidate_id {candidate_id!r} not found in rec-002.json")
    check("every review entry candidate_id exists in rec-002", errors)

    # Check 7: every rec-002 candidate has exactly one review entry.
    errors = []
    entry_ids = [entry.get("candidate_id") for entry in entries]
    for candidate_id in rec_candidates_by_id:
        count = entry_ids.count(candidate_id)
        if count == 0:
            errors.append(f"rec-002 candidate {candidate_id!r} has no review entry")
        elif count > 1:
            errors.append(f"rec-002 candidate {candidate_id!r} has {count} review entries, expected exactly one")
    check("every rec-002 candidate has exactly one review entry", errors)

    # Check 8: no unknown candidate IDs / mismatched recommendation_set_id in review entries.
    errors = []
    known_ids = set(rec_candidates_by_id)
    seen_ids = set()
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        candidate_id = entry.get("candidate_id")
        if candidate_id not in known_ids:
            errors.append(f"review_entries[{index}] references unknown candidate_id {candidate_id!r}")
        if candidate_id in seen_ids:
            errors.append(f"review_entries[{index}] duplicates candidate_id {candidate_id!r}")
        seen_ids.add(candidate_id)
        if entry.get("recommendation_set_id") != "rec-002":
            errors.append(
                f"review_entries[{index}] recommendation_set_id "
                f"{entry.get('recommendation_set_id')!r} must be 'rec-002'"
            )
    check("no unknown candidate IDs appear in review entries", errors)

    # Check 9: every review entry has all required fields.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        for field in REQUIRED_REVIEW_ENTRY_FIELDS:
            if field not in entry:
                errors.append(f"review_entries[{index}] missing required field {field!r}")
    check("every review entry has all required fields", errors)

    # Check 10: every review_status is an allowed Product Owner review state.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("review_status") not in ALLOWED_ENTRY_STATUSES:
            errors.append(
                f"{entry_label(index, entry)} review_status {entry.get('review_status')!r} "
                f"is not one of {sorted(ALLOWED_ENTRY_STATUSES)}"
            )
    check("every review_status is an allowed Product Owner review state", errors)

    entry_statuses = [entry.get("review_status") for entry in entries]
    non_neutral_present = any(status in NON_NEUTRAL_ENTRY_STATUSES for status in entry_statuses)
    under_review_present = any(status == "under_review" for status in entry_statuses)
    top_level_status = review_doc.get("review_status")

    # Check 11: top-level review_status is consistent with entry review states.
    errors = []
    if top_level_status not in ALLOWED_TOP_LEVEL_STATUSES:
        errors.append(
            f"top-level review_status {top_level_status!r} is not one of "
            f"{sorted(ALLOWED_TOP_LEVEL_STATUSES)}"
        )
    else:
        if top_level_status in SCAFFOLD_TOP_LEVEL_STATUSES and non_neutral_present:
            errors.append(
                f"top-level review_status {top_level_status!r} is a scaffold state but "
                "non-neutral entry review states have been recorded; use 'in_progress' or 'completed'"
            )
        if top_level_status == "completed" and under_review_present:
            errors.append(
                "top-level review_status 'completed' requires that no entry remain 'under_review'"
            )
    check("top-level review_status is consistent with entry review states", errors)

    # Check 12: progressed entries record reviewed_at, rationale, and a resolved testing_required.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        status = entry.get("review_status")
        reviewed_at = entry.get("reviewed_at")
        if status in NON_NEUTRAL_ENTRY_STATUSES:
            if not isinstance(reviewed_at, str) or not ISO_DATE_PATTERN.fullmatch(reviewed_at):
                errors.append(
                    f"{entry_label(index, entry)} is {status!r} but reviewed_at "
                    f"{reviewed_at!r} is not an ISO 8601 date"
                )
            if not str(entry.get("rationale") or "").strip():
                errors.append(f"{entry_label(index, entry)} is {status!r} but rationale is empty")
            if entry.get("testing_required") is None:
                errors.append(
                    f"{entry_label(index, entry)} is {status!r} but testing_required is unresolved (null)"
                )
        else:
            if reviewed_at is not None and (
                not isinstance(reviewed_at, str) or not ISO_DATE_PATTERN.fullmatch(reviewed_at)
            ):
                errors.append(
                    f"{entry_label(index, entry)} reviewed_at {reviewed_at!r} is not null or an ISO 8601 date"
                )
    check("progressed entries record reviewed_at, rationale, and resolved testing_required", errors)

    # Check 13: needs_testing entries require testing evidence before proceeding.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("review_status") != "needs_testing":
            continue
        if entry.get("testing_required") is not True:
            errors.append(f"{entry_label(index, entry)} is 'needs_testing' but testing_required is not true")
        if not str(entry.get("testing_notes") or "").strip():
            errors.append(f"{entry_label(index, entry)} is 'needs_testing' but testing_notes is empty")
    check("needs_testing entries require testing evidence", errors)

    # Check 14: accepted_for_decision and needs_testing do not change the deck.
    # Entry-level guard: even a Product-Owner-progressed entry still requires
    # the decision-log and new-deck-version path, and carries no decision fields.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        status = entry.get("review_status")
        if status in {"accepted_for_decision", "needs_testing"}:
            candidate = rec_candidates_by_id.get(entry.get("candidate_id")) or {}
            if candidate.get("decision_log_required") is True and entry.get("decision_log_required") is not True:
                errors.append(
                    f"{entry_label(index, entry)} is {status!r} but decision_log_required is not true"
                )
            if (
                candidate.get("creates_new_deck_version") is True
                and entry.get("creates_new_deck_version_if_accepted") is not True
            ):
                errors.append(
                    f"{entry_label(index, entry)} is {status!r} but "
                    "creates_new_deck_version_if_accepted is not true"
                )
    check("accepted_for_decision and needs_testing do not change the deck", errors)

    # Check 15: explicit boundary flags remain review-only.
    errors = []
    boundary = review_doc.get("explicit_boundary") or {}
    if boundary.get("deck_change_authorized") is not False:
        errors.append("explicit_boundary.deck_change_authorized must be false")
    if boundary.get("decision_log_created") is not False:
        errors.append("explicit_boundary.decision_log_created must be false")
    if boundary.get("new_deck_version_created") is not False:
        errors.append("explicit_boundary.new_deck_version_created must be false")
    conclusive_present = any(status in CONCLUSIVE_ENTRY_STATUSES for status in entry_statuses)
    if boundary.get("accepted_or_rejected_or_deferred") is not conclusive_present:
        errors.append(
            "explicit_boundary.accepted_or_rejected_or_deferred must be "
            f"{conclusive_present} to match the recorded entry states"
        )
    check("explicit boundary flags remain review-only", errors)

    # Check 16: explicit boundary says no deck change is authorized.
    errors = []
    boundary_text = json.dumps(boundary, ensure_ascii=False).lower()
    if "no deck change is authorized" not in boundary_text:
        errors.append("explicit_boundary statement does not say 'no deck change is authorized'")
    check("explicit boundary says no deck change is authorized", errors)

    # Check 17/18: decision_log_required and creates_new_deck_version_if_accepted mirror
    # the underlying candidate's own boundary fields for deck-altering candidates.
    errors_17 = []
    errors_18 = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        candidate = rec_candidates_by_id.get(entry.get("candidate_id"))
        if not candidate:
            continue
        if candidate.get("decision_log_required") is True:
            if entry.get("decision_log_required") is not True:
                errors_17.append(
                    f"{entry_label(index, entry)} decision_log_required "
                    "must be true because the candidate itself requires a decision log"
                )
        if candidate.get("creates_new_deck_version") is True:
            if entry.get("creates_new_deck_version_if_accepted") is not True:
                errors_18.append(
                    f"{entry_label(index, entry)} "
                    "creates_new_deck_version_if_accepted must be true because the candidate "
                    "itself creates a new deck version if accepted"
                )
    check("decision_log_required is true for candidates that could lead to deck changes", errors_17)
    check("creates_new_deck_version_if_accepted is true for candidates that could lead to deck changes", errors_18)

    # Check 19: decision files are placeholders, non-authorizing scaffolds, or
    # non-authorizing designs only. Empty placeholder decision files are allowed.
    # Populated decision files are allowed only as decision scaffolds (pending
    # deck-change design, explicitly non-authorizing and non-implemented, with no
    # outgoing cuts chosen, traceable to an accepted_for_decision rec-002
    # candidate) or as pre-version deck-change design artifacts (explicitly
    # non-authorizing and non-implemented proposals awaiting Product Owner
    # approval, traceable to existing decision scaffolds).
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        for field in sorted(DECISION_LAYER_ENTRY_FIELDS & set(entry)):
            errors.append(
                f"{entry_label(index, entry)} carries decision-layer field {field!r}; "
                "decisions are recorded in decisions/, not in review entries"
            )
    accepted_candidate_ids = {
        entry.get("candidate_id")
        for entry in entries
        if entry.get("review_status") == "accepted_for_decision"
    }
    needs_testing_candidate_ids = {
        entry.get("candidate_id")
        for entry in entries
        if entry.get("review_status") == "needs_testing"
    }
    # Per decision_status, the fields a decision record must carry. Scaffolds
    # are non-authorizing; implemented decisions record a completed
    # decision -> design -> approval -> version chain for v1.1.
    decision_state_required_values = {
        "pending_deck_change_design": [
            ("decision_type", "candidate_accepted_for_decision_path"),
            ("deck_change_authorized", False),
            ("deck_change_implemented", False),
            ("creates_new_deck_version", False),
            ("target_deck_version", None),
            ("proposed_outgoing_cards", []),
            ("required_next_step", "deck_change_design_before_v1.1"),
        ],
        "implemented_as_v1.1": [
            ("decision_type", "candidate_accepted_for_decision_path"),
            ("deck_change_authorized", True),
            ("deck_change_implemented", True),
            ("creates_new_deck_version", True),
            ("target_deck_version", "v1.1"),
            ("implemented_in_version", "v1.1"),
            ("implementation_source", "deck-change-design-v1.1"),
            ("required_next_step", "post_implementation_validation_or_report"),
        ],
    }
    design_common_required_values = [
        ("design_type", "pre_version_deck_change_design"),
    ]
    # Per design_status, the fields the design must carry. Proposed designs
    # await Product Owner review; approved designs record the approval but
    # still implement nothing; implemented designs record that the approved
    # change became DeckVersion v1.1.
    design_state_required_values = {
        "proposed_for_product_owner_review": [
            ("deck_change_authorized", False),
            ("deck_change_implemented", False),
            ("creates_new_deck_version", False),
            ("product_owner_review_required", True),
            ("required_next_step", "product_owner_approval_before_v1.1"),
        ],
        "product_owner_approved": [
            ("deck_change_authorized", False),
            ("deck_change_implemented", False),
            ("creates_new_deck_version", False),
            ("product_owner_approved", True),
            ("product_owner_approval_required", False),
            ("required_next_step", "create_deck_version_v1.1"),
        ],
        "implemented_as_v1.1": [
            ("deck_change_authorized", True),
            ("deck_change_implemented", True),
            ("creates_new_deck_version", True),
            ("product_owner_approved", True),
            ("implemented_version_id", "v1.1"),
            ("required_next_step", "post_implementation_validation_or_report"),
        ],
    }
    for decision_path in sorted(DECISIONS_DIR.glob("*.json")):
        try:
            decision_doc = load_json(decision_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{decision_path} is not valid JSON: {exc}")
            continue
        if decision_doc == {}:
            continue
        rel_path = decision_path.relative_to(REPO_ROOT)
        if decision_doc.get("design_type") == "pre_version_deck_change_design":
            # Non-authorizing pre-version design artifact (proposed or approved).
            design_status = decision_doc.get("design_status")
            if design_status not in design_state_required_values:
                errors.append(
                    f"{rel_path} design_status {design_status!r} is not one of "
                    f"{sorted(design_state_required_values)}"
                )
                design_required_values = design_common_required_values
            else:
                design_required_values = (
                    design_common_required_values + design_state_required_values[design_status]
                )
            for field, expected in design_required_values:
                if field not in decision_doc:
                    errors.append(f"{rel_path} design is missing required field {field!r}")
                elif decision_doc.get(field) != expected:
                    errors.append(
                        f"{rel_path} design field {field!r} must be {expected!r}, "
                        f"found {decision_doc.get(field)!r}"
                    )
            design_boundary = decision_doc.get("explicit_boundary")
            boundary_text = (
                json.dumps(design_boundary, ensure_ascii=False).lower()
                if isinstance(design_boundary, dict)
                else ""
            )
            if not isinstance(design_boundary, dict):
                errors.append(f"{rel_path} design is missing an explicit_boundary object")
            elif design_status == "product_owner_approved":
                if "approv" not in boundary_text or "not implemented" not in boundary_text:
                    errors.append(
                        f"{rel_path} explicit_boundary must state the design is approved "
                        "but not implemented"
                    )
            elif design_status == "implemented_as_v1.1":
                if "implemented" not in boundary_text or "v1.1" not in boundary_text:
                    errors.append(
                        f"{rel_path} explicit_boundary must state the design was "
                        "implemented as v1.1"
                    )
            elif "no deck change is authorized" not in boundary_text:
                errors.append(
                    f"{rel_path} explicit_boundary does not say 'no deck change is authorized'"
                )
            source_decision_ids = decision_doc.get("source_decision_ids")
            if not isinstance(source_decision_ids, list) or not source_decision_ids:
                errors.append(f"{rel_path} design must list its source_decision_ids")
            else:
                for source_decision_id in source_decision_ids:
                    if not (DECISIONS_DIR / f"{source_decision_id}.json").is_file():
                        errors.append(
                            f"{rel_path} design references missing decision file "
                            f"{source_decision_id!r}"
                        )
            continue
        decision_status = decision_doc.get("decision_status")
        if decision_status not in decision_state_required_values:
            errors.append(
                f"{rel_path} decision_status {decision_status!r} is not one of "
                f"{sorted(decision_state_required_values)}"
            )
            decision_required_values = []
        else:
            decision_required_values = decision_state_required_values[decision_status]
        for field, expected in decision_required_values:
            if field not in decision_doc:
                errors.append(f"{rel_path} decision is missing required field {field!r}")
            elif decision_doc.get(field) != expected:
                errors.append(
                    f"{rel_path} decision field {field!r} must be {expected!r}, "
                    f"found {decision_doc.get(field)!r}"
                )
        decision_boundary = decision_doc.get("explicit_boundary")
        decision_boundary_text = (
            json.dumps(decision_boundary, ensure_ascii=False).lower()
            if isinstance(decision_boundary, dict)
            else ""
        )
        if not isinstance(decision_boundary, dict):
            errors.append(f"{rel_path} decision is missing an explicit_boundary object")
        elif decision_status == "implemented_as_v1.1":
            if "implemented" not in decision_boundary_text or "v1.1" not in decision_boundary_text:
                errors.append(
                    f"{rel_path} explicit_boundary must state the decision was "
                    "implemented as v1.1"
                )
        elif "no deck change is authorized" not in decision_boundary_text:
            errors.append(
                f"{rel_path} explicit_boundary does not say 'no deck change is authorized'"
            )
        source_candidate_id = decision_doc.get("source_candidate_id")
        if source_candidate_id in needs_testing_candidate_ids:
            errors.append(
                f"{rel_path} references {source_candidate_id!r}, which is needs_testing; "
                "needs_testing candidates may not have decision scaffolds"
            )
        elif source_candidate_id not in accepted_candidate_ids:
            errors.append(
                f"{rel_path} references {source_candidate_id!r}, which is not an "
                "accepted_for_decision candidate in review-rec-002"
            )
    check("decision files are placeholders, valid scaffolds/designs, or implemented v1.1 records", errors)

    # Check 20: deck versions beyond v1.0 exist only as implemented-design outcomes.
    # An empty placeholder is always allowed. A populated version file is allowed
    # only when an implemented design artifact records it as its
    # implemented_version_id, and the version document is structurally sound
    # (correct version_id, parent v1.0, implemented status, 1 commander,
    # 99 main-deck entries, 7 sideboard entries).
    errors = []
    implemented_design_version_ids = set()
    for decision_path in sorted(DECISIONS_DIR.glob("*.json")):
        try:
            doc = load_json(decision_path)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(doc, dict)
            and doc.get("design_type") == "pre_version_deck_change_design"
            and doc.get("design_status") == "implemented_as_v1.1"
            and doc.get("implemented_version_id")
        ):
            implemented_design_version_ids.add(doc.get("implemented_version_id"))
    for version_path in sorted(VERSIONS_DIR.glob("*.json")):
        if version_path.name == "v1.0.json":
            continue
        try:
            version_doc = load_json(version_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{version_path} is not valid JSON: {exc}")
            continue
        if version_doc == {}:
            continue
        rel_path = version_path.relative_to(REPO_ROOT)
        version_id = version_path.stem
        if version_id not in implemented_design_version_ids:
            errors.append(
                f"{rel_path} is populated but no implemented design artifact records "
                f"{version_id!r} as its implemented_version_id"
            )
            continue
        if version_doc.get("version_id") != version_id:
            errors.append(f"{rel_path} version_id must be {version_id!r}")
        if version_doc.get("parent_version_id") != "v1.0":
            errors.append(f"{rel_path} parent_version_id must be 'v1.0'")
        if version_doc.get("version_status") != "implemented":
            errors.append(f"{rel_path} version_status must be 'implemented'")
        if not isinstance(version_doc.get("commander"), dict) or not version_doc["commander"].get("name"):
            errors.append(f"{rel_path} must record exactly one commander entry")
        main_deck = version_doc.get("main_deck")
        if not isinstance(main_deck, list) or len(main_deck) != 99:
            errors.append(
                f"{rel_path} main_deck must contain exactly 99 entries, found "
                f"{len(main_deck) if isinstance(main_deck, list) else 'non-list'}"
            )
        sideboard = version_doc.get("sideboard")
        if not isinstance(sideboard, list) or len(sideboard) != 7:
            errors.append(
                f"{rel_path} sideboard must contain exactly 7 entries, found "
                f"{len(sideboard) if isinstance(sideboard, list) else 'non-list'}"
            )
    check("deck versions beyond v1.0 exist only as implemented-design outcomes", errors)

    # Check 21: rec-002 candidate records remain unmodified by review.
    errors = []
    for candidate_id, candidate in rec_candidates_by_id.items():
        if candidate.get("status") != "proposed":
            errors.append(f"rec-002 candidate {candidate_id!r} status is no longer 'proposed'")
        if candidate.get("is_actionable") is not False:
            errors.append(f"rec-002 candidate {candidate_id!r} is_actionable is no longer false")
        if candidate.get("user_decision") is not None:
            errors.append(f"rec-002 candidate {candidate_id!r} user_decision is no longer null")
        if candidate.get("decision_id") is not None:
            errors.append(f"rec-002 candidate {candidate_id!r} decision_id is no longer null")
    check("rec-002 candidate records remain unmodified by review", errors)

    # Check 22: review artifact does not modify rec-002 candidates (this validator is read-only).
    errors = []
    rec_mtime_before = rec_json_path.stat().st_mtime
    rec_bytes_before = rec_json_path.read_bytes()
    review_bytes_before = REVIEW_JSON_PATH.read_bytes() if REVIEW_JSON_PATH.is_file() else None
    # Re-read after all prior checks to confirm nothing in this run touched the files.
    if rec_json_path.read_bytes() != rec_bytes_before or rec_json_path.stat().st_mtime != rec_mtime_before:
        errors.append(f"{rec_json_path} was modified during validation")
    if REVIEW_JSON_PATH.is_file() and (
        REVIEW_JSON_PATH.read_bytes() != review_bytes_before
        or REVIEW_JSON_PATH.stat().st_mtime != review_mtime_before
    ):
        errors.append(f"{REVIEW_JSON_PATH} was modified during validation")
    check("review artifact does not modify rec-002 candidates", errors)

    # Check 23: review markdown states the no-deck-change boundary.
    errors = []
    md_lower = review_md_text.lower()
    if "does not change the deck" not in md_lower and "no deck change is authorized" not in md_lower:
        errors.append("review-rec-002.md does not state the no-deck-change boundary")
    check("review markdown states the no-deck-change boundary", errors)

    # Check 24: review markdown states Product Owner review.
    errors = []
    if "product owner" not in md_lower:
        errors.append("review-rec-002.md does not mention Product Owner review")
    check("review markdown states Product Owner review", errors)

    # Check 25: review markdown mentions every candidate ID from rec-002.
    errors = []
    for candidate_id in rec_candidates_by_id:
        if candidate_id not in review_md_text:
            errors.append(f"review-rec-002.md does not mention candidate_id {candidate_id!r}")
    check("review markdown mentions every candidate ID from rec-002", errors)

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
        print(f"FAIL: {failed} of {len(checks)} recommendation review checks failed.")
        return 1
    print(f"PASS: all {len(checks)} recommendation review validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
