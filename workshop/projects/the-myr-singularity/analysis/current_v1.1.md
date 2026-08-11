# Current Structural Analysis - The Myr Singularity v1.1

Post-implementation current-state structural analysis. This document reports
repository-derived deck facts; it does not report simulated or gameplay outcomes.

## Identity and Provenance

- Analysis id: `current_v1.1`
- Method: `structural-analysis-v1` v1.1
- DeckVersion: `v1.1`
- Deck-content fingerprint: `deck-content-sha256-canonical-v2:510ba8e90025aec8d289edbf895405b7ddde6614161502a3ec47d4beaa56b120`
- Commander: Urtet, Remnant of Memnarch
- Format: Commander

An artifact combo-control engine disguised as a Myr tribal deck.

## Current Composition

| Fact | Value |
| --- | ---: |
| Playable cards | 100 |
| Lands | 34 |
| Nonlands | 66 |
| Artifacts | 49 |
| Creatures | 24 |
| Myr typal cards | 14 |
| Colored nonlands | 24 |
| Average nonland mana value | 3.02 |
| Sideboard cards | 7 |

### Nonland mana-value curve

| Mana value | Cards |
| --- | ---: |
| 0 | 1 |
| 1 | 6 |
| 2 | 22 |
| 3 | 20 |
| 4 | 7 |
| 5 | 5 |
| 6+ | 5 |

### Color requirements and land-role counts

- Colored nonland cards: 24
- Colored mana symbols in nonland costs: B 2, G 0, R 3, U 26, W 5
- Land cards carrying `colored_source`: 23
- Land cards carrying `fixing_land`: 14

These are card and role counts, not estimates of color access or casting success.

## Functional Role Density

| Role | Cards |
| --- | ---: |
| `artifact_engine` | 3 |
| `artifact_land` | 6 |
| `artifact_recursion` | 5 |
| `artifact_tutor` | 9 |
| `board_wipe` | 3 |
| `bounce` | 2 |
| `burst_card_draw` | 2 |
| `card_filtering` | 4 |
| `colored_source` | 23 |
| `colorless_source` | 17 |
| `combo_payoff` | 1 |
| `cost_reduction` | 9 |
| `counterspell` | 4 |
| `creature_body` | 23 |
| `damage_payoff` | 5 |
| `defensive_pillowfort` | 2 |
| `enabler` | 13 |
| `fetch_or_search_land` | 1 |
| `fixing_land` | 14 |
| `graveyard_card_access` | 1 |
| `graveyard_hate` | 2 |
| `hexproof_or_shroud` | 2 |
| `impulse_or_selection` | 4 |
| `indestructible_or_regeneration` | 3 |
| `land_tutor` | 1 |
| `mana_engine` | 3 |
| `mana_fixing` | 5 |
| `mana_rock` | 14 |
| `payoff_engine` | 5 |
| `protection` | 4 |
| `ramp` | 14 |
| `repeatable_card_draw` | 4 |
| `rule_modifier` | 3 |
| `sacrifice_outlet` | 4 |
| `scaling_threat` | 6 |
| `setup_piece` | 1 |
| `stax_or_hate_piece` | 2 |
| `tap_untap_engine` | 7 |
| `targeted_removal` | 2 |
| `token_engine` | 1 |
| `token_producer` | 4 |
| `topdeck_manipulation` | 3 |
| `tutor` | 6 |
| `utility_land` | 8 |
| `utility_land_mana` | 2 |
| `utility_piece` | 6 |

## Package and Category Grouping

| Category | Cards with any role | Primary cards | Role assignments |
| --- | ---: | ---: | ---: |
| Mana Development | 25 | 22 | 44 |
| Card Advantage | 11 | 6 | 11 |
| Selection and Tutoring | 18 | 15 | 23 |
| Interaction | 14 | 11 | 15 |
| Protection and Resilience | 8 | 5 | 11 |
| Recursion and Recovery | 5 | 4 | 5 |
| Engine and Scaling | 15 | 12 | 25 |
| Combo and Win Conditions | 5 | 5 | 6 |
| Board Presence | 25 | 3 | 27 |
| Utility and Support | 21 | 9 | 27 |
| Lands and Mana Base | 34 | 33 | 69 |

## Structural Observations

- The playable 100 contains 34 lands, 49 artifacts, 24 creatures, and 14 Myr typal cards.
- The current Functional Knowledge assigns 14 ramp roles, 14 mana-rock roles, 9 artifact-tutor roles, 7 tap-untap-engine roles, and 5 damage-payoff roles.
- The current mana base contains 23 land cards with the colored_source role and 14 with the fixing_land role.
- The nonland curve contains 49 cards at mana value three or less and has an average mana value of 3.02.

## Structural Dependencies and Pressure Points

Dependencies:

- The artifact engine and scaling categories depend on the 49 artifact cards and the recorded artifact-engine, mana-rock, tutor, and tap-untap roles.
- The commander-facing Myr structure depends on 14 cards whose canonical type lines include Myr and on the current Myr-related Functional Knowledge coverage.
- The current role model identifies artifact-directed recursion but no creature_recursion, graveyard_recursion, or permanent_recursion role in the playable 100.

Pressure points:

- Current Functional Knowledge has no combo_piece, combo_enabler, finisher, or alternate_win_condition role in the playable 100; this records a classification boundary, not a gameplay conclusion.
- The current interaction category contains 14 cards with any interaction role and 2 targeted-removal role assignments.
- The playable 100 has no anti_wipe_protection role; the current sideboard includes the only recorded anti_wipe_protection assignment.
- The sideboard remains separate from the playable 100, and its Commander-play relationship is not defined by this analysis.

## Unsupported or Uncertain Classifications

- Functional-role assignments are first-pass human-curated knowledge: 87 playable cards are high confidence and 13 are medium confidence.
- Canonical card facts and role assignments do not establish the sequencing, interaction, or reliability of structural packages in play.
- This analysis does not encode a complete card-by-card combo-line map; missing combo roles may reflect Functional Knowledge coverage limits rather than deck-content facts.

## Historical v1.0 Context

Exact DeckVersion delta from `v1.0`: added City of Brass, Mana Confluence, Tezzeret the Seeker, Urza's Saga; removed Nevinyrral's Disk, Urza's Mine, Urza's Power Plant, Urza's Tower.

These are exact deck-content changes and current structural counts. Their performance consequences remain unmeasured.

## Assumptions and Limitations

Assumptions:

- DeckVersion v1.1 is the immutable implemented deck state identified by project.json.
- Canonical Card Facts and Functional Knowledge are authoritative for the factual type, mana-cost, and role fields counted here.
- The playable analysis population is the commander plus 99 main-deck cards; the sideboard is reported separately.

Limitations:

- No simulation engine was run and no SimulationRun, SimulationResult, or ComparisonResult exists.
- Land counts, mana symbols, and role counts do not measure keep rates, land drops, color access, mulligans, or gameplay outcomes.
- This analysis does not compare v1.1 quality against v1.0 and does not authorize a deck change.

## Suggested Evidence Question

- `question-001-mana-color` (not_executed): Test the preregistered v1.0 and v1.1 mana-color hypothesis after a simulation engine produces valid evidence.

## Boundary

This is a current-state structural analysis only. It creates no simulation evidence, recommendation, Product Owner Decision, or DeckVersion mutation, and it makes no gameplay or comparative performance claim.
