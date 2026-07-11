# Project Report v1.1

## Executive Summary

The Myr Singularity implemented DeckVersion v1.1 from baseline v1.0. Implementation and traceability are verified; post-implementation outcomes are not measured.

## Project Identity

- Format: Commander
- Commander: Urtet, Remnant of Memnarch
- Identity: An artifact combo-control engine disguised as a Myr tribal deck.
- Resource model: Myr and artifact bodies are used as resources, not merely as attackers.
- Constraint: Preserve the unusual Myr identity.

## Design Brief

- Preserve the Myr identity.
- Improve explosiveness.
- Improve consistency.
- Improve mana fixing.
- Improve resilience.

These are recorded project goals, not verified post-implementation outcomes.

## Baseline v1.0

Baseline analysis `baseline_v1.0` examined DeckVersion `v1.0` structurally.

## Identified Pressure or Weakness

- Colored-cast consistency for the five-color identity was unverified in the baseline structural analysis.
- The baseline recorded a small card-advantage layer and a mana base with substantial colorless production.
- Myr typal density and the reliability of the commander's Myr triggers remained untested.

## Recommendation

`rec-002` proposed external candidates for recorded mana, artifact-access, and engine pressure points.

## Product Owner Review

Accepted for decision: cand-007, cand-008, cand-011.

Needs testing: cand-009, cand-010.

The Product Owner review recorded disposition and did not directly modify the deck.

## Decisions

- `decision-002`: IN City of Brass, Mana Confluence; OUT Urza's Mine, Urza's Power Plant. Expected to replace two colorless-only lands with any-color lands.
- `decision-003`: IN Urza's Saga; OUT Urza's Tower. Expected to add a land-slot artifact search and Construct-token capability.
- `decision-004`: IN Tezzeret the Seeker; OUT Nevinyrral's Disk. Expected to add artifact tutoring and repeatable artifact untapping.

## Approved Deck-Change Design

`deck-change-design-v1.1` was approved by Product Owner and implemented as `v1.1`.

## Implemented DeckVersion v1.1

implementation traceability and DeckVersion integrity are verified by existing validators.

## Exact Version Change

### IN

- 1 City of Brass (main_deck; decision-002)
- 1 Mana Confluence (main_deck; decision-002)
- 1 Urza's Saga (main_deck; decision-003)
- 1 Tezzeret the Seeker (main_deck; decision-004)

### OUT

- 1 Urza's Mine (main_deck; decision-002)
- 1 Urza's Power Plant (main_deck; decision-002)
- 1 Urza's Tower (main_deck; decision-003)
- 1 Nevinyrral's Disk (main_deck; decision-004)

Commander unchanged: true. Sideboard unchanged: true. Playable total: 100.

## Knowledge and Provenance State

Implemented cards are present in canonical Card Facts and have canonical Functional Knowledge: City of Brass, Mana Confluence, Urza's Saga, Tezzeret the Seeker.

Historical candidate provenance remains resolvable. Active needs-testing candidates: Krark-Clan Ironworks, Mana Echoes.

## What Is Verified

- Implementation result: verified
- The recorded decisions, approved design, resulting DeckVersion, and current decklist align.
- The exact four-card IN and four-card OUT delta is recorded above.

## What Is Expected but Not Yet Measured

- Expected to improve access to colored mana.
- Adds an additional artifact-tutor capability.
- Adds a repeatable artifact-untap capability.
- Replaces the incomplete Tron package with independently functional lands.

These are expected effects from the recorded design, not measured performance outcomes.

## Deferred Candidates

- Krark-Clan Ironworks: needs_testing; not implemented.
- Mana Echoes: needs_testing; not implemented.

## Limitations

- Post-implementation analysis has not been run.
- Gameplay and simulation outcomes are not measured.
- Krark-Clan Ironworks remains needs_testing.
- Mana Echoes remains needs_testing.
- Generic version-state cleanup and append-only transition history remain future work.
- Final Sprint 1 certification remains pending Task 28.

## Next Actions

Immediate: Task 28 - Sprint 1 Final Certification.

- Post-v1.1 structural analysis.
- Focused mana/color simulation.
- Krark-Clan Ironworks testing.
- Mana Echoes testing.

## Structured Sources

- project: workshop/projects/the-myr-singularity/project.json
- brief: workshop/projects/the-myr-singularity/brief/brief.json
- baseline_deck_version: workshop/projects/the-myr-singularity/versions/v1.0.json
- resulting_deck_version: workshop/projects/the-myr-singularity/versions/v1.1.json
- current_decklist: workshop/projects/the-myr-singularity/deck/current.txt
- baseline_analysis: workshop/projects/the-myr-singularity/analysis/baseline_v1.0.json
- recommendation: workshop/projects/the-myr-singularity/recommendations/rec-002.json
- product_owner_review: workshop/projects/the-myr-singularity/recommendations/review-rec-002.json
- decisions: workshop/projects/the-myr-singularity/decisions/decision-002.json, workshop/projects/the-myr-singularity/decisions/decision-003.json, workshop/projects/the-myr-singularity/decisions/decision-004.json
- deck_change_design: workshop/projects/the-myr-singularity/decisions/deck-change-design-v1.1.json
- design_approval: workshop/projects/the-myr-singularity/decisions/deck-change-design-v1.1.json
- card_facts: workshop/card-data/cards.json
- functional_knowledge: workshop/knowledge/functional_roles.json
- candidate_lifecycle_metadata: workshop/card-data/candidate_card_import_metadata.json
