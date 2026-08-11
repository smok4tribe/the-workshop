"""Authoritative Sprint 1 certification contract and reusable validation helpers."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


EXPECTED_BASE_COMMIT = "7387afcb9a6345a97083506245fa6414504ad654"
PROJECT_ID = "the-myr-singularity"
SPRINT_ID = "Sprint 1"
CERTIFICATION_SCOPE = "sprint_1_local_prototype"
HISTORICALLY_IMMUTABLE_SPRINT_1_ARTIFACTS = frozenset({
    "workshop/projects/the-myr-singularity/versions/v1.0.json",
    "workshop/projects/the-myr-singularity/versions/v1.1.json",
    "workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json",
    "workshop/projects/the-myr-singularity/analysis/baseline_v1.0.md",
    "workshop/projects/the-myr-singularity/recommendations/rec-001.json",
    "workshop/projects/the-myr-singularity/recommendations/rec-002.json",
    "workshop/projects/the-myr-singularity/recommendations/review-rec-002.json",
    "workshop/projects/the-myr-singularity/decisions/decision-002.json",
    "workshop/projects/the-myr-singularity/decisions/decision-003.json",
    "workshop/projects/the-myr-singularity/decisions/decision-004.json",
    "workshop/projects/the-myr-singularity/decisions/deck-change-design-v1.1.json",
    "workshop/projects/the-myr-singularity/reports/project_report_v1.1.json",
    "workshop/projects/the-myr-singularity/reports/project_report_v1.1.md",
    "workshop/card-data/cards.json",
    "workshop/card-data/candidate_cards.json",
    "workshop/card-data/candidate_card_import_metadata.json",
    "workshop/knowledge/functional_roles.json",
})

CERTIFICATION_RECORDING_PATHS = {
    "certification": "workshop/projects/the-myr-singularity/reports/sprint_1_certification.json",
    "markdown": "workshop/projects/the-myr-singularity/reports/sprint_1_certification.md",
    "independent_review": "workshop/projects/the-myr-singularity/reports/sprint_1_certification_review.json",
}

CANONICAL_INDEPENDENT_REVIEW_SOURCE = {
    "path": CERTIFICATION_RECORDING_PATHS["independent_review"],
}

SPRINT_1_SOURCE_REFERENCE_CONTRACT = {
    "project": {"path": "workshop/projects/the-myr-singularity/project.json", "id": "the-myr-singularity"},
    "brief": {"path": "workshop/projects/the-myr-singularity/brief/brief.json", "project_id": "the-myr-singularity"},
    "current_decklist": {"path": "workshop/projects/the-myr-singularity/deck/current.txt"},
    "baseline_deck_version": {"path": "workshop/projects/the-myr-singularity/versions/v1.0.json", "id": "v1.0"},
    "resulting_deck_version": {"path": "workshop/projects/the-myr-singularity/versions/v1.1.json", "id": "v1.1"},
    "card_facts": {"path": "workshop/card-data/cards.json"},
    "active_candidate_facts": {"path": "workshop/card-data/candidate_cards.json"},
    "functional_knowledge": {"path": "workshop/knowledge/functional_roles.json"},
    "candidate_lifecycle_metadata": {"path": "workshop/card-data/candidate_card_import_metadata.json"},
    "baseline_analysis": {"path": "workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json", "id": "baseline_v1.0"},
    "rec_001": {"path": "workshop/projects/the-myr-singularity/recommendations/rec-001.json", "id": "rec-001"},
    "rec_002": {"path": "workshop/projects/the-myr-singularity/recommendations/rec-002.json", "id": "rec-002"},
    "product_owner_review": {"path": "workshop/projects/the-myr-singularity/recommendations/review-rec-002.json", "recommendation_id": "rec-002"},
    "decisions": [
        {"path": "workshop/projects/the-myr-singularity/decisions/decision-002.json", "id": "decision-002"},
        {"path": "workshop/projects/the-myr-singularity/decisions/decision-003.json", "id": "decision-003"},
        {"path": "workshop/projects/the-myr-singularity/decisions/decision-004.json", "id": "decision-004"},
    ],
    "deck_change_design": {"path": "workshop/projects/the-myr-singularity/decisions/deck-change-design-v1.1.json", "id": "deck-change-design-v1.1"},
    "project_report": {"path": "workshop/projects/the-myr-singularity/reports/project_report_v1.1.json", "id": "project-report-v1.1"},
    "changelog": {"path": "workshop/projects/the-myr-singularity/reports/changelog.md"},
    "notes": {"path": "workshop/projects/the-myr-singularity/notes/notes.md"},
    "backlog": {"path": "workshop/projects/the-myr-singularity/notes/backlog.json"},
    "regression_checklists": [
        {"path": "workshop/tests/regression/product_principles.md"},
        {"path": "workshop/tests/regression/data_model.md"},
        {"path": "workshop/tests/regression/reasoning.md"},
        {"path": "workshop/tests/regression/simulation.md"},
    ],
    "validation_documentation": {"path": "workshop/tests/validation/README.md"},
    "project_readme": {"path": "workshop/projects/the-myr-singularity/README.md"},
    "documentation_handoff": {"path": "workshop/projects/the-myr-singularity/notes/sprint_1_documentation_handoff.md"},
}

REQUIRED_SOURCE_KEYS = frozenset(SPRINT_1_SOURCE_REFERENCE_CONTRACT)

LOOP_CONTRACT = [
    ("loop-01", "Project", ["project"], ["the-myr-singularity"]),
    ("loop-02", "Brief", ["brief"], ["Initial Sprint 1 Project Brief"]),
    ("loop-03", "Deck Import", ["current_decklist", "baseline_deck_version"], ["v1.0"]),
    ("loop-04", "Baseline DeckVersion", ["baseline_deck_version"], ["v1.0"]),
    ("loop-05", "Card Facts", ["card_facts", "active_candidate_facts", "candidate_lifecycle_metadata"], ["canonical-card-facts", "candidate-card-facts"]),
    ("loop-06", "Functional Knowledge", ["functional_knowledge"], ["Functional Role Assignments"]),
    ("loop-07", "Baseline Analysis", ["baseline_analysis"], ["baseline_v1.0"]),
    ("loop-08", "Structural Weakness", ["baseline_analysis"], ["baseline_v1.0:structural_pressure_points"]),
    ("loop-09", "Recommendation", ["rec_001", "rec_002"], ["rec-001", "rec-002"]),
    ("loop-10", "Product Owner Review", ["product_owner_review", "rec_002"], ["rec-002:product-owner-review"]),
    ("loop-11", "Decision", ["decisions", "product_owner_review"], ["decision-002", "decision-003", "decision-004"]),
    ("loop-12", "Deck-change Design", ["deck_change_design", "decisions"], ["deck-change-design-v1.1"]),
    ("loop-13", "Product Owner Approval", ["deck_change_design"], ["deck-change-design-v1.1:approval"]),
    ("loop-14", "Resulting DeckVersion", ["resulting_deck_version", "current_decklist", "deck_change_design"], ["v1.1"]),
    ("loop-15", "Report", ["project_report"], ["project-report-v1.1"]),
]

CRITERION_SOURCES = {
    "exit-01": ["project"], "exit-02": ["project"], "exit-03": ["brief"],
    "exit-04": ["current_decklist"], "exit-05": ["baseline_deck_version"],
    "exit-06": ["baseline_deck_version", "resulting_deck_version"],
    "exit-07": ["card_facts", "candidate_lifecycle_metadata"],
    "exit-08": ["functional_knowledge", "card_facts"],
    "exit-09": ["baseline_analysis", "baseline_deck_version"],
    "exit-10": ["baseline_analysis"], "exit-11": ["rec_001", "rec_002"],
    "exit-12": ["rec_002"],
    "exit-13": ["rec_002", "product_owner_review", "baseline_deck_version"],
    "exit-14": ["product_owner_review", "rec_002"],
    "exit-15": ["decisions", "rec_002"], "exit-16": ["decisions"],
    "exit-17": ["decisions", "deck_change_design", "resulting_deck_version"],
    "exit-18": ["baseline_deck_version", "resulting_deck_version"],
    "exit-19": ["current_decklist", "resulting_deck_version"],
    "exit-20": ["project_report"], "exit-21": ["project_report"],
    "exit-22": ["validation_documentation", "regression_checklists"],
    "exit-23": ["notes"], "exit-24": ["documentation_handoff", "backlog"],
    "exit-25": ["backlog"],
    "exit-26": ["project_report", "active_candidate_facts", "product_owner_review"],
    "exit-27": ["project", "project_readme"],
}

GATE_CONTRACT = [
    ("gate-project", "Project Gate", ["exit-01", "exit-02", "exit-03", "exit-04", "exit-05", "exit-06"]),
    ("gate-analysis", "Analysis Gate", ["exit-07", "exit-08", "exit-09", "exit-10"]),
    ("gate-recommendation", "Recommendation Gate", ["exit-11", "exit-12", "exit-13", "exit-14"]),
    ("gate-decision-versioning", "Decision and Versioning Gate", ["exit-15", "exit-16", "exit-17", "exit-18", "exit-19"]),
    ("gate-report", "Report Gate", ["exit-20", "exit-21"]),
    ("gate-product-loop", "Product Loop Gate", [f"loop-{index:02d}" for index in range(1, 16)]),
    ("gate-data-knowledge", "Data and Knowledge Boundary Gate", ["exit-07", "exit-08"]),
    ("gate-evidence-honesty", "Evidence Honesty Gate", ["exit-26", "exit-27"]),
    ("gate-reproducibility", "Reproducibility Gate", ["exit-22"]),
    ("gate-scope-control", "Scope-Control Gate", ["exit-06", "exit-13", "exit-27"]),
]

DOD_CAPABILITIES = [
    "project workspace", "deck import and DeckVersion", "Card Facts and Knowledge",
    "analysis", "recommendation", "review and decision", "versioning", "reporting",
    "validation",
]

VALIDATION_COMMANDS = [
    ("validation-knowledge", "Knowledge", "python workshop/tests/validation/validate_knowledge_layer.py"),
    ("validation-candidate-facts", "Candidate Card Facts", "python workshop/tests/validation/validate_candidate_card_facts.py"),
    ("validation-rec-001", "Recommendation rec-001", "python workshop/tests/validation/validate_recommendation_schema.py [rec-001]"),
    ("validation-rec-002", "Recommendation rec-002", "python workshop/tests/validation/validate_recommendation_schema.py [rec-002]"),
    ("validation-review", "Product Owner review", "python workshop/tests/validation/validate_recommendation_review.py"),
    ("validation-decision", "Decision pipeline", "python workshop/tests/validation/validate_decision_pipeline.py"),
    ("validation-deck-version", "DeckVersion", "python workshop/tests/validation/validate_deck_versions.py"),
    ("validation-project-report", "Project report", "python workshop/tests/validation/validate_project_reports.py"),
    ("validation-lower-regressions", "Lower-level regression suite", "python -m unittest workshop.tests.validation.test_validation_architecture -v"),
    ("validation-all-json", "All Workshop JSON", "parse workshop/**/*.json"),
    ("validation-cert-renderer", "Certification renderer", "render certification JSON to Markdown"),
    ("validation-backlog-renderer", "Backlog renderer", "render backlog JSON to Markdown"),
    ("validation-report-renderer", "Project report renderer", "render project report JSON to Markdown"),
    ("validation-scope", "Scope-control diff", "git diff candidate base to HEAD"),
]

CHECKLIST_CONTRACT = {
    "product_principles.md": ("# Product Principles Regression Checklist", {"PP-01", "PP-02", "PP-03"}),
    "data_model.md": ("# Data Model Regression Checklist", {"DM-01", "DM-02", "DM-03"}),
    "reasoning.md": ("# Reasoning Regression Checklist", {"RS-01", "RS-02", "RS-03"}),
    "simulation.md": ("# Simulation Regression Checklist", {"SIM-01", "SIM-02", "SIM-03"}),
}

CHECKLIST_EVIDENCE = {
    "PP-01": {"workshop/projects/the-myr-singularity/project.json", "workshop/projects/the-myr-singularity/brief/brief.json"},
    "PP-02": {"workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json", "workshop/projects/the-myr-singularity/recommendations/rec-002.json"},
    "PP-03": {"workshop/projects/the-myr-singularity/recommendations/review-rec-002.json", "workshop/projects/the-myr-singularity/reports/project_report_v1.1.json"},
    "DM-01": {"workshop/projects/the-myr-singularity/project.json", "workshop/card-data/cards.json"},
    "DM-02": {"workshop/projects/the-myr-singularity/versions/v1.0.json", "workshop/projects/the-myr-singularity/versions/v1.1.json"},
    "DM-03": {"workshop/card-data/candidate_card_import_metadata.json", "workshop/card-data/candidate_cards.json"},
    "RS-01": {"workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json", "workshop/projects/the-myr-singularity/recommendations/rec-002.json"},
    "RS-02": {"workshop/projects/the-myr-singularity/decisions/decision-002.json", "workshop/projects/the-myr-singularity/decisions/decision-003.json", "workshop/projects/the-myr-singularity/decisions/decision-004.json"},
    "RS-03": {"workshop/projects/the-myr-singularity/reports/project_report_v1.1.json"},
    "SIM-01": {"workshop/projects/the-myr-singularity/reports/project_report_v1.1.json"},
    "SIM-02": {"workshop/projects/the-myr-singularity/reports/project_report_v1.1.json"},
    "SIM-03": {"workshop/projects/the-myr-singularity/notes/backlog.json"},
}

CHECKLIST_STATES = {
    "PP-01": "x", "PP-02": "x", "PP-03": "x",
    "DM-01": "x", "DM-02": "x", "DM-03": "x",
    "RS-01": "x", "RS-02": "x", "RS-03": "x",
    "SIM-01": "~", "SIM-02": "~", "SIM-03": "~",
}

BACKLOG_WORK_TYPES = {
    "post_implementation_analysis", "mana_color_simulation", "candidate_testing_kci",
    "candidate_testing_mana_echoes", "version_state_cleanup",
    "append_only_transition_history", "external_rfc_sync",
}

NON_GOALS = [
    "polished UI", "SaaS architecture", "production database",
    "automatic recommendation generation", "full Commander rules engine",
    "full gameplay simulation", "multiplayer modeling", "power or win-rate accuracy",
    "production scalability", "complete external platform integration",
]

CLAIM_BOUNDARY = (
    "Certification concerns local product-loop execution, structure, traceability, "
    "reproducibility, and evidence honesty. It does not claim measured deck performance."
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_repo_path(root, reference):
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        return None
    path = (root / reference["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def run(root, args, env=None):
    process_env = os.environ.copy()
    if env:
        process_env.update({key: str(value) for key, value in env.items()})
    return subprocess.run(
        [str(value) for value in args], cwd=root, env=process_env,
        text=True, encoding="utf-8", capture_output=True, check=False,
    )


def git(root, *args):
    return run(root, ["git", *args])


def normalize_git_path(value):
    if not isinstance(value, str):
        raise ValueError("Git name-status path is not text")
    path = value.strip().replace("\\", "/")
    if not path or path.startswith("/") or path.startswith("../") or "/../" in path:
        raise ValueError(f"invalid Git name-status path: {value!r}")
    return path


def parse_git_name_status(output):
    """Parse ``git diff --name-status -M`` output without dropping rename sides."""
    records = []
    for raw_line in output.splitlines():
        if not raw_line:
            raise ValueError("empty Git name-status record")
        fields = raw_line.split("\t")
        status = fields[0]
        kind = status[:1]
        if kind in {"A", "M", "D", "T"}:
            if status != kind or len(fields) != 2:
                raise ValueError(f"malformed Git name-status record: {raw_line!r}")
            paths = (normalize_git_path(fields[1]),)
        elif kind in {"R", "C"}:
            if not status[1:].isdigit() or len(fields) != 3:
                raise ValueError(f"malformed Git name-status record: {raw_line!r}")
            paths = (normalize_git_path(fields[1]), normalize_git_path(fields[2]))
        else:
            raise ValueError(f"unsupported Git name-status record: {raw_line!r}")
        records.append((status, paths))
    return tuple(sorted(records, key=lambda record: (record[1], record[0])))


def immutable_name_status_changes(records):
    """Return deterministic (status, paths) records touching historical evidence."""
    return tuple(
        record for record in records
        if any(path in HISTORICALLY_IMMUTABLE_SPRINT_1_ARTIFACTS for path in record[1])
    )


def source_reference_contract_errors(references):
    if not isinstance(references, dict):
        return ["source_references must be an object"]
    errors = []
    if set(references) != REQUIRED_SOURCE_KEYS:
        errors.append("certification source contract does not match the required source set")
    for key, expected in SPRINT_1_SOURCE_REFERENCE_CONTRACT.items():
        if references.get(key) != expected:
            errors.append(f"source {key!r} does not match the canonical Sprint 1 source-reference contract")
    return errors


def parse_checklist(root, path, expected_heading, expected_ids):
    errors = []
    text = path.read_text(encoding="utf-8")
    if expected_heading not in text or "## Required Checks" not in text:
        errors.append(f"{path.name} is missing required checklist sections")
    pattern = re.compile(r"^- \[(x|~| )\] ([A-Z]+-\d+) \| ([^|]+) \| evidence: (.+)$")
    items = []
    for line in text.splitlines():
        if line.startswith("- ["):
            match = pattern.fullmatch(line)
            if not match:
                errors.append(f"{path.name} contains malformed checklist item: {line}")
                continue
            state, item_id, _, evidence = match.groups()
            items.append((state, item_id, [value.strip() for value in evidence.split(",")]))
    ids = [item_id for _, item_id, _ in items]
    if not items:
        errors.append(f"{path.name} contains no checklist items")
    if len(ids) != len(set(ids)):
        errors.append(f"{path.name} contains duplicate checklist IDs")
    if set(ids) != expected_ids:
        errors.append(f"{path.name} checklist IDs do not match the required set")
    for state, item_id, evidence_paths in items:
        expected_state = CHECKLIST_STATES.get(item_id)
        if state != expected_state:
            errors.append(f"{path.name} checklist item {item_id} state does not match the authoritative contract")
        for relative in evidence_paths:
            if not (root / relative).is_file():
                errors.append(f"{path.name} checklist item {item_id} evidence does not resolve: {relative}")
        if set(evidence_paths) != CHECKLIST_EVIDENCE.get(item_id, set()):
            errors.append(f"{path.name} checklist item {item_id} evidence is not authoritative")
    return errors


def normalized(value):
    return " ".join(str(value).casefold().split())


def card_names_from_candidate(candidate, cards_by_id):
    names = []
    for reference in candidate.get("incoming_cards", []):
        match = re.fullmatch(r"candidate:scryfall:([0-9a-f-]+)", str(reference))
        if match and match.group(1) in cards_by_id:
            names.append(cards_by_id[match.group(1)].get("name"))
    return names
