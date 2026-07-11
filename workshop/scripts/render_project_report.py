#!/usr/bin/env python3
"""Render a committed Project Report Markdown file from its structured JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity" / "reports"
REQUIRED_FIELDS = {
    "report_id",
    "project_identity",
    "brief_summary",
    "baseline_summary",
    "recommendation_summary",
    "product_owner_review_summary",
    "decision_summary",
    "implementation_summary",
    "version_delta",
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


def render_report(report):
    missing = sorted(REQUIRED_FIELDS - set(report))
    if missing:
        raise ValueError(f"report is missing required fields: {missing}")

    identity = report["project_identity"]
    delta = report["version_delta"]
    evidence = report["evidence_status"]
    lines = [
        f"# Project Report {report['report_version']}",
        "",
        "## Executive Summary",
        "",
        f"{identity['name']} implemented DeckVersion {report['resulting_deck_version_id']} from "
        f"baseline {report['baseline_deck_version_id']}. Implementation and traceability are verified; "
        "post-implementation outcomes are not measured.",
        "",
        "## Project Identity",
        "",
        f"- Format: {identity['format']}",
        f"- Commander: {identity['commander']}",
        f"- Identity: {identity['identity']}",
        f"- Resource model: {identity['resource_model']}",
        f"- Constraint: {identity['identity_constraint']}",
        "",
        "## Design Brief",
        "",
        *bullet_lines(report["brief_summary"]["goals"]),
        "",
        report["brief_summary"]["outcome_boundary"],
        "",
        "## Baseline v1.0",
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
        f"`{report['recommendation_summary']['recommendation_id']}` proposed external candidates for "
        "recorded mana, artifact-access, and engine pressure points.",
        "",
        "## Product Owner Review",
        "",
        f"Accepted for decision: {', '.join(report['product_owner_review_summary']['accepted_candidate_ids'])}.",
        "",
        f"Needs testing: {', '.join(report['product_owner_review_summary']['needs_testing_candidate_ids'])}.",
        "",
        report["product_owner_review_summary"]["review_boundary"],
        "",
        "## Decisions",
        "",
    ]
    for decision in report["decision_summary"]:
        lines.append(
            f"- `{decision['decision_id']}`: IN {', '.join(decision['incoming_cards'])}; "
            f"OUT {', '.join(decision['outgoing_cards'])}. {decision['expected_effect']}"
        )
    lines.extend([
        "",
        "## Approved Deck-Change Design",
        "",
        f"`{report['implementation_summary']['design_id']}` was approved by "
        f"{report['implementation_summary']['approval_by']} and implemented as "
        f"`{report['implementation_summary']['resulting_version_id']}`.",
        "",
        "## Implemented DeckVersion v1.1",
        "",
        report["implementation_summary"]["validation_status"],
        "",
        "## Exact Version Change",
        "",
        "### IN",
        "",
    ])
    lines.extend(
        f"- {item['quantity']} {item['card_name']} ({item['zone']}; {item['source_decision_id']})"
        for item in delta["added"]
    )
    lines.extend(["", "### OUT", ""])
    lines.extend(
        f"- {item['quantity']} {item['card_name']} ({item['zone']}; {item['source_decision_id']})"
        for item in delta["removed"]
    )
    lines.extend([
        "",
        f"Commander unchanged: {str(delta['commander_unchanged']).lower()}. Sideboard unchanged: "
        f"{str(delta['sideboard_unchanged']).lower()}. Playable total: {delta['playable_total']}.",
        "",
        "## Knowledge and Provenance State",
        "",
        "Implemented cards are present in canonical Card Facts and have canonical Functional Knowledge: "
        f"{', '.join(report['knowledge_alignment']['implemented_cards_in_canonical_facts'])}.",
        "",
        "Historical candidate provenance remains resolvable. Active needs-testing candidates: "
        f"{', '.join(report['knowledge_alignment']['active_needs_testing_candidates'])}.",
        "",
        "## What Is Verified",
        "",
        f"- Implementation result: {evidence['implementation_result']}",
        "- The recorded decisions, approved design, resulting DeckVersion, and current decklist align.",
        "- The exact four-card IN and four-card OUT delta is recorded above.",
        "",
        "## What Is Expected but Not Yet Measured",
        "",
        *bullet_lines(report["expected_impacts"]),
        "",
        "These are expected effects from the recorded design, not measured performance outcomes.",
        "",
        "## Deferred Candidates",
        "",
        "- Krark-Clan Ironworks: needs_testing; not implemented.",
        "- Mana Echoes: needs_testing; not implemented.",
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
    ])
    for key, value in report["source_references"].items():
        if isinstance(value, list):
            lines.append(f"- {key}: {', '.join(item['path'] for item in value)}")
        else:
            lines.append(f"- {key}: {value['path']}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = argv or sys.argv[1:]
    report_path = Path(argv[0]) if argv else REPORTS_DIR / "project_report_v1.1.json"
    markdown_path = report_path.with_suffix(".md")
    markdown_path.write_text(render_report(load_json(report_path)), encoding="utf-8")
    print(f"Rendered {markdown_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
