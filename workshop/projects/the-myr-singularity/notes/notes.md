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

## 2026-07-09 - Sprint 1 Recommendation Candidate Schema Checkpoint

Recommendation candidate schema defined in `recommendations/rec-001.json` and `rec-001.md`.

- Schema only: the `candidates` array is empty and no cards are named.
- Candidates must trace to baseline analysis pressure points/open questions, project goals, card facts (Scryfall IDs), and functional roles.
- Lifecycle defined: proposed, under_review, accepted, rejected, deferred, needs_testing; accepted/rejected require a user decision and decision log entry.
- No deck changes are authorized by the schema; deck changes require a new version file plus a decision log entry.
- Next natural phase: populating candidate records as a separate task.

## 2026-07-09 - Sprint 1 Recommendation Schema Validator Checkpoint

Recommendation schema validator added at `workshop/tests/validation/validate_recommendation_schema.py`.

- Validates the rec-001 schema structure, allowed values, lifecycle rules, and schema-only boundaries.
- Confirms the candidates array is empty and no real card names or actionable deck-change language appear.
- Includes a per-candidate validation helper for future candidate records.
- No recommendations were created and no deck, version, card-data, knowledge, or analysis files changed.

## 2026-07-09 - Sprint 1 First Internal Recommendation Candidates Checkpoint

First internal recommendation candidate set populated in `recommendations/rec-001.json`.

- Six candidates are proposed for Product Owner review.
- Task 16B candidates are limited to internal/current-card-facts candidates only.
- External add/swap candidates require a later Candidate Card Facts Intake task before outside cards can be referenced in `affected_cards`.
- All candidates remain non-actionable and undecided.
- No deck, version, card-data, Knowledge, analysis, decision, or report files changed.
- Recommendation schema validator now supports schema-only and candidate-set modes.

## 2026-07-09 - Sprint 1 Candidate Card Facts Intake Checkpoint

Candidate Card Facts intake created for six external cards.

- Candidate facts were imported into `card-data/candidate_cards.json`.
- Import metadata was recorded in `card-data/candidate_card_import_metadata.json`.
- No recommendation candidates were created.
- No deck changes were made.
- Future external recommendation candidates can be built in a later task after validator support is updated.
