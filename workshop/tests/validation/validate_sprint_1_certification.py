#!/usr/bin/env python3
"""Derive Sprint 1 certification claims from authoritative repository evidence."""
from __future__ import annotations

import json
import os
import re
import sys
from copy import deepcopy
from pathlib import Path

_IMPORT_ROOT = Path(__file__).resolve().parents[3]
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from workshop.tests.validation.certification_contract import (
    BACKLOG_WORK_TYPES,
    CLAIM_BOUNDARY,
    CERTIFICATION_SCOPE,
    CHECKLIST_CONTRACT,
    CRITERION_SOURCES,
    DOD_CAPABILITIES,
    EXPECTED_BASE_COMMIT,
    GATE_CONTRACT,
    LOOP_CONTRACT,
    NON_GOALS,
    PROJECT_ID,
    PROTECTED_PREFIXES,
    REQUIRED_SOURCE_KEYS,
    SPRINT_ID,
    VALIDATION_COMMANDS,
    card_names_from_candidate,
    git,
    load_json,
    load_module,
    normalized,
    parse_checklist,
    resolve_repo_path,
    run,
)


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "workshop" / "projects" / PROJECT_ID
VALIDATION_DIR = ROOT / "workshop" / "tests" / "validation"
CERT_PATH = PROJECT / "reports" / "sprint_1_certification.json"


def emit(checks):
    failed = 0
    for name, errors in checks:
        print(f"[{'PASS' if not errors else 'FAIL'}] {name}")
        for error in errors:
            print(f"       - {error}")
        failed += bool(errors)
    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} certification checks failed.")
        return 1
    print(f"PASS: all {len(checks)} Sprint certification checks passed.")
    return 0


def source_values(value):
    return value if isinstance(value, list) else [value]


def renderer_matches(markdown_path, render):
    try:
        return bool(markdown_path and markdown_path.is_file() and markdown_path.read_text(encoding="utf-8") == render())
    except (KeyError, TypeError, ValueError, OSError):
        return False


def load_sources(cert, errors):
    references = cert.get("source_references")
    if not isinstance(references, dict):
        errors.append("source_references must be an object")
        return {}, {}, {}
    if set(references) != REQUIRED_SOURCE_KEYS:
        errors.append("certification source contract does not match the required source set")
    paths, documents, texts = {}, {}, {}
    for key, value in references.items():
        loaded_paths, loaded_docs, loaded_texts = [], [], []
        for reference in source_values(value):
            path = resolve_repo_path(ROOT, reference)
            if not path or not path.is_file():
                errors.append(f"source {key!r} does not resolve")
                continue
            loaded_paths.append(path)
            if path.suffix.casefold() == ".json":
                try:
                    loaded_docs.append(load_json(path))
                except json.JSONDecodeError as exc:
                    errors.append(f"source {key!r} is invalid JSON: {exc}")
            else:
                loaded_texts.append(path.read_text(encoding="utf-8"))
        paths[key] = loaded_paths if isinstance(value, list) else (loaded_paths[0] if loaded_paths else None)
        documents[key] = loaded_docs if isinstance(value, list) else (loaded_docs[0] if loaded_docs else None)
        texts[key] = loaded_texts if isinstance(value, list) else (loaded_texts[0] if loaded_texts else None)
    return paths, documents, texts


def validate_source_identities(cert, docs, texts):
    errors = []
    project = docs.get("project") or {}
    brief = docs.get("brief") or {}
    baseline = docs.get("baseline_deck_version") or {}
    resulting = docs.get("resulting_deck_version") or {}
    analysis = docs.get("baseline_analysis") or {}
    rec_001 = docs.get("rec_001") or {}
    rec_002 = docs.get("rec_002") or {}
    review = docs.get("product_owner_review") or {}
    design = docs.get("deck_change_design") or {}
    report = docs.get("project_report") or {}
    decisions = docs.get("decisions") or []
    references = cert.get("source_references", {})

    if project.get("id") != PROJECT_ID or references.get("project", {}).get("id") != PROJECT_ID:
        errors.append("project source identity does not match certification project")
    if project.get("name") != cert.get("project_name") or project.get("sprint") != SPRINT_ID:
        errors.append("project source name or sprint does not match certification")
    if project.get("current_version_id") != "v1.1":
        errors.append("project current version is not v1.1")
    if "local product loop complete" not in str(project.get("scope", {}).get("phase", "")).casefold() or "pending independent review" not in str(project.get("scope", {}).get("phase", "")).casefold():
        errors.append("project scope phase does not record completed loop with pending certification")
    if brief.get("project_id") != PROJECT_ID or brief.get("commander") != project.get("commander"):
        errors.append("brief source identity does not match project")
    if not brief.get("primary_goal") or not brief.get("improvement_areas"):
        errors.append("brief source lacks goal structure")
    for label, version, expected in (("baseline", baseline, "v1.0"), ("resulting", resulting, "v1.1")):
        reference = references.get(f"{label}_deck_version", {})
        if version.get("version_id") != expected or version.get("project_id") != PROJECT_ID or reference.get("id") != expected:
            errors.append(f"{label} DeckVersion source identity does not match certification")
    if resulting.get("parent_version_id") != "v1.0" or project.get("current_version_id") != resulting.get("version_id"):
        errors.append("resulting DeckVersion relationship does not match baseline/current project state")
    if analysis.get("analysis_id") != "baseline_v1.0" or analysis.get("project_id") != PROJECT_ID or analysis.get("deck_version_id") != "v1.0" or references.get("baseline_analysis", {}).get("id") != "baseline_v1.0":
        errors.append("baseline analysis source identity does not match certification")
    for key, recommendation, expected in (("rec_001", rec_001, "rec-001"), ("rec_002", rec_002, "rec-002")):
        if recommendation.get("recommendation_set_id") != expected or recommendation.get("project_id") != PROJECT_ID or references.get(key, {}).get("id") != expected:
            errors.append(f"{expected} source identity does not match certification")
    if review.get("artifact_type") != "product_owner_candidate_review" or review.get("project_id") != PROJECT_ID or review.get("recommendation_set_id") != "rec-002":
        errors.append("Product Owner review source identity does not match rec-002")
    candidate_ids = {item.get("candidate_id") for item in rec_002.get("candidates", [])}
    if {item.get("candidate_id") for item in review.get("review_entries", [])} != candidate_ids:
        errors.append("Product Owner review does not exactly cover rec-002 candidates")
    decision_ids = []
    for reference, decision in zip(references.get("decisions", []), decisions):
        decision_id = reference.get("id")
        decision_ids.append(decision_id)
        if decision.get("decision_id") != decision_id or decision.get("project_id") != PROJECT_ID:
            errors.append(f"decision source identity mismatch for {decision_id!r}")
        if decision.get("source_recommendation_id") != "rec-002" or decision.get("source_candidate_id") not in candidate_ids or decision.get("implemented_in_version") != "v1.1":
            errors.append(f"decision {decision_id!r} has invalid recommendation/candidate/version lineage")
    if decision_ids != ["decision-002", "decision-003", "decision-004"]:
        errors.append("decision source set does not match implemented Sprint 1 decisions")
    if design.get("design_id") != "deck-change-design-v1.1" or design.get("project_id") != PROJECT_ID or references.get("deck_change_design", {}).get("id") != design.get("design_id"):
        errors.append("deck-change design source identity does not match certification")
    if design.get("product_owner_approved") is not True or design.get("implemented_version_id") != "v1.1" or design.get("source_decision_ids") != decision_ids:
        errors.append("deck-change design approval/version/decision relationship is invalid")
    if report.get("report_id") != "project-report-v1.1" or references.get("project_report", {}).get("id") != report.get("report_id") or report.get("project_id") != PROJECT_ID:
        errors.append("project report source identity does not match certification")
    if report.get("baseline_deck_version_id") != "v1.0" or report.get("resulting_deck_version_id") != "v1.1" or report.get("report_status") != "implementation_verified_outcomes_not_measured":
        errors.append("project report version/status relationship does not match certification")
    if not isinstance((docs.get("card_facts") or {}).get("cards"), list):
        errors.append("canonical Card Facts source has wrong shape")
    if not isinstance((docs.get("active_candidate_facts") or {}).get("candidate_cards"), list):
        errors.append("active candidate facts source has wrong shape")
    if (docs.get("functional_knowledge") or {}).get("name") != "Functional Role Assignments" or not isinstance((docs.get("functional_knowledge") or {}).get("assignments"), list):
        errors.append("Functional Knowledge source has wrong shape")
    lifecycle = docs.get("candidate_lifecycle_metadata") or {}
    if not isinstance(lifecycle.get("candidate_intake_scryfall_ids"), list) or not isinstance(lifecycle.get("promoted_candidate_records"), list):
        errors.append("candidate lifecycle source has wrong shape")
    backlog = docs.get("backlog") or {}
    if backlog.get("project_id") != PROJECT_ID or backlog.get("backlog_id") != "the-myr-singularity-backlog" or not isinstance(backlog.get("items"), list):
        errors.append("backlog source identity or shape does not match project")
    return errors


def validate_git_boundary(cert, expected_base_commit):
    errors = []
    base = cert.get("candidate_base_commit")
    expected = expected_base_commit
    if base != expected:
        errors.append("candidate_base_commit does not match the intended Sprint integration base")
        return errors, False
    if git(ROOT, "cat-file", "-e", f"{base}^{{commit}}").returncode:
        errors.append("candidate_base_commit is not a real git commit")
        return errors, False
    if git(ROOT, "merge-base", "--is-ancestor", base, "HEAD").returncode:
        errors.append("candidate_base_commit is not an ancestor of HEAD")
    diff = git(ROOT, "diff", "--name-only", f"{base}..HEAD")
    if diff.returncode:
        errors.append("cannot inspect certification candidate scope diff")
        return errors, False
    changed = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    protected = [path for path in changed if any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)]
    if protected:
        errors.append(f"protected artifacts changed since candidate base: {protected}")
    return errors, not errors


def validate_backlog(backlog, review, resulting):
    errors = []
    items = backlog.get("items") if isinstance(backlog, dict) else None
    if not isinstance(items, list):
        return ["backlog items must be an array"], False
    ids = [item.get("backlog_id") for item in items]
    work_types = [item.get("work_type") for item in items]
    if len(ids) != len(set(ids)):
        errors.append("backlog IDs must be unique")
    if set(work_types) != BACKLOG_WORK_TYPES or len(work_types) != len(set(work_types)):
        errors.append("backlog work types do not exactly cover the required deferred work")
    allowed_status = {"deferred", "needs_testing"}
    allowed_priority = {"low", "medium", "high"}
    by_type = {item.get("work_type"): item for item in items}
    for item in items:
        if item.get("project_id") != PROJECT_ID:
            errors.append(f"backlog item {item.get('backlog_id')!r} has wrong project ID")
        if item.get("status") not in allowed_status or item.get("priority") not in allowed_priority:
            errors.append(f"backlog item {item.get('backlog_id')!r} has unsupported status or priority")
        if not item.get("purpose") or not item.get("dependency") or not item.get("acceptance_criteria"):
            errors.append(f"backlog item {item.get('backlog_id')!r} lacks purpose, dependency, or acceptance criteria")
    review_statuses = {item.get("candidate_id"): item.get("review_status") for item in review.get("review_entries", [])}
    version_names = {normalized(item.get("name")) for item in resulting.get("main_deck", [])}
    for work_type, candidate_id, name in (
        ("candidate_testing_kci", "cand-009", "Krark-Clan Ironworks"),
        ("candidate_testing_mana_echoes", "cand-010", "Mana Echoes"),
    ):
        item = by_type.get(work_type, {})
        if item.get("related_candidate_id") != candidate_id or item.get("status") != "needs_testing" or item.get("implementation_authorized") is not False:
            errors.append(f"{work_type} backlog candidate link/status/authorization is invalid")
        if review_statuses.get(candidate_id) != "needs_testing" or normalized(name) in version_names:
            errors.append(f"{work_type} contradicts review or implemented DeckVersion state")
    if by_type.get("post_implementation_analysis", {}).get("related_version_id") != "v1.1":
        errors.append("post-implementation analysis backlog item must target v1.1")
    assumptions = set(by_type.get("mana_color_simulation", {}).get("required_assumptions", []))
    if assumptions != {"mulligan_policy_pending", "simulation_assumptions_pending", "no_existing_result_claim"}:
        errors.append("simulation backlog item lacks required pending assumptions")
    if set(by_type.get("external_rfc_sync", {}).get("external_rfc_ids", [])) != {"RFC-007", "RFC-008", "RFC-009", "RFC-013"}:
        errors.append("external RFC backlog item does not cover RFC-007/008/009/013")
    return errors, not errors


def validate_closure_documents(project, texts):
    errors = []
    readme = texts.get("project_readme") or ""
    for heading in (
        "## Project Identity", "## Sprint 1 Fixture", "## Version State",
        "## Completed Product Loop", "## Exact Implemented Delta", "## Evidence Boundary",
        "## Deferred Candidates", "## Key Artifacts", "## Validation",
        "## Certification Status", "## Next Action",
    ):
        if heading not in readme:
            errors.append(f"project README is missing required section {heading!r}")
    for marker in (
        "The Myr Singularity", "Urtet, Remnant of Memnarch", "v1.0", "v1.1",
        "Krark-Clan Ironworks", "Mana Echoes", "pending independent review",
        "not certified",
    ):
        if marker.casefold() not in readme.casefold():
            errors.append(f"project README lacks required fact {marker!r}")
    if project.get("id") != PROJECT_ID or project.get("name") != "The Myr Singularity" or project.get("format") != "Commander" or project.get("commander") != "Urtet, Remnant of Memnarch" or project.get("current_version_id") != "v1.1":
        errors.append("project identity/current version changed during certification closure")
    scope = project.get("scope", {})
    phase = str(scope.get("phase", "")).casefold()
    if "local product loop complete" not in phase or "pending independent review" not in phase or not scope.get("included") or not scope.get("not_included"):
        errors.append("project scope does not represent completed local loop with pending certification")
    notes = texts.get("notes") or ""
    if notes.count("# 2026-07-12 - Sprint 1 Certification Candidate") != 1:
        errors.append("Sprint notes must contain one certification-candidate checkpoint")
    for marker in ("Task 27 report layer is merged", "independent review remains pending", "performance", "KCI", "Mana Echoes", "has not declared"):
        if marker.casefold() not in notes.casefold():
            errors.append(f"Sprint notes certification checkpoint lacks marker {marker!r}")
    handoff = texts.get("documentation_handoff") or ""
    for rfc_id in ("RFC-007", "RFC-008", "RFC-009", "RFC-013"):
        if f"## {rfc_id}" not in handoff:
            errors.append(f"documentation handoff is missing {rfc_id} section")
    if "does not modify external RFC documents" not in handoff:
        errors.append("documentation handoff does not preserve the external-file boundary")
    validation_docs = texts.get("validation_documentation") or ""
    for marker in (
        "Certification JSON records the result", "candidate_base_commit",
        "Independent review uses a structured", "Regression checklists use this parseable syntax",
    ):
        if marker not in validation_docs:
            errors.append(f"validation documentation lacks certification contract marker {marker!r}")
    changelog = texts.get("changelog") or ""
    if "v1.1" not in changelog or "Sprint 1" not in changelog:
        errors.append("changelog does not identify the Sprint 1 v1.1 closure state")
    return errors


def validate_evidence(cert, docs):
    errors = []
    report = docs.get("project_report") or {}
    evidence = report.get("evidence_status", {})
    expected = {
        "implementation": "verified", "post_implementation_analysis": "not_run",
        "simulation": "not_run", "gameplay_validation": "not_recorded",
        "performance": "not_measured",
    }
    actual = {
        "implementation": evidence.get("implementation_result"),
        "post_implementation_analysis": evidence.get("post_implementation_analysis", {}).get("status"),
        "simulation": evidence.get("post_implementation_simulation", {}).get("status"),
        "gameplay_validation": evidence.get("gameplay_validation", {}).get("status"),
        "performance": evidence.get("performance_claim", {}).get("status"),
    }
    if actual != expected or {key: cert.get("evidence_boundary", {}).get(key) for key in expected} != expected:
        errors.append("certification evidence boundary does not match authoritative project report")
    rec_002 = docs.get("rec_002") or {}
    review = docs.get("product_owner_review") or {}
    decisions = docs.get("decisions") or []
    design = docs.get("deck_change_design") or {}
    resulting = docs.get("resulting_deck_version") or {}
    active = docs.get("active_candidate_facts") or {}
    cards_by_id = {item.get("scryfall_id"): item for item in active.get("candidate_cards", [])}
    candidates = {item.get("candidate_id"): item for item in rec_002.get("candidates", [])}
    review_status = {item.get("candidate_id"): item.get("review_status") for item in review.get("review_entries", [])}
    decision_candidates = {item.get("source_candidate_id") for item in decisions}
    design_names = {normalized(item.get("name")) for item in design.get("incoming_cards", [])}
    version_names = {normalized(item.get("name")) for item in resulting.get("main_deck", [])}
    certified_candidates = {item.get("candidate_id"): item for item in cert.get("evidence_boundary", {}).get("needs_testing_candidates", [])}
    for candidate_id in ("cand-009", "cand-010"):
        candidate = candidates.get(candidate_id, {})
        names = card_names_from_candidate(candidate, cards_by_id)
        recorded = certified_candidates.get(candidate_id, {})
        candidate_references = candidate.get("incoming_cards", [])
        expected_reference = candidate_references[0] if len(candidate_references) == 1 else None
        if (len(names) != 1 or recorded.get("name") != names[0]
                or recorded.get("review_status") != "needs_testing"
                or recorded.get("implementation_status") != "not_implemented"
                or recorded.get("source_candidate_reference") != expected_reference):
            errors.append(f"certification candidate state for {candidate_id!r} does not match active candidate facts")
            continue
        name = normalized(names[0])
        if review_status.get(candidate_id) != "needs_testing" or candidate_id in decision_candidates or name in design_names or name in version_names:
            errors.append(f"needs-testing candidate {candidate_id!r} is incorrectly authorized or implemented")
    if set(certified_candidates) != {"cand-009", "cand-010"}:
        errors.append("certification needs-testing candidate set is incomplete")
    return errors


def canonical_pending_projection(recorded_certification: dict) -> dict:
    """Restore only the lifecycle fields that may change while recording review."""
    projected = deepcopy(recorded_certification)
    projected["certification_status"] = "pending_independent_review"
    projected["independent_review"] = {
        "status": "pending",
        "reviewer_role": None,
        "reviewer": None,
        "verdict": None,
        "reviewed_commit": None,
        "reviewed_at": None,
        "review_source": None,
        "blocking_findings": [],
        "non_blocking_followups": [],
        "rationale": None,
    }
    projected["next_action"] = {
        "action_id": "request_independent_review",
        "description": "Obtain independent Sprint 1 certification review.",
    }
    for gate in projected.get("quality_gates", []):
        gate["limitations"] = "Independent review remains pending."
    return projected


def validate_review_lifecycle(cert):
    errors = []
    status = cert.get("certification_status")
    review = cert.get("independent_review", {})
    supported = {"pending_independent_review", "certified", "certified_with_non_blocking_followups", "not_certified"}
    if status not in supported:
        return ["unsupported certification status"]
    null_fields = ("reviewer", "reviewer_role", "verdict", "reviewed_commit", "reviewed_at", "review_source", "rationale")
    if status == "pending_independent_review":
        if review.get("status") != "pending" or any(review.get(key) is not None for key in null_fields) or review.get("blocking_findings") != [] or review.get("non_blocking_followups") != []:
            errors.append("pending independent review contains completed or finding fields")
        return errors
    if review.get("status") != "completed" or not review.get("reviewer") or review.get("reviewer_role") != "independent_reviewer" or not review.get("reviewed_commit") or not review.get("reviewed_at"):
        errors.append("completed certification state lacks independent review identity")
        return errors
    if git(ROOT, "cat-file", "-e", f"{review['reviewed_commit']}^{{commit}}").returncode or git(ROOT, "merge-base", "--is-ancestor", review["reviewed_commit"], "HEAD").returncode:
        errors.append("independent review reviewed_commit is not a valid reviewed ancestor")
    else:
        candidate_path = "workshop/projects/the-myr-singularity/reports/sprint_1_certification.json"
        candidate = git(ROOT, "show", f"{review['reviewed_commit']}:{candidate_path}")
        try:
            reviewed_candidate = json.loads(candidate.stdout) if not candidate.returncode else {}
        except json.JSONDecodeError:
            reviewed_candidate = {}
        reviewed_review = reviewed_candidate.get("independent_review") or {}
        if (reviewed_candidate.get("certification_id") != cert.get("certification_id")
                or reviewed_candidate.get("project_id") != PROJECT_ID
                or reviewed_candidate.get("candidate_base_commit") != cert.get("candidate_base_commit")
                or reviewed_candidate.get("certification_status") != "pending_independent_review"
                or reviewed_review.get("status") != "pending"):
            errors.append("reviewed_commit does not contain the pending certification candidate")
        elif (any(reviewed_review.get(key) is not None for key in (
                "reviewer", "reviewer_role", "verdict", "reviewed_commit", "reviewed_at",
                "review_source", "rationale",
            )) or reviewed_review.get("blocking_findings") != []
                or reviewed_review.get("non_blocking_followups") != []):
            errors.append("reviewed_commit pending certification candidate contains completed review data")
        elif reviewed_candidate != canonical_pending_projection(cert):
            errors.append("reviewed_commit certification candidate differs from the canonical pending projection of the recorded certification")
        changed = git(ROOT, "diff", "--name-only", f"{review['reviewed_commit']}..HEAD")
        allowed = (
            "workshop/projects/the-myr-singularity/reports/sprint_1_certification.json",
            "workshop/projects/the-myr-singularity/reports/sprint_1_certification.md",
            "workshop/projects/the-myr-singularity/reports/sprint_1_certification_review",
        )
        unexpected = [
            line.strip().replace("\\", "/") for line in changed.stdout.splitlines()
            if line.strip() and not line.strip().replace("\\", "/").startswith(allowed)
        ]
        if changed.returncode or unexpected:
            errors.append("changes after reviewed_commit exceed certification review recording scope")
    source = resolve_repo_path(ROOT, review.get("review_source"))
    if not source or not source.is_file():
        errors.append("independent review source does not resolve")
        return errors
    try:
        artifact = load_json(source)
    except json.JSONDecodeError:
        errors.append("independent review source is invalid JSON")
        return errors
    expected = {
        "artifact_type": "sprint_certification_review", "certification_id": cert.get("certification_id"),
        "project_id": PROJECT_ID, "reviewer": review.get("reviewer"),
        "reviewer_role": review.get("reviewer_role"), "verdict": review.get("verdict"),
        "reviewed_commit": review.get("reviewed_commit"), "reviewed_at": review.get("reviewed_at"),
        "blocking_findings": review.get("blocking_findings"),
        "non_blocking_followups": review.get("non_blocking_followups"),
        "rationale": review.get("rationale"),
    }
    if any(artifact.get(key) != value for key, value in expected.items()):
        errors.append("independent review source does not agree with certification review fields")
    if status == "certified" and (review.get("verdict") != "APPROVE" or review.get("blocking_findings")):
        errors.append("certified state requires APPROVE with no blocking findings")
    if status == "certified_with_non_blocking_followups" and (review.get("verdict") not in {"APPROVE", "APPROVE WITH NON-BLOCKING FOLLOW-UP"} or review.get("blocking_findings") or not review.get("non_blocking_followups")):
        errors.append("certified-with-followups state requires approval and explicit non-blocking follow-ups")
    if status == "not_certified" and (review.get("verdict") not in {"REQUEST CHANGES", "HOLD — INSUFFICIENT EVIDENCE"} or not review.get("blocking_findings") or not review.get("rationale")):
        errors.append("not-certified state requires rejection rationale and blocking findings")
    return errors


def validate_certification(root: Path, *, expected_base_commit: str, run_lower_regressions: bool):
    global ROOT, PROJECT, VALIDATION_DIR, CERT_PATH
    ROOT = Path(root)
    PROJECT = ROOT / "workshop" / "projects" / PROJECT_ID
    VALIDATION_DIR = ROOT / "workshop" / "tests" / "validation"
    CERT_PATH = PROJECT / "reports" / "sprint_1_certification.json"
    checks = []
    try:
        cert = load_json(CERT_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        return emit([("certification artifact parses", [str(exc)])])

    errors = []
    if cert.get("certification_id") != "sprint-1-certification-candidate" or cert.get("certification_type") != "sprint_final_certification_candidate" or cert.get("project_id") != PROJECT_ID or cert.get("sprint_id") != SPRINT_ID or cert.get("certification_scope") != CERTIFICATION_SCOPE:
        errors.append("certification identity or scope is invalid")
    checks.append(("certification identity", errors))

    source_errors = []
    paths, docs, texts = load_sources(cert, source_errors)
    source_errors.extend(validate_source_identities(cert, docs, texts))
    checks.append(("structured source identity and relationships", source_errors))

    git_errors, scope_ok = validate_git_boundary(cert, expected_base_commit)
    checks.append(("candidate base commit and protected-path scope", git_errors))

    backlog_errors, backlog_ok = validate_backlog(docs.get("backlog") or {}, docs.get("product_owner_review") or {}, docs.get("resulting_deck_version") or {})
    checks.append(("structured backlog semantics", backlog_errors))

    checklist_errors = []
    checklist_paths = paths.get("regression_checklists") or []
    by_name = {path.name: path for path in checklist_paths}
    if set(by_name) != set(CHECKLIST_CONTRACT):
        checklist_errors.append("regression checklist source set is incomplete")
    for name, (heading, ids) in CHECKLIST_CONTRACT.items():
        if name in by_name:
            checklist_errors.extend(parse_checklist(ROOT, by_name[name], heading, ids))
    checks.append(("regression checklist semantics", checklist_errors))

    closure_errors = validate_closure_documents(docs.get("project") or {}, texts)
    checks.append(("README, scope, notes, and documentation handoff", closure_errors))

    evidence_errors = validate_evidence(cert, docs)
    checks.append(("evidence honesty and candidate state", evidence_errors))

    state_errors = []
    version_state = cert.get("version_state", {})
    baseline = docs.get("baseline_deck_version") or {}
    report_doc = docs.get("project_report") or {}
    expected_version_state = {
        "baseline_version_id": baseline.get("version_id"),
        "resulting_version_id": (docs.get("resulting_deck_version") or {}).get("version_id"),
        "current_version_id": (docs.get("project") or {}).get("current_version_id"),
        "commander_unchanged": (docs.get("resulting_deck_version") or {}).get("commander") == baseline.get("commander"),
        "sideboard_unchanged": (docs.get("resulting_deck_version") or {}).get("sideboard") == baseline.get("sideboard"),
    }
    if version_state != expected_version_state or report_doc.get("baseline_deck_version_id") != expected_version_state["baseline_version_id"] or report_doc.get("resulting_deck_version_id") != expected_version_state["resulting_version_id"]:
        state_errors.append("certification version_state does not match authoritative version sources")
    external = cert.get("external_documentation", {})
    external_backlog = next((item for item in (docs.get("backlog") or {}).get("items", []) if item.get("work_type") == "external_rfc_sync"), {})
    if external != {"status": "pending_external_sync", "backlog_work_type": "external_rfc_sync", "rfc_ids": ["RFC-007", "RFC-008", "RFC-009", "RFC-013"], "external_files_modified": False} or external_backlog.get("work_type") != "external_rfc_sync":
        state_errors.append("external documentation state does not match backlog and certification scope")
    deferred = cert.get("deferred_work")
    expected_deferred = [{"work_type": item.get("work_type"), "backlog_id": item.get("backlog_id")} for item in (docs.get("backlog") or {}).get("items", [])]
    if deferred != expected_deferred:
        state_errors.append("deferred work references do not exactly match structured backlog")
    if cert.get("certification_claim_boundary") != CLAIM_BOUNDARY:
        state_errors.append("certification claim boundary does not match the authoritative contract")
    if cert.get("sprint_1_non_goals") != NON_GOALS:
        state_errors.append("Sprint 1 non-goal set does not match the authoritative contract")
    actions = {"pending_independent_review": {"action_id": "request_independent_review", "description": "Obtain independent Sprint 1 certification review."}, "certified": {"action_id": "merge_and_record_certification", "description": "Merge, record certification closure, and synchronize external RFC documentation."}, "certified_with_non_blocking_followups": {"action_id": "merge_record_and_track_followups", "description": "Merge, record certification, and track non-blocking follow-ups."}, "not_certified": {"action_id": "remediate_and_request_new_review", "description": "Remediate blocking findings and request a new independent review."}}
    if cert.get("next_action") != actions.get(cert.get("certification_status")):
        state_errors.append("next_action does not match certification lifecycle state")
    checks.append(("derived version, external documentation, deferred work, and lifecycle action", state_errors))

    review_errors = validate_review_lifecycle(cert)
    checks.append(("independent review lifecycle and source", review_errors))

    runtime_errors = []
    runtime = {}
    commands = [
        ("validation-knowledge", "validate_knowledge_layer.py", None),
        ("validation-candidate-facts", "validate_candidate_card_facts.py", None),
        ("validation-review", "validate_recommendation_review.py", None),
        ("validation-decision", "validate_decision_pipeline.py", None),
        ("validation-deck-version", "validate_deck_versions.py", None),
        ("validation-project-report", "validate_project_reports.py", None),
    ]
    for validation_id, script, env in commands:
        result = run(ROOT, [sys.executable, VALIDATION_DIR / script], env)
        runtime[validation_id] = result.returncode == 0
        if result.returncode:
            runtime_errors.append(f"layer validator {script} failed")
    recommendation_source_ok = {
        rec_name: not any(error.startswith(f"{rec_name} source identity") for error in source_errors)
        for rec_name in ("rec-001", "rec-002")
    }
    for validation_id, rec_name in (("validation-rec-001", "rec-001"), ("validation-rec-002", "rec-002")):
        env = {
            "WORKSHOP_RECOMMENDATION_JSON": f"workshop/projects/{PROJECT_ID}/recommendations/{rec_name}.json",
            "WORKSHOP_RECOMMENDATION_MD": f"workshop/projects/{PROJECT_ID}/recommendations/{rec_name}.md",
        }
        result = run(ROOT, [sys.executable, VALIDATION_DIR / "validate_recommendation_schema.py"], env)
        runtime[validation_id] = result.returncode == 0 and recommendation_source_ok[rec_name]
        if not runtime[validation_id]:
            runtime_errors.append(f"{rec_name} validator failed")

    if run_lower_regressions:
        result = run(ROOT, [sys.executable, "-m", "unittest", "workshop.tests.validation.test_validation_architecture", "-v"])
        runtime["validation-lower-regressions"] = result.returncode == 0
        if result.returncode:
            runtime_errors.append("lower-level regression suite failed")
    else:
        runtime["validation-lower-regressions"] = True

    json_errors = []
    for path in sorted((ROOT / "workshop").rglob("*.json")):
        try:
            load_json(path)
        except json.JSONDecodeError as exc:
            json_errors.append(f"invalid Workshop JSON {path.relative_to(ROOT)}: {exc}")
    runtime["validation-all-json"] = not json_errors
    runtime_errors.extend(json_errors)

    closure_renderer = load_module("certification_renderer", ROOT / "workshop" / "scripts" / "render_sprint_1_closure.py")
    project_renderer = load_module("project_report_renderer", ROOT / "workshop" / "scripts" / "render_project_report.py")
    cert_md = CERT_PATH.with_suffix(".md")
    backlog_path = paths.get("backlog")
    project_report_path = paths.get("project_report")
    parity = {
        "validation-cert-renderer": renderer_matches(cert_md, lambda: closure_renderer.render_certification(cert)),
        "validation-backlog-renderer": renderer_matches(backlog_path.with_suffix(".md") if backlog_path else None, lambda: closure_renderer.render_backlog(docs.get("backlog"))),
        "validation-report-renderer": renderer_matches(project_report_path.with_suffix(".md") if project_report_path else None, lambda: project_renderer.render_report(docs.get("project_report"))),
    }
    runtime.update(parity)
    for validation_id, diagnostic in (
        ("validation-cert-renderer", "certification Markdown differs from deterministic renderer output"),
        ("validation-backlog-renderer", "backlog Markdown differs from deterministic renderer output"),
        ("validation-report-renderer", "project report Markdown differs from deterministic renderer output"),
    ):
        if not parity[validation_id]:
            runtime_errors.append(diagnostic)
    runtime["validation-scope"] = scope_ok
    checks.append(("validation orchestration, all JSON, and deterministic renderers", runtime_errors))

    deck = load_module("deck_helpers_for_certification", VALIDATION_DIR / "validate_deck_versions.py")
    current, current_errors = deck.parse_current_deck(paths.get("current_decklist"))
    resulting = docs.get("resulting_deck_version") or {}
    resulting_counters = {zone: deck.section_counter(resulting, zone)[0] for zone in ("commander", "main_deck", "sideboard")}
    current_aligned = not current_errors and current == resulting_counters
    def source_key_ok(key, *markers):
        unresolved = f"source {key!r}"
        return not any(
            error.startswith(unresolved) or any(marker in error for marker in markers)
            for error in source_errors
        )

    source_key_truth = {key: source_key_ok(key) for key in REQUIRED_SOURCE_KEYS}
    source_key_truth.update({
        "project": source_key_ok("project", "project source", "project current", "project scope"),
        "brief": source_key_ok("brief", "brief source"),
        "baseline_deck_version": source_key_ok("baseline_deck_version", "baseline DeckVersion"),
        "resulting_deck_version": source_key_ok("resulting_deck_version", "resulting DeckVersion"),
        "baseline_analysis": source_key_ok("baseline_analysis", "baseline analysis"),
        "rec_001": recommendation_source_ok["rec-001"],
        "rec_002": recommendation_source_ok["rec-002"],
        "product_owner_review": source_key_ok("product_owner_review", "Product Owner review"),
        "decisions": source_key_ok("decisions", "decision source", "decision source set"),
        "deck_change_design": source_key_ok("deck_change_design", "deck-change design"),
        "project_report": source_key_ok("project_report", "project report source", "project report version"),
        "card_facts": source_key_ok("card_facts", "canonical Card Facts"),
        "active_candidate_facts": source_key_ok("active_candidate_facts", "active candidate facts"),
        "functional_knowledge": source_key_ok("functional_knowledge", "Functional Knowledge"),
        "candidate_lifecycle_metadata": source_key_ok("candidate_lifecycle_metadata", "candidate lifecycle"),
        "backlog": source_key_ok("backlog", "backlog source"),
    })
    source_domain_truth = {
        "project": all(source_key_truth[key] for key in ("project", "brief", "project_readme", "notes")),
        "deck_version": all(source_key_truth[key] for key in ("current_decklist", "baseline_deck_version", "resulting_deck_version")),
        "card_facts_knowledge": all(source_key_truth[key] for key in ("card_facts", "active_candidate_facts", "functional_knowledge", "candidate_lifecycle_metadata")),
        "analysis": source_key_truth["baseline_analysis"],
        "recommendation": all(source_key_truth[key] for key in ("rec_001", "rec_002")),
        "review_decision": all(source_key_truth[key] for key in ("product_owner_review", "decisions", "deck_change_design")),
        "versioning": all(source_key_truth[key] for key in ("current_decklist", "baseline_deck_version", "resulting_deck_version", "decisions", "deck_change_design")),
        "reporting": source_key_truth["project_report"],
        "validation": all(source_key_truth[key] for key in ("validation_documentation", "regression_checklists", "backlog")),
    }
    report_parity = runtime.get("validation-report-renderer", False)
    stage_truth = {
        step_id: all(source_key_truth.get(key, False) for key in source_keys)
        for step_id, _, source_keys, _ in LOOP_CONTRACT
    }
    stage_truth["loop-07"] = stage_truth["loop-07"] and bool((docs.get("baseline_analysis") or {}).get("analysis_id"))
    stage_truth["loop-08"] = stage_truth["loop-08"] and bool((docs.get("baseline_analysis") or {}).get("structural_pressure_points"))
    stage_truth["loop-09"] = source_domain_truth["recommendation"] and runtime.get("validation-rec-001", False) and runtime.get("validation-rec-002", False)
    stage_truth["loop-11"] = stage_truth["loop-11"] and len(docs.get("decisions") or []) == 3
    stage_truth["loop-13"] = stage_truth["loop-13"] and (docs.get("deck_change_design") or {}).get("product_owner_approved") is True
    stage_truth["loop-14"] = stage_truth["loop-14"] and current_aligned
    stage_truth["loop-15"] = stage_truth["loop-15"] and report_parity
    loop_errors = []
    records = cert.get("product_loop") if isinstance(cert.get("product_loop"), list) else []
    if [item.get("step_id") for item in records] != [item[0] for item in LOOP_CONTRACT]:
        loop_errors.append("product loop stage order does not match the canonical contract")
    by_step = {item.get("step_id"): item for item in records}
    for step_id, title, source_keys, artifact_ids in LOOP_CONTRACT:
        item = by_step.get(step_id, {})
        expected_status = "complete" if stage_truth[step_id] else "incomplete"
        boundaries = (item.get("input_boundary"), item.get("output_boundary"), item.get("evidence_note"))
        if (item.get("title") != title or item.get("source_keys") != source_keys
                or item.get("artifact_ids") != artifact_ids or item.get("status") != expected_status
                or not all(isinstance(value, str) and value.strip() for value in boundaries)):
            loop_errors.append(f"product loop stage {step_id} does not match derived completion evidence")
    checks.append(("derived ordered product loop", loop_errors))

    report_evidence_ok = not evidence_errors
    criterion_truth = {
        criterion_id: all(source_key_truth.get(key, False) for key in source_keys)
        for criterion_id, source_keys in CRITERION_SOURCES.items()
    }
    criterion_truth.update({
        "exit-06": criterion_truth["exit-06"] and (docs.get("resulting_deck_version") or {}).get("parent_version_id") == "v1.0",
        "exit-10": criterion_truth["exit-10"] and bool((docs.get("baseline_analysis") or {}).get("structural_pressure_points")),
        "exit-11": source_domain_truth["recommendation"] and runtime.get("validation-rec-001", False) and runtime.get("validation-rec-002", False),
        "exit-12": source_key_truth["rec_002"] and runtime.get("validation-rec-002", False),
        "exit-13": criterion_truth["exit-13"] and runtime.get("validation-rec-002", False),
        "exit-14": criterion_truth["exit-14"] and runtime.get("validation-rec-002", False) and runtime.get("validation-review", False),
        "exit-15": criterion_truth["exit-15"] and len(docs.get("decisions") or []) == 3,
        "exit-16": criterion_truth["exit-16"] and all(item.get("implementation_rationale") for item in (docs.get("decisions") or [])),
        "exit-17": criterion_truth["exit-17"] and (docs.get("deck_change_design") or {}).get("product_owner_approved") is True,
        "exit-18": criterion_truth["exit-18"] and (docs.get("resulting_deck_version") or {}).get("parent_version_id") == "v1.0",
        "exit-19": criterion_truth["exit-19"] and current_aligned,
        "exit-20": criterion_truth["exit-20"] and report_parity,
        "exit-22": criterion_truth["exit-22"] and not runtime_errors,
        "exit-23": criterion_truth["exit-23"] and not closure_errors,
        "exit-24": criterion_truth["exit-24"] and not closure_errors and backlog_ok,
        "exit-25": criterion_truth["exit-25"] and backlog_ok,
        "exit-26": criterion_truth["exit-26"] and report_evidence_ok,
        "exit-27": criterion_truth["exit-27"] and scope_ok and not closure_errors,
    })
    criterion_errors = []
    criteria = cert.get("sprint_exit_criteria") if isinstance(cert.get("sprint_exit_criteria"), list) else []
    if [item.get("criterion_id") for item in criteria] != list(CRITERION_SOURCES):
        criterion_errors.append("Sprint exit criterion set/order does not match the canonical contract")
    derived_status = {}
    for item in criteria:
        criterion_id = item.get("criterion_id")
        if criterion_id not in CRITERION_SOURCES:
            continue
        status = "pending_external_review" if criterion_id == "exit-24" and criterion_truth[criterion_id] else ("pass" if criterion_truth[criterion_id] else "fail")
        derived_status[criterion_id] = status
        if item.get("status") != status:
            criterion_errors.append(f"Sprint exit criterion {criterion_id} status does not match derived evidence")
        if item.get("evidence_source_keys") != CRITERION_SOURCES[criterion_id]:
            criterion_errors.append(f"Sprint exit criterion {criterion_id} evidence source keys are incorrect")
        expected_limitation = "External RFC and ADR synchronization remains pending." if criterion_id == "exit-24" and status == "pending_external_review" else None
        if item.get("requirement_level") != "required" or item.get("limitations") != expected_limitation or not item.get("title") or not item.get("rationale"):
            criterion_errors.append(f"Sprint exit criterion {criterion_id} requirement metadata is incorrect")
    checks.append(("derived Sprint exit criteria", criterion_errors))

    gate_errors = []
    gates = cert.get("quality_gates") if isinstance(cert.get("quality_gates"), list) else []
    if [item.get("gate_id") for item in gates] != [item[0] for item in GATE_CONTRACT]:
        gate_errors.append("quality gate set/order does not match the canonical contract")
    by_gate = {item.get("gate_id"): item for item in gates}
    lifecycle_limitations = {
        "pending_independent_review": "Independent review remains pending.",
        "certified": None,
        "certified_with_non_blocking_followups": "Non-blocking follow-ups remain to be tracked.",
        "not_certified": "Blocking independent-review findings require remediation.",
    }
    expected_gate_limitation = lifecycle_limitations.get(cert.get("certification_status"))
    for gate_id, label, dependencies in GATE_CONTRACT:
        item = by_gate.get(gate_id, {})
        dependency_pass = all(stage_truth.get(dep, False) if dep.startswith("loop-") else derived_status.get(dep) in {"pass", "pending_external_review"} for dep in dependencies)
        expected_sources = sorted({key for dep in dependencies if dep.startswith("exit-") for key in CRITERION_SOURCES[dep]})
        if (item.get("label") != label or item.get("dependency_ids") != dependencies
                or item.get("status") != ("pass" if dependency_pass else "fail")
                or item.get("evidence_source_keys") != expected_sources
                or item.get("outcome") != "All declared dependencies are derived as satisfied."
                or item.get("limitations") != expected_gate_limitation):
            gate_errors.append(f"quality gate {gate_id} does not match derived dependencies")
    checks.append(("derived quality gates", gate_errors))

    dod_errors = []
    dod = cert.get("definition_of_done") if isinstance(cert.get("definition_of_done"), list) else []
    if [item.get("capability") for item in dod] != DOD_CAPABILITIES:
        dod_errors.append("Definition of Done capability set/order is incorrect")
    rec_ok = runtime.get("validation-rec-001", False) and runtime.get("validation-rec-002", False)
    capability_truth = {
        "project workspace": (source_domain_truth["project"] and not closure_errors, source_domain_truth["project"], source_domain_truth["project"] and not closure_errors),
        "deck import and DeckVersion": (source_domain_truth["deck_version"] and current_aligned, source_domain_truth["deck_version"] and current_aligned, source_domain_truth["deck_version"] and current_aligned),
        "Card Facts and Knowledge": (source_domain_truth["card_facts_knowledge"] and runtime.get("validation-knowledge", False), source_domain_truth["card_facts_knowledge"], source_domain_truth["card_facts_knowledge"] and runtime.get("validation-knowledge", False)),
        "analysis": (source_domain_truth["analysis"] and stage_truth["loop-07"], source_domain_truth["analysis"], source_domain_truth["analysis"] and stage_truth["loop-08"]),
        "recommendation": (source_domain_truth["recommendation"] and rec_ok, source_domain_truth["recommendation"] and rec_ok, source_domain_truth["recommendation"] and rec_ok and runtime.get("validation-review", False)),
        "review and decision": (source_domain_truth["review_decision"] and runtime.get("validation-review", False), source_domain_truth["review_decision"] and runtime.get("validation-decision", False), source_domain_truth["review_decision"] and stage_truth["loop-11"]),
        "versioning": (source_domain_truth["versioning"] and runtime.get("validation-deck-version", False), source_domain_truth["versioning"] and current_aligned, source_domain_truth["versioning"] and current_aligned),
        "reporting": (source_domain_truth["reporting"] and report_parity, source_domain_truth["reporting"] and runtime.get("validation-project-report", False) and report_parity, source_domain_truth["reporting"] and report_evidence_ok),
        "validation": (source_domain_truth["validation"] and not runtime_errors, source_domain_truth["validation"] and runtime.get("validation-lower-regressions", False) and runtime.get("validation-all-json", False), source_domain_truth["validation"] and not runtime_errors),
    }
    for item in dod:
        truth = capability_truth.get(item.get("capability"), (False, False, False))
        expected = {"functional_done": "pass" if truth[0] else "fail", "structural_done": "pass" if truth[1] else "fail", "product_done": "pass" if truth[2] else "fail"}
        for field, value in expected.items():
            if item.get(field) != value:
                dod_errors.append(f"Definition of Done {item.get('capability')!r} {field} does not match derived evidence")
    checks.append(("derived Functional, Structural, and Product Done", dod_errors))

    contract_errors = []
    contract = cert.get("validation_contract") if isinstance(cert.get("validation_contract"), list) else []
    if [item.get("validation_id") for item in contract] != [item[0] for item in VALIDATION_COMMANDS]:
        contract_errors.append("validation contract set/order does not match actual certification execution")
    by_validation = {item.get("validation_id"): item for item in contract}
    for validation_id, label, command in VALIDATION_COMMANDS:
        item = by_validation.get(validation_id, {})
        expected_status = "pass" if runtime.get(validation_id, False) else "fail"
        if item.get("label") != label or item.get("command") != command or item.get("status") != expected_status:
            contract_errors.append(f"validation contract record {validation_id} does not match actual execution")
    checks.append(("validation contract matches actual execution", contract_errors))

    return emit(checks)


def main():
    return validate_certification(
        ROOT,
        expected_base_commit=EXPECTED_BASE_COMMIT,
        run_lower_regressions=True,
    )


if __name__ == "__main__":
    sys.exit(main())
