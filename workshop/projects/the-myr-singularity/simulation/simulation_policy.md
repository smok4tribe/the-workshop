# Simulation Policy sim-policy-v2

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

- Canonical Card Facts land types and produced_mana in workshop/card-data/cards.json.
- Explicit project-scoped overrides in card_semantics.json for cards whose canonical produced_mana is null or absent.

Unsupported behavior handling: Any card behavior that is neither resolvable from canonical Card Facts nor declared in card_semantics.json is unsupported. Unsupported behavior must be recorded as a visible limitation on any SimulationRun and SimulationResult that touches the card, and the card contributes nothing to any success metric on account of the unsupported behavior.

Hard invariant: Unsupported card behavior must never silently contribute to a success metric.

Fixture-specific modeled card behavior lives in `workshop/projects/the-myr-singularity/simulation/card_semantics.json`.

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
