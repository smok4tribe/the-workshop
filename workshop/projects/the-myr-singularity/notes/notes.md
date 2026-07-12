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

## 2026-07-09 - Sprint 1 External Recommendation Reference Model Checkpoint

External recommendation reference model added to the recommendation validator.

- Qualified references are supported: `deck:scryfall:<id>`, `candidate:scryfall:<id>`, and legacy `scryfall:<id>` for `rec-001` only.
- `incoming_cards` and `outgoing_cards` groundwork was added for future deck-changing candidates.
- `rec-001` remains internal-only and unchanged.
- No external candidates were created.
- No deck changes were made.
- Future `rec-002` should carry an updated candidate schema, likely schema version `1.1`.

## 2026-07-09 - Sprint 1 External Proposed Candidates Checkpoint

rec-002 created as the first external proposed recommendation candidate set.

- Five candidates (cand-007 to cand-011) reference external candidate Card Facts via `candidate:scryfall:<id>`.
- All candidates are proposed, non-actionable, and undecided; outgoing slots are deliberately empty pending Product Owner review.
- Candidate Card Facts remain facts-only; rec-001 remains internal-only and unchanged.
- No recommendations were accepted and no deck changes were made.
- Product Owner review is required before any action; accepted changes additionally require a decision log entry and a new deck version.

## 2026-07-10 - Sprint 1 Product Owner Review Schema Checkpoint

Product Owner review schema and rec-002 review scaffold added.

- `review_schema.json` defines the review artifact contract, including
  allowed review statuses and the explicit distinction that
  `accepted_for_decision` does not change the deck by itself.
- `review-rec-002.json`/`review-rec-002.md` created as the first Product
  Owner review scaffold, covering cand-007 through cand-011.
- All rec-002 review entries are `under_review` only; none are
  `accepted_for_decision`, `rejected`, `deferred`, or `needs_testing` yet.
- No candidates were accepted, rejected, or deferred.
- No deck changes were made.
- No decision log entries were created.
- No new deck version was created.
- `rec-001` and `rec-002` remain unmodified by this review layer.

## 2026-07-10 - Sprint 1 Review Validator Non-Neutral States Checkpoint

Review validator extended to support progressed Product Owner reviews.

- The validator now accepts non-neutral entry states (`needs_testing`,
  `deferred`, `accepted_for_decision`, `rejected`) alongside the scaffold
  state, with top-level `review_status` values `in_progress` and
  `completed`.
- Non-neutral entries must record `reviewed_at`, `rationale`, and a
  resolved `testing_required`; `needs_testing` additionally requires
  testing notes.
- Boundaries still enforced: `accepted_for_decision` and `needs_testing`
  do not change the deck, no decision log entries are created, no new
  deck version (v1.1) is created, and rec-002 candidate records remain
  proposed, non-actionable, and undecided.
- `review-rec-002.json` itself is unchanged: all entries remain
  `under_review` and no candidate has been accepted, rejected, or
  deferred.
- No deck changes were made.

## 2026-07-10 - Sprint 1 Product Owner Review Recorded Checkpoint

Product Owner review recorded for rec-002.

- cand-007, cand-008, and cand-011 are `accepted_for_decision`: eligible
  for a future decision-log task, with no deck change authorized.
- cand-009 and cand-010 are `needs_testing`: testing is required before
  any decision-log task for those candidates.
- Top-level review status moved to `in_progress`; every entry records
  `reviewed_at`, rationale, and testing intent.
- rec-002 candidate records remain proposed, non-actionable, and
  undecided.
- No decision logs were created.
- No deck changes were made.
- No v1.1 was created.

## 2026-07-10 - Sprint 1 Decision Log Scaffold Checkpoint

Decision-log scaffolds created for the accepted rec-002 candidates.

- decision-002 (cand-007, City of Brass / Mana Confluence), decision-003
  (cand-008, Urza's Saga), and decision-004 (cand-011, Tezzeret the
  Seeker) created with status `pending_deck_change_design`.
- cand-009 and cand-010 remain `needs_testing` and untouched.
- No outgoing cuts selected; every `proposed_outgoing_cards` is empty.
- No deck changes made; `deck_change_authorized` and
  `deck_change_implemented` are false in every scaffold.
- No v1.1 created; `target_deck_version` is null in every scaffold.
- Next step is deck-change design for accepted candidates
  (`deck_change_design_before_v1.1`).

## 2026-07-10 - Sprint 1 Review Validator Decision Scaffold Support Checkpoint

Review validator relaxed to accept non-authorizing decision scaffolds.

- The old assumption that every `decisions/*.json` must be an empty
  placeholder no longer holds after Task 21; the check is now "decision
  files are placeholders or non-authorizing scaffolds only".
- Populated decision files must be `pending_deck_change_design` scaffolds:
  non-authorizing, non-implemented, no outgoing cuts, no target deck
  version, boundary stating no deck change is authorized, and traceable
  to an `accepted_for_decision` rec-002 candidate (never `needs_testing`).
- The decision scaffolds' boundary statements now include the canonical
  "No deck change is authorized." phrase required by the validator.
- All validators pass again, including the review validator at 25/25.
- No deck changes were made and no v1.1 was created.

## 2026-07-10 - Sprint 1 v1.1 Deck-Change Design Checkpoint

v1.1 deck-change design artifact created for the accepted rec-002 decisions.

- `deck-change-design-v1.1.json`/`.md` cover decision-002, decision-003,
  and decision-004.
- Proposed IN: City of Brass, Mana Confluence, Urza's Saga, Tezzeret the
  Seeker. Proposed OUT for Product Owner review: Urza's Mine, Urza's
  Power Plant, Urza's Tower, Nevinyrral's Disk (alternatives documented:
  Propaganda, Prismatic Lens).
- The review validator now also accepts non-authorizing pre-version
  design artifacts; proposing cuts is not authorizing them.
- cand-009 and cand-010 remain `needs_testing` and untouched.
- No deck change was made; `deck/current.txt` and `versions/v1.0.json`
  are unchanged.
- No v1.1 was created; `versions/v1.1.json` remains an empty placeholder.
- Next step is Product Owner approval or revision of the design
  (`product_owner_approval_before_v1.1`).

## 2026-07-10 - Sprint 1 Product Owner Design Approval Checkpoint

Product Owner approved deck-change-design-v1.1 as proposed.

- Approved IN: City of Brass, Mana Confluence, Urza's Saga, Tezzeret the
  Seeker.
- Approved OUT: Urza's Mine, Urza's Power Plant, Urza's Tower,
  Nevinyrral's Disk.
- The design artifact is now `product_owner_approved` but remains
  non-implementing: `deck_change_authorized` and
  `deck_change_implemented` stay false.
- No deck change was made; `deck/current.txt` is unchanged.
- No v1.1 was created; `versions/v1.1.json` remains an empty placeholder.
- cand-009 and cand-010 remain `needs_testing` and untouched.
- Next step is create DeckVersion v1.1 (`create_deck_version_v1.1`).

## 2026-07-10 - Sprint 1 DeckVersion v1.1 Implementation Checkpoint

DeckVersion v1.1 created and implemented from the approved design.

- `deck/current.txt` updated to v1.1; `versions/v1.1.json` populated as
  the first implemented deck version (parent v1.0).
- IN: City of Brass, Mana Confluence, Urza's Saga, Tezzeret the Seeker.
- OUT: Urza's Mine, Urza's Power Plant, Urza's Tower, Nevinyrral's Disk.
- Counts preserved: 1 commander + 99 main deck + 7 sideboard; 34 lands.
- decision-002/003/004 and deck-change-design-v1.1 are now
  `implemented_as_v1.1`; the full trace candidate -> review -> decision ->
  design -> approval -> implementation is recorded.
- cand-009 and cand-010 remain `needs_testing` and untouched.
- Card Facts were not manually authored; incoming cards remain referenced
  through candidate Card Facts.
- Next natural step: post-implementation validation/report for v1.1.

## 2026-07-10 - Sprint 1 v1.1 Implementation Checkpoint

DeckVersion v1.1 implementation is complete and traceable through rec-002,
Product Owner review, decisions, deck-change design, approval, and implementation
(PRs #20-#27).

- Canonical Card Facts and functional-role alignment for the four implemented
  v1.1 incoming cards is complete.
- The v1.1 structured and readable post-implementation project report is complete.
- Implementation, traceability, validator reliability, canonical Knowledge alignment,
  and report completeness are ready for final Sprint 1 certification review.
- Sprint 1 is not yet declared certified; Task 28 remains pending.
- v1.1 is live: `deck/current.txt` and `versions/v1.1.json` agree
  (1 commander + 99 main + 7 sideboard, 34 lands).
- Open threads: cand-009/cand-010 testing gate; Task 28 final certification is the
  next task.
# 2026-07-12 - Sprint 1 Certification Candidate

- Task 27 report layer is merged and the certification evidence package is created.
- Machine-verifiable Sprint exit criteria pass; independent review remains pending.
- No deck-performance claim is made. KCI and Mana Echoes remain `needs_testing`.
- The implementation owner has not declared the final Sprint status.
