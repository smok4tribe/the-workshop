# Simulation Contracts and Policy

This directory holds the Sprint 2 simulation semantic contract for
The Myr Singularity. Task 30 freezes the contract before any simulation engine
is implemented or run. No SimulationRun, SimulationResult, or comparison result
exists here, and no deck artifact is changed.

## Artifacts and ownership

| Artifact | Owns |
| --- | --- |
| `simulation_policy.json` | Universal, versioned simulation semantics and resolution rules: commander scenario, turn/draw semantics, observation horizon, executable mulligan/keep/bottoming transitions, Level 1 and Level 2 sequencing, seed/RNG identity, iteration and uncertainty policy, deck-content fingerprint definition, card-behavior boundary, and evidence-language boundary. |
| `mana_source_semantics.json` | Project-scoped normalized executable source registry for every Level 2 mana source in DeckVersions v1.0 and v1.1, including structured profiles, conditions, priority selection, payments, online timing, untap behavior, and unsupported-mode boundaries. |
| `card_semantics.json` | Project-scoped, source-aware modeled card behavior for cards whose canonical `produced_mana` is null (City of Brass, Mana Confluence, Urza's Saga). The policy references this artifact; fixture-specific card behavior is never encoded in the policy. |
| `contracts/simulation_question.contract.json` | The SimulationQuestion data contract. |
| `contracts/simulation_question_lifecycle.contract.json` | The canonical mutable persistence lifecycle contract for an immutable SimulationQuestion. |
| `contracts/simulation_run.contract.json` | The SimulationRun data contract. |
| `contracts/simulation_result.contract.json` | The SimulationResult data contract. |
| `contracts/comparison_result.contract.json` | The ComparisonResult data contract. |
| `contracts/failure_pattern_taxonomy.json` | The closed failure-pattern vocabulary and the exact emitting/non-emitting Result inclusion contract. |
| `questions/question-001-mana-color.json` | The immutable first evidence question. |
| `lifecycle/question-001-mana-color.json` | Canonical preregistered lifecycle state for the first evidence question. |
| `*.md` companions | Deterministic rendered Markdown for the policy and the question. |

Deck identity itself (commander, exact 99-card library, zones) is owned by the
immutable DeckVersion files under `../versions/`. Simulation artifacts reference
DeckVersions by id, path, and deck-content fingerprint; they never copy deck
content.

## Result-changing assumption ownership

Every result-changing assumption has one authoritative home:

- Deck content and identity: `../versions/v1.0.json`, `../versions/v1.1.json`.
- Project-scoped card overrides: `card_semantics.json`.
- Executable Level 2 mana source behavior: `mana_source_semantics.json`.
- Everything else (mulligan, keep, bottoming, draw/turn semantics, horizon,
  sequencing levels, mana/color/ramp resolution, seed/RNG, iterations,
  uncertainty, fingerprint definition, evidence language): `simulation_policy.json`.
- Failure-pattern category identities and Result emission boundary: `contracts/failure_pattern_taxonomy.json`.

Level 2 projects every registered land separately from its modeled mana output:
an unsupported-only canonical land remains a legal land drop but contributes
zero colors and zero mana. Conditional profiles contribute only when their
registered pre-selection conditions are satisfied. Conditional end-step removal
uses a separate post-development state transition.

Unsupported executable profiles present in a tested DeckVersion are recorded
on both Run and Result as deterministic
`unsupported_mana_profile:<oracle_id>:<unsupported_reason_id>` limitation IDs.

## Lifecycle boundary

`SimulationPolicy` and the immutable `SimulationQuestion` do not carry results.
The separate canonical lifecycle artifact records caller-owned persistence
transitions and is never part of the seed-bound semantic identity.
`SimulationRun` carries exact-closed configuration and identity, not metrics.
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
immutable DeckVersions, validates the immutable Question, and verifies the
canonical lifecycle state.
