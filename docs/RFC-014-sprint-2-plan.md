# RFC-014 — The Workshop Sprint 2 Plan

Evidence-driven iteration on the certified local product loop

| Status | Approved / Ready for Kickoff |
| --- | --- |
| Version | v0.1 |
| Sprint | 2 |
| Sprint Name | Evidence Loop Foundation |
| Document Type | Sprint Plan / Execution Plan |
| Owner | Product Owner / Domain Expert |
| Technical Owner | Software Architect / CTO |
| Repository | smok4tribe/the-workshop |
| Baseline Branch | sprint-1-local-prototype |
| Baseline Commit | 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| Primary Fixture | The Myr Singularity — DeckVersion v1.1 |

> Sprint 2 Decision<br>Sprint 1 proved the complete local product loop and is certified.<br>Sprint 2 will prove that the loop can generate reproducible post-implementation evidence.<br>The primary proof is analysis plus deterministic mana/color simulation, not UI or deck automation.<br>No new DeckVersion is required unless evidence later supports a separate Product Owner decision.

## 1. Purpose

This document defines the execution plan for Sprint 2 of The Workshop.

Sprint 1 proved that one real Commander project can move from brief and baseline through analysis, recommendation, Product Owner review, decision, implementation, reporting, validation, and independent certification. Sprint 2 must now prove the next missing product capability: evidence-driven iteration after implementation.

The goal is not to claim that DeckVersion v1.1 is better. The goal is to create trustworthy evidence that can support or challenge that claim.

## 2. Sprint Name and Core Question

| Field | Decision |
| --- | --- |
| Sprint Name | Sprint 2 — Evidence Loop Foundation |
| Primary Product Proof | Reproducible post-implementation analysis and focused simulation tied to exact DeckVersions. |
| Core Question | Can The Workshop compare v1.0 and v1.1, measure a bounded mana/color hypothesis under explicit assumptions, interpret the result honestly, and record a Product Owner decision without automatically changing the deck? |
| Primary Fixture | The Myr Singularity — Urtet, Remnant of Memnarch |
| Compared Versions | Baseline v1.0 and certified implemented v1.1 |

## 3. Sprint Goal

Create the first reproducible evidence loop for The Workshop.

By the end of Sprint 2, the repository must be able to:

- produce a structured post-implementation analysis of DeckVersion v1.1;

- define an explicit Commander simulation policy and data contract;

- run deterministic opening-hand, land-drop, ramp-access, and color-availability tests;

- compare exact DeckVersions v1.0 and v1.1 under the same configuration;

- store SimulationRun and SimulationResult artifacts with assumptions, seed, metrics, uncertainty, and limitations;

- interpret results through a structured ReasoningOutput;

- record a Product Owner decision such as accept evidence, request more testing, defer, or authorize a future recommendation;

- generate a readable evidence report backed by structured sources;

- pass deterministic validation and independent review before Sprint closure.

## 4. Why This Scope Comes Next

- Sprint 1 deliberately stopped before performance claims. Implementation and traceability were proven, but post-implementation analysis, simulation, gameplay validation, and performance remained unmeasured.

- The mana-base change creates a bounded test question. City of Brass and Mana Confluence were added specifically to improve color access; v1.0 and v1.1 provide an exact comparison pair.

- Simulation is a core architectural promise. RFC-005 defines simulation as evidence for hypotheses, but Sprint 1 did not execute that capability.

- Evidence must precede another deck change. KCI, Mana Echoes, or any other candidate should not be implemented merely because the local loop now works.

- A UI is not yet the highest-risk uncertainty. The immediate product risk is whether The Workshop can produce honest, reproducible evidence rather than attractive but unsupported claims.

## 5. Primary Evidence Question

> Committed Question<br>Does DeckVersion v1.1 materially improve early mana development and five-color availability relative to v1.0 under one explicit Commander mulligan policy, without degrading keepable-hand and land-drop rates?

The question is intentionally narrower than “Is v1.1 better?” It tests the stated mana-fixing hypothesis and reports remaining failure patterns without converting a local probability model into a gameplay or win-rate claim.

### 5.1 Required Metrics

- keepable opening-hand rate under the recorded mulligan policy;

- zero-land, one-land, and excessive-land hand rates;

- land-drop success by target turn;

- ramp access by early target turns;

- number of distinct commander colors available by target turn;

- all-five-color availability by target turn where meaningful;

- commander castability under the explicit model, if the required semantics are implemented;

- dominant failure-pattern categories;

- absolute and relative deltas between v1.0 and v1.1;

- uncertainty presentation appropriate to the selected iteration count.

## 6. Committed Scope

### 6.1 Must Have

| Capability | Required Outcome |
| --- | --- |
| Simulation policy | A versioned policy defines mulligans, keep rules, draw semantics, turn horizon, seed policy, iteration policy, modeled card behavior, exclusions, and evidence language. |
| Simulation contracts | SimulationQuestion, SimulationRun, SimulationResult, comparison, and failure-pattern structures are explicit and validated. |
| Post-v1.1 analysis | A new structured analysis describes v1.1 and does not reuse v1.0 conclusions as if they were current evidence. |
| Deterministic engine | The same DeckVersion, policy, configuration, and seed reproduce the same result. |
| Version comparison | v1.0 and v1.1 run under identical policy and metrics, with exact DeckVersion identity preserved. |
| Reasoning interpretation | Results are interpreted against the Design Brief, hypothesis, limitations, and evidence boundary. |
| Product Owner decision | The user records what the evidence means for the project; simulation does not modify the deck. |
| Readable report | A generated report links to structured analysis, policy, runs, results, interpretation, and decision. |
| Validation and review | Schemas, semantics, determinism, renderers, evidence honesty, and lifecycle recording receive regression coverage and independent review. |

### 6.2 Should Have

- confidence intervals or an equivalent uncertainty presentation for probability outputs;

- multiple fixed seeds for sensitivity checks while preserving one canonical saved run;

- comparison renderer for human-readable baseline/current deltas;

- failure-pattern summaries that distinguish mana quantity from color access;

- project-specific keep rules rather than a universal Commander definition of a good hand.

### 6.3 Could Have

- a minimal CLI entry point for creating and executing saved simulation questions;

- a second bounded simulation question if the primary question is complete and stable;

- candidate-evaluation preparation for KCI or Mana Echoes without implementation authorization;

- a lightweight local evidence dashboard generated from existing structured artifacts.

### 6.4 Explicit Non-Goals

- full Commander gameplay simulation;

- opponent, politics, threat assessment, or stack modeling;

- win-rate or average-win-turn claims;

- automatic recommendation generation;

- automatic deck modification or creation of v1.2;

- implementation of Krark-Clan Ironworks or Mana Echoes;

- full web UI, SaaS architecture, authentication, or production database migration;

- general proof that the simulator supports every Commander deck or every card interaction.

## 7. Simulation Boundary

| Boundary | Sprint 2 Rule |
| --- | --- |
| Deck identity | Every run references one exact immutable DeckVersion and records a deck-content fingerprint or equivalent integrity check. |
| Commander and zones | Commander, main deck, and excluded zones are explicit. Sideboard or considering cards must not silently enter a run. |
| Mulligan | Working policy: one free mulligan, then London mulligan. Keep and bottoming logic must be explicit, project-aware, deterministic, and validated. |
| Turn and draw semantics | Play/draw assumptions and first-turn draw behavior are recorded in the policy rather than hidden in code. |
| Card behavior | Only behavior explicitly supported by structured Card Facts and simulation semantics may affect results. |
| Sequencing | Sprint 2 targets draw/access and simplified mana development. Complex tutor, stack, combat, and opponent sequencing are excluded unless separately modeled and disclosed. |
| Randomness | Seed and random generator behavior are recorded. Re-running the same saved run must reproduce the result. |
| Evidence language | Results describe the simulated model, not real-game win probability or universal deck quality. |

## 8. Planned Artifact Model

| Artifact | Purpose |
| --- | --- |
| Simulation Policy | Defines assumptions, mulligan rules, modeled semantics, iteration and seed policy, metrics, limitations, and reporting language. |
| Simulation Question | Binds the hypothesis, compared DeckVersions, target metrics, and success interpretation. |
| Simulation Run | Stores exact configuration, version identity, seed, iterations, execution status, and source references. |
| Simulation Result | Stores metrics, uncertainty, failure patterns, observations, and limitations. |
| Comparison Result | Compares v1.0 and v1.1 using identical policy and metrics. |
| Post-Implementation Analysis | Describes current v1.1 structure before interpreting simulation evidence. |
| Reasoning Output | Explains what the evidence means under the brief and what uncertainty remains. |
| Product Owner Decision | Records accept, defer, test-more, or future-recommendation disposition. |
| Sprint 2 Evidence Report | Human-readable summary generated from structured sources. |

Exact paths and schemas are finalized in the first implementation task. The ownership boundary is fixed: policy and run configuration are not result data; result data are not reasoning; reasoning is not a Product Owner decision.

## 9. Work Breakdown and Sequence

| Task | Outcome | Review Boundary |
| --- | --- | --- |
| Task 30 — Simulation Policy and Contracts | Simulation policy, artifact contracts, renderer/validator expectations, and fixture semantics. | No simulation result or performance statement. |
| Task 31 — Post-v1.1 Analysis | Structured current-state analysis of v1.1 with evidence boundary. | No comparison conclusion before simulation. |
| Task 32 — Deterministic Simulation Core | Opening-hand, land-drop, ramp-access, and color-availability engine with regression fixtures. | No production evidence run until semantics are reviewed. |
| Task 33 — Comparative Evidence Run | Saved canonical runs for v1.0 and v1.1 plus structured comparison. | Exact same policy/configuration; results remain uninterpreted evidence. |
| Task 34 — Reasoning and Product Owner Decision | Interpretation against brief and explicit user disposition. | No automatic version creation. |
| Task 35 — Reporting and Sprint 2 Certification | Readable report, full validation, independent review, lifecycle recording, and merge. | Exact reviewed commit binding required. |

## 10. Quality Gates

| Gate | Pass Condition |
| --- | --- |
| Baseline Integrity Gate | v1.0 and v1.1 are immutable, exact, and independently identifiable. |
| Policy Gate | Every assumption capable of changing results is explicit or explicitly declared unsupported. |
| Card-Fact Gate | Required mana and card attributes come from controlled structured sources; missing semantics fail or limit the run visibly. |
| Determinism Gate | Saved runs reproduce under the same version, policy, configuration, and seed. |
| Semantic Correctness Gate | Known fixture cases prove mulligan, draw, land, mana, color, and failure-pattern behavior. |
| Comparison Gate | Compared versions use identical policy and metric definitions. |
| Evidence Honesty Gate | Reports do not translate simulated access/castability into gameplay performance or win rate. |
| Reasoning Gate | Interpretation distinguishes result, inference, hypothesis, limitation, and recommendation readiness. |
| User Agency Gate | Only the Product Owner records the project disposition; no deck change is automatic. |
| Independent Review Gate | Final certification binds to an exact reviewed commit and permits only narrow lifecycle recording afterward. |

## 11. Definition of Done

- The primary evidence question has a saved, versioned, reproducible answer for both v1.0 and v1.1.

- The post-v1.1 analysis exists independently of the simulation result.

- Every result links to exact policy, question, run configuration, DeckVersion, seed, and structured sources.

- Deterministic and adversarial tests cover normal and misleading cases.

- The readable report can be regenerated without manual edits.

- The evidence boundary explicitly rejects win-rate and real-game-performance claims.

- A Product Owner decision records what happens next, including the valid outcome of making no deck change.

- Independent review returns no blocking findings, the review is recorded against an exact commit, and the Sprint 2 result is merged into its integration branch.

## 12. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| False precision | Record iterations, uncertainty, assumptions, and model limitations; avoid excessive decimal precision. |
| Hidden gameplay assumptions | Policy-first implementation and schema validation before any production result. |
| Card-semantics overreach | Support only explicit deterministic semantics; fail or disclose unsupported behavior. |
| Fixture overfitting | Use small synthetic regression fixtures in addition to The Myr Singularity. |
| Simulation interpreted as judgment | Separate SimulationResult from ReasoningOutput and Product Owner Decision. |
| Scope expansion into full gameplay | Keep Sprint 2 at access, land, mana, ramp, and color evidence. |
| Pressure to implement a candidate | KCI and Mana Echoes remain needs_testing and require a new authorized decision. |

## 13. Sprint Exit Criteria

1. Sprint 2 integration branch contains the complete evidence-loop artifacts and validated implementation.

2. The primary v1.0 versus v1.1 comparison is reproducible and honestly bounded.

3. All required validators, architecture regressions, simulation regressions, JSON checks, and renderers pass.

4. Sol independently reviews the exact candidate commit.

5. The review is recorded without changing protected evidence or implementation artifacts.

6. The certified result is merged and the Sprint Log, Backlog, ADR register, and execution record are synchronized afterward.

## 14. Expected Sprint Outcome

> Successful Sprint 2<br>The Workshop can move from an implemented DeckVersion to reproducible evidence, interpretation, and a user-owned decision.<br>The product can say what changed in the simulated model, what did not change, and what remains unknown.<br>The next deck change, if any, starts from evidence rather than enthusiasm.
