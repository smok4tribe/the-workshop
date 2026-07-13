# RFC-015 — The Workshop Sprint 2 Kickoff

Operational start of the evidence-driven iteration sprint

| Status | Active / Kickoff |
| --- | --- |
| Version | v0.1 |
| Sprint | 2 |
| Sprint Name | Evidence Loop Foundation |
| Document Type | Sprint Kickoff / Execution Start |
| Owner | Product Owner / Domain Expert |
| Technical Owner | Software Architect / CTO |
| Repository | smok4tribe/the-workshop |
| Source Baseline | sprint-1-local-prototype @ 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| Integration Branch | sprint-2-evidence-loop |
| Primary Fixture | The Myr Singularity — v1.0 compared with v1.1 |

> Kickoff State<br>Sprint 1 is complete, certified, and merged.<br>Sprint 2 scope is approved: post-implementation analysis plus reproducible mana/color evidence.<br>Execution may begin only from the exact certified Sprint 1 merge baseline.<br>The first task is policy and contracts; no production simulation result is created before those are reviewed.

## 1. Purpose

This document officially opens Sprint 2 of The Workshop.

Sprint 2 begins from a certified local product loop. It does not reopen Sprint 1. Its job is to add the missing evidence layer while preserving the same boundaries between fact, analysis, simulation, reasoning, recommendation, decision, versioning, reporting, and review.

## 2. Operational Goal

> Sprint Goal<br>Prove that The Workshop can compare exact DeckVersions through reproducible post-implementation analysis and focused simulation, interpret the evidence honestly, and preserve Product Owner control over the next action.

The first committed question is whether v1.1 improves early mana development and five-color availability relative to v1.0 under an explicit Commander mulligan policy, without worsening keepable-hand and land-drop rates.

## 3. Baseline and Branch Strategy

| Item | Kickoff Decision |
| --- | --- |
| Authoritative source branch | sprint-1-local-prototype |
| Authoritative source commit | 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| Sprint 2 integration branch | sprint-2-evidence-loop |
| Branch creation rule | Create the Sprint 2 integration branch from the exact authoritative source commit; do not silently rebase onto another branch. |
| Task branch rule | One task, one branch, one draft PR, one review cycle, one merge into the Sprint 2 integration branch. |
| Task base rule | Every task records the exact integration head used as its base before implementation begins. |
| Review freeze rule | Once a candidate SHA is handed to Sol, the branch must not move until the verdict is returned. |
| Final certification rule | The final review records the exact reviewed commit and permits only explicitly allowed lifecycle-recording changes afterward. |

## 4. Roles and Authority

| Role | Authority and Responsibility |
| --- | --- |
| Product Owner / Domain Expert | Defines project intent, approves simulation questions and assumptions, reviews interpretation, records decisions, and authorizes any future DeckVersion change. |
| Software Architect / CTO | Defines boundaries, contracts, sequencing, quality gates, review prompts, and acceptance criteria; verifies that implementation matches the product thesis. |
| Implementation Agent — Terra | Implements one scoped task at a time, writes tests and deterministic artifacts, reports exact commands and SHAs, and never self-certifies. |
| Independent Reviewer — Sol | Performs adversarial review against an exact commit, verifies trust boundaries and evidence honesty, and returns APPROVE, REQUEST CHANGES, or HOLD. |

## 5. Sprint 2 Operating Rules

1. Policy before results. No saved production simulation result exists before the policy, contracts, and semantics are reviewed.

2. Exact versions only. Every analysis, run, result, and report references a specific immutable DeckVersion.

3. No hidden assumptions. Mulligan, draw, sequencing, card behavior, seed, iteration count, and success definitions are recorded.

4. Evidence is not judgment. SimulationResult, ReasoningOutput, and Product Owner Decision remain separate artifacts.

5. No automatic deck changes. A simulation cannot create or edit a DeckVersion.

6. No performance overclaim. Access, castability, and mana-development metrics do not become win-rate or gameplay-quality claims.

7. Source truth remains controlled. Card behavior comes from structured facts and explicitly implemented semantics, not model memory.

8. Generated readable artifacts must match structured sources and pass no-drift checks.

9. Terra cannot approve Terra. Sol reviews final candidates independently.

10. A moved candidate invalidates the review and requires a new exact-SHA review.

## 6. Fixture and Comparison Boundary

| Field | Kickoff Value |
| --- | --- |
| Project | The Myr Singularity |
| Commander | Urtet, Remnant of Memnarch |
| Baseline | DeckVersion v1.0 |
| Current implemented version | DeckVersion v1.1 |
| Implemented delta | IN City of Brass, Mana Confluence, Urza's Saga, Tezzeret the Seeker; OUT Urza's Mine, Urza's Power Plant, Urza's Tower, Nevinyrral's Disk. |
| Primary hypothesis | The v1.1 mana-base changes improve early color availability while preserving acceptable hand and land-development quality. |
| Evidence boundary | The comparison measures the explicit simulation model only. It does not prove superior multiplayer performance. |
| Candidate boundary | Krark-Clan Ironworks and Mana Echoes remain needs_testing, unimplemented, and outside committed Sprint 2 implementation scope. |

## 7. Working Simulation Assumptions

Task 30 formalizes and validates these assumptions. Until that task is approved, they are working decisions rather than executable evidence.

| Assumption | Working Decision |
| --- | --- |
| Mulligan | One free mulligan, then London mulligan. Keep and bottoming rules must be explicit and deterministic. |
| Deck zones | Commander and exact 99-card main deck are modeled; sideboard, considering, and unimplemented candidates are excluded. |
| Turn horizon | Primary evidence through turn six, with metric-specific target turns recorded. |
| Draw/play semantics | Explicitly recorded in policy; no hidden first-turn draw assumption. |
| Sequencing level | Level 1 draw/access plus Level 2 simplified mana development. No opponent or combat model. |
| Card semantics | Lands and explicitly supported mana/ramp behavior only. Unsupported behavior is excluded or produces a visible limitation. |
| Randomness | Deterministic seed and reproducible random generator behavior. |
| Comparison | v1.0 and v1.1 use identical policy, iterations, seed strategy, metrics, and interpretation thresholds. |
| Reporting | Percentages include uncertainty or an approved equivalent; false precision is prohibited. |

## 8. Execution Sequence

| Order | Task | Entry Condition | Exit Condition |
| --- | --- | --- | --- |
| 1 | Task 30 — Simulation Policy and Contracts | Sprint 2 branch created from exact baseline. | Policy, schemas/contracts, fixture semantics, tests, and validators approved. |
| 2 | Task 31 — Post-v1.1 Structural Analysis | Policy task merged. | Current-state v1.1 analysis exists and passes analysis validation. |
| 3 | Task 32 — Deterministic Simulation Core | Required card facts and contracts stable. | Synthetic and project fixtures prove deterministic opening-hand, land, ramp, and color behavior. |
| 4 | Task 33 — Comparative Evidence Run | Simulation semantics independently checked. | Canonical v1.0 and v1.1 runs plus comparison artifacts saved and reproducible. |
| 5 | Task 34 — Reasoning Interpretation and Decision | Results are stable and frozen. | Reasoning output and Product Owner disposition recorded without deck mutation. |
| 6 | Task 35 — Reporting and Certification | All product artifacts complete. | Readable report, full validation, independent review, recording commit, and merge. |

## 9. First Task — Task 30

| Field | Task 30 Decision |
| --- | --- |
| Title | Sprint 2 Simulation Policy and Contracts |
| Branch | task-30-s2-simulation-policy-contracts |
| Base | sprint-2-evidence-loop at its initial head derived from 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| PR mode | Draft; unmerged until architectural and adversarial checks pass. |
| Primary outcome | Freeze the semantic contract before implementing or running simulation. |
| Production results | Forbidden in Task 30. |
| Deck changes | Forbidden. |

### 9.1 Required Task 30 Deliverables

- versioned Commander mulligan policy;

- keepability and bottoming-rule contract with project-specific extension points;

- draw/play and turn-index semantics;

- SimulationQuestion, SimulationRun, SimulationResult, and comparison contracts;

- seed, iteration, reproducibility, and uncertainty policy;

- supported and unsupported card-behavior boundary;

- failure-pattern taxonomy for hand, land, mana, ramp, and color failures;

- readable policy renderer or companion Markdown;

- validator and regression tests for malformed, contradictory, and misleading configurations;

- documentation of the exact first evidence question without executing it.

### 9.2 Task 30 Acceptance Criteria

- Every result-changing assumption has one authoritative source.

- The contract prevents a run from floating without Project, DeckVersion, question, policy, seed, and limitations.

- The same semantic field is not duplicated with conflicting meanings across artifacts.

- The policy supports the committed one-free-mulligan-then-London workflow explicitly.

- Unknown or unsupported card behavior cannot silently contribute to a success metric.

- A run cannot claim win rate, gameplay performance, or generic deck quality.

- Tests demonstrate deterministic fixture construction and reject contradictory configuration.

- No production evidence or deck artifact changes are included.

## 10. Review Gates

| Review Stage | Required Check |
| --- | --- |
| Architectural review | Ownership boundaries, schema authority, version identity, and extensibility are correct before implementation proceeds. |
| Implementation review | Patch scope, deterministic semantics, negative tests, and no production-result leakage are verified. |
| Evidence-run review | Exact versions, configuration parity, seed policy, output stability, and limitation language are verified. |
| Reasoning review | The interpretation follows evidence without converting probability into unsupported performance claims. |
| Product Owner review | Matteo explicitly accepts, rejects, defers, or requests more evidence. |
| Sprint certification | Sol reviews the exact final candidate commit; a separate narrow recording commit follows only after APPROVE. |

## 11. Kickoff Readiness Checklist

| Check | State |
| --- | --- |
| Sprint 1 certified and merged | READY — merge commit 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| Post-certification RFC package uploaded | READY |
| Sprint 2 primary proof selected | READY — evidence loop |
| Primary fixture and exact versions selected | READY — v1.0 and v1.1 |
| Primary evidence question selected | READY |
| Integration branch named | READY — sprint-2-evidence-loop |
| First task scoped | READY — Task 30 policy and contracts |
| Independent review model retained | READY |
| Production performance claim | NOT PRESENT — intentionally |

## 12. Immediate Next Action

> Start Sprint 2<br>Create branch sprint-2-evidence-loop from exact commit 8d8be6db90302da7e0ca808344372f8cbaedc8df.<br>Create task branch task-30-s2-simulation-policy-contracts from the new integration head.<br>Open one draft PR and implement only Task 30.<br>Do not run or record the v1.0 versus v1.1 production comparison yet.

## 13. Kickoff Declaration

Sprint 2 is active. Its success will not be measured by how many simulations are run or how many cards are changed. It will be measured by whether The Workshop can create evidence that is exact, reproducible, limited, interpretable, and owned by the user.
