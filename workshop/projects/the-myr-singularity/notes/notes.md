# Notes

## 2026-07-09 - Sprint 1 Card Facts Checkpoint

Card Facts layer complete.

- 106/106 records resolved.
- Canonical facts come from Scryfall.
- No roles, tags, synergies, analysis, recommendations, prices, popularity data, or EDHREC data have been added.
- Original decklist flavor names are preserved through `original_decklist_name` and `display_name` where aliases were resolved.

Scryfall `flavor_name` aliases resolved:

- Bridge of Khazad-dûm -> Ensnaring Bridge
- Egg Hammer -> Myr Battlesphere
- Hope's Aero Magic -> Cyclonic Rift
- Shadowbringers -> Dovin's Veto

Next natural phase: Knowledge / Role Taxonomy.

## 2026-07-09 - Sprint 1 Functional Role Taxonomy Checkpoint

Functional role taxonomy defined as project-independent Card Knowledge vocabulary.

- Roles describe what cards can do in Commander deck construction terms.
- No roles have been assigned to specific cards.
- No synergies, analysis, recommendations, project-specific weights, or overrides have been added.

## 2026-07-09 - Sprint 1 Functional Role Assignment Schema Checkpoint

Functional Role Assignment schema defined.

- No card roles have been assigned yet.
- The schema defines the future data contract for card-to-role assignments.
- Next natural phase: first-pass role assignment for The Myr Singularity.

## 2026-07-09 - Sprint 1 First-Pass Functional Role Assignment Checkpoint

First-pass Functional Role Assignments populated for The Myr Singularity.

- 106/106 card records have one functional role assignment.
- Assignments use the existing project-independent role taxonomy.
- Assignments remain functional Card Knowledge, not recommendations, deck analysis, synergy maps, or project-specific weights.

## 2026-07-09 - Sprint 1 Baseline Structural Analysis Checkpoint

Baseline structural analysis created for deck version v1.0.

- `analysis/baseline_v1.0.json` and `analysis/baseline_v1.0.md` populated from the brief, the v1.0 decklist, Card Facts, and Functional Role assignments.
- Knowledge Layer validator passed 18/18 before analysis.
- Analysis is structural only: role/category distributions, strengths, pressure points, and open questions.
- No recommendations, no deck changes, no simulation, no power scoring.
- Next natural phase: recommendation analysis as a separate task.
