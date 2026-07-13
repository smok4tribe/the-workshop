#!/usr/bin/env python3
"""Render Simulation Policy and Simulation Question Markdown from structured JSON.

The renderer is deterministic and data-driven: a clean render must leave the
committed Markdown companions unchanged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "workshop" / "projects" / "the-myr-singularity" / "simulation"
DEFAULT_POLICY = SIM_DIR / "simulation_policy.json"
DEFAULT_QUESTION = SIM_DIR / "questions" / "question-001-mana-color.json"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bullet_lines(items):
    return [f"- {item}" for item in items]


def render_policy(policy):
    scenario = policy["commander_scenario"]
    turns = policy["turn_semantics"]
    mull = policy["mulligan_policy"]
    keep = policy["keep_rule"]
    base = keep["base_rule"]
    bottom = policy["bottoming_rule"]
    rng = policy["randomness_policy"]
    iters = policy["iteration_policy"]
    unc = policy["uncertainty_policy"]
    fp = policy["deck_fingerprint_policy"]
    boundary = policy["card_behavior_boundary"]
    lines = [
        f"# Simulation Policy {policy['policy_version']}",
        "",
        f"Policy id: `{policy['policy_id']}` — project `{policy['project_id']}`",
        "",
        "## Purpose",
        "",
        policy["purpose"],
        "",
        "## Commander Scenario",
        "",
        f"- Format: {scenario['format']}",
        f"- Table: {scenario['table']}",
        f"- Seat: {scenario['seat']}",
        f"- First-turn draw: {str(scenario['first_turn_draw']).lower()}",
        f"- Opening hand size: {scenario['opening_hand_size']}",
        f"- Commander starts in command zone: {str(scenario['commander_starts_in_command_zone']).lower()}",
        "",
        f"{scenario['first_turn_draw_note']}",
        "",
        "## Turn Semantics",
        "",
        f"- Turn indexing: {turns['turn_indexing']}",
        f"- Opening hand is turn: {turns['opening_hand_is_turn']}",
        f"- First drawn turn: {turns['first_drawn_turn']}",
        f"- Observation horizon turn: {turns['observation_horizon_turn']}",
        "",
        turns["horizon_note"],
        "",
        "## Mulligan Policy",
        "",
        f"- Policy: {mull['policy_name']}",
        f"- Free mulligans: {mull['free_mulligans']}",
        f"- Subsequent rule: {mull['subsequent_mulligan_rule']}",
        f"- Maximum mulligans: {mull['max_mulligans']}",
        "",
        mull["description"],
        "",
        "Resolution order:",
        "",
        *[f"{index}. {step}" for index, step in enumerate(mull["resolution_order"], start=1)],
        "",
        "## Keep Rule",
        "",
        f"Rule id: `{keep['rule_id']}`",
        "",
        f"- {base['keep_land_count_range']['description']}",
        f"- One-land hand: {base['one_land_exception']['condition']}",
        f"- Zero-land hands: {base['zero_land_hands']}",
        f"- Six-or-seven-land hands: {base['six_or_seven_land_hands']}",
        "",
        "Modeled unconditional early acceleration: "
        f"{base['one_land_exception']['modeled_unconditional_early_acceleration']}",
        "",
        "Explicitly not evaluated:",
        "",
        *bullet_lines(keep["explicitly_not_evaluated"]),
        "",
        "Project extension points:",
        "",
        *bullet_lines(keep["project_extension_points"]["overridable_fields"]),
        "",
        "Non-overridable invariants:",
        "",
        *bullet_lines(keep["project_extension_points"]["non_overridable_invariants"]),
        "",
        "## Bottoming Rule",
        "",
        f"Rule id: `{bottom['rule_id']}`",
        "",
        *[
            f"{entry['rank']}. {entry['selector']} — {entry['description']}"
            for entry in bottom["priority_order"]
        ],
        "",
        "## Card Behavior Boundary",
        "",
        "Supported behavior sources:",
        "",
        *bullet_lines(boundary["supported_behavior_sources"]),
        "",
        f"Unsupported behavior handling: {boundary['unsupported_behavior_handling']['rule']} "
        f"{boundary['unsupported_behavior_handling']['surfacing']}",
        "",
        f"Hard invariant: {boundary['unsupported_behavior_handling']['hard_invariant']}",
        "",
        f"Fixture-specific modeled card behavior lives in `{policy['references']['card_semantics']}`.",
        "",
        "## Randomness Policy",
        "",
        f"- RNG id: {rng['rng_id']}",
        f"- Seed type: {rng['seed_type']}",
        f"- Seed derivation: `{rng['canonical_seed_derivation']['algorithm_id']}` over "
        f"{' + '.join(rng['canonical_seed_derivation']['inputs_in_order'])}",
        f"- Seed extraction: {rng['canonical_seed_derivation']['seed_extraction']}",
        "",
        "## Iteration and Uncertainty",
        "",
        f"- Minimum saved iterations: {iters['minimum_saved_iterations']}",
        f"- Canonical comparative iterations: {iters['canonical_comparative_iterations']}",
        f"- Confidence presentation: {unc['confidence_presentation']} ({unc['interval_method']})",
        f"- Required reported fields: {', '.join(unc['required_reported_fields'])}",
        f"- Relative delta: {unc['relative_delta_rule']['status']}; valid only when "
        f"{unc['relative_delta_rule']['valid_only_when']}",
        "",
        "## Deck-Content Fingerprint",
        "",
        f"Algorithm id: `{fp['algorithm_id']}`",
        "",
        f"- Included zones: {', '.join(zone['zone_label'] for zone in fp['included_zones'])}",
        f"- Excluded: {', '.join(fp['excluded_from_fingerprint'])}",
        "",
        f"Reference fingerprints (deck identity only, not results): v1.0 "
        f"`{fp['reference_fingerprints']['v1.0']}`; v1.1 `{fp['reference_fingerprints']['v1.1']}`.",
        "",
        "## Evidence-Language Boundary",
        "",
        policy["evidence_language_boundary"]["statement"],
        "",
        "Forbidden claims:",
        "",
        *bullet_lines(policy["evidence_language_boundary"]["forbidden_claims"]),
        "",
        "## Lifecycle Boundary",
        "",
        policy["lifecycle_boundary"]["statement"],
        "",
        "## Boundary",
        "",
        policy["explicit_boundary"]["statement"],
    ]
    return "\n".join(lines) + "\n"


def render_question(question):
    lines = [
        f"# Simulation Question {question['question_id']}",
        "",
        f"Project `{question['project_id']}` — policy `{question['policy_id']}` "
        f"({question['policy_version']})",
        "",
        f"Execution status: **{question['execution_status']}**",
        "",
        question["execution_note"],
        "",
        "## Hypothesis",
        "",
        question["hypothesis"],
        "",
        "## Question",
        "",
        question["question_text"],
        "",
        "## Compared Versions",
        "",
        *[
            f"- {version['deck_version_id']} ({version['run_role']}): "
            f"`{version['deck_content_fingerprint']}`"
            for version in question["compared_versions"]
        ],
        "",
        "## Target Metrics",
        "",
        *[
            f"- {metric['metric_id']} by turn {metric['target_turn']}"
            for metric in question["target_metrics"]
        ],
        "",
        "## Success Interpretation",
        "",
        question["success_interpretation"]["directional_expectation"],
        "",
        question["success_interpretation"]["notes"],
        "",
        "## Limitations",
        "",
        *bullet_lines(question["limitations"]),
        "",
        "## Boundary",
        "",
        question["explicit_boundary"]["statement"],
    ]
    return "\n".join(lines) + "\n"


def render_target(path):
    document = load_json(path)
    artifact_type = document.get("artifact_type")
    if artifact_type == "simulation_policy":
        return path.with_suffix(".md"), render_policy(document)
    if artifact_type == "simulation_question":
        return path.with_suffix(".md"), render_question(document)
    raise ValueError(f"unsupported artifact_type for rendering: {artifact_type!r}")


def main(argv=None):
    argv = argv or sys.argv[1:]
    targets = [Path(arg) for arg in argv] if argv else [DEFAULT_POLICY, DEFAULT_QUESTION]
    for target in targets:
        markdown_path, text = render_target(target)
        markdown_path.write_text(text, encoding="utf-8")
        print(f"Rendered {markdown_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
