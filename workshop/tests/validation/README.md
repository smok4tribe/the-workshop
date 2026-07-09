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
