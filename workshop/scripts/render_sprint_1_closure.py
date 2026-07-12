#!/usr/bin/env python3
"""Deterministically render Sprint certification and backlog artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = ROOT / "workshop" / "projects" / "the-myr-singularity"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bullets(values):
    return [f"- {value}" for value in values]


def render_backlog(doc):
    lines = [f"# {doc['backlog_id']}", "", f"Project: {doc['project_id']}", ""]
    for item in doc["items"]:
        lines += [
            f"## {item['backlog_id']} - {item['title']}", "",
            f"- Work type: {item['work_type']}",
            f"- Status: {item['status']}",
            f"- Priority: {item['priority']}",
            f"- Purpose: {item['purpose']}",
            f"- Dependency: {item['dependency']}",
        ]
        for key, label in (
            ("related_version_id", "Related version"),
            ("related_candidate_id", "Related candidate"),
            ("implementation_authorized", "Implementation authorized"),
        ):
            if key in item:
                lines.append(f"- {label}: {item[key]}")
        if item.get("required_assumptions"):
            lines += ["", "Required assumptions:", *bullets(item["required_assumptions"])]
        if item.get("external_rfc_ids"):
            lines += ["", "External RFCs:", *bullets(item["external_rfc_ids"])]
        lines += ["", "Acceptance criteria:", *bullets(item["acceptance_criteria"]), ""]
    return "\n".join(lines).rstrip() + "\n"


def review_lines(doc):
    review = doc["independent_review"]
    status = doc["certification_status"]
    if status == "pending_independent_review":
        return ["Certification candidate prepared; independent review pending.", "", "- Status: pending"]
    review_source = review.get("review_source")
    source_text = review_source.get("path") if isinstance(review_source, dict) else review_source
    lines = [
        f"Certification status: {status}.", "",
        f"- Review status: {review.get('status')}",
        f"- Reviewer: {review.get('reviewer')}",
        f"- Reviewer role: {review.get('reviewer_role')}",
        f"- Verdict: {review.get('verdict')}",
        f"- Reviewed commit: {review.get('reviewed_commit')}",
        f"- Reviewed at: {review.get('reviewed_at')}",
        f"- Review source: {source_text}",
    ]
    if review.get("rationale"):
        lines.append(f"- Rationale: {review['rationale']}")
    if review.get("blocking_findings"):
        lines += ["", "Blocking findings:", *bullets(review["blocking_findings"])]
    if review.get("non_blocking_followups"):
        lines += ["", "Non-blocking follow-ups:", *bullets(review["non_blocking_followups"])]
    return lines


def render_certification(doc):
    version = doc["version_state"]
    external = doc["external_documentation"]
    lines = [
        f"# {doc['sprint_id']} Certification Candidate", "",
        "## Executive Certification Summary", "",
        *review_lines(doc), "",
        "## Certification Identity", "",
        f"- Type: {doc['certification_type']}",
        f"- Project: {doc['project_name']} ({doc['project_id']})",
        f"- Sprint: {doc['sprint_id']}",
        f"- Scope: {doc['certification_scope']}",
        f"- Status: {doc['certification_status']}",
        f"- Candidate base commit: {doc['candidate_base_commit']}", "",
        "## Claim Boundary", "", doc["certification_claim_boundary"], "",
        "## Version State", "",
        f"- Baseline: {version['baseline_version_id']}",
        f"- Resulting: {version['resulting_version_id']}",
        f"- Current: {version['current_version_id']}",
        f"- Commander unchanged: {version['commander_unchanged']}",
        f"- Sideboard unchanged: {version['sideboard_unchanged']}", "",
        "## Completed Product Loop", "",
    ]
    lines += [
        f"- {item['step_id']}: {item['title']} ({item['status']}); sources: "
        f"{', '.join(item['source_keys'])}; artifacts: {', '.join(item['artifact_ids'])}"
        for item in doc["product_loop"]
    ]
    lines += ["", "## Sprint Exit Criteria", ""] + [
        f"- {item['criterion_id']}: {item['title']} ({item['status']}); evidence: "
        f"{', '.join(item['evidence_source_keys'])}"
        for item in doc["sprint_exit_criteria"]
    ]
    lines += ["", "## Quality Gates", ""] + [
        f"- {item['gate_id']} - {item['label']}: {item['status']}"
        for item in doc["quality_gates"]
    ]
    lines += ["", "## Functional / Structural / Product Done", ""] + [
        f"- {item['capability']}: functional {item['functional_done']}; "
        f"structural {item['structural_done']}; product {item['product_done']}"
        for item in doc["definition_of_done"]
    ]
    lines += ["", "## Validation Contract", ""] + [
        f"- {item['validation_id']}: {item['label']} ({item['status']}) - `{item['command']}`"
        for item in doc["validation_contract"]
    ]
    boundary = doc["evidence_boundary"]
    lines += ["", "## Evidence and Performance Boundary", ""] + [
        f"- {key}: {value}" for key, value in boundary.items() if key != "needs_testing_candidates"
    ]
    lines += [
        f"- {item['name']} ({item['candidate_id']}): {item['review_status']}; "
        f"{item['implementation_status']}; source {item['source_candidate_reference']}"
        for item in boundary["needs_testing_candidates"]
    ]
    lines += ["", "## Deferred Non-Blocking Work", "", *bullets(doc["deferred_backlog_ids"])]
    lines += ["", "## Sprint 1 Non-Goals", "", *bullets(doc["sprint_1_non_goals"])]
    lines += [
        "", "## External Documentation Review", "",
        f"- Status: {external['status']}",
        f"- Backlog work type: {external['backlog_work_type']}",
        f"- External files modified: {external['external_files_modified']}",
        *[f"- {rfc_id}" for rfc_id in external["rfc_ids"]],
        "", "## Independent Review", "", *review_lines(doc),
        "", "## Structured Sources", "",
    ]
    for key, value in sorted(doc["source_references"].items()):
        refs = value if isinstance(value, list) else [value]
        lines.append(f"- {key}: {', '.join(item['path'] for item in refs)}")
    lines += ["", "## Next Action", "", doc["next_action"]]
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    project = Path(argv[0]).resolve() if argv else DEFAULT_PROJECT
    cert_path = Path(argv[1]).resolve() if len(argv) > 1 else project / "reports" / "sprint_1_certification.json"
    backlog_path = Path(argv[2]).resolve() if len(argv) > 2 else project / "notes" / "backlog.json"
    cert_path.with_suffix(".md").write_text(render_certification(load(cert_path)), encoding="utf-8")
    backlog_path.with_suffix(".md").write_text(render_backlog(load(backlog_path)), encoding="utf-8")
    print("Rendered Sprint 1 closure artifacts.")


if __name__ == "__main__":
    main()
