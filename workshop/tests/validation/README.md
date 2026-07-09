# Validation

Automated consistency checks for Sprint 1. Three validators live here:

- `validate_knowledge_layer.py` — guards the Card Facts / Card Knowledge
  boundary (see "Knowledge Layer Validation" below).
- `validate_recommendation_schema.py` — guards the recommendation candidate
  schema, schema-only mode, and candidate-set mode (see "Recommendation Schema
  Validation" below).
- `validate_candidate_card_facts.py` — guards the external candidate Card Facts
  intake layer (see "Candidate Card Facts Validation" below).

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
