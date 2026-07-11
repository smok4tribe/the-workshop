#!/usr/bin/env python3
"""Validate Product Owner recommendation-review artifacts only."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ID = os.environ.get("WORKSHOP_PROJECT_ID", "the-myr-singularity")
PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / PROJECT_ID
RECOMMENDATIONS_DIR = PROJECT_DIR / "recommendations"
REVIEW_SCHEMA_PATH = RECOMMENDATIONS_DIR / "review_schema.json"
REVIEW_JSON_PATH = Path(
    os.environ.get(
        "WORKSHOP_REVIEW_JSON",
        RECOMMENDATIONS_DIR / "review-rec-002.json",
    )
)
REVIEW_MD_PATH = Path(
    os.environ.get(
        "WORKSHOP_REVIEW_MD",
        REVIEW_JSON_PATH.with_suffix(".md"),
    )
)

REQUIRED_ENTRY_FIELDS = {
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
}
DECISION_LAYER_FIELDS = {
    "decision_id",
    "user_decision",
    "incoming_cards",
    "outgoing_cards",
    "implemented_in_version",
    "implementation_source",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_iso8601(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


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
        print(f"FAIL: {failed} of {len(checks)} recommendation review checks failed.")
        return 1
    print(f"PASS: all {len(checks)} recommendation review validation checks passed.")
    return 0


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    errors = []
    try:
        schema = load_json(REVIEW_SCHEMA_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        schema = {}
        errors.append(f"review schema cannot be loaded: {exc}")
    check("review schema parses as JSON", errors)

    review_bytes_before = None
    errors = []
    try:
        review_bytes_before = REVIEW_JSON_PATH.read_bytes()
        review = json.loads(review_bytes_before.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        review = {}
        errors.append(f"review artifact cannot be loaded: {exc}")
    check("review artifact parses as UTF-8 JSON", errors)
    if errors:
        return report(checks)

    errors = []
    review_md_text = ""
    try:
        review_md_text = REVIEW_MD_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"review Markdown cannot be loaded: {exc}")
    check("review Markdown exists", errors)

    source_ref = review.get("source_recommendation_file")
    source_path = REPO_ROOT / source_ref if source_ref else None
    rec_bytes_before = None
    errors = []
    try:
        rec_bytes_before = source_path.read_bytes() if source_path else None
        recommendation = json.loads(rec_bytes_before.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
        recommendation = {}
        errors.append(f"source recommendation cannot be loaded: {exc}")
    recommendation_id = review.get("recommendation_set_id")
    if recommendation.get("recommendation_set_id") != recommendation_id:
        errors.append("review recommendation_set_id does not match its source recommendation")
    if source_path and source_path.stem != recommendation_id:
        errors.append("source recommendation filename does not match recommendation_set_id")
    check("review source recommendation resolves", errors)

    candidates = {
        item.get("candidate_id"): item
        for item in recommendation.get("candidates", [])
        if isinstance(item, dict) and item.get("candidate_id")
    }
    entries = review.get("review_entries")
    entries = entries if isinstance(entries, list) else []

    errors = []
    counts = Counter(
        item.get("candidate_id") for item in entries if isinstance(item, dict) and item.get("candidate_id")
    )
    for candidate_id in candidates:
        if counts[candidate_id] != 1:
            errors.append(
                f"candidate {candidate_id!r} has {counts[candidate_id]} review entries, expected exactly one"
            )
    unknown = set(counts) - set(candidates)
    if unknown:
        errors.append(f"review contains unknown candidate IDs: {sorted(unknown)}")
    check("recommendation candidates and review entries are one-to-one", errors)

    errors = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"review_entries[{index}] is not an object")
            continue
        missing = REQUIRED_ENTRY_FIELDS - set(entry)
        if missing:
            errors.append(f"review_entries[{index}] is missing fields {sorted(missing)}")
        if entry.get("recommendation_set_id") != recommendation_id:
            errors.append(f"review_entries[{index}] has the wrong recommendation_set_id")
        forbidden = DECISION_LAYER_FIELDS & set(entry)
        if forbidden:
            errors.append(
                f"review entry {entry.get('candidate_id')!r} carries decision-layer fields {sorted(forbidden)}"
            )
    check("review entries contain only required review-layer fields", errors)

    allowed_statuses = set(schema.get("allowed_review_statuses") or [])
    errors = []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("review_status") not in allowed_statuses:
            errors.append(
                f"candidate {entry.get('candidate_id')!r} has unsupported review status "
                f"{entry.get('review_status')!r}"
            )
    check("review statuses use the controlled vocabulary", errors)

    statuses = [entry.get("review_status") for entry in entries if isinstance(entry, dict)]
    top_status = review.get("review_status")
    errors = []
    if statuses and all(status == "under_review" for status in statuses):
        if top_status not in {"not_started", "pending_product_owner_review"}:
            errors.append("all-under-review entries require a pending top-level review_status")
    else:
        if top_status not in {"in_progress", "completed"}:
            errors.append("progressed entries require top-level review_status in_progress or completed")
        if top_status == "completed" and "under_review" in statuses:
            errors.append("completed review cannot contain under_review entries")
    check("top-level review status matches entry progression", errors)

    errors = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("review_status") == "under_review":
            continue
        candidate_id = entry.get("candidate_id")
        if not entry.get("rationale"):
            errors.append(f"{candidate_id} progressed review is missing rationale")
        if not valid_iso8601(entry.get("reviewed_at")):
            errors.append(f"{candidate_id} progressed review has invalid reviewed_at")
        if not isinstance(entry.get("testing_required"), bool):
            errors.append(f"{candidate_id} progressed review must resolve testing_required")
    check("progressed reviews record rationale, timestamp, and testing disposition", errors)

    errors = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("review_status") != "needs_testing":
            continue
        candidate_id = entry.get("candidate_id")
        if entry.get("testing_required") is not True:
            errors.append(f"{candidate_id} needs_testing requires testing_required=true")
        if not entry.get("testing_notes"):
            errors.append(f"{candidate_id} needs_testing requires testing_notes")
    check("needs-testing reviews include a concrete testing gate", errors)

    errors = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        candidate = candidates.get(entry.get("candidate_id")) or {}
        if entry.get("review_status") in {"accepted_for_decision", "needs_testing"}:
            if candidate.get("decision_log_required") is True and entry.get("decision_log_required") is not True:
                errors.append(f"{entry.get('candidate_id')} review bypasses its decision-log requirement")
            if candidate.get("creates_new_deck_version") is True:
                if entry.get("creates_new_deck_version_if_accepted") is not True:
                    errors.append(
                        f"{entry.get('candidate_id')} review bypasses its new-version requirement"
                    )
    check("review transitions preserve decision and DeckVersion gates", errors)

    boundary = review.get("explicit_boundary")
    boundary_text = json.dumps(boundary, ensure_ascii=False).lower() if isinstance(boundary, dict) else ""
    errors = []
    if not isinstance(boundary, dict):
        errors.append("review artifact is missing explicit_boundary")
    else:
        for field in ("deck_change_authorized", "decision_log_created", "new_deck_version_created"):
            if boundary.get(field) is not False:
                errors.append(f"review boundary requires {field}=false")
        if "no deck change is authorized" not in boundary_text:
            errors.append("review boundary does not state that no deck change is authorized")
        expected_progressed = any(
            status in {"accepted_for_decision", "rejected", "deferred"} for status in statuses
        )
        if boundary.get("accepted_or_rejected_or_deferred") is not expected_progressed:
            errors.append("review boundary progression flag does not match entry states")
    check("review boundary remains non-authorizing and internally consistent", errors)

    errors = []
    for candidate_id, candidate in candidates.items():
        if candidate.get("status") != "proposed":
            errors.append(f"{candidate_id} recommendation status changed from proposed")
        if candidate.get("is_actionable") is not False:
            errors.append(f"{candidate_id} became actionable in the recommendation artifact")
        if candidate.get("user_decision") is not None or candidate.get("decision_id") is not None:
            errors.append(f"{candidate_id} recommendation record was mutated by review")
    check("source recommendation candidates remain proposed and non-actionable", errors)

    errors = []
    md_lower = review_md_text.lower()
    if "product owner" not in md_lower:
        errors.append("review Markdown does not identify Product Owner review")
    if "does not change the deck" not in md_lower and "no deck change is authorized" not in md_lower:
        errors.append("review Markdown does not state the no-deck-change boundary")
    for candidate_id in candidates:
        if candidate_id not in review_md_text:
            errors.append(f"review Markdown does not mention {candidate_id}")
    check("review Markdown reflects scope, boundary, and all candidates", errors)

    errors = []
    if review_bytes_before is not None and REVIEW_JSON_PATH.read_bytes() != review_bytes_before:
        errors.append("review validator modified the review artifact")
    if rec_bytes_before is not None and source_path.read_bytes() != rec_bytes_before:
        errors.append("review validator modified the recommendation artifact")
    check("review validation is read-only", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
