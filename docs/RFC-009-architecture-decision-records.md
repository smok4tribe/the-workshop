# RFC-009 — The Workshop Architecture Decision Records

Accepted product and architecture decisions after Sprint 1 certification

| Status | Active |
| --- | --- |
| Version | v0.2 |
| Last Updated | 13 July 2026 |
| Document Type | Architecture Decision Record Register |
| Decision Owners | Product Owner / Domain Expert; Software Architect / CTO |
| Evidence Baseline | Certified Sprint 1 local prototype |

> Sprint 1 Ratification<br>ADR-008, ADR-009, ADR-010, and ADR-011 move from Proposed to Accepted.<br>ADR-016 is added to preserve certification integrity and exact reviewed-candidate identity.<br>No previous accepted ADR is superseded or deprecated.

## 1. Purpose

Architecture Decision Records preserve why The Workshop is built the way it is. They prevent implementation convenience, AI behavior, or short-term delivery pressure from silently changing the product constitution.

## 2. ADR Status Values

| Status | Meaning |
| --- | --- |
| Proposed | Decision is written but not yet ratified by evidence or explicit acceptance. |
| Accepted | Decision is active and governs current work. |
| Superseded | A later ADR replaces this decision while preserving historical context. |
| Deprecated | Decision is no longer recommended but still explains historical work. |
| Rejected | Alternative was explicitly considered and declined. |
| Deferred | Decision is important but intentionally postponed. |

## 3. ADR Index

| ID | Decision | Status |
| --- | --- | --- |
| ADR-001 | Projects Are the Root Entity | Accepted |
| ADR-002 | AI Is a Reasoning Layer, Not the Source of Truth | Accepted |
| ADR-003 | Card Knowledge Must Be Structured and Inspectable | Accepted |
| ADR-004 | Recommendations Require Context and Explanation | Accepted |
| ADR-005 | Simulation Is Evidence for Hypotheses, Not a Perfect Game Model | Accepted |
| ADR-006 | DeckVersions Are Immutable Snapshots | Accepted |
| ADR-007 | Decisions Produce Meaningful Deck Version Changes | Accepted |
| ADR-008 | MVP Starts Local-First | Accepted in Sprint 1 |
| ADR-009 | MVP Storage Starts with Markdown and JSON | Accepted in Sprint 1 |
| ADR-010 | Canonical Card Facts Require an External Source | Accepted in Sprint 1 |
| ADR-011 | MVP Prioritizes the Core Engineering Loop Over Full UI | Accepted in Sprint 1 |
| ADR-012 | Popularity Data Is Evidence, Never Proof | Accepted |
| ADR-013 | User Agency Must Be Preserved | Accepted |
| ADR-014 | Accepted Risks Are First-Class Project Knowledge | Accepted |
| ADR-015 | AI-Suggested Knowledge Starts Unvalidated | Accepted |
| ADR-016 | Certification Binds to an Exact Reviewed Commit | Accepted in Sprint 1 |

## 4. Accepted Decisions

### ADR-001 — Projects Are the Root Entity

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-000, RFC-001, RFC-002; The Myr Singularity project structure |

#### Context

A decklist cannot preserve design intent, constraints, history, evidence, decisions, versions, and accepted risks.

#### Decision

Project is the root entity. Decks, DeckVersions, briefs, analysis, recommendations, decisions, reports, notes, and backlog items belong to or are referenced by a Project.

#### Rationale

Deck engineering requires context and history. A project-first model prevents The Workshop from collapsing into a deck editor with attached AI suggestions.

#### Consequences

Serious analysis begins from a Project. Lightweight one-off tools may exist later but cannot replace the project workflow.

#### Revisit Trigger

Revisit only if a lightweight mode is added; serious work should remain project-aware.

### ADR-002 — AI Is a Reasoning Layer, Not the Source of Truth

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-003, RFC-004; external Card Facts and structured review records |

#### Context

AI can explain and propose but is not reliable enough to own canonical card data, simulations, accepted decisions, or project history.

#### Decision

AI may interpret structured evidence, generate hypotheses, evaluate trade-offs, and prepare explanations. Canonical facts and stored state must come from controlled sources and explicit records.

#### Rationale

Trust requires separation between fact, interpretation, hypothesis, recommendation, decision, and evidence.

#### Consequences

AI output must remain attributable and reviewable. The product requires structured data and deterministic validation around AI-assisted work.

#### Revisit Trigger

Revisit tooling, not the separation principle, when future models become more reliable.

### ADR-003 — Card Knowledge Must Be Structured and Inspectable

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-003; functional_roles.json and candidate metadata |

#### Context

The same card can serve different functions across projects. Freeform descriptions are insufficient for repeatable analysis and recommendation logic.

#### Decision

Separate Card Facts, derived data, general Card Knowledge, project-specific knowledge, relationship knowledge, and hypotheses. Track source, confidence, validation state, and scope.

#### Rationale

Structured knowledge enables role density, package fit, synergy, risk, and constraint reasoning without reducing decisions to popularity.

#### Consequences

MVP taxonomies must remain compact. Project overrides are allowed and must not corrupt global facts.

#### Revisit Trigger

Revisit storage representation when the knowledge model outgrows JSON, not before.

### ADR-004 — Recommendations Require Context and Explanation

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | rec-001, rec-002, review-rec-002 |

#### Context

A card suggestion without project context, problem definition, trade-offs, and fit is not a Workshop recommendation.

#### Decision

Recommendations must link to a project, version, analysis or hypothesis, constraints, expected benefit, trade-off, risk, confidence, and suggested validation.

#### Rationale

Explainability preserves user agency and allows later decisions to be reconstructed.

#### Consequences

Recommendations cannot directly edit the deck. They move through Product Owner review and explicit decision records.

#### Revisit Trigger

Revisit only for deliberately lightweight product modes.

### ADR-005 — Simulation Is Evidence for Hypotheses, Not a Perfect Game Model

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-005; Sprint 1 evidence boundary |

#### Context

Commander games are too complex and social for a first simulation system to produce a universal deck score or deterministic judgment.

#### Decision

Every SimulationRun must answer an explicit question, record assumptions and limitations, reference an immutable DeckVersion, and produce reproducible evidence.

#### Rationale

Focused probability evidence can improve decisions without pretending to model complete multiplayer games.

#### Consequences

Sprint 1 may remain valid without simulation. Unrun simulations must be recorded as not_run, not inferred from implementation.

#### Revisit Trigger

Revisit model scope when specific product questions justify additional complexity.

### ADR-006 — DeckVersions Are Immutable Snapshots

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | DeckVersion v1.0 and v1.1 |

#### Context

Mutable deck state destroys comparison, reproducibility, and the ability to explain why a result changed.

#### Decision

A meaningful deck state is stored as an immutable DeckVersion linked to its parent and source decision. Current state points to a version; it does not rewrite history.

#### Rationale

Immutable versions create stable analysis and simulation targets and protect the baseline.

#### Consequences

Storage grows over time, but history remains reconstructable. Cleanup must not rewrite accepted versions.

#### Revisit Trigger

Revisit only the storage mechanism, not immutability.

### ADR-007 — Decisions Produce Meaningful Deck Version Changes

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | decision-002, decision-003, decision-004; deck-change-design-v1.1 |

#### Context

Recommendations are advisory. Without a decision boundary, the system can silently optimize away the user’s intent.

#### Decision

Accepted, modified, rejected, deferred, and test-first outcomes must be recorded. Only approved decisions and design changes may produce a new DeckVersion.

#### Rationale

The user remains the designer. Decision records explain why changes happened and what was intentionally not changed.

#### Consequences

Version creation requires review and approval artifacts. Rejected and deferred candidates remain project knowledge.

#### Revisit Trigger

Revisit only if a future automatic mode is explicitly selected by the user.

### ADR-008 — MVP Starts Local-First

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Certified Sprint 1 repository and merge commit 8d8be6db… |

#### Context

The first proof needed to validate product boundaries and traceability faster than a production web architecture could be justified.

#### Decision

The MVP begins as a repository-local workspace using files, scripts, tests, and version control.

#### Rationale

Local-first maximizes inspectability, fast iteration, and evidence quality while avoiding premature infrastructure.

#### Consequences

Multi-user collaboration, authentication, hosting, and production operations remain deferred. Local-first is a starting architecture, not the final product form.

#### Revisit Trigger

Revisit after the local workflow is stable and a user-facing multi-user need is concrete.

### ADR-009 — MVP Storage Starts with Markdown and JSON

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | 25 Workshop JSON files; deterministic certification, backlog, and report renderers |

#### Context

The prototype requires human-readable reports and machine-verifiable structured sources without committing early to a database schema and migration layer.

#### Decision

Use JSON for structured artifacts and Markdown for readable projections. Generated Markdown must be reproducible from structured sources where applicable.

#### Rationale

This format is inspectable, versionable, portable, and sufficient for a single-user local proof.

#### Consequences

Concurrency, querying, permissions, and large-scale migration remain limited. Database adoption requires an explicit trigger.

#### Revisit Trigger

Revisit when file-based storage blocks collaboration, consistency, performance, or evolution.

### ADR-010 — Canonical Card Facts Require an External Source

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | cards.json, candidate_cards.json, candidate import metadata |

#### Context

AI-authored oracle text, color identity, legality, mana values, and other canonical facts would make analysis untrustworthy.

#### Decision

Canonical Card Facts must be imported or referenced from an external authoritative data source. The current prototype uses Scryfall-derived card data and source metadata.

#### Rationale

External source identity separates factual game data from derived knowledge and AI interpretation.

#### Consequences

Imports require validation, identity checks, and provenance. Project knowledge may interpret facts but cannot replace them.

#### Revisit Trigger

Revisit the provider if coverage, licensing, reliability, or data requirements change.

### ADR-011 — MVP Prioritizes the Core Engineering Loop Over Full UI

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Certified 15-stage product loop |

#### Context

A polished interface could hide an unproven workflow and encourage premature deck-editor behavior.

#### Decision

Prove Project → Brief → Version → Knowledge → Analysis → Recommendation → Review → Decision → Version → Report before implementing a full UI.

#### Rationale

The engineering loop is the product core. UI should expose and support it rather than define it accidentally.

#### Consequences

Sprint 1 remains repository-driven. Sprint 2 may select a narrow user-facing surface after the core loop is certified.

#### Revisit Trigger

Revisit now that Sprint 1 is certified, through an explicit Sprint 2 product decision.

### ADR-012 — Popularity Data Is Evidence, Never Proof

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-000, RFC-003, RFC-004 |

#### Context

Common inclusion can indicate synergy, habit, budget, copying, or meta bias. Popularity alone cannot establish project fit.

#### Decision

Popularity may discover candidates but cannot justify a recommendation without project-specific reasoning and evidence.

#### Rationale

The Workshop optimizes for the Design Brief, identity, constraints, packages, risks, and user goals.

#### Consequences

MVP may omit popularity data entirely. Future integrations must label it as one weighted signal.

#### Revisit Trigger

Revisit when external popularity or metagame data is introduced.

### ADR-013 — User Agency Must Be Preserved

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | Product Owner review and decision pipeline |

#### Context

Commander decks express personal philosophy, budget, variance, social goals, pet cards, and accepted trade-offs.

#### Decision

The user remains the designer. The system may analyze, explain, suggest, test, and document, but cannot silently change the deck or override intent.

#### Rationale

A technically stronger list may be a worse product outcome for the user.

#### Consequences

Review actions must include accept, reject, modify, defer, test-first, and accepted-risk outcomes.

#### Revisit Trigger

Revisit only for explicit automatic modes with clear user authorization.

### ADR-014 — Accepted Risks Are First-Class Project Knowledge

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-002, RFC-003, RFC-004 |

#### Context

Not every weakness should be fixed. Repeatedly flagging intentional trade-offs makes the system noisy and untrustworthy.

#### Decision

Store accepted risks, intentional trade-offs, rejected concerns, and revisit triggers as durable project knowledge.

#### Rationale

This preserves intent and prevents repetitive recommendations.

#### Consequences

Accepted risks remain visible in briefs, decisions, reports, and reasoning context without being treated as unresolved defects.

#### Revisit Trigger

Revisit an accepted risk when its trigger, meta, strategy, or evidence changes.

### ADR-015 — AI-Suggested Knowledge Starts Unvalidated

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | Knowledge validation contracts |

#### Context

AI can infer useful roles and relationships but may be wrong, overly generic, or project-inappropriate.

#### Decision

AI-suggested knowledge begins as unvalidated and records source, scope, confidence, and validation status. Promotion requires controlled review or evidence.

#### Rationale

This allows assistance without converting guesses into canonical knowledge.

#### Consequences

Analysis and recommendations must distinguish validated knowledge from hypotheses.

#### Revisit Trigger

Revisit promotion workflows when knowledge editing becomes a user-facing feature.

### ADR-016 — Certification Binds to an Exact Reviewed Commit

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Sol APPROVE on c0de66c…; recording commit cded1e1…; certification validator |

#### Context

A later recording commit could otherwise repair or alter the artifact that an independent reviewer supposedly approved.

#### Decision

Certification records the exact reviewed commit. The completed record must structurally equal the reviewed pending candidate after projecting only permitted lifecycle fields: certification status, independent review, next action, and gate limitations.

#### Rationale

Independent approval is meaningful only when the reviewed artifact and recorded certification are provably the same substantive candidate.

#### Consequences

Review recording is limited to the certification JSON, generated certification Markdown, and structured review artifact. Material candidate changes require a new review.

#### Revisit Trigger

Revisit only if certification storage changes; exact candidate identity and substantive equivalence must remain.

## 5. Sprint 1 Ratification Evidence

| Decision | Evidence |
| --- | --- |
| ADR-008 Local-first | The complete product loop was executed and reviewed in a repository-local workspace. |
| ADR-009 Markdown/JSON | Structured JSON and deterministic Markdown projections passed validation and no-drift checks. |
| ADR-010 External facts | Card facts and candidate facts retain external source identity and validation boundaries. |
| ADR-011 Core loop before UI | A certified 15-stage loop exists without requiring a full application UI. |
| ADR-016 Exact reviewed commit | Full candidate equivalence and lifecycle-only recording changes were independently tested and approved. |

## 6. Decisions Still Needed

| Candidate ADR | Question |
| --- | --- |
| ADR-017 | What Commander mulligan policy and confidence model governs saved simulations? |
| ADR-018 | When must file-based state migrate to an append-only event model or database? |
| ADR-019 | What first user-facing surface should expose the certified engineering loop? |
| ADR-020 | What evidence threshold moves a needs_testing candidate into recommendation-ready state? |
| ADR-021 | What automation is permitted in recommendation generation without weakening user agency? |

## 7. ADR Maintenance Rules

- Do not rewrite an accepted ADR to make later implementation appear inevitable.

- Use Superseded when a new decision replaces an earlier one.

- Reference concrete artifacts, tests, or delivery evidence when a Proposed ADR becomes Accepted.

- Keep decisions separate from implementation detail unless the detail is itself a durable constraint.

- Record revisit triggers so accepted decisions remain challengeable without becoming unstable.
