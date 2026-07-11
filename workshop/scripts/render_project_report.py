#!/usr/bin/env python3
"""Render committed Project Report Markdown files from structured JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = (
    REPO_ROOT
    / "workshop"
    / "projects"
    / "the-myr-singularity"
    / "reports"
    / "project_report_v1.1.json"
)
REQUIRED_FIELDS = {
    "report_id",
    "report_version",
    "project_identity",
    "brief_summary",
    "baseline_summary",
    "recommendation_summary",
    "decision_summary",
    "implementation_summary",
    "version_delta",
    "candidate_dispositions",
    "knowledge_alignment",
    "evidence_status",
    "expected_impacts",
    "limitations_and_open_items",
    "next_actions",
    "source_references",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def bullet_lines(items):
    return [f"- {item}" for item in items]


def evidence_value(value):
    if isinstance(value, dict):
        return str(value.get("status", "unknown"))
    return str(value)


def render_delta(items):
    return [
        f"- {item['quantity']} {item['card_name']} "
        f"({item['zone']}; {item['source_decision_id']})"
        for item in items
    ]


def render_dispositions(dispositions, status):
    matching = [item for item in dispositions if item.get("review_status") == status]
    if not matching:
        return ["- None."]
    return [
        f"- {item['candidate_name']}: {item['review_status']}; "
        f"{item['implementation_status']}."
        for item in matching
    ]


def render_sources(sources):
    lines = []
    for key in sorted(sources):
        value = sources[key]
        values = value if isinstance(value, list) else [value]
        paths = [item.get("path", "<missing path>") for item in values if isinstance(item, dict)]
        lines.append(f"- {key}: {', '.join(paths)}")
    return lines


def render_report(report):
    missing = sorted(REQUIRED_FIELDS - set(report))
    if missing:
        raise ValueError(f"report is missing required fields: {missing}")

    identity = report["project_identity"]
    delta = report["version_delta"]
    evidence = report["evidence_status"]
    dispositions = report["candidate_dispositions"]
    baseline_id = report["baseline_deck_version_id"]
    resulting_id = report["resulting_deck_version_id"]
    added_count = sum(item.get("quantity", 0) for item in delta["added"])
    removed_count = sum(item.get("quantity", 0) for item in delta["removed"])
    lines = [
        f"# Project Report {report['report_version']}",
        "",
        "## Executive Summary",
        "",
        f"{identity['name']} records DeckVersion {resulting_id} from baseline {baseline_id}. "
        f"Implementation evidence is {evidence_value(evidence['implementation_result'])}; "
        f"performance claims are {evidence_value(evidence['performance_claim'])}.",
        "",
        "## Project Identity",
        "",
        f"- Format: {identity['format']}",
        f"- Commander: {identity['commander']}",
        f"- Curated identity summary: {identity['curated_summary']['identity']}",
        f"- Curated resource model: {identity['curated_summary']['resource_model']}",
        f"- Curated constraint: {identity['curated_summary']['identity_constraint']}",
        "",
        "## Design Brief",
        "",
        *bullet_lines(report["brief_summary"]["goals"]),
        "",
        report["brief_summary"]["outcome_boundary"],
        "",
        f"## Baseline {baseline_id}",
        "",
        f"Baseline analysis `{report['baseline_summary']['analysis_id']}` examined DeckVersion "
        f"`{report['baseline_summary']['deck_version_id']}` structurally.",
        "",
        "## Identified Pressure or Weakness",
        "",
        *bullet_lines(report["baseline_summary"]["relevant_pressure_points"]),
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation_summary']['recommendation_id']}`: "
        f"{report['recommendation_summary']['problem_statement']}",
        "",
        "## Candidate Dispositions",
        "",
    ]
    for status in sorted({item.get("review_status", "unknown") for item in dispositions}):
        lines.extend([f"### {status}", "", *render_dispositions(dispositions, status), ""])
    lines.extend(["## Decisions", ""])
    for decision in report["decision_summary"]:
        lines.append(
            f"- `{decision['decision_id']}`: IN {', '.join(decision['incoming_cards'])}; "
            f"OUT {', '.join(decision['outgoing_cards'])}. Recorded rationale: "
            f"{decision['source_rationale']}"
        )
    implementation = report["implementation_summary"]
    lines.extend([
        "",
        "## Approved Deck-Change Design",
        "",
        f"`{implementation['design_id']}` was approved by {implementation['approval_by']} and "
        f"implemented as `{implementation['resulting_version_id']}`.",
        "",
        f"## Implemented DeckVersion {resulting_id}",
        "",
        f"Validation status: {implementation['validation_status']}.",
        "",
        "## Exact Version Change",
        "",
        f"The report records {added_count} additions and {removed_count} removals.",
        "",
        "### IN",
        "",
        *render_delta(delta["added"]),
        "",
        "### OUT",
        "",
        *render_delta(delta["removed"]),
        "",
        f"Commander unchanged: {str(delta['commander_unchanged']).lower()}. "
        f"Sideboard unchanged: {str(delta['sideboard_unchanged']).lower()}. "
        f"Playable total: {delta['playable_total']}.",
        "",
        "## Knowledge and Provenance State",
        "",
        "Implemented cards in canonical Card Facts: "
        f"{', '.join(report['knowledge_alignment']['implemented_cards_in_canonical_facts'])}.",
        "",
        "Historical candidate provenance: "
        f"{report['knowledge_alignment']['historical_candidate_provenance']}.",
        "",
        "## What Is Verified",
        "",
        f"- Implementation result: {evidence_value(evidence['implementation_result'])}",
        f"- Current deck alignment: {str(delta['current_decklist_matches_resulting_version']).lower()}",
        f"- Resulting version is current: {str(report['resulting_version_is_current']).lower()}",
        "",
        "## What Is Expected but Not Yet Measured",
        "",
        *bullet_lines(report["expected_impacts"]),
        "",
        "## Evidence Status",
        "",
        f"- Post-implementation analysis: {evidence_value(evidence['post_implementation_analysis'])}",
        f"- Post-implementation simulation: {evidence_value(evidence['post_implementation_simulation'])}",
        f"- Gameplay validation: {evidence_value(evidence['gameplay_validation'])}",
        f"- Performance claim: {evidence_value(evidence['performance_claim'])}",
        "",
        "## Limitations",
        "",
        *bullet_lines(report["limitations_and_open_items"]),
        "",
        "## Next Actions",
        "",
        f"Immediate: {report['next_actions']['immediate']}.",
        "",
        *bullet_lines(report["next_actions"]["future"]),
        "",
        "## Structured Sources",
        "",
        *render_sources(report["source_references"]),
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = argv or sys.argv[1:]
    report_path = Path(argv[0]) if argv else DEFAULT_REPORT
    markdown_path = report_path.with_suffix(".md")
    markdown_path.write_text(render_report(load_json(report_path)), encoding="utf-8")
    print(f"Rendered {markdown_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
