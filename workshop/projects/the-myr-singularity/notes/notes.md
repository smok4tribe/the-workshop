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
