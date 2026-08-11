#!/usr/bin/env python3
"""Render a current-state structural analysis Markdown companion from JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_DIR = REPO_ROOT / "workshop" / "tests" / "validation"
sys.path.insert(0, str(VALIDATION_DIR))
from structural_analysis import PROJECT_ID  # noqa: E402


DEFAULT_ANALYSIS = REPO_ROOT / "workshop" / "projects" / PROJECT_ID / "analysis" / "current_v1.1.json"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bullets(items):
    return [f"- {item}" for item in items]


def render_analysis(analysis):
    computed = analysis["computed"]
    identity = computed["deck_identity_summary"]
    composition = identity["composition"]
    colors = computed["color_requirements"]
    categories = computed["category_distribution"]["categories"]
    roles = computed["functional_role_density"]
    delta = analysis["historical_context"]["exact_deck_content_delta_from_v1.0"]
    lines = [
        f"# Current Structural Analysis - The Myr Singularity {analysis['deck_version_id']}",
        "",
        "Post-implementation current-state structural analysis. This document reports",
        "repository-derived deck facts; it does not report simulated or gameplay outcomes.",
        "",
        "## Identity and Provenance",
        "",
        f"- Analysis id: `{analysis['analysis_id']}`",
        f"- Method: `{analysis['analysis_method']['id']}` v{analysis['analysis_method']['version']}",
        f"- DeckVersion: `{analysis['deck_version_id']}`",
        f"- Deck-content fingerprint: `{computed['deck_content_fingerprint']}`",
        f"- Commander: {identity['commander']}",
        f"- Format: {identity['format']}",
        "",
        identity["stated_identity"],
        "",
        "## Current Composition",
        "",
        "| Fact | Value |",
        "| --- | ---: |",
        *[
            f"| {label} | {value} |"
            for label, value in (
                ("Playable cards", composition["playable_cards"]),
                ("Lands", composition["lands"]),
                ("Nonlands", composition["nonland_cards"]),
                ("Artifacts", composition["artifact_cards"]),
                ("Creatures", composition["creature_cards"]),
                ("Myr typal cards", composition["myr_typal_cards"]),
                ("Colored nonlands", composition["colored_nonland_cards"]),
                ("Average nonland mana value", composition["average_mana_value_nonland"]),
                ("Sideboard cards", composition["sideboard_cards"]),
            )
        ],
        "",
        "### Nonland mana-value curve",
        "",
        "| Mana value | Cards |",
        "| --- | ---: |",
        *[f"| {bucket.replace('_plus', '+')} | {count} |" for bucket, count in composition["mana_value_curve_nonland"].items()],
        "",
        "### Color requirements and land-role counts",
        "",
        f"- Colored nonland cards: {colors['colored_nonland_cards']}",
        f"- Colored mana symbols in nonland costs: " + ", ".join(f"{color} {count}" for color, count in colors["mana_symbol_counts"].items()),
        f"- Land cards carrying `colored_source`: {colors['colored_land_sources_by_role']}",
        f"- Land cards carrying `fixing_land`: {colors['fixing_lands_by_role']}",
        "",
        "These are card and role counts, not estimates of color access or casting success.",
        "",
        "## Functional Role Density",
        "",
        "| Role | Cards |",
        "| --- | ---: |",
        *[f"| `{role_id}` | {count} |" for role_id, count in roles.items()],
        "",
        "## Package and Category Grouping",
        "",
        "| Category | Cards with any role | Primary cards | Role assignments |",
        "| --- | ---: | ---: | ---: |",
        *[f"| {record['label']} | {record['cards_with_any_role']} | {record['cards_with_primary_role']} | {record['role_assignments_in_category']} |" for record in categories.values()],
        "",
        "## Structural Observations",
        "",
        *bullets(analysis["structural_observations"]),
        "",
        "## Structural Dependencies and Pressure Points",
        "",
        "Dependencies:",
        "",
        *bullets(analysis["structural_dependencies"]),
        "",
        "Pressure points:",
        "",
        *bullets(analysis["structural_pressure_points"]),
        "",
        "## Unsupported or Uncertain Classifications",
        "",
        *bullets(analysis["unsupported_or_uncertain_classifications"]),
        "",
        "## Historical v1.0 Context",
        "",
        f"Exact DeckVersion delta from `{delta['from_deck_version_id']}`: added {', '.join(delta['added'])}; removed {', '.join(delta['removed'])}.",
        "",
        analysis["historical_context"]["observation"],
        "",
        "## Assumptions and Limitations",
        "",
        "Assumptions:",
        "",
        *bullets(analysis["assumptions"]),
        "",
        "Limitations:",
        "",
        *bullets(analysis["limitations"]),
        "",
        "## Suggested Evidence Question",
        "",
        *[f"- `{question['question_id']}` ({question['execution_status']}): {question['purpose']}" for question in analysis["suggested_evidence_questions"]],
        "",
        "## Boundary",
        "",
        analysis["explicit_boundary"]["statement"],
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    argv = argv or sys.argv[1:]
    targets = [Path(arg) for arg in argv] if argv else [DEFAULT_ANALYSIS]
    for target in targets:
        target.with_suffix(".md").write_text(render_analysis(load_json(target)), encoding="utf-8")
        print(f"Rendered {target.with_suffix('.md').relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
