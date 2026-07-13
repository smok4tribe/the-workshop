# RFC-008 — The Workshop Backlog

Prioritized work after the certified Sprint 1 local prototype

| Status | Active |
| --- | --- |
| Version | v0.2 |
| Snapshot | 13 July 2026 |
| Document Type | Product / Architecture / Delivery Backlog |
| Owner | Product Owner / Domain Expert |
| Technical Owner | Software Architect / CTO |
| Baseline | Sprint 1 certified and merged |

> Backlog Boundary<br>Completed Sprint 1 work is archived, not reopened.<br>Deferred analysis, simulation, and candidate testing are future work, not missing Sprint 1 deliverables.<br>KCI and Mana Echoes are not implementation-authorized.<br>Sprint 2 — Evidence Loop Foundation.<br>Status: Active / Kickoff.<br>RFC-014 — Sprint 2 Plan approves the scope; RFC-015 — Sprint 2 Kickoff activates it.<br>Certified baseline: 8d8be6db90302da7e0ca808344372f8cbaedc8df.<br>Integration branch: sprint-2-evidence-loop.<br>Primary fixture: The Myr Singularity v1.0 versus v1.1.<br>Task 30 — Simulation Policy and Contracts is the first execution task.<br>No simulation result may be produced before policy and contracts are reviewed.

## 1. Purpose

This backlog converts product strategy, architecture debt, validation findings, and project opportunities into explicit work. It is not a list of every possible feature. It exists to protect priority, scope, and sequencing.

## 2. Backlog Rules

- Every active item must have a concrete outcome or acceptance boundary.

- Priority reflects product sequencing, not intellectual interest.

- A recommendation candidate is not implementation work until the Product Owner authorizes it.

- Simulation work must state assumptions and test questions before generating results.

- Completed items move to the archive; they are not left open for historical convenience.

- New Sprint scope is selected from the backlog but becomes committed only in a Sprint Plan and Kickoff.

## 3. Status and Priority Model

| Value | Meaning |
| --- | --- |
| P0 | Required to start or close the current delivery phase. |
| P1 | High-value next work with clear product impact. |
| P2 | Important enabling work that can follow the main outcome. |
| P3 | Useful enhancement or cleanup. |
| P4 | Long-horizon or exploratory work. |

| Status | Meaning |
| --- | --- |
| open | Defined but not started. |
| ready | Dependencies resolved and suitable for Sprint selection. |
| in_progress | Actively being executed. |
| needs_testing | Candidate requires evidence before implementation authorization. |
| deferred | Intentionally postponed. |
| blocked | Cannot progress without a named dependency or decision. |
| completed | Acceptance criteria met and evidence recorded. |

## 4. Completed Archive

### 4.1 Sprint 0

- Product Vision, System Architecture, Data Model, Knowledge Engine, Reasoning Engine, Simulation Engine, and UI/UX foundations.

- Sprint Log, Backlog, ADR, Testing Strategy, Sprint 1 Plan, and Sprint 1 Kickoff.

### 4.2 Sprint 1

- Local project skeleton and The Myr Singularity fixture.

- Project and Design Brief contracts.

- Deck import and immutable baseline DeckVersion v1.0.

- External Card Facts, candidate metadata, and Functional Knowledge.

- Baseline structural analysis.

- Structured recommendation, Product Owner review, decisions, and approved deck-change design.

- DeckVersion v1.1 and synchronized current deck.

- Structured and readable reporting.

- Validation architecture, adversarial regressions, deterministic renderers, independent certification, and final merge.

## 5. Post-Certification Transition

| ID | Item | Priority | Status | Acceptance Boundary |
| --- | --- | --- | --- | --- |
| TRANS-001 | Synchronize RFC-007, RFC-008, RFC-009, and RFC-013 | P0 | in_progress / pending PR #33 merge | Updated documents accurately reflect certified Sprint 1 outcomes and do not claim unmeasured performance; completion follows PR #33 merge. |
| TRANS-002 | Define Sprint 2 outcome and scope | P0 | completed | RFC-014 states the approved primary outcome, committed scope, non-goals, risks, and evidence requirements. |
| TRANS-003 | Create Sprint 2 Kickoff | P0 | completed | RFC-015 records roles, branch strategy, fixture scope, review gates, and the first task. |

## 6. Priority Backlog

### 6.1 P0 — Sprint 2 Definition

| ID | Work Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| S2-001 | Select the Sprint 2 primary product proof | completed | RFC-014 selects reproducible post-implementation analysis plus deterministic mana/color simulation. |
| S2-002 | Define evidence and review gates | completed | RFC-014 and RFC-015 name the required artifacts, review gates, and evidence boundaries before execution. |
| S2-003 | Publish approved Sprint 2 Plan and Kickoff | completed | RFC-014 and RFC-015 publish committed scope, non-goals, sequence, owners, and Task 30. |

### 6.2 P1 — Analysis and Simulation Evidence

| ID | Work Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| backlog-001 | Post-v1.1 structural analysis | ready / planned for Task 31 | Structured analysis of v1.1 exists and remains distinct from performance claims. |
| backlog-002 | Focused mana and color simulation | blocked by Task 30 policy/contracts and Task 31 current-state analysis; planned for the deterministic simulation task | Mulligan policy, assumptions, seed policy, metrics, and limitations are recorded before results. |
| SIM-001 | Define Commander mulligan policy for saved simulations | ready / Task 30 | Policy explicitly handles the free mulligan, hand rejection logic, and reproducibility. |
| SIM-002 | Define minimum useful iteration count and confidence presentation | ready / Task 30 | Results include uncertainty and do not imply false precision. |

### 6.3 P1 — Candidate Testing

| ID | Candidate | Status | Required Evidence |
| --- | --- | --- | --- |
| backlog-003 | Krark-Clan Ironworks | needs_testing | Test question, expected role, package impact, cut pressure, gameplay or simulation evidence, Product Owner decision. |
| backlog-004 | Mana Echoes | needs_testing | Test question, tribal scaling assumptions, dead-card risk, package impact, Product Owner decision. |

Neither item is authorized for implementation. A future recommendation must preserve the separation between candidate evaluation, Product Owner review, decision, and DeckVersion creation.

### 6.4 P2 — Platform and Data Integrity

| ID | Work Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| backlog-005 | Generic version-state cleanup | deferred | Version contracts no longer encode fixture-specific or v1.1-specific assumptions. |
| backlog-006 | Append-only transition history | deferred | Decision, approval, implementation, and certification transitions are modeled without rewriting historical records. |
| DATA-001 | Expand canonical Card Facts coverage safely | open | Import remains external-source-driven and validates identity, schema, and source metadata. |
| IMP-001 | Generalize deck import beyond the first supported fixture format | open | Additional formats do not weaken deterministic parsing or baseline preservation. |

### 6.5 P2 — User-Facing Product Surface

| ID | Work Item | Status | Acceptance Criteria |
| --- | --- | --- | --- |
| UX-001 | Select the first user-facing workflow surface | open | Decision compares CLI, local web UI, and structured workspace view against Sprint 2 goals. |
| UX-002 | Expose project status and evidence boundaries | open | Users can see current version, latest analysis, recommendations, decisions, pending tests, and what has not been measured. |
| UX-003 | Recommendation review interaction | open | Accept, reject, modify, defer, and test-first remain explicit actions. |

## 7. Sprint 2 Committed Scope

| Class | Committed Scope |
| --- | --- |
| Must Have | Simulation policy and contracts; post-v1.1 analysis; deterministic comparison of exact v1.0 and v1.1; SimulationRun and SimulationResult artifacts; reasoning interpretation; Product Owner decision; readable evidence report; deterministic validation and independent review. |
| Explicit Non-Goals | No full Commander simulation; no win-rate claim; no automatic deck modification; no v1.2 unless separately authorized; no Krark-Clan Ironworks or Mana Echoes implementation; no full UI or SaaS scope. |

## 8. Open Product Decisions

1. What exact mulligan and bottoming policy details should Task 30 finalize for saved Commander tests?

2. What iteration and uncertainty policy should Task 30 freeze for the first deterministic evidence runs?

3. What evidence threshold should a `needs_testing` candidate meet before it becomes recommendation-ready?

4. When should Markdown/JSON storage stop being sufficient?

5. Which transitions need append-only event history before the product becomes multi-user?

## 9. Long-Horizon Backlog

- Production database and migration tooling.

- Multi-user collaboration, permissions, and concurrent editing.

- Full web application and polished workspace UI.

- Richer Commander rules and interaction modeling.

- Multiplayer simulation and opponent archetype modeling.

- External popularity, price, meta, and collection integrations with explicit evidence weighting.

- Cross-project user memory and reusable personal deckbuilding preferences.

## 10. Backlog Maintenance

- Review priorities at every Sprint definition, not continuously during implementation.

- Link completed items to commits, PRs, decisions, or artifacts.

- Split items that combine product proof, implementation, and validation into independently reviewable work.
