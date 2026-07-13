# Simulation Policy sim-policy-v1

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

By explicit Sprint 2 decision the modeled first player draws on turn 1. This is a deliberate modeling choice for reproducibility and is not the paper on-the-play rule; it is recorded here rather than hidden in engine code.

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

Rule id: `deterministic-bottoming-v1`

1. highest_mana_value_nonland — The single highest-mana-value nonland card.
2. remaining_high_mana_value_nonlands — Remaining nonland cards in descending mana value.
3. lands_above_three — Lands only when more than three lands remain in hand, removing surplus lands above three.
4. stable_normalized_card_identity_tiebreak — Ties at any rank are broken by ascending NFKC-normalized card identity so bottoming is fully deterministic.

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
- Seed derivation: `sim-seed-sha256-v1` over question_id + policy_version + deck_content_fingerprint + run_role
- Seed extraction: The seed is the first 64 bits of the digest read as the first 8 bytes in big-endian order, interpreted as an unsigned 64-bit integer.

## Iteration and Uncertainty

- Minimum saved iterations: 10000
- Canonical comparative iterations: 100000
- Confidence presentation: wilson_95 (wilson_score_interval)
- Required reported fields: raw_count, sample_size, probability, confidence_interval, absolute_delta
- Relative delta: secondary; valid only when baseline probability is non-zero

## Deck-Content Fingerprint

Algorithm id: `deck-content-sha256-v1`

- Included zones: commander, library
- Excluded: sideboard

Reference fingerprints (deck identity only, not results): v1.0 `deck-content-sha256-v1:be721eb9d1662606812ceeb16ed476ebd7a0a7070bfd68b8e76efa085b364d3e`; v1.1 `deck-content-sha256-v1:064801f0679b6dea14e52695efb0c1e92b095e810612d9d0929b45d6223c7cf4`.

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
