# Validation

Automated consistency checks for Sprint 1. Two validators live here:

- `validate_knowledge_layer.py` — guards the Card Facts / Card Knowledge
  boundary (see "Knowledge Layer Validation" below).
- `validate_recommendation_schema.py` — guards the recommendation candidate
  schema and its schema-only state (see "Recommendation Schema Validation"
  below).

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

`validate_recommendation_schema.py` validates the recommendation candidate
schema in
`workshop/projects/the-myr-singularity/recommendations/rec-001.json` and its
companion `rec-001.md` in their current schema-only state.

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
- `recommendation_type` is `candidate_schema` and `status` is `schema_only`.
- `candidates` is an empty array while the set is schema-only.
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
- No real recommendation candidate exists, no real card names appear in the
  schema-only recommendation files, and no actionable deck-change language
  appears (schema vocabulary such as add/cut/swap in field names and
  descriptions is allowed by design).
- `rec-001.md` exists and states that it is schema-only, not a
  recommendation, that the candidates array is empty, and that no deck
  change is authorized.

The script also carries a `validate_candidate` helper for future candidate
records; it runs per candidate and is vacuous while `candidates` is empty.

## What it does not do

This validator checks schema structure and boundaries only. It does not
generate recommendations, create candidates, evaluate cards, run analysis
or simulation, or alter deck, version, card-data, knowledge, or analysis
files.
