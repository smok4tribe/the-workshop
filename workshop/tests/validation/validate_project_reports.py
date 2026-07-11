#!/usr/bin/env python3
"""Validate structured project reports and their deterministic Markdown renderings."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity"
REPORTS_DIR = PROJECT_DIR / "reports"
VERSIONS_DIR = PROJECT_DIR / "versions"
RENDERER_PATH = REPO_ROOT / "workshop" / "scripts" / "render_project_report.py"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_name(value):
    return " ".join(str(value).casefold().split())


def counters(version, section):
    if section == "commander":
        entries = [version.get("commander")]
    else:
        entries = version.get(section, [])
    counter = Counter()
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") and isinstance(entry.get("quantity"), int):
            counter[normalize_name(entry["name"])] += entry["quantity"]
    return counter


def renderer():
    spec = importlib.util.spec_from_file_location("project_report_renderer", RENDERER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report_delta_counter(items):
    result = {"commander": Counter(), "main_deck": Counter(), "sideboard": Counter()}
    errors = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"delta item {index} must be an object")
            continue
        zone = item.get("zone")
        if zone not in result:
            errors.append(f"delta item {index} has unsupported zone {zone!r}")
            continue
        if not item.get("card_name") or not isinstance(item.get("quantity"), int):
            errors.append(f"delta item {index} is missing card_name or integer quantity")
            continue
        result[zone][normalize_name(item["card_name"])] += item["quantity"]
    return result, errors


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


def main():
    checks = []
    def check(description, errors):
        checks.append((description, errors))

    report_paths = sorted(REPORTS_DIR.glob("project_report_v*.json"))
    errors = []
    if not report_paths:
        errors.append("no structured project reports found")
    check("structured project report files exist", errors)

    reports = []
    errors = []
    for path in report_paths:
        try:
            reports.append((path, load_json(path)))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name} is invalid JSON: {exc}")
    check("structured project reports parse", errors)
    if errors:
        return report(checks)

    report_ids = [doc.get("report_id") for _, doc in reports]
    check("report IDs are unique", [f"duplicate report_id {value!r}" for value in set(report_ids) if report_ids.count(value) > 1])

    project = load_json(PROJECT_DIR / "project.json")
    review = load_json(PROJECT_DIR / "recommendations" / "review-rec-002.json")
    review_statuses = {entry.get("candidate_id"): entry.get("review_status") for entry in review.get("review_entries", [])}

    for path, doc in reports:
        label = doc.get("report_id") or path.stem
        markdown_path = path.with_suffix(".md")
        errors = []
        for field in ("project_id", "baseline_deck_version_id", "resulting_deck_version_id", "report_status", "source_references", "version_delta", "evidence_status", "candidate_dispositions"):
            if field not in doc:
                errors.append(f"{label} is missing {field!r}")
        if doc.get("project_id") != project.get("id"):
            errors.append(f"{label} project_id does not resolve")
        baseline_id = doc.get("baseline_deck_version_id")
        resulting_id = doc.get("resulting_deck_version_id")
        baseline_path = VERSIONS_DIR / f"{baseline_id}.json"
        resulting_path = VERSIONS_DIR / f"{resulting_id}.json"
        if not baseline_path.is_file():
            errors.append(f"baseline DeckVersion {baseline_id!r} does not resolve")
        if not resulting_path.is_file():
            errors.append(f"resulting DeckVersion {resulting_id!r} does not resolve")
        if baseline_id == resulting_id:
            errors.append("baseline and resulting DeckVersions must differ")
        if resulting_id != project.get("current_version_id"):
            errors.append("resulting DeckVersion is not the project current version")
        check(f"{label} identity and DeckVersion references resolve", errors)
        if errors:
            continue

        baseline = load_json(baseline_path)
        resulting = load_json(resulting_path)
        errors = []
        if resulting.get("parent_version_id") != baseline_id:
            errors.append("resulting DeckVersion parent does not match report baseline")
        sources = doc["source_references"]
        required_sources = {"project", "brief", "baseline_deck_version", "resulting_deck_version", "current_decklist", "baseline_analysis", "recommendation", "product_owner_review", "decisions", "deck_change_design", "design_approval", "card_facts", "functional_knowledge", "candidate_lifecycle_metadata"}
        missing_sources = sorted(required_sources - set(sources))
        if missing_sources:
            errors.append(f"missing required structured sources: {missing_sources}")
        for key, value in sources.items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                source_path = REPO_ROOT / item.get("path", "") if isinstance(item, dict) else None
                if not source_path or not source_path.is_file():
                    errors.append(f"source {key!r} does not exist: {item!r}")
        if errors:
            check(f"{label} structured sources and decision chain are coherent", errors)
            continue
        analysis = load_json(REPO_ROOT / sources["baseline_analysis"]["path"])
        if analysis.get("deck_version_id") != baseline_id:
            errors.append("baseline analysis does not reference report baseline")
        recommendation = load_json(REPO_ROOT / sources["recommendation"]["path"])
        if recommendation.get("recommendation_set_id") != sources["recommendation"].get("id"):
            errors.append("recommendation source ID does not match artifact")
        source_review = load_json(REPO_ROOT / sources["product_owner_review"]["path"])
        if source_review.get("recommendation_set_id") != recommendation.get("recommendation_set_id"):
            errors.append("review source does not match recommendation")
        design = load_json(REPO_ROOT / sources["deck_change_design"]["path"])
        if design.get("implemented_version_id") != resulting_id or design.get("product_owner_approved") is not True:
            errors.append("design approval does not agree with resulting DeckVersion")
        check(f"{label} structured sources and decision chain are coherent", errors)

        errors = []
        actual_added = {zone: counters(resulting, zone) - counters(baseline, zone) for zone in ("commander", "main_deck", "sideboard")}
        actual_removed = {zone: counters(baseline, zone) - counters(resulting, zone) for zone in ("commander", "main_deck", "sideboard")}
        report_added, item_errors = report_delta_counter(doc["version_delta"].get("added", []))
        errors.extend(item_errors)
        report_removed, item_errors = report_delta_counter(doc["version_delta"].get("removed", []))
        errors.extend(item_errors)
        if report_added != actual_added or report_removed != actual_removed:
            errors.append("report version delta does not match the derived parent-child DeckVersion diff")
        if doc["version_delta"].get("commander_unchanged") is not (actual_added["commander"] == actual_removed["commander"] == Counter()):
            errors.append("report commander unchanged claim does not match versions")
        if doc["version_delta"].get("sideboard_unchanged") is not (actual_added["sideboard"] == actual_removed["sideboard"] == Counter()):
            errors.append("report sideboard unchanged claim does not match versions")
        current_text = (REPO_ROOT / sources["current_decklist"]["path"]).read_text(encoding="utf-8")
        if "sideboard:" not in current_text.casefold() or doc["version_delta"].get("current_decklist_matches_resulting_version") is not True:
            errors.append("report current decklist alignment claim is not valid")
        check(f"{label} version delta and deck claims match DeckVersions", errors)

        errors = []
        dispositions = {item.get("candidate_id"): item for item in doc["candidate_dispositions"] if isinstance(item, dict)}
        for candidate_id in ("cand-009", "cand-010"):
            item = dispositions.get(candidate_id)
            if not item or item.get("implementation_status") != "not_implemented" or review_statuses.get(candidate_id) != "needs_testing":
                errors.append(f"{candidate_id} disposition does not preserve needs_testing/non-implemented state")
        for candidate_id in ("cand-007", "cand-008", "cand-011"):
            item = dispositions.get(candidate_id)
            if not item or item.get("implementation_status") != "implemented" or review_statuses.get(candidate_id) != "accepted_for_decision":
                errors.append(f"{candidate_id} disposition does not match accepted implementation state")
        check(f"{label} candidate dispositions match review and implementation state", errors)

        errors = []
        evidence = doc["evidence_status"]
        expected_evidence = {"post_implementation_analysis": "not_run", "post_implementation_simulation": "not_run", "gameplay_validation": "not_recorded", "performance_claim_status": "not_measured"}
        for field, value in expected_evidence.items():
            if evidence.get(field) != value:
                errors.append(f"evidence status {field!r} must be {value!r} without post-implementation evidence")
        if doc.get("report_status") != "implementation_verified_outcomes_not_measured":
            errors.append("report status must not imply measured success")
        check(f"{label} separates verified implementation from unmeasured outcomes", errors)

        errors = []
        if not markdown_path.is_file():
            errors.append(f"{markdown_path.name} does not exist")
        else:
            try:
                expected_markdown = renderer().render_report(doc)
                actual_markdown = markdown_path.read_text(encoding="utf-8")
                if actual_markdown != expected_markdown:
                    errors.append("committed Markdown differs from deterministic renderer output")
                for heading in ("## Executive Summary", "## Exact Version Change", "## What Is Verified", "## What Is Expected but Not Yet Measured", "## Structured Sources"):
                    if heading not in actual_markdown:
                        errors.append(f"committed Markdown is missing heading {heading!r}")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"cannot render Markdown: {exc}")
        check(f"{label} Markdown is complete and matches deterministic rendering", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
