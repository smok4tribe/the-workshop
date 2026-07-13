# RFC-013 — The Workshop Sprint 1 Execution / Local Prototype

Final execution record and independently certified closure

| Status | Completed / Certified |
| --- | --- |
| Version | v1.0 |
| Sprint | 1 |
| Completion | 13 July 2026 CEST |
| Document Type | Sprint Execution / Local Prototype Closure |
| Owner | Product Owner / Domain Expert |
| Technical Owner | Software Architect / CTO |
| Fixture | The Myr Singularity |
| Final Merge | 8d8be6db90302da7e0ca808344372f8cbaedc8df |

> Certified Outcome<br>The complete local Deck Engineering product loop was implemented, validated, independently approved, and merged.<br>Certification status: certified.<br>Independent reviewer: Sol — APPROVE.<br>No measured deck-performance claim is included.

## 1. Purpose

RFC-013 is the final execution record for Sprint 1. It replaces the initial not-started build snapshot with the actual repository structure, product-loop outcome, deviations, evidence, certification, and deferred work.

The document does not introduce new product theory. It records what was built and what was not proven.

## 2. Sprint 1 Build Target

Sprint 1 was a product-loop proof sprint. Success required one real Commander project to move through a traceable engineering workflow without becoming a generic card-suggestion tool.

| Success Criterion | Final State |
| --- | --- |
| Project and brief exist | Complete |
| Immutable baseline DeckVersion exists | Complete — v1.0 preserved |
| Canonical Card Facts and functional knowledge exist | Complete |
| Baseline analysis identifies structural pressure | Complete |
| Structured recommendation exists without editing the deck | Complete |
| Product Owner review and decisions exist | Complete |
| Approved changes create a new immutable version | Complete — v1.1 |
| Readable report links to structured evidence | Complete |
| Process is deterministic and independently reviewable | Complete and certified |

## 3. Selected Fixture

| Field | Value |
| --- | --- |
| Project | The Myr Singularity |
| Commander | Urtet, Remnant of Memnarch |
| Working Identity | Artifact combo-control engine disguised as Myr tribal |
| Baseline | DeckVersion v1.0 |
| Resulting Version | DeckVersion v1.1 |
| Reason for Selection | Real project complexity, established user intent, meaningful mana and engine trade-offs, and sufficient structure to test the full workflow. |

## 4. Final Repository Structure

The local prototype established a repository workspace with separated product, evidence, and validation concerns.

| Area | Representative Contents |
| --- | --- |
| Project Workspace | project.json, README, brief, notes, backlog |
| Deck State | deck/current.txt, versions/v1.0.json, versions/v1.1.json |
| Card Data | canonical cards, candidate cards, source/import metadata |
| Knowledge | functional role assignments and validation |
| Analysis | baseline_v1.0 structured analysis |
| Recommendation | rec-001, rec-002, Product Owner review |
| Decision and Design | decision-002 through decision-004, deck-change-design-v1.1 |
| Reporting | project_report_v1.1, Sprint closure and certification artifacts |
| Validation | architecture tests, certification tests, deterministic renderers, checklists |

## 5. Executed Product Loop

| Stage | Status | Evidence Boundary |
| --- | --- | --- |
| Project | complete | Project identity and workspace exist. |
| Brief | complete | Intent, constraints, preferences, and assumptions recorded. |
| Deck Import | complete | Current deck and baseline version aligned. |
| Baseline DeckVersion | complete | v1.0 immutable and retained. |
| Card Facts | complete | External-source factual data validated. |
| Functional Knowledge | complete | Fixture roles structured and inspectable. |
| Baseline Analysis | complete | Structural pressure points recorded. |
| Recommendation | complete | Structured recommendations remain advisory. |
| Product Owner Review | complete | User agency and candidate disposition explicit. |
| Decision | complete | Accepted, deferred, and test-first outcomes recorded. |
| Deck-change Design | complete | Exact approved delta specified. |
| Product Owner Approval | complete | Implementation authorized for the approved delta only. |
| Resulting DeckVersion | complete | v1.1 links to v1.0 and source decisions. |
| Report | complete | Readable report backed by structured sources. |
| Certification | complete | Exact reviewed candidate independently approved and recorded. |

## 6. Actual Deck Change

| IN | OUT | Purpose |
| --- | --- | --- |
| City of Brass | Urza's Mine | Five-color consistency |
| Mana Confluence | Urza's Power Plant | Five-color consistency |
| Urza's Saga | Urza's Tower | Artifact utility and engine access |
| Tezzeret the Seeker | Nevinyrral's Disk | Artifact tutoring and engine support |

The implementation preserved the commander, sideboard, baseline v1.0, and exact approved four-in/four-out delta.

## 7. Candidate Disposition and User Agency

- Recommendations did not modify the deck directly.

- The Product Owner reviewed recommendation evidence before implementation.

- Decisions and deck-change design defined the exact authorized delta.

- Krark-Clan Ironworks remains needs_testing and unimplemented.

- Mana Echoes remains needs_testing and unimplemented.

- Future implementation of either candidate requires new evidence and Product Owner authorization.

## 8. Planned Versus Actual Execution

| Initial Plan | Actual Outcome |
| --- | --- |
| One first recommendation and decision record | The workflow matured into rec-001, rec-002, Product Owner review, three decision records, and an approved deck-change design. |
| Resulting project report named around v1.0 | The final report correctly represents resulting DeckVersion v1.1. |
| Simulation optional | Simulation was deliberately not run; the certification records not_run instead of manufacturing evidence. |
| Basic implementation validation | Scope expanded into adversarial trust-boundary tests, localized capability truth, candidate equivalence, and independent certification. |
| Proposed MVP ADRs | Local-first, Markdown/JSON, external Card Facts, and core-loop-before-UI were ratified by execution. |

## 9. Validation and Certification

| Artifact / Check | Result |
| --- | --- |
| Sprint certification validator | 15/15 PASS |
| Architecture regression suite | 41/41 PASS |
| Certification regression suite | 25/25 PASS |
| Full validation discovery | 66/66 PASS |
| Workshop JSON | 25/25 parsed |
| Certification renderer | No drift |
| Backlog renderer | No drift |
| Project-report renderer | No drift |
| git diff --check | PASS |

### 9.1 Independent Review Record

| Field | Value |
| --- | --- |
| Reviewer | Sol |
| Verdict | APPROVE |
| Reviewed Commit | c0de66c59fbebbf87dd1fea53bd87fe305f9ae1c |
| Recording Commit | cded1e13547c1eff4d524e2d2f0adc0a783077f4 |
| Merge Commit | 8d8be6db90302da7e0ca808344372f8cbaedc8df |
| Blocking Findings | None |
| Non-Blocking Follow-ups | None |

## 10. Certification Trust Boundaries

- Production execution cannot bypass the authoritative base commit or lower-level regressions through environment variables.

- Source failures affect only declared capability domains rather than globally collapsing unrelated completion claims.

- A pending reviewed candidate must contain clean, empty review fields.

- The recorded certification must equal the complete reviewed pending candidate after projecting only permitted lifecycle fields.

- The final recording commit may change only certification JSON, generated certification Markdown, and the structured review artifact.

- Test fixtures canonicalize lifecycle state using the production projection function rather than duplicated logic.

## 11. Evidence Boundary

> What Sprint 1 Proves<br>The local product loop can be executed end to end.<br>Artifacts are structured, linked, reproducible, and reviewable.<br>The approved deck delta was implemented exactly.<br>Certification refers to a specific independently reviewed candidate.

> What Sprint 1 Does Not Prove<br>That DeckVersion v1.1 performs better in real games.<br>That mana consistency improved by a measured amount.<br>That simulation results exist.<br>That gameplay validation or win-rate evidence exists.<br>That KCI or Mana Echoes should be implemented.

## 12. Risk Outcomes

| Initial Risk | Outcome |
| --- | --- |
| False progress through attractive documents | Mitigated through structured sources, deterministic renderers, validators, and independent review. |
| Jumping directly to card suggestions | Mitigated through project, brief, knowledge, analysis, review, decision, and version boundaries. |
| Overbuilding parser or knowledge | Controlled by one fixture format and a compact functional taxonomy. |
| Simulation distraction | Avoided; simulation remained explicitly not_run. |
| Fixture complexity | Managed by implementing one approved, bounded four-card delta. |
| Self-certification | Prevented through Sol’s independent adversarial review and exact commit binding. |

## 13. Deferred Work

| Backlog | Deferred Outcome |
| --- | --- |
| backlog-001 | Post-v1.1 structural analysis |
| backlog-002 | Focused mana and color simulation after assumptions are defined |
| backlog-003 | Krark-Clan Ironworks testing |
| backlog-004 | Mana Echoes testing |
| backlog-005 | Generic version-state cleanup |
| backlog-006 | Append-only transition history |
| backlog-007 | External RFC and ADR synchronization |

## 14. Sprint 1 Closure

Sprint 1 is complete. The product-loop proof is no longer theoretical: it exists in the integration branch, has a fixed evidence boundary, passed deterministic and adversarial validation, received independent approval, and was merged.

The next work is not Sprint 1 cleanup. It is the deliberate definition of Sprint 2.

## 15. Next Action

1. Accept and publish the synchronized RFC-007, RFC-008, RFC-009, and RFC-013 package.

2. Create the Sprint 2 Plan.

3. Create the Sprint 2 Kickoff.

4. Select the first Sprint 2 task only after the outcome and evidence requirements are explicit.
