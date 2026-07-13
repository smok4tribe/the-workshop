# Simulation Question question-001-mana-color

Project `the-myr-singularity` — policy `the-myr-singularity-simulation-policy` (sim-policy-v1)

Execution status: **not_executed**

Documented in Task 30 per RFC-015. This question is NOT executed in Task 30: no SimulationRun, no SimulationResult, and no v1.0-versus-v1.1 comparison are produced.

## Hypothesis

The v1.1 mana-base changes (adding City of Brass and Mana Confluence as any-color sources and Urza's Saga, removing three colorless Urza's Tron lands) improve early mana development and five-color availability relative to v1.0 while preserving acceptable keepable-hand and land-drop quality, under the simulated model only.

## Question

Under the sim-policy-v1 model, does The Myr Singularity DeckVersion v1.1 improve early mana development and five-color availability relative to v1.0 through turn 6 under the one-free-mulligan-then-London policy, without degrading keepable-hand and land-drop rates?

## Compared Versions

- v1.0 (baseline_v1.0): `deck-content-sha256-v1:be721eb9d1662606812ceeb16ed476ebd7a0a7070bfd68b8e76efa085b364d3e`
- v1.1 (candidate_v1.1): `deck-content-sha256-v1:064801f0679b6dea14e52695efb0c1e92b095e810612d9d0929b45d6223c7cf4`

## Target Metrics

- keepable_opening_hand_rate by turn 0
- zero_land_hand_rate by turn 0
- one_land_hand_rate by turn 0
- excessive_land_hand_rate by turn 0
- land_drop_success_by_turn by turn 6
- ramp_access_by_turn by turn 3
- distinct_commander_colors_by_turn by turn 6
- five_color_availability_by_turn by turn 6
- commander_castability_by_turn by turn 3

## Success Interpretation

v1.1 shows equal-or-higher five-color-availability and distinct-color-by-turn probabilities and equal-or-higher early mana development, with keepable-hand and land-drop rates not materially lower than v1.0.

This is interpretation guidance only. Whether any observed delta is material is a reasoning-stage judgment recorded in a later task. commander_castability_by_turn is an optional sanity metric, not a success criterion. No thresholds here convert into a gameplay or win-rate claim.

## Limitations

- Measures the explicit sim-policy-v1 model only: draw/access (Level 1) and simplified mana development (Level 2).
- No opponent, combat, stack, politics, or Level 3 sequencing.
- City of Brass and Mana Confluence any-color production and Urza's Saga colorless production are modeled via card_semantics.json because canonical produced_mana is null for those cards; Urza's Saga chapter timing, tokens, tutor, and self-sacrifice are not modeled.
- Does not prove superior multiplayer gameplay performance.

## Boundary

This question binds a hypothesis to compared DeckVersions, the policy, and target metrics. It carries no results, authorizes no deck change, and is not a gameplay claim.
