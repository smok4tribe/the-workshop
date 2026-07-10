# Validation

Automated consistency checks for Sprint 1. Four validators live here:

- `validate_knowledge_layer.py` — guards the Card Facts / Card Knowledge
  boundary (see "Knowledge Layer Validation" below).
- `validate_recommendation_schema.py` — guards the recommendation candidate
  schema, schema-only mode, and candidate-set mode (see "Recommendation Schema
  Validation" below).
- `validate_candidate_card_facts.py` — guards the external candidate Card Facts
  intake layer (see "Candidate Card Facts Validation" below).
- `validate_recommendation_review.py` — guards the Product Owner review
  layer, scaffold and progressed states alike (see "Recommendation Review
  Validation" below).

# Knowledge Layer Validation

Automated consistency checks for the Sprint 1 Knowledge Layer. The validator
guards the Card Facts / Card Knowledge boundary: Card Facts in
`workshop/card-data/cards.json` are canonical external data, while functional
role assignments in `workshop/knowledge/functional_roles.json` are curated
Card Knowledge constrained by the controlled vocabulary in
`workshop/knowledge/role_taxonomy.json`.

## How to run

From the repository root:

```bash
python workshop/tests/validation/validate_knowledge_layer.py
```

Standard library only; no external dependencies. Prints a per-check
`[PASS]`/`[FAIL]` line for every check. Exits `0` with a PASS summary when
all checks pass, exits `1` with failure details when any check fails.

## What it checks

- `cards.json`, `role_taxonomy.json`, and `functional_roles.json` parse as JSON.
- `cards.json` contains exactly 106 card records.
- `functional_roles.json` contains exactly 106 assignment records.
- Every card record has exactly one assignment matched by Scryfall ID.
- No assignments exist for cards outside `cards.json`.
- Every role ID used in `roles`, `primary_roles`, and `secondary_roles` exists
  in `role_taxonomy.json`.
- `primary_roles` and `secondary_roles` are subsets of `roles`, do not overlap,
  and their union equals `roles`.
- `confidence` is one of `low`, `medium`, `high`.
- `source_type` is one of `human_curated`, `taxonomy_inference`,
  `project_override`.
- `card_source_ref.source` is `scryfall` for all Sprint 1 assignments.
- `evidence` is present and non-empty for every assignment.
- `evidence` and `source_note` contain no recommendation/cut/add language.
- `evidence` and `source_note` contain no analysis/power-level/ranking/
  importance-score language.

## What it does not do

The validator checks structural and boundary consistency only. It does not
perform deck analysis, produce recommendations, evaluate card quality, build
synergy maps, or touch decks, versions, decisions, or reports.

# Recommendation Schema Validation

`validate_recommendation_schema.py` validates recommendation candidate data in
`workshop/projects/the-myr-singularity/recommendations/rec-001.json` and its
companion `rec-001.md`.

The validator supports two modes:

- Schema-only mode: `recommendation_type` is `candidate_schema`, `status` is
  `schema_only`, and `candidates` is empty.
- Candidate-set mode: `recommendation_type` is `candidate_set`, `status` is
  `candidates_proposed`, and `candidates` contains proposed, non-actionable
  records.

## How to run

From the repository root:

```bash
python workshop/tests/validation/validate_recommendation_schema.py
```

Standard library only; no external dependencies. Prints a per-check
`[PASS]`/`[FAIL]` line for every check. Exits `0` with a PASS summary when
all checks pass, exits `1` with failure details when any check fails.

The validator defaults to `rec-001.json`/`rec-001.md`. To validate another
recommendation set such as `rec-002`, point it at the files with environment
variables:

```bash
WORKSHOP_RECOMMENDATION_JSON=workshop/projects/the-myr-singularity/recommendations/rec-002.json \
WORKSHOP_RECOMMENDATION_MD=workshop/projects/the-myr-singularity/recommendations/rec-002.md \
python workshop/tests/validation/validate_recommendation_schema.py
```

Both sets must pass: run once with defaults for `rec-001` and once with the
variables for `rec-002`.

## What it checks

- `rec-001.json` parses as JSON and has every required top-level field
  (schema_version through candidates).
- `recommendation_type` and `status` form a valid schema-only or candidate-set
  pairing.
- `candidates` is empty while the set is schema-only and non-empty while the
  set is a candidate set.
- `generated_from` references existing baseline analysis, brief, deck
  version, card facts, functional roles, and role taxonomy files.
- `candidate_schema` contains the identity, traceability, evidence,
  content, boundary, and review field groups, with the required allowed
  values for `candidate_type`, `status`, `evidence_type`, and `confidence`.
- `candidate_lifecycle` has terminal accepted/rejected states, requires
  `user_decision` and `decision_id` for terminal states, and states that
  acceptance does not change the deck by itself.
- `explicit_no_recommendations_boundary` states that no deck change is
  authorized.
- In schema-only mode, no real recommendation candidate exists and no real card
  names appear in the recommendation files.
- In candidate-set mode, real card names may appear in human-readable summaries,
  but `affected_cards` references must use Scryfall IDs from
  `workshop/card-data/cards.json`.
- Candidate-set records are `proposed`, non-actionable, undecided, and trace to
  baseline analysis, project goals, card facts, and functional roles.
- Deck-altering candidates require Product Owner decision, testing, a decision
  log, and a new deck version before implementation.
- Qualified recommendation card references resolve against the correct fact
  store:
  - `deck:scryfall:<id>` resolves against `workshop/card-data/cards.json`.
  - `candidate:scryfall:<id>` resolves against
    `workshop/card-data/candidate_cards.json`, must not exist in `cards.json`,
    and must have `recommendation_status: "facts_only"`.
  - legacy bare `scryfall:<id>` resolves against `cards.json` only for
    `rec-001`; future recommendation sets must use qualified references.
- Directional card fields are supported for future deck-changing candidates:
  - `affected_cards` contains every card touched by a candidate.
  - `incoming_cards` contains cards entering the deck and must use
    `candidate:scryfall:<id>`.
  - `outgoing_cards` contains cards leaving the deck and must use
    `deck:scryfall:<id>`.
  - `affected_cards` must include every reference from `incoming_cards` and
    `outgoing_cards`.
- `outgoing_cards` must resolve to playable v1.0 commander/main deck cards,
  not sideboard-only cards. Sideboard cards in `affected_cards` still pass.
- `incoming_cards` must be Commander-legal and within the commander color
  identity derived from the v1.0 commander Card Facts record.
- `candidate_scope_limitation.scope_type:
  "internal_current_card_facts_only"` rejects `candidate:scryfall:<id>`
  references, preserving the rec-001 internal-only boundary.
- `rec-001.md` exists and reflects the active mode and no-deck-change boundary.

`candidate_card_facts` is accepted by the validator as a future evidence type.
Candidate facts remain facts-only; external recommendation candidates are not
created by Task 18A.

`rec-001` is frozen as the internal/current-card-facts candidate set. Its
embedded `candidate_schema` does not yet mention `incoming_cards` or
`outgoing_cards`, and it uses legacy bare `scryfall:<id>` references. Future
`rec-002` work should carry an updated candidate schema, likely schema version
`1.1`, so the data contract and validator converge again.

The recommendation validator relates to
`validate_candidate_card_facts.py` as follows: candidate Card Facts validation
proves the external facts layer is facts-only and structurally valid; the
recommendation schema validator controls whether future recommendation
candidates may reference that layer.

## What it does not do

This validator checks schema structure, candidate traceability, and boundaries
only. It does not generate candidates, evaluate cards, run analysis or
simulation, or alter deck, version, card-data, knowledge, analysis, decision, or
report files.

# Candidate Card Facts Validation

`validate_candidate_card_facts.py` validates the external candidate Card Facts
intake layer in `workshop/card-data/candidate_cards.json` and
`workshop/card-data/candidate_card_import_metadata.json`.

It complements the other validators:

- `validate_knowledge_layer.py` validates the existing deck Card Facts and
  functional role assignments.
- `validate_recommendation_schema.py` validates recommendation candidate
  schema and candidate-set boundaries.
- `validate_candidate_card_facts.py` validates external Card Facts that may be
  referenced by future recommendation candidates after validator support exists.

## How to run

From the repository root:

```bash
python workshop/tests/validation/validate_candidate_card_facts.py
```

Standard library only; no external dependencies. Prints a per-check
`[PASS]`/`[FAIL]` line for every check. Exits `0` with a PASS summary when
all checks pass, exits `1` with failure details when any check fails.

## What it checks

- `candidate_cards.json` and `candidate_card_import_metadata.json` parse as
  JSON.
- Exactly six candidate card records exist.
- Metadata reports six imported cards, zero unresolved cards, and an empty
  unresolved list.
- The required candidate card names are present exactly.
- Every record has a Scryfall ID and Scryfall source reference.
- Every record has required canonical fields such as name, type line, color
  identity, legalities, and oracle text where applicable.
- Scryfall IDs are unique.
- Candidate cards do not already exist in `workshop/card-data/cards.json` by
  Scryfall ID or exact name.
- Every record has `recommendation_status: "facts_only"`.
- Candidate facts and metadata contain no actionable recommendation language.

## What it does not do

This validator does not import card facts, create recommendation candidates,
change decks, change versions, update Knowledge, write decisions, or alter any
files.

# Recommendation Review Validation

`validate_recommendation_review.py` validates the Product Owner review
layer: `workshop/projects/the-myr-singularity/recommendations/
review_schema.json` (the review artifact contract) and
`review-rec-002.json`/`review-rec-002.md` (the first review artifact,
scoped to rec-002). It supports both the initial scaffold and reviews the
Product Owner has progressed with non-neutral states.

## What the review artifact is

A review artifact is where a human Product Owner records review intent
about proposed recommendation candidates: notes, rationale, testing needs,
and an eventual review conclusion (`review_status`). It is a separate
artifact from the recommendation candidates it reviews — it never edits
`rec-002.json`, and it never creates a decision or a deck change by itself.

## Layer distinctions

- **Proposed candidate** (`rec-002.json`): a generated, non-actionable
  recommendation candidate record. `status: "proposed"`,
  `is_actionable: false`.
- **Product Owner review** (`review-rec-002.json`): a human review record
  about a candidate. `review_status` values are `under_review`,
  `needs_testing`, `deferred`, `accepted_for_decision`, and `rejected`.
- **`accepted_for_decision`**: a review status meaning the Product Owner
  believes the candidate may proceed to a future decision log task. It
  does **not** change the deck by itself and does not create a decision.
- **Decision log**
  (`workshop/projects/the-myr-singularity/decisions/`): a separate, later
  artifact recording an actual Product Owner decision, created only after
  review.
- **Deck version**
  (`workshop/projects/the-myr-singularity/versions/`): the only place an
  actual deck change is recorded, and only after a decision log entry
  exists.

**Product Owner review does not change the deck.** Only a decision log
entry plus a new deck version file authorize a deck change.

## How to run

From the repository root:

```bash
python workshop/tests/validation/validate_recommendation_review.py
```

Standard library only; no external dependencies. Prints a per-check
`[PASS]`/`[FAIL]` line for every check. Exits `0` with a PASS summary when
all checks pass, exits `1` with failure details when any check fails.

## Artifact states

The validator supports two artifact states:

- **Scaffold state**: every entry is `under_review` and the top-level
  `review_status` is `not_started` or `pending_product_owner_review`.
- **Progressed state**: the Product Owner has recorded non-neutral entry
  states (`needs_testing`, `deferred`, `accepted_for_decision`,
  `rejected`) and the top-level `review_status` is `in_progress` or
  `completed` (`completed` requires that no entry remain `under_review`).

In both states the same boundaries hold: `accepted_for_decision` and
`needs_testing` do not change the deck, no decision log entry is created,
no new deck version (v1.1) is created, and no candidate record is
modified.

## What it checks

- `review_schema.json` and `review-rec-002.json` parse as JSON, and
  `review-rec-002.md` exists.
- The review artifact's `source_recommendation_file` and
  `recommendation_set_id` reference `rec-002.json`, which exists and
  parses.
- Every review entry's `candidate_id` exists in `rec-002.json`, every
  rec-002 candidate has exactly one review entry, and no review entry
  references an unknown or duplicate candidate.
- Every review entry has all required fields (`candidate_id`,
  `recommendation_set_id`, `review_status`, `reviewer_role`,
  `reviewer_notes`, `rationale`, `testing_required`, `testing_notes`,
  `decision_log_required`, `creates_new_deck_version_if_accepted`,
  `reviewed_at`).
- Every entry `review_status` is one of the five allowed Product Owner
  review states, and the top-level `review_status` is consistent with the
  recorded entry states (see "Artifact states" above).
- Every non-neutral entry records a non-null ISO 8601 `reviewed_at`, a
  non-empty `rationale`, and a resolved (non-null) `testing_required`;
  `needs_testing` entries additionally require `testing_required: true`
  and non-empty `testing_notes`.
- `accepted_for_decision` and `needs_testing` entries keep
  `decision_log_required` and `creates_new_deck_version_if_accepted` true
  for deck-changing candidates: progressing a review never bypasses the
  decision-log and new-deck-version path.
- The artifact's `explicit_boundary` keeps `deck_change_authorized`,
  `decision_log_created`, and `new_deck_version_created` false, states
  that no deck change is authorized, and its
  `accepted_or_rejected_or_deferred` flag matches whether any entry is
  `accepted_for_decision`, `rejected`, or `deferred`.
- `decision_log_required` and `creates_new_deck_version_if_accepted` are
  `true` on review entries for candidates whose own `decision_log_required`
  / `creates_new_deck_version` fields are `true` in `rec-002.json`.
- No review entry carries decision-layer fields (`decision_id`,
  `user_decision`), and no decision file in
  `workshop/projects/the-myr-singularity/decisions/` is populated while
  only review states exist.
- No deck version file beyond `v1.0.json` is populated: review states
  never create v1.1.
- rec-002 candidate records remain unmodified: every candidate stays
  `proposed`, `is_actionable: false`, `user_decision: null`, and
  `decision_id: null` regardless of review states.
- The validator does not modify `rec-002.json` or `review-rec-002.json`.
- `review-rec-002.md` states the no-deck-change boundary, mentions Product
  Owner review, and mentions every candidate ID from rec-002.

## What it does not do

This validator does not accept, reject, or defer any candidate, does not
create a decision log entry or a new deck version, does not modify
`rec-001.json`/`rec-001.md`/`rec-002.json`/`rec-002.md`, and does not
alter card-data, Knowledge, analysis, decision, or report files. Recording
an actual review state is a Product Owner action performed by editing
`review-rec-002.json`; this validator only checks the result.
