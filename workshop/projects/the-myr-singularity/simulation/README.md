# Simulation Contracts and Policy

This directory holds the Sprint 2, Task 30 simulation semantic contract for
The Myr Singularity. Task 30 freezes the contract before any simulation engine
is implemented or run. No SimulationRun, SimulationResult, or comparison result
exists here, and no deck artifact is changed.

## Artifacts and ownership

| Artifact | Owns |
| --- | --- |
| `simulation_policy.json` | Universal, versioned simulation semantics and resolution rules: commander scenario, turn/draw semantics, observation horizon, mulligan/keep/bottoming rules, Level 1 and Level 2 sequencing, mana/color/ramp resolution, seed/RNG identity, iteration and uncertainty policy, deck-content fingerprint definition, card-behavior boundary, and evidence-language boundary. |
| `card_semantics.json` | Project-scoped, source-aware modeled card behavior for cards whose canonical `produced_mana` is null (City of Brass, Mana Confluence, Urza's Saga). The policy references this artifact; fixture-specific card behavior is never encoded in the policy. |
| `contracts/simulation_question.contract.json` | The SimulationQuestion data contract. |
| `contracts/simulation_run.contract.json` | The SimulationRun data contract. |
| `contracts/simulation_result.contract.json` | The SimulationResult data contract. |
| `contracts/comparison_result.contract.json` | The ComparisonResult data contract. |
| `contracts/failure_pattern_taxonomy.json` | The closed set of failure-pattern category identities. |
| `questions/question-001-mana-color.json` | The first evidence question, documented and `not_executed`. |
| `*.md` companions | Deterministic rendered Markdown for the policy and the question. |

Deck identity itself (commander, exact 99-card library, zones) is owned by the
immutable DeckVersion files under `../versions/`. Simulation artifacts reference
DeckVersions by id, path, and deck-content fingerprint; they never copy deck
content.

## Result-changing assumption ownership

Every result-changing assumption has one authoritative home:

- Deck content and identity: `../versions/v1.0.json`, `../versions/v1.1.json`.
- Fixture-specific modeled card behavior: `card_semantics.json`.
- Everything else (mulligan, keep, bottoming, draw/turn semantics, horizon,
  sequencing levels, mana/color/ramp resolution, seed/RNG, iterations,
  uncertainty, fingerprint definition, evidence language): `simulation_policy.json`.
- Failure-pattern category identities: `contracts/failure_pattern_taxonomy.json`.

## Lifecycle boundary

`SimulationPolicy` and `SimulationQuestion` do not carry results.
`SimulationRun` carries configuration and identity, not metrics.
`SimulationResult` carries metrics, not interpretation. Reasoning
interpretation and Product Owner decisions are separate later artifacts. No
simulation artifact creates or edits a DeckVersion.

## Regeneration and validation

```bash
python workshop/scripts/render_simulation_policy.py
python workshop/tests/validation/validate_simulation_contracts.py
python -m unittest workshop.tests.validation.test_simulation_contracts -v
```

The renderer is deterministic: a clean render leaves the committed Markdown
unchanged. The validator recomputes the deck-content fingerprints from the
immutable DeckVersions and verifies the recorded values.
