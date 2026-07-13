# RFC-007 — The Workshop Sprint Log

Operational history from documentation foundation to the certified local product loop

| Status | Active |
| --- | --- |
| Version | v0.2 |
| Coverage | Sprint 0, Sprint 1, and Sprint 2 kickoff |
| Last Updated | 13 July 2026 |
| Document Type | Project Execution / Sprint Tracking |
| Owner | Product Owner / Domain Expert |
| Technical Owner | Software Architect / CTO |
| Repository | smok4tribe/the-workshop |
| Integration Branch | Sprint 1: sprint-1-local-prototype; Sprint 2: sprint-2-evidence-loop |

> Current State<br>Sprint 0: completed.<br>Sprint 1: completed, independently approved, certified, and merged.<br>Sprint 2 — Evidence Loop Foundation.<br>Status: Active / Kickoff.<br>Sprint 2 Plan: RFC-014 — Sprint 2 Plan approved.<br>Sprint 2 Kickoff: RFC-015 — Sprint 2 Kickoff active.<br>Certified baseline: 8d8be6db90302da7e0ca808344372f8cbaedc8df.<br>Fixture: The Myr Singularity v1.0 versus v1.1.<br>First execution task: Task 30 — Simulation Policy and Contracts.<br>Integration branch: sprint-2-evidence-loop, to be created or verified from the exact certified baseline before Task 30.<br>Documentation synchronization: represented by PR #33 and pending merge until this PR is accepted.

## 1. Purpose

The Sprint Log is the operational memory of The Workshop. It records what was intended, what was actually produced, which decisions changed the product, what evidence exists, and what remains open.

It does not replace RFCs, ADRs, repository history, structured project artifacts, or validation results. It connects them into a readable execution narrative.

## 2. Logging Principles

- Record outcomes, not activity noise. A sprint entry should explain product movement, not reproduce every conversation.

- Separate plan from evidence. Planned work is not complete until an artifact, validation result, or explicit decision proves it.

- Do not rewrite history. Changes in direction are recorded as changes, not silently normalized into the original plan.

- Preserve user agency. Recommendations, decisions, and implemented versions remain distinct.

- Keep evidence boundaries explicit. Unrun simulations and unmeasured performance remain unclaimed.

## 3. Sprint 0 — Documentation Foundation

| Field | Recorded Outcome |
| --- | --- |
| Status | Completed |
| Goal | Define the product, architecture, data, knowledge, reasoning, simulation, UI, execution, backlog, ADR, and testing foundations before implementation. |
| Primary Output | RFC-000 through RFC-012 established the initial product constitution and Sprint 1 operating plan. |
| Key Transition | The Workshop moved from an idea and conversation history to an explicit Deck Engineering Platform specification. |

Sprint 0 established the durable principles used to evaluate Sprint 1: project-first workspaces, immutable DeckVersions, external factual sources, context before recommendations, decisions before implementation, and simulation as evidence rather than judgment.

### 3.1 Sprint 0 Decisions Carried Forward

- Project is the root unit of work; a decklist is one artifact inside a project.

- AI may reason and explain but is not the canonical source of card facts, decisions, simulations, or history.

- Card knowledge must be structured, inspectable, source-aware, and project-sensitive.

- Recommendations must explain problem, benefit, trade-off, risk, confidence, and fit.

- DeckVersions are immutable; meaningful changes require recorded decisions.

- User intent, accepted risks, and deck identity remain first-class constraints.

## 4. Sprint 1 — Local Product Loop

| Field | Final Record |
| --- | --- |
| Status | Completed and certified |
| Fixture | The Myr Singularity — Urtet, Remnant of Memnarch |
| Goal | Prove that one real Commander project can move from brief and baseline to analysis, recommendation, review, decision, DeckVersion, and report with traceable evidence. |
| Final Version | DeckVersion v1.1 |
| Certification | Independent reviewer Sol — APPROVE |
| Merge | PR #32 merged with commit 8d8be6db90302da7e0ca808344372f8cbaedc8df |

### 4.1 Completed Product Loop

1. Create Project and Design Brief.

2. Import the deck and preserve immutable baseline DeckVersion v1.0.

3. Load external canonical Card Facts and candidate metadata.

4. Create compact Functional Knowledge for the fixture.

5. Produce baseline structural analysis and identify pressure points.

6. Create structured recommendations without directly changing the deck.

7. Run Product Owner review and record explicit decisions.

8. Create and approve a deck-change design.

9. Implement DeckVersion v1.1 while preserving v1.0.

10. Generate structured and readable reports.

11. Build deterministic validation, adversarial regressions, and certification evidence.

12. Obtain independent approval, record the review, and merge the certified result.

### 4.2 Implemented Deck Delta

| IN | OUT |
| --- | --- |
| City of Brass | Urza's Mine |
| Mana Confluence | Urza's Power Plant |
| Urza's Saga | Urza's Tower |
| Tezzeret the Seeker | Nevinyrral's Disk |

Krark-Clan Ironworks and Mana Echoes were deliberately not implemented. Both remain needs_testing and require future Product Owner authorization.

### 4.3 Delivery and Review Chronology

| Increment | Outcome |
| --- | --- |
| PRs #29–#30 | Established the executable local loop and implemented the approved v1.1 deck delta. |
| PR #31 | Completed the post-implementation reporting layer; merge base became 7387afcb9a6345a97083506245fa6414504ad654. |
| PR #32 candidate | Built Sprint 1 closure artifacts, validation contracts, backlog, checklists, certification renderer, and adversarial tests. |
| Independent review | Sol requested hardening of trust boundaries, source localization, review cleanliness, and full candidate equivalence before approving. |
| Approved candidate | c0de66c59fbebbf87dd1fea53bd87fe305f9ae1c received APPROVE with no findings or follow-ups. |
| Recording commit | cded1e13547c1eff4d524e2d2f0adc0a783077f4 recorded certification status and the structured review artifact. |
| Final merge | 8d8be6db90302da7e0ca808344372f8cbaedc8df merged PR #32 into sprint-1-local-prototype. |

## 5. Sprint 1 Validation and Certification

| Check | Final Result |
| --- | --- |
| Sprint certification validator | 15/15 PASS |
| Architecture regressions | 41/41 PASS |
| Certification regressions | 25/25 PASS |
| Full validation discovery | 66/66 PASS |
| Workshop JSON | 25/25 parsed |
| Renderers | Certification, backlog, and project report: no drift |
| Independent review | APPROVE — no blocking findings; no non-blocking follow-ups |

Certification is limited to local product-loop execution, structure, traceability, reproducibility, and evidence honesty. It does not claim that v1.1 performs better in games.

- Post-implementation analysis: not run.

- Simulation: not run.

- Gameplay validation: not recorded.

- Performance and win rate: not measured.

## 6. Sprint 1 Decisions Ratified by Execution

- ADR-008: the MVP starts local-first.

- ADR-009: Markdown and JSON are the initial storage and reporting format.

- ADR-010: canonical Card Facts require an external source; the prototype uses Scryfall-derived data.

- ADR-011: the core engineering loop takes priority over full UI implementation.

- ADR-016: final certification must bind to an exact reviewed commit and permit only explicit lifecycle-recording changes afterward.

## 7. Deferred Work

| Backlog ID | Work | Status |
| --- | --- | --- |
| backlog-001 | Post-v1.1 structural analysis | ready / planned for Task 31 |
| backlog-002 | Focused mana and color simulation | blocked by Task 30 policy/contracts and Task 31 current-state analysis; planned for the deterministic simulation task |
| backlog-003 | Krark-Clan Ironworks testing | needs_testing / outside committed Sprint 2 implementation scope |
| backlog-004 | Mana Echoes testing | needs_testing / outside committed Sprint 2 implementation scope |
| backlog-005 | Generic version-state cleanup | deferred / low |
| backlog-006 | Append-only transition history | deferred / low |
| backlog-007 | External RFC and ADR synchronization | in_progress / pending PR #33 merge |

## 8. Sprint 1 Learnings

- Traceability is a product feature. Readable Markdown is insufficient unless it can be reconstructed from structured sources.

- Certification needs adversarial review. Passing happy-path tests did not prove the reviewed candidate was the artifact later recorded.

- Capability truth must be localized. One unrelated source failure must not collapse every completion claim.

- Tests must survive lifecycle transitions. Fixtures cannot assume production remains permanently pending.

- Evidence honesty is non-negotiable. Implementation completion and performance improvement are separate claims.

## 9. Transition to Sprint 2

Sprint 1 is closed. Sprint 2 is active under the approved plan and kickoff documents.

### Completed

1. Sprint 2 primary proof selected: reproducible post-implementation analysis plus deterministic mana/color simulation.
2. RFC-014 — Sprint 2 Plan created and approved.
3. RFC-015 — Sprint 2 Kickoff created and activated.
4. Exact certified baseline selected: `8d8be6db90302da7e0ca808344372f8cbaedc8df`.
5. Sprint 2 integration branch name selected: `sprint-2-evidence-loop`.

### Next

1. Merge Task 29 documentation sync.
2. Create or verify `sprint-2-evidence-loop` from the exact certified baseline.
3. Begin Task 30 — Simulation Policy and Contracts.
4. Do not create production simulation results before Task 30 is reviewed.

## 10. Current Project State

> Project Snapshot<br>Product vision and architecture: documented.<br>Sprint 1: closed and certified.<br>Sprint 2: active at kickoff; RFC-014 and RFC-015 govern the current sprint.<br>Fixture project: The Myr Singularity v1.0 versus v1.1.<br>Sprint 1 certified baseline: 8d8be6db90302da7e0ca808344372f8cbaedc8df.<br>Next execution task: Task 30 — Simulation Policy and Contracts.<br>No Sprint 2 simulation result exists yet.
