# Simulation Question question-001-mana-color

Project `the-myr-singularity` — policy `the-myr-singularity-simulation-policy` (sim-policy-v2)

Execution status: **not_executed**

Documented in Task 30 per RFC-015. This question is NOT executed in Task 30: no SimulationRun, no SimulationResult, and no v1.0-versus-v1.1 comparison are produced.

## Hypothesis

The v1.1 mana-base changes (adding City of Brass and Mana Confluence as any-color sources and Urza's Saga, removing three colorless Urza's Tron lands) increase the specified early mana-development and five-color-availability metrics relative to v1.0 under the simulated model only.

## Question

Under the sim-policy-v2 model, how do The Myr Singularity DeckVersion v1.1 and v1.0 compare on the preregistered early mana-development, five-color-availability, keepable-hand, and land-drop metrics through turn 6 under the one-free-mulligan-then-London policy?

## Compared Versions

- v1.0 (baseline_v1.0): `deck-content-sha256-canonical-v2:d70d0097753c001192e49f1e270359bf3b5bf20b53fd91c16e69c3bed1e337fa`
- v1.1 (candidate_v1.1): `deck-content-sha256-canonical-v2:510ba8e90025aec8d289edbf895405b7ddde6614161502a3ec47d4beaa56b120`

## Target Metrics

- keepable_opening_hand_rate by turn 0
- zero_land_hand_rate by turn 0
- one_land_hand_rate by turn 0
- excessive_land_hand_rate by turn 0
- land_drop_success_by_turn by turn 6
- ramp_access_by_turn by turn 3
- distinct_commander_colors_by_turn by turn 6
- five_color_availability_by_turn by turn 6

## Optional Sanity Metrics

- commander_castability_by_turn by turn 3

## Success Interpretation

The primary comparison reports five-color availability, distinct colors by turn, and early mana development for v1.0 and v1.1; keepable-hand and land-drop metrics are reported alongside them.

This question preregisters metric identities, target turns, and comparison direction only. It defines no qualitative adequacy band or threshold. commander_castability_by_turn is an optional sanity metric, not a success criterion. No thresholds here convert into a gameplay or win-rate claim.

## Limitations

- Measures the explicit sim-policy-v2 model only: draw/access (Level 1) and simplified mana development (Level 2).
- No opponent, combat, stack, politics, or Level 3 sequencing.
- City of Brass and Mana Confluence any-color production and Urza's Saga colorless production are modeled via card_semantics.json because canonical produced_mana is null for those cards; Urza's Saga bounded deterministic final-chapter removal is modeled; tokens, tutor, exact stack interaction, and exact intra-turn Saga rules are not modeled.
- Does not prove superior multiplayer gameplay performance.

## Boundary

This question binds a hypothesis to compared DeckVersions, the policy, and target metrics. It carries no results, authorizes no deck change, and is not a gameplay claim.
