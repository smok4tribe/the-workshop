#!/usr/bin/env python3
"""Deterministically render Sprint 1 certification and backlog Markdown."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "workshop" / "projects" / "the-myr-singularity"

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def bullets(values): return [f"- {value}" for value in values]

def render_backlog(doc):
    lines=["# Project Backlog", ""]
    for item in doc["items"]:
        lines += [f"## {item['backlog_id']} - {item['title']}", "", f"- Status: {item['status']}", f"- Priority: {item['priority']}", f"- Purpose: {item['purpose']}", f"- Dependency: {item['dependency']}", "", "Acceptance criteria:", *bullets(item["acceptance_criteria"]), ""]
    return "\n".join(lines).rstrip()+"\n"

def render_certification(doc):
    lines=["# Sprint 1 Certification Candidate", "", "## Executive Certification Summary", "", "Certification candidate prepared; independent review pending.", "", "## Certification Scope", "", f"- Project: {doc['project_id']}", f"- Scope: {doc['certification_scope']}", f"- Status: {doc['certification_status']}", "", "## Claim Boundary", "", doc["certification_claim_boundary"], "", "## Project and Fixture", "", "The Myr Singularity is the local Sprint 1 fixture.", "", "## Completed Product Loop", ""]
    lines += [f"- {x['step_id']}: {x['title']} ({x['status']})" for x in doc['product_loop']]
    lines += ["", "## Sprint Exit Criteria", ""] + [f"- {x['criterion_id']}: {x['title']} ({x['status']})" for x in doc['sprint_exit_criteria']]
    lines += ["", "## Quality Gates", ""] + [f"- {x['gate_id']}: {x['status']}" for x in doc['quality_gates']]
    lines += ["", "## Functional / Structural / Product Done", ""] + [f"- {x['capability']}: functional {x['functional_done']}; structural {x['structural_done']}; product {x['product_done']}" for x in doc['definition_of_done']]
    lines += ["", "## Validation Evidence", ""] + bullets(doc['validation_contract'])
    lines += ["", "## Implemented Version State", "", "- Baseline: v1.0", "- Resulting/current: v1.1", "", "## Evidence and Performance Boundary", ""] + [f"- {k}: {v}" for k,v in doc['evidence_boundary'].items() if k != 'needs_testing_candidates']
    lines += [f"- {x['name']}: needs_testing; {x['implementation_status']}" for x in doc['evidence_boundary']['needs_testing_candidates']]
    lines += ["", "## Deferred Non-Blocking Work", ""] + bullets(doc['deferred_backlog_ids'])
    lines += ["", "## Sprint 1 Non-Goals", ""] + bullets(doc['sprint_1_non_goals'])
    lines += ["", "## External Documentation Review", "", "External RFC documentation synchronization is deferred to backlog-007.", "", "## Independent Review Status", "", f"- Status: {doc['independent_review']['status']}", "", "## Structured Sources", ""]
    for key,value in sorted(doc['source_references'].items()):
        refs=value if isinstance(value,list) else [value]
        lines.append(f"- {key}: {', '.join(x['path'] for x in refs)}")
    lines += ["", "## Next Action", "", doc['next_action']]
    return "\n".join(lines).rstrip()+"\n"

def main():
    cert=PROJECT/'reports'/'sprint_1_certification.json'; backlog=PROJECT/'notes'/'backlog.json'
    cert.with_suffix('.md').write_text(render_certification(load(cert)),encoding='utf-8')
    backlog.with_suffix('.md').write_text(render_backlog(load(backlog)),encoding='utf-8')
    print('Rendered Sprint 1 closure artifacts.')
if __name__=='__main__': main()
