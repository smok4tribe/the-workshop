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
    level_two = policy["level_2_sequencing"]
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
        "Executable transition:",
        "",
        *bullet_lines(mull["executable_state_transition"]["rejected_hand_transition"]),
        "",
        f"RNG reset permitted: {str(mull['executable_state_transition']['rng_reset_permitted']).lower()}",
        f"Bottoming consumes RNG: {str(mull['executable_state_transition']['bottoming_consumes_rng']).lower()}",
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
        "Unsupported limitation representation:",
        "",
        f"- Format: `{boundary['unsupported_behavior_handling']['limitation_representation']['format']}`",
        f"- Derivation: {boundary['unsupported_behavior_handling']['limitation_representation']['derivation']}",
        f"- Metric boundary: {boundary['unsupported_behavior_handling']['limitation_representation']['metric_boundary']}",
        "",
        f"Fixture-specific modeled card behavior lives in `{policy['references']['card_semantics']['path']}`.",
        f"Executable mana-source profiles live in `{policy['references']['mana_source_semantics']['path']}`.",
        "",
        "## Randomness Policy",
        "",
        f"- RNG id: {rng['rng_id']}",
        f"- Seed type: {rng['seed_type']}",
        f"- Seed derivation: `{rng['canonical_seed_derivation']['algorithm_id']}` over "
        f"{' + '.join(rng['canonical_seed_derivation']['inputs_in_order'])}",
        f"- Iteration derivation: `{rng['iteration_seed_derivation']['algorithm_id']}`; fresh RNG per iteration and continuous stream across mulligans.",
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
        "## Metric Registry",
        "",
        "| Metric | Target turn | Shape | Required |",
        "| --- | ---: | --- | --- |",
        *[
            f"| {metric['metric_id']} | {metric['target_turn']} | {metric['shape']} | "
            f"{'yes' if metric['kind'] == 'primary' else 'no'} |"
            for metric in policy["metric_catalog"]["metrics"]
        ],
        "",
        "## Metric Measurement Contracts",
        "",
        "Each metric below is measured only under its complete Policy-owned contract.",
        "",
        *[
            "\n".join((
                f"### {metric['metric_id']}",
                "",
                "```json",
                json.dumps(metric["measurement_contract"], ensure_ascii=False, indent=2),
                "```",
                "",
            ))
            for metric in policy["metric_catalog"]["metrics"]
        ],
        "## Deterministic Level 2 Trace",
        "",
        *[f"{index}. `{step}`" for index, step in enumerate(level_two["turn_order"], start=1)],
        "",
        f"Urza's Saga timing: {level_two['urzas_saga_final_chapter_timing']}",
        "",
        f"Source-capability projection: {level_two['observation_projections']['source_capability']}",
        f"Spendable-mana projection: {level_two['observation_projections']['spendable_mana']}",
        "",
        f"Unsupported actions: {level_two['unsupported_actions']}",
        "",
        "## Floating Mana Model",
        "",
        "Within the bounded Level-2 development model, this is phase-scoped resource state; it is not a complete Magic mana system.",
        "",
        "```json",
        json.dumps(level_two["floating_mana_model"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Executable Mana Source Boundary",
        "",
        f"Authority: `{level_two['mana_source_resolution']['authority']}`",
        f"Oracle-text runtime parsing: {str(level_two['mana_source_resolution']['oracle_text_runtime_parsing']).lower()}",
        f"Replacement selection: `{level_two['mana_source_resolution']['replacement_profile_selection']}`",
        f"Independent modes: {level_two['mana_source_resolution']['independent_mode_selection']}",
        f"State-transition timing: {level_two['mana_source_resolution']['state_transition_timing']}",
        "",
        "## Level 2 Selector Projection",
        "",
        f"Contract id: `{level_two['mana_source_projection']['contract_id']}`",
        "",
        level_two['mana_source_projection']['condition_state_boundary'],
        "",
        "Condition evaluation phases:",
        "",
        *[
            f"- `{candidate}`: " + "; ".join(f"`{condition}` = {phase}" for condition, phase in phases.items())
            for candidate, phases in level_two['mana_source_projection']['condition_evaluation_phases'].items()
        ],
        "",
        "End-of-turn source-capability observation:",
        "",
        f"Contract id: `{level_two['mana_source_projection']['source_capability_observation']['contract_id']}`",
        *[f"- `{field}`: {rule}" for field, rule in level_two['mana_source_projection']['source_capability_observation'].items() if field != 'contract_id'],
        "",
        "Land selector fields:",
        "",
        *[f"- `{field}`: {rule}" for field, rule in level_two['mana_source_projection']['land_selector_fields'].items()],
        "",
        "Ramp selector fields:",
        "",
        *[f"- `{field}`: {rule}" for field, rule in level_two['mana_source_projection']['ramp_selector_fields'].items()],
        "",
        level_two['mana_source_projection']['unsupported_profile_boundary'],
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
        "Immutable preregistered semantic Question. Execution lifecycle is recorded separately at the canonical lifecycle path derived from this Question id.",
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
        "## Comparison Orientation",
        "",
        f"- Baseline run role: `{question['comparison_sides']['baseline_run_role']}`",
        f"- Candidate run role: `{question['comparison_sides']['candidate_run_role']}`",
        "- Delta direction: candidate minus baseline",
        "",
        "## Target Metrics",
        "",
        *[
            f"- {metric['metric_id']} by turn {metric['target_turn']}"
            for metric in question["required_metrics"]
        ],
        "",
        "## Optional Sanity Metrics",
        "",
        *[
            f"- {metric['metric_id']} by turn {metric['target_turn']}"
            for metric in question["optional_metrics"]
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
