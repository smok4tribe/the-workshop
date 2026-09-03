# Simulation Policy sim-policy-v6

Policy id: `the-myr-singularity-simulation-policy` — project `the-myr-singularity`

## Purpose

Defines the universal, versioned semantic contract for The Workshop simulation of The Myr Singularity. It owns every result-changing assumption that is not deck content: mulligan, keep and bottoming rules, draw/play and turn semantics, observation horizon, Level 1 and Level 2 sequencing semantics, mana/color/ramp resolution rules, the supported-versus-unsupported card-behavior boundary, deterministic seed and RNG identity, iteration and uncertainty policy, the deck-content fingerprint definition, and the evidence-language boundary. Deck identity is owned by immutable DeckVersion files; fixture-specific modeled card behavior is owned by the project-scoped card_semantics.json artifact this policy references.

## Commander Scenario

- Format: Commander
- Table: multiplayer
- Seat: first_player
- First-turn draw: true
- Opening hand size: 7
- Commander starts in command zone: true

The modeled first player draws on turn 1 because that is normal multiplayer Commander behavior under the paper rules. The rule is recorded explicitly so it remains visible and reproducible in the engine contract.

## Turn Semantics

- Turn indexing: one_based
- Opening hand is turn: 0
- First drawn turn: 1
- Observation horizon turn: 6

Primary evidence is observed through turn 6 inclusive. Metric-specific target turns are recorded on each metric and never exceed the horizon.

## Mulligan Policy

- Policy: one_free_mulligan_then_london
- Free mulligans: 1
- Subsequent rule: london
- Maximum mulligans: 6

Draw a fresh seven each mulligan. The first mulligan is free (keep seven cards). Each mulligan after the first is a London mulligan: draw seven, then bottom one card per mulligan taken beyond the free one when the hand is kept.

Resolution order:

1. Draw opening_hand_size cards.
2. Evaluate the hand against keep_rule.
3. If keepable, keep; apply bottoming_rule to bottom (mulligans_taken - free_mulligans) cards when positive.
4. If not keepable and mulligans_taken < max_mulligans, mulligan again.
5. If the maximum is reached, keep the final hand and apply bottoming for the required count.

Executable transition:

- return_all_physical_tokens_to_eligibility
- reconstruct_full_library_in_canonical_instance_token_order
- increment_mulligans_taken_before_recording_next_attempt
- fisher_yates_full_library_with_same_continuous_iteration_pcg32
- draw_opening_hand_size

RNG reset permitted: false
Bottoming consumes RNG: false

## Keep Rule

Rule id: `myr-singularity-keep-v1`

- Keep hands containing 2 through 5 lands.
- One-land hand: Keep a one-land hand only when modeled unconditional early acceleration can produce at least two mana by turn 2.
- Zero-land hands: reject
- Six-or-seven-land hands: reject

Modeled unconditional early acceleration: A nonland mana source in hand that is castable and online by turn 2 under Level 2 semantics using only the single land plus that source (for example a one-mana rock cast off the single land on turn 1, or a zero-cost rock), such that at least two mana are available by turn 2. Conditional accelerants that require a second land, additional colors, or another permanent first do not qualify.

Explicitly not evaluated:

- combo quality
- interaction quality
- generic hand strength
- matchup quality

Project extension points:

- keep_land_count_range
- one_land_exception
- additional_project_conditions

Non-overridable invariants:

- zero-land hands are always rejected
- keep evaluation never scores combo, interaction, generic strength, or matchup quality

## Bottoming Rule

Rule id: `deterministic-bottoming-v2`

1. nonlands_descending_mana_value — All nonlands by descending mana value, then lowercase oracle_id and duplicate ordinal ascending.
2. lands_above_three — Lands while more than three remain, by lowercase oracle_id and duplicate ordinal ascending.
3. remaining_lands — If bottoms remain owed, remaining lands by lowercase oracle_id and duplicate ordinal ascending.

## Card Behavior Boundary

Supported behavior sources:

- Canonical Card Facts provide immutable card identity, type, and raw canonical facts only.
- card_semantics.json provides approved project-scoped parity behavior only for City of Brass, Mana Confluence, and Urza's Saga.
- mana_source_semantics.json is the authoritative executable Level 2 mana-source registry for the v1.0/v1.1 modeled source union.

Unsupported behavior handling: Behavior is unsupported unless an approved supported executable profile or state rule in mana_source_semantics.json represents it after any required card_semantics.json parity rule is applied. Unsupported behavior must be recorded as a visible limitation on any SimulationRun and SimulationResult that touches the card, and it contributes nothing to any success metric on account of that unsupported behavior.

Hard invariant: No supported executable registry profile may be classified as unsupported by the general boundary, and unsupported behavior must never silently contribute to a success metric.

Unsupported limitation representation:

- Format: `unsupported_mana_profile:<oracle_id>:<unsupported_reason_id>`
- Derivation: For every unsupported executable profile on a source present in the run DeckVersion, derive exactly one limitation ID. The SimulationRun and its SimulationResult must both carry the complete applicable set.
- Metric boundary: Unsupported behavior contributes zero modeled mana/colors and cannot improve a success metric.

Fixture-specific modeled card behavior lives in `workshop/projects/the-myr-singularity/simulation/card_semantics.json`.
Executable mana-source profiles live in `workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json`.

## Randomness Policy

- RNG id: pcg32-v1
- Seed type: unsigned_64_bit
- Seed derivation: `sim-seed-sha256-v2` over question_content_fingerprint + policy_content_fingerprint + deck_content_fingerprint + run_role
- Iteration derivation: `sim-iteration-seed-sha256-v1`; fresh RNG per iteration and continuous stream across mulligans.
- Seed extraction: first 8 digest bytes, big-endian unsigned 64-bit

## Iteration and Uncertainty

- Minimum saved iterations: 10000
- Canonical comparative iterations: 100000
- Confidence presentation: wilson_95 (wilson_score_interval)
- Required reported fields: raw_count, sample_size, probability, confidence_interval
- Relative delta: secondary; valid only when baseline probability is non-zero

## Deck-Content Fingerprint

Algorithm id: `deck-content-sha256-canonical-v2`

- Included zones: commander, library
- Excluded: sideboard

Reference fingerprints (deck identity only, not results): v1.0 `deck-content-sha256-canonical-v2:d70d0097753c001192e49f1e270359bf3b5bf20b53fd91c16e69c3bed1e337fa`; v1.1 `deck-content-sha256-canonical-v2:510ba8e90025aec8d289edbf895405b7ddde6614161502a3ec47d4beaa56b120`.

## Metric Registry

| Metric | Target turn | Shape | Required |
| --- | ---: | --- | --- |
| keepable_opening_hand_rate | 0 | bernoulli_probability | yes |
| zero_land_hand_rate | 0 | bernoulli_probability | yes |
| one_land_hand_rate | 0 | bernoulli_probability | yes |
| excessive_land_hand_rate | 0 | bernoulli_probability | yes |
| land_drop_success_by_turn | 6 | bernoulli_probability | yes |
| ramp_access_by_turn | 3 | bernoulli_probability | yes |
| distinct_commander_colors_by_turn | 6 | categorical_count | yes |
| five_color_availability_by_turn | 6 | bernoulli_probability | yes |
| commander_castability_by_turn | 3 | bernoulli_probability | no |

## Metric Measurement Contracts

Each metric below is measured only under its complete Policy-owned contract.

### keepable_opening_hand_rate

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_1",
  "target_turn": 0,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "first_natural_opening_hand",
    "hand_size": 7,
    "before_mulligan": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "initial_hand_satisfies_registered_keep_rule",
    "keep_rule_id": "myr-singularity-keep-v1",
    "one_land_exception_source": "keep_rule.base_rule.one_land_exception"
  }
}
```

### zero_land_hand_rate

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_1",
  "target_turn": 0,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "first_natural_opening_hand",
    "hand_size": 7,
    "before_mulligan": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "initial_hand_land_count_equals",
    "land_count": 0
  }
}
```

### one_land_hand_rate

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_1",
  "target_turn": 0,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "first_natural_opening_hand",
    "hand_size": 7,
    "before_mulligan": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "initial_hand_land_count_equals",
    "land_count": 1
  }
}
```

### excessive_land_hand_rate

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_1",
  "target_turn": 0,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "first_natural_opening_hand",
    "hand_size": 7,
    "before_mulligan": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "initial_hand_land_count_inclusive_range",
    "minimum_land_count": 6,
    "maximum_land_count": 7
  }
}
```

### land_drop_success_by_turn

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_2",
  "target_turn": 6,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "end_of_target_turn_after_level_2_sequencing",
    "after_pending_time_dependent_removals": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "legal_land_drop_on_every_turn",
    "first_required_turn": 1,
    "last_required_turn": "metric.target_turn",
    "inclusive": true,
    "later_removal_erases_historical_success": false
  }
}
```

### ramp_access_by_turn

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_1",
  "target_turn": 3,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "final_kept_hand_plus_normal_draws_through_target_turn",
    "hand_state": "final_kept_hand",
    "draw_window": "normal_draws_through_target_turn"
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "registered_ramp_identity_seen",
    "registry_ref": "ramp_access_registry.oracle_ids",
    "access_only": true,
    "requires_castability": false,
    "requires_deployment": false,
    "requires_online": false,
    "requires_mana_production": false
  }
}
```

### distinct_commander_colors_by_turn

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_2",
  "target_turn": 6,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "end_of_target_turn_after_level_2_sequencing",
    "after_pending_time_dependent_removals": true,
    "source_capability_observation_contract_id": "source-capability-observation-v1"
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "categorical_count",
  "value": {
    "id": "surviving_online_source_capability_color_cardinality",
    "projection": "source_capability",
    "domain": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
    "colors": [
      "W",
      "U",
      "B",
      "R",
      "G"
    ],
    "excluded_colors": [
      "C"
    ],
    "source_state": "surviving_and_online",
    "earlier_tapping_removes_capability": false
  }
}
```

### five_color_availability_by_turn

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_2",
  "target_turn": 6,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "end_of_target_turn_after_level_2_sequencing",
    "after_pending_time_dependent_removals": true,
    "source_capability_observation_contract_id": "source-capability-observation-v1"
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "all_required_source_capability_colors_available",
    "projection": "source_capability",
    "required_colors": [
      "W",
      "U",
      "B",
      "R",
      "G"
    ],
    "excluded_colors": [
      "C"
    ],
    "source_state": "surviving_and_online",
    "earlier_tapping_removes_capability": false,
    "requires_simultaneous_spendable_mana": false,
    "requires_commander_castability": false
  }
}
```

### commander_castability_by_turn

```json
{
  "contract_id": "metric-measurement-v1",
  "population": {
    "id": "all_preregistered_run_iterations",
    "iteration_index_range": {
      "first": 1,
      "last": "simulation_run.iteration_count",
      "inclusive": true
    },
    "conditional_exclusion_permitted": false,
    "observation_failure": "invalidates_run_and_result"
  },
  "sample_size_rule": {
    "id": "equals_run_iteration_count",
    "source": "simulation_run.iteration_count"
  },
  "sequencing_level": "level_2",
  "target_turn": 3,
  "target_turn_semantics": "metric.target_turn",
  "observation_point": {
    "id": "end_of_target_turn_after_level_2_sequencing",
    "after_pending_time_dependent_removals": true
  },
  "unsupported_behavior": {
    "iteration_remains_in_population": true,
    "cannot_contribute_to_success": true,
    "supported_behavior_may_independently_succeed": true
  },
  "result_shape": "bernoulli_probability",
  "event": {
    "id": "legal_commander_payment_exists",
    "projection": "spendable_mana",
    "resources": "remaining_untapped_after_development",
    "cost_source": "current_modeled_command_zone_cost",
    "commander_card_reference": {
      "path": "workshop/card-data/cards.json",
      "oracle_id": "6222fccf-fc08-4190-8d40-a56d6d1423df",
      "mana_cost": "{3}"
    },
    "base_cost": {
      "generic": 3,
      "colored": []
    },
    "previous_commander_casts": 0,
    "commander_tax_generic": 0,
    "alternate_or_unmodeled_resources_allowed": false,
    "commander_actually_cast": false
  }
}
```

## Deterministic Level 2 Trace

1. `untap_and_clear_floating_mana`
2. `draw`
3. `advance_time_dependent_state`
4. `select_and_play_one_land`
5. `repeatedly_deploy_payable_registered_ramp`
6. `resolve_pending_time_dependent_removals`
7. `record_end_of_turn_observations`

Urza's Saga timing: At controller-turn offset 2, Urza's Saga remains usable during the approved development window, then its final-chapter removal occurs before end-of-turn observation; once removed it contributes to no end-of-turn metric.

Source-capability projection: surviving online source color capabilities, irrespective of earlier tapping
Spendable-mana projection: actual remaining untapped payable sources after deterministic development

Unsupported actions: Actions without explicit complete policy registration cannot be selected or improve a metric.

## Executable Mana Source Boundary

Authority: `workshop/projects/the-myr-singularity/simulation/mana_source_semantics.json`
Oracle-text runtime parsing: false
Replacement selection: `highest_priority_matching_profile`
Independent modes: legal profiles are alternatives and cannot combine outputs from one source activation
State-transition timing: registered end-step removal conditions execute after deterministic same-turn development actions and before the applicable end-of-turn observation

## Level 2 Selector Projection

Contract id: `mana-source-projection-v1`

Each registered condition is evaluated at its contract-defined phase. Generic payments from other sources exclude the candidate source; land selection and actual end-step removal use distinct pre-selection and post-development states.

Condition evaluation phases:

- `land_candidate`: `generic_payment_available_from_other_sources` = pre_play_resources_excluding_candidate; `complete_tron_set_controlled` = hypothetical_post_play_controlled_lands_including_candidate; `bounded_controller_turn_window` = candidate_controller_turn_offset_default_zero; `commander_color_identity` = static_scenario_state; `artifact_controlled` = pre_selection_state_for_selector_persistence; `end_step_remove_unless_condition` = post_development_state
- `ramp_candidate`: `deployment_payment` = pre_deployment_resources; `activation_profiles` = post_deployment_residual_resources_after_reserved_payment; `self_funding` = forbidden
- `end_of_turn_source_capability_observation`: `evaluation_phase` = after_deterministic_development_and_pending_removals_before_end_of_turn_observation; `source_snapshot` = surviving_online_sources_after_post_development_removals; `earlier_tapping_and_spending` = do_not_remove_gross_source_capability; `generic_payment_available_from_other_sources` = gross_nonrecursive_base_capacity_from_other_surviving_online_sources; `self_funding` = forbidden; `conditional_profiles_feed_base_capacity` = False; `spendable_mana_relation` = remaining_untapped_payable_resources_only

End-of-turn source-capability observation:

Contract id: `source-capability-observation-v1`
- `projection`: gross_surviving_online_capability
- `base_capacity_ledger`: For each other surviving online source, use the greatest supported profile mana_units whose conditions are satisfied at observation and which has no generic_payment_available_from_other_sources condition. Conditional generic-payment profiles never recursively contribute.
- `conditional_profile_rule`: A candidate profile requiring generic payment is legal exactly when the sum of other-source base-capacity units meets required_units. The candidate source is excluded.
- `tapping_rule`: Earlier tapping or mana spent during development does not erase gross source capability.
- `spendable_mana_rule`: Spendable mana remains actual remaining untapped payable resources and is not substituted for source capability.
- `removal_rule`: Only surviving online sources after registered post-development removals contribute.

Land selector fields:

- `colors`: union of W, U, B, R, and G output_capabilities of currently legal supported profiles for the land; C never contributes to this commander-color selector field.
- `five_color_source`: true exactly when currently legal supported profiles provide source-capability W, U, B, R, and G.
- `permanent`: false for a legal bounded/removing profile; otherwise true unless the pre-selection state predicts a registered removal transition. A later same-turn development action is evaluated separately at end step.
- `remaining_availability`: for a bounded profile, inclusive remaining controller-turn offsets through its registered end_offset; for a conditional-removal source, only the current turn when pre-selection predicts removal, otherwise inclusive turns from current_turn through horizon_turn.
- `mana_units`: maximum gross registered mana_units among currently legal supported profiles whose contract-phase conditions and payments from other sources are already satisfiable. It is a selector heuristic output quantity, not net mana gain.
- `identity`: ['oracle_id', 'ordinal']

Ramp selector fields:

- `payable`: true only when the deployment casting cost is payable from pre-deployment modeled resources and at least one supported profile remains legal after that payment is reserved.
- `same_turn_online_noncreature`: true only for a mana_rock with a supported immediate profile legal after deployment payment reservation.
- `output_units`: maximum mana_units among supported profiles legal after deployment payment reservation.
- `color_flexibility`: maximum output_capabilities cardinality among supported profiles legal after deployment payment reservation.
- `mana_value`: deployment.casting_cost.generic plus the number of deployment.casting_cost.colored symbols.
- `identity`: ['oracle_id', 'ordinal']

Unsupported-only profiles and sources produce zero Level 2 output and are not payable registered ramp. Level 1 access registration remains independent.

## Evidence-Language Boundary

Simulation output describes the explicit simulated model only. It reports access, land development, mana availability, and color availability under the recorded assumptions. It must never be phrased as, or converted into, real-game win rate, average win turn, gameplay performance, matchup performance, or generic deck quality.

Forbidden claims:

- win rate
- win probability
- average win turn
- gameplay performance
- matchup performance
- generic deck quality
- the deck is better

## Lifecycle Boundary

SimulationPolicy, SimulationQuestion, SimulationRun, SimulationResult, ComparisonResult, ReasoningOutput, and Product Owner Decision are distinct lifecycle stages. Policy and question do not carry results; runs carry configuration and identity, not metrics; results carry metrics, not interpretation; interpretation and Product Owner decisions are separate later artifacts. No simulation artifact creates or edits a DeckVersion.

## Boundary

This policy freezes the semantic contract for Sprint 2 simulation. It contains no SimulationRun, no SimulationResult, and no comparison values. It authorizes no deck change, edits no canonical Card Facts, and makes no performance claim.
