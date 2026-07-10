#!/usr/bin/env python3
"""Product Owner Recommendation Review validation checks for Sprint 1 (Task 19).

Validates the Product Owner review scaffold layer:

- workshop/projects/the-myr-singularity/recommendations/review_schema.json
  (the review artifact contract)
- workshop/projects/the-myr-singularity/recommendations/review-rec-002.json
  and its companion review-rec-002.md (the first review artifact, scoped to
  rec-002)

This validator guards the boundary between three layers:

* Recommendation candidates (rec-002.json) are generated, proposed,
  non-actionable artifacts.
* Product Owner review (review-rec-002.json) records human review intent
  about those candidates without editing them, without creating a decision,
  and without changing the deck.
* Decision logs and deck versions are separate, later artifacts that this
  validator does not create or touch.

Standard library only. No external dependencies.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
RECOMMENDATIONS_DIR = PROJECT_DIR / "recommendations"

REVIEW_SCHEMA_PATH = RECOMMENDATIONS_DIR / "review_schema.json"
REVIEW_JSON_PATH = RECOMMENDATIONS_DIR / "review-rec-002.json"
REVIEW_MD_PATH = RECOMMENDATIONS_DIR / "review-rec-002.md"
DEFAULT_REC_JSON_PATH = RECOMMENDATIONS_DIR / "rec-002.json"

NON_NEUTRAL_REVIEW_STATUSES = {
    "accepted_for_decision",
    "rejected",
    "deferred",
    "needs_testing",
}

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


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


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
    entry_ids = [entry.get("candidate_id") for entry in review_entries if isinstance(entry, dict)]
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

    # Required fields present on every entry (supports later checks).
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        for field in REQUIRED_REVIEW_ENTRY_FIELDS:
            if field not in entry:
                errors.append(f"review_entries[{index}] missing required field {field!r}")
    check("every review entry has all required fields", errors)

    # Check 9: every initial review entry has review_status == 'under_review'.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("review_status") != "under_review":
            errors.append(
                f"review_entries[{index}] ({entry.get('candidate_id')!r}) review_status "
                f"{entry.get('review_status')!r} is not 'under_review'"
            )
    check("every initial review entry has review_status 'under_review'", errors)

    # Check 10: no entry is accepted_for_decision, rejected, deferred, or needs_testing yet.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("review_status") in NON_NEUTRAL_REVIEW_STATUSES:
            errors.append(
                f"review_entries[{index}] ({entry.get('candidate_id')!r}) has non-neutral "
                f"review_status {entry.get('review_status')!r}"
            )
    check("no entry is accepted_for_decision, rejected, deferred, or needs_testing yet", errors)

    # Check 11: no reviewed_at value is set yet.
    errors = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("reviewed_at") is not None:
            errors.append(
                f"review_entries[{index}] ({entry.get('candidate_id')!r}) reviewed_at "
                f"must be null, found {entry.get('reviewed_at')!r}"
            )
    check("no reviewed_at value is set yet", errors)

    # Check 12: no user decision / deck decision is created.
    errors = []
    boundary = review_doc.get("explicit_boundary") or {}
    if boundary.get("accepted_or_rejected_or_deferred") is not False:
        errors.append("explicit_boundary.accepted_or_rejected_or_deferred must be false")
    if boundary.get("decision_log_created") is not False:
        errors.append("explicit_boundary.decision_log_created must be false")
    if boundary.get("new_deck_version_created") is not False:
        errors.append("explicit_boundary.new_deck_version_created must be false")
    if review_doc.get("review_status") not in {"not_started", "pending_product_owner_review"}:
        errors.append(
            f"top-level review_status {review_doc.get('review_status')!r} must be "
            "'not_started' or 'pending_product_owner_review'"
        )
    check("no user decision / deck decision is created", errors)

    # Check 13: explicit boundary says no deck change is authorized.
    errors = []
    if boundary.get("deck_change_authorized") is not False:
        errors.append("explicit_boundary.deck_change_authorized must be false")
    boundary_text = json.dumps(boundary, ensure_ascii=False).lower()
    if "no deck change is authorized" not in boundary_text:
        errors.append("explicit_boundary statement does not say 'no deck change is authorized'")
    check("explicit boundary says no deck change is authorized", errors)

    # Check 14/15: decision_log_required and creates_new_deck_version_if_accepted mirror
    # the underlying candidate's own boundary fields for deck-altering candidates.
    errors_14 = []
    errors_15 = []
    for index, entry in enumerate(review_entries):
        if not isinstance(entry, dict):
            continue
        candidate = rec_candidates_by_id.get(entry.get("candidate_id"))
        if not candidate:
            continue
        if candidate.get("decision_log_required") is True:
            if entry.get("decision_log_required") is not True:
                errors_14.append(
                    f"review_entries[{index}] ({entry.get('candidate_id')!r}) decision_log_required "
                    "must be true because the candidate itself requires a decision log"
                )
        if candidate.get("creates_new_deck_version") is True:
            if entry.get("creates_new_deck_version_if_accepted") is not True:
                errors_15.append(
                    f"review_entries[{index}] ({entry.get('candidate_id')!r}) "
                    "creates_new_deck_version_if_accepted must be true because the candidate "
                    "itself creates a new deck version if accepted"
                )
    check("decision_log_required is true for candidates that could lead to deck changes", errors_14)
    check("creates_new_deck_version_if_accepted is true for candidates that could lead to deck changes", errors_15)

    # Check 16: review artifact does not modify rec-002 candidates (this validator is read-only).
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

    # Check 17: review markdown states the no-deck-change boundary.
    errors = []
    md_lower = review_md_text.lower()
    if "does not change the deck" not in md_lower and "no deck change is authorized" not in md_lower:
        errors.append("review-rec-002.md does not state the no-deck-change boundary")
    check("review markdown states the no-deck-change boundary", errors)

    # Check 18: review markdown states Product Owner review.
    errors = []
    if "product owner" not in md_lower:
        errors.append("review-rec-002.md does not mention Product Owner review")
    check("review markdown states Product Owner review", errors)

    # Check 19: review markdown mentions every candidate ID from rec-002.
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
