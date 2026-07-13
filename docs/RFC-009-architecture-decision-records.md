# RFC-009 — The Workshop Architecture Decision Records

| Field | Current Record |
| --- | --- |
| Status | Active |
| Version | v0.2 |
| Document Type | Architecture Decision Record Register |
| Decision Owners | Product Owner / Domain Expert; Software Architect / CTO |
| Evidence Baseline | Certified Sprint 1 local prototype |

## Version and Source History

RFC-009 v0.1 established ADR governance and ADR-001 through ADR-015. RFC-009 v0.2 ratifies Sprint 1 decisions, records implementation evidence, and adds ADR-016 plus future ADR candidates. Current status changes do not erase the original decision context, alternatives, consequences, or revisit triggers.

## Part I — ADR Governance and Original Decision History (v0.1 Historical Record)

### v0.1 Metadata

Status: Draft Version: v0.1 Sprint: 0 / Sprint 1 Planning Depends on: RFC-000, RFC-001, RFC-002, RFC-003, RFC-004, RFC-005, RFC-006, RFC-007, RFC-008 Document Type: Architecture Decision Records Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

### 1. Purpose

This document records the major architectural and product decisions made during the development of The Workshop.

The ADR exists to preserve why important choices were made.

The Workshop is not only a product.

It is an engineered system.

Therefore, major decisions should be:

- explicit

- dated

- justified

- reversible when appropriate

- connected to trade-offs

- connected to the relevant RFCs

- readable by future contributors

The goal is not bureaucracy.

The goal is project memory.

Six months from now, the team should be able to understand not only what The Workshop became, but why it became that way.

### 2. ADR Thesis

The Workshop must not drift into a generic deck builder, chatbot, or card suggestion tool.

The ADR system exists to protect the core product thesis by documenting decisions that affect:

- product direction

- architecture

- data model

- knowledge model

- AI boundaries

- recommendation behavior

- simulation philosophy

- UI structure

- MVP scope

- implementation strategy

A decision is important enough for an ADR when changing it later would affect the shape of the product.

### 3. ADR Responsibilities

The ADR is responsible for recording:

- major architecture decisions

- product-shaping decisions

- MVP implementation decisions

- module boundary decisions

- AI responsibility boundaries

- storage and persistence decisions

- knowledge source decisions

- simulation assumptions

- UI workflow decisions

- accepted trade-offs

- rejected alternatives

- future revisit triggers

The ADR is not responsible for:

- tracking every task

- replacing the Backlog

- replacing RFCs

- storing implementation notes too small for architecture

- acting as a changelog

- storing informal brainstorming

Small tasks belong in the Backlog.

Execution history belongs in the Sprint Log.

Stable system design belongs in RFCs.

Important decisions belong here.

### 4. ADR Format

Each ADR should use the following structure:

#### ADR-XXX — Title

Status:

Date:

Related RFCs:

Decision Owner:

Technical Owner:

#### Context

What problem, uncertainty, or architectural question required a decision?

#### Decision

What did we decide?

#### Rationale

Why did we choose this?

#### Alternatives Considered

What other options were considered?

#### Consequences

What becomes easier?

What becomes harder?

What trade-offs did we accept?

#### Revisit Trigger

When should this decision be reviewed again?

### 5. ADR Status Values

Recommended ADR status values:

- Proposed

- Accepted

- Superseded

- Deprecated

- Rejected

- Deferred

Proposed

The decision is drafted but not final.

Accepted

The decision is currently active.

Superseded

The decision was replaced by a later ADR.

Deprecated

The decision is no longer recommended, but may still explain historical context.

Rejected

The decision was considered and explicitly rejected.

Deferred

The decision is important but intentionally postponed.

### 6. ADR Index

| ADR | Title | Status |
| --- | --- | --- |
| ADR-001 | Projects Are the Root Entity | Accepted |
| ADR-002 | AI Is a Reasoning Layer, Not the Source of Truth | Accepted |
| ADR-003 | Card Knowledge Must Be Structured and Inspectable | Accepted |
| ADR-004 | Recommendations Require Context and Explanation | Accepted |
| ADR-005 | Simulation Is Evidence for Hypotheses, Not a Perfect Game Model | Accepted |
| ADR-006 | DeckVersions Are Immutable Snapshots | Accepted |
| ADR-007 | Decisions Produce Meaningful Deck Version Changes | Accepted |
| ADR-008 | MVP Should Start Local-First | Proposed |
| ADR-009 | MVP Storage Should Start with Markdown and JSON | Proposed |
| ADR-010 | Canonical Card Facts Require an External Source | Proposed |
| ADR-011 | MVP Should Prioritize the Core Engineering Loop Over Full UI | Proposed |
| ADR-012 | Popularity Data Is Evidence, Never Proof | Accepted |
| ADR-013 | User Agency Must Be Preserved | Accepted |
| ADR-014 | Accepted Risks Are First-Class Project Knowledge | Accepted |
| ADR-015 | AI-Suggested Knowledge Starts Unvalidated | Accepted |

#### ADR-001 — Projects Are the Root Entity

Status: Accepted Date: Sprint 0 Related RFCs: RFC-000, RFC-001, RFC-002, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Most deckbuilding tools treat the decklist as the primary object.

The Workshop does not only need to store a list of cards.

It needs to store:

- Design Brief

- commander

- deck identity

- user constraints

- deck versions

- analysis reports

- recommendations

- decisions

- simulation results

- notes

- backlog items

- project-specific knowledge

- accepted risks

- reasoning history

A decklist alone cannot preserve why changes happened or what the deck is trying to become.

Decision

The root entity of The Workshop is Project, not Decklist.

A Project owns or references every meaningful artifact in the workspace.

A decklist is only one artifact inside a Project.

Rationale

The Workshop is a Deck Engineering Platform.

Engineering requires context, history, constraints, hypotheses, tests, and decisions.

A Project can answer:

- What are we trying to build?

- What does better mean here?

- What version are we testing?

- What weaknesses were identified?

- What did we decide?

- What did we reject?

- What changed over time?

A decklist cannot answer those questions by itself.

Alternatives Considered

Decklist-first model

Rejected.

It would be simpler, but it would push the product toward becoming a normal deck editor with AI suggestions attached.

Commander-first model

Rejected.

A commander is important, but it does not define the whole project.

Two decks with the same commander can have different identities, constraints, budgets, metas, and success criteria.

User-first model

Deferred.

User-level memory may matter later, but the MVP should focus on individual deck engineering projects.

Consequences

This decision makes the system more structured.

It also means the MVP must create projects before performing serious analysis.

The product may feel heavier than a normal deck builder, so the UI must make project creation lightweight.

Revisit Trigger

Review this decision if The Workshop later supports lightweight one-off analysis without project persistence.

Even then, serious analysis should still prefer Project context.

#### ADR-002 — AI Is a Reasoning Layer, Not the Source of Truth

Status: Accepted Date: Sprint 0 Related RFCs: RFC-000, RFC-001, RFC-003, RFC-004, RFC-005 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

AI can generate useful explanations, hypotheses, and recommendations.

However, AI should not be trusted as the canonical source for:

- oracle text

- mana cost

- color identity

- legality

- rulings

- prices

- exact card facts

- stored decisions

- simulation results

- project history

If the AI becomes the source of truth, the system becomes unreliable.

Decision

AI is a reasoning layer.

AI may:

- interpret the Design Brief

- explain deck identity

- reason about trade-offs

- generate hypotheses

- evaluate candidates

- suggest tests

- prepare recommendation rationale

- summarize reports

- document decisions

AI must not be the only source for canonical facts, simulations, accepted decisions, or stored history.

Rationale

The Workshop depends on trust.

Trust requires a separation between:

- fact

- interpretation

- hypothesis

- recommendation

- decision

AI is useful for interpretation.

It is not reliable enough to own factual game data or historical project records.

Alternatives Considered

AI-as-database

Rejected.

This would make the system fast to prototype but impossible to trust.

AI-only deck consultant

Rejected.

That would recreate the generic chatbot behavior The Workshop is explicitly avoiding.

Fully deterministic system with no AI

Rejected.

The Workshop needs reasoning, explanation, trade-off analysis, and collaboration.

AI is valuable when grounded in structured data.

Consequences

The architecture must include structured knowledge, persistent project data, and explicit decision records.

The MVP can still use AI assistance, but AI outputs must be marked as reasoning, not truth.

Revisit Trigger

Review only if future AI systems can reliably cite, verify, and update canonical game data through controlled tools.

Even then, source separation should remain.

#### ADR-003 — Card Knowledge Must Be Structured and Inspectable

Status: Accepted Date: Sprint 0 Related RFCs: RFC-001, RFC-002, RFC-003 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop needs to understand more than card names.

It needs to know:

- what a card says

- what a card does mechanically

- what role it usually plays

- what role it plays in a specific project

- what engines it supports

- what packages it belongs to

- what synergies it creates

- what risks it introduces

- what constraints it may violate

If this knowledge is not structured, recommendations become generic and hard to explain.

Decision

Card knowledge must be structured, inspectable, source-tracked, and confidence-scored.

The system must separate:

- Card Facts

- Derived Card Data

- Card Knowledge

- Project-Specific Knowledge

- User-Defined Knowledge

- Relationship Knowledge

- Reasoning Hypotheses

Rationale

A card can mean different things in different decks.

Example:

- Globally, a card may be ramp.

- In one project, it may be artifact count support.

- In another project, it may be a combo piece.

- In another project, it may be off-plan filler.

The system must be able to explain that difference.

Structured knowledge allows The Workshop to reason about engines, packages, roles, synergies, risks, and constraints instead of only card popularity.

Alternatives Considered

Freeform AI descriptions only

Rejected.

They are not reliable enough for analysis, filtering, simulation, or repeatable recommendation logic.

Massive graph model from day one

Rejected for MVP.

It may be useful later, but it risks over-modeling too early.

Simple tags only

Accepted only as an MVP starting point.

Tags are useful, but they must not become noisy or unbounded.

Consequences

The MVP should start with a compact FunctionalRole taxonomy and semi-structured JSON where appropriate.

The system must avoid tag spam.

Knowledge should be useful only when it improves analysis, reasoning, recommendation, simulation, or reporting.

Revisit Trigger

Review when the MVP role taxonomy becomes too limited or when project-level JSON becomes hard to query.

#### ADR-004 — Recommendations Require Context and Explanation

Status: Accepted Date: Sprint 0 Related RFCs: RFC-000, RFC-001, RFC-002, RFC-004, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Most deckbuilding advice jumps directly to card suggestions.

The Workshop must not behave like:

“Add this staple because it is strong.”

A recommendation can be powerful in general but wrong for the project.

Examples:

- A tutor may improve consistency but violate a low-tutor philosophy.

- A staple may increase power but damage originality.

- A combo piece may improve win rate but break the target bracket.

- A mana upgrade may be correct online but invalid for a paper budget.

Decision

A recommendation is valid only if it is contextual and explainable.

Every serious recommendation should include:

- problem solved

- proposed change

- affected engine or package

- expected benefit

- trade-off

- risk

- constraint check

- confidence

- test suggestion when useful

- rationale

Rationale

The Workshop does not optimize decks in the abstract.

It improves a specific deck, for a specific player, under a specific brief.

A recommendation without context is just a suggestion.

A recommendation with rationale becomes an engineering proposal.

Alternatives Considered

Generic suggestion feed

Rejected.

This would make The Workshop too similar to existing deckbuilding tools.

Automatic optimizer

Rejected.

The system should not silently modify decks or override user taste.

Recommendation after full simulation only

Rejected.

Some recommendations are obvious enough without simulation.

Simulation should support uncertain or high-impact decisions, not block all reasoning.

Consequences

The Recommendation Engine must depend on Design Brief, Analysis, Reasoning, Knowledge, and Project History.

The UI must present recommendations as reviewable proposals, not automatic upgrades.

Revisit Trigger

Review if the MVP becomes too slow or heavy because every recommendation requires too much structure.

The likely adjustment should be mode-based depth, not removal of explanation.

#### ADR-005 — Simulation Is Evidence for Hypotheses, Not a Perfect Game Model

Status: Accepted Date: Sprint 0 Related RFCs: RFC-001, RFC-002, RFC-004, RFC-005, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Commander games are complex.

A full simulation would need to model:

- four-player interaction

- politics

- stack interaction

- threat assessment

- mulligans

- tutors

- hidden information

- sequencing

- removal timing

- table behavior

- deck-specific heuristics

Trying to simulate all of Commander in the MVP would be unrealistic.

But smaller simulations can still answer useful deckbuilding questions.

Decision

Simulation in The Workshop is evidence for specific hypotheses.

It is not a perfect game model.

A SimulationRun must have a test question.

Correct:

“How often does this DeckVersion produce double-white by turn six?”

Incorrect:

“Is this deck good?”

Rationale

Simulation is valuable when it tests concrete engineering questions.

Useful MVP simulation types include:

- opening hand quality

- land drop probability

- mana consistency

- color availability

- ramp access

- engine access

- mulligan quality

- basic goldfish Level 1 / Level 2

Simulation should increase confidence.

It should not create false certainty.

Alternatives Considered

No simulation in MVP

Rejected as a long-term principle, but some simulation can be delayed.

The Workshop needs evidence-based testing to support the engineering loop.

Full Commander gameplay simulation

Rejected for MVP.

Too complex and likely misleading.

Generic deck score

Rejected.

A deck score hides assumptions and pushes the product toward shallow optimization.

Consequences

Every SimulationResult must show:

- test question

- DeckVersion tested

- assumptions

- mulligan policy

- iterations

- key metrics

- failure patterns

- limitations

The Reasoning Engine interprets simulation results.

The Simulation Engine does not decide deck quality by itself.

Revisit Trigger

Review when MVP Level 1 and Level 2 simulations are stable and the project is ready to experiment with heuristic sequencing.

#### ADR-006 — DeckVersions Are Immutable Snapshots

Status: Accepted Date: Sprint 0 Related RFCs: RFC-001, RFC-002, RFC-005, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop needs to compare deck states over time.

If decklists are edited in place, the system loses:

- historical accuracy

- simulation validity

- recommendation traceability

- decision history

- rollback ability

- changelog generation

A simulation result is meaningful only if the exact tested deck state is preserved.

Decision

DeckVersions are immutable snapshots.

Meaningful deck changes create new DeckVersions.

Corrections, experiments, accepted recommendations, rejected experiments, and reverts should preserve history.

Rationale

Deckbuilding is an iterative engineering loop:

Brief → Analyze → Recommend → Test → Decide → Version

Each version represents a known state in that loop.

Immutable versions allow The Workshop to answer:

- What did the deck look like then?

- What changed?

- Why did it change?

- What test was run?

- Did the change work?

- Should we revert?

Alternatives Considered

Mutable current deck only

Rejected.

Too simple for serious project history.

Git-like full branching from day one

Deferred.

The concept is useful, but MVP can start with parent_version_id and simple version chains.

Consequences

The MVP must create a new DeckVersion for meaningful changes.

The current version should point to the active DeckVersion.

Reverts should create new versions rather than deleting history.

Revisit Trigger

Review when branching, paper/online variants, or budget/high-power variants become necessary.

#### ADR-007 — Decisions Produce Meaningful Deck Version Changes

Status: Accepted Date: Sprint 0 Related RFCs: RFC-002, RFC-004, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Recommendations are proposals.

They should not automatically modify the deck.

The user remains the designer.

The system needs to record not only what was suggested, but what was actually chosen.

Decision

Only a Decision can produce a meaningful new DeckVersion.

A Recommendation does not modify the deck by itself.

A Decision may:

- accept

- reject

- defer

- modify

- test first

- accept as experiment

- revert

- mark as accepted risk

Rationale

This preserves user agency and project memory.

The Workshop should be able to answer:

- What did the system propose?

- What did the user choose?

- What was accepted?

- What was rejected?

- What was modified?

- What evidence supported the decision?

- What version resulted?

Alternatives Considered

Recommendations automatically update the deck

Rejected.

This would make the system too authoritarian and reduce trust.

Manual deck editing with no decision record

Rejected.

This would lose the reasoning history.

Consequences

The UI must include Recommendation Review and Decision Log surfaces.

The data model must separate Recommendation from Decision.

The project history must preserve rejected and deferred recommendations.

Revisit Trigger

Review if the MVP includes lightweight temporary edits before formal decisions.

Even then, serious changes should still be decision-backed.

#### ADR-008 — MVP Should Start Local-First

Status: Proposed Date: Sprint 1 Planning Related RFCs: RFC-001, RFC-007, RFC-008 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop can be implemented first as:

- a local-first prototype

- a web-first application

- a chatbot-assisted workflow

- a database-backed service

A web-first product would better represent the long-term UX, but it adds significant complexity early.

Sprint 1 should prove the product loop before building a full application.

Decision

The MVP should start local-first.

The first prototype should use local files, scripts, Markdown, and JSON to prove the core product loop.

Rationale

A local-first prototype allows fast iteration on:

- project structure

- deck import

- Design Brief format

- DeckVersion format

- card data import

- role taxonomy

- analysis report templates

- decision log format

- simple simulations

- Markdown reports

This proves whether the core model works before UI complexity is introduced.

Alternatives Considered

Web-first application

Deferred.

Better for final UX, but slower for Sprint 1.

Chatbot-only prototype

Rejected.

It would not prove the structured system model.

Database-first backend

Deferred.

The data model is rich, but premature infrastructure could slow learning.

Consequences

Sprint 1 should focus on repository structure and local project files.

The architecture should remain migration-friendly so local files can later move into a database-backed app.

Revisit Trigger

Review after the local prototype can complete the MVP loop on at least one real deck project.

#### ADR-009 — MVP Storage Should Start with Markdown and JSON

Status: Proposed Date: Sprint 1 Planning Related RFCs: RFC-001, RFC-002, RFC-007, RFC-008 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop data model includes many entities:

- Project

- DesignBrief

- DeckVersion

- DeckCard

- Card

- CardKnowledge

- AnalysisReport

- Recommendation

- Decision

- SimulationRun

- SimulationResult

- Report

- Note

- BacklogItem

A full relational or graph database may eventually be useful.

However, Sprint 1 needs to prove the product loop quickly.

Decision

MVP project storage should start with Markdown and JSON.

Structured data should live in JSON files.

Human-readable outputs should live in Markdown files.

Rationale

Markdown and JSON are:

- easy to inspect

- easy to version

- easy to edit manually

- easy to generate with scripts

- easy to migrate later

- enough to prove the MVP loop

This approach keeps the system concrete without overcommitting to a final database technology.

Alternatives Considered

SQLite

Useful, but deferred.

May become the next step after file schemas stabilize.

PostgreSQL

Too heavy for Sprint 1.

Better for a web-backed product later.

Graph database

Deferred.

Potentially useful for knowledge relationships, but too complex for MVP.

Markdown only

Rejected.

Readable but not structured enough.

JSON only

Rejected.

Structured but not friendly for reports and human review.

Consequences

The MVP should define clear file schemas.

Markdown outputs should include or reference structured metadata.

The project folder structure becomes the first implementation of the product model.

Revisit Trigger

Review when file-based storage becomes hard to query, validate, compare, or migrate.

#### ADR-010 — Canonical Card Facts Require an External Source

Status: Proposed Date: Sprint 1 Planning Related RFCs: RFC-001, RFC-002, RFC-003, RFC-008 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop requires reliable card facts.

These include:

- card name

- oracle text

- mana cost

- mana value

- type line

- color identity

- colors

- legality

- produced mana

- printings

- rulings

- prices where available

The AI must not author these facts.

Decision

The Workshop must use a canonical external card data source for card facts.

The exact source should be selected during Sprint 1.

Rationale

Reliable card data is required for:

- deck parsing

- legality checks

- role classification

- mana analysis

- color availability simulation

- recommendation validation

- report generation

Without canonical card facts, the system cannot be trusted.

Alternatives Considered

AI-generated card facts

Rejected.

Too unreliable.

User-entered card facts

Rejected except for custom notes or overrides.

Too much manual effort and too error-prone.

Multiple sources immediately

Deferred.

MVP should use one canonical source first, then add enrichment sources later.

Consequences

Sprint 1 must choose and document the card data source.

The import pipeline must preserve source metadata and refresh strategy.

Card Facts and Card Knowledge must remain separate.

Revisit Trigger

Review when the MVP needs price accuracy, rulings depth, popularity data, or collection integration beyond the first source.

#### ADR-011 — MVP Should Prioritize the Core Engineering Loop Over Full UI

Status: Proposed Date: Sprint 1 Planning Related RFCs: RFC-001, RFC-006, RFC-007, RFC-008 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The full Workshop UI includes:

- Project Dashboard

- Design Brief

- Deck View

- Component Map

- Engine View

- Analysis Reports

- Simulation Results

- Recommendation Review

- Decision Log

- Version History

- Notes / Backlog

Building all of this immediately would slow the project and increase scope risk.

Decision

The MVP should prioritize the core engineering loop over full UI.

The first implementation should prove:

Project → Brief → Deck Import → Analysis → Recommendation → Decision → Version → Report

Rationale

The Workshop’s value is not visual polish first.

Its value is structured deck engineering.

If the core loop works in files and reports, the UI can later make that loop easier and more beautiful.

If the core loop does not work, a polished UI will not save the product.

Alternatives Considered

Build dashboard first

Deferred.

Useful later, but not the first proof.

Build deck editor first

Rejected for MVP priority.

This risks making the product feel like a normal deck builder.

Build chat-first UX

Rejected.

The Workshop should not be a chatbot with deck features.

Consequences

Sprint 1 should focus on schemas, parser, card data, analysis, reports, and decision records.

UI design remains important, but implementation can wait until the product loop is proven.

Revisit Trigger

Review after the local prototype can produce useful reports and versioned decisions.

#### ADR-012 — Popularity Data Is Evidence, Never Proof

Status: Accepted Date: Sprint 0 Related RFCs: RFC-000, RFC-003, RFC-004 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Commander deckbuilding tools often over-rely on popularity.

A card being widely played does not mean it belongs in a specific deck.

Popularity may reflect:

- real synergy

- format staples

- budget availability

- social copying

- outdated trends

- generic goodstuff

- cEDH bias

- casual bias

- precon upgrade patterns

The Workshop must not become an EDHREC clone.

Decision

Popularity data is evidence, never proof.

Popularity may suggest candidates.

It cannot justify inclusion by itself.

Rationale

The Workshop optimizes for project fit.

A card should be evaluated through:

- Design Brief

- deck identity

- engine fit

- package fit

- role density

- user constraints

- budget

- bracket

- meta

- trade-offs

- testing evidence

Popularity can help discovery.

It cannot replace reasoning.

Alternatives Considered

Ignore popularity completely

Deferred.

Popularity may be useful as one signal.

Use popularity as recommendation ranking

Rejected.

This would bias the system toward generic deckbuilding.

Consequences

Recommendation rationale must not say only:

“This card is commonly played.”

It must explain why the card solves a project-specific problem.

Popularity data may be excluded from MVP to avoid bias.

Revisit Trigger

Review when adding external popularity or meta data sources.

#### ADR-013 — User Agency Must Be Preserved

Status: Accepted Date: Sprint 0 Related RFCs: RFC-000, RFC-004, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

The Workshop should feel like collaborating with an experienced deck engineer.

It should not feel like a system dictating the correct list.

Commander deckbuilding is personal.

The user defines:

- deck philosophy

- budget

- power target

- acceptable variance

- tutor tolerance

- combo tolerance

- table experience

- pet cards

- originality requirements

- accepted risks

Decision

The user remains the designer.

The system can analyze, explain, suggest, test, and document.

It must not silently change the deck or override user intent.

Rationale

A technically stronger deck may be a worse deck for the user.

The Workshop exists to make the user a better deckbuilder, not to remove them from the process.

Alternatives Considered

Fully automated deck optimization

Rejected.

Wrong product.

AI-driven final decklist generation

Rejected as the default behavior.

Possible as a future lightweight mode, but not the core product.

Consequences

The UI must support:

- review

- accept

- reject

- modify

- defer

- test first

- accepted risk

- alternatives

The Decision Log is required.

Revisit Trigger

Review only if future product modes explicitly support automatic generation.

Even then, automatic generation should not replace the engineering workflow.

#### ADR-014 — Accepted Risks Are First-Class Project Knowledge

Status: Accepted Date: Sprint 0 Related RFCs: RFC-002, RFC-003, RFC-004, RFC-006 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

Not every weakness should be fixed.

Some weaknesses are intentional trade-offs.

Examples:

- low graveyard hate because the meta does not require it

- fewer tutors because the user values variance

- lower interaction density because the deck prioritizes engine density

- slower win condition because table experience matters

- expensive card excluded because of paper budget

- generic staple rejected because it damages identity

If the system keeps flagging intentional trade-offs, it becomes annoying and untrustworthy.

Decision

Accepted Risks are first-class project knowledge.

The system should store them, display them, and respect them in future reasoning.

Rationale

Accepted risks preserve user intent.

They also prevent repetitive recommendations.

The system should distinguish:

- unresolved problem

- intentional trade-off

- accepted risk

- rejected concern

- deferred issue

Alternatives Considered

Treat all weaknesses as problems to fix

Rejected.

This would violate the product philosophy.

Hide accepted risks completely

Rejected.

They should remain visible as project memory, but not noisy.

Consequences

Accepted risks should appear in:

- Design Brief

- Decision Log

- Reports

- Project Dashboard

- Recommendation Review

- Reasoning context

Accepted risks should have revisit triggers.

Revisit Trigger

Review if accepted risks become stale due to meta changes, deck strategy changes, or repeated gameplay failures.

#### ADR-015 — AI-Suggested Knowledge Starts Unvalidated

Status: Accepted Date: Sprint 0 Related RFCs: RFC-003, RFC-004 Decision Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

Context

AI can help suggest:

- functional roles

- risk tags

- synergies

- combo candidates

- project-specific interpretations

- archetype relationships

- possible cuts

- possible package issues

However, AI-suggested knowledge may be wrong, incomplete, or overconfident.

If AI-generated knowledge is stored as trusted truth, the Knowledge Engine becomes polluted.

Decision

AI-suggested knowledge starts unvalidated.

It must be marked with:

- source: AI-suggested

- confidence

- validation status

- scope

- explanation

- evidence if available

AI-suggested knowledge should not become global curated knowledge without review.

Rationale

This preserves the distinction between:

- fact

- interpretation

- hypothesis

- user-defined knowledge

- project override

- validated knowledge

The AI can accelerate knowledge creation without silently corrupting the system.

Alternatives Considered

Allow AI to write trusted knowledge directly

Rejected.

Too risky.

Forbid AI-assisted knowledge creation

Rejected.

Too slow and wastes a useful capability.

Allow AI knowledge only inside chat

Rejected.

Useful project-specific interpretations should be persistable when clearly marked.

Consequences

The Knowledge Engine must support confidence and validation status.

The Reasoning Engine must expose uncertainty when using unvalidated knowledge.

The UI should not display AI-suggested knowledge as verified fact.

Revisit Trigger

Review when a validation workflow exists for promoting AI-suggested knowledge to curated knowledge.

### 7. ADRs Still Needed

The following ADRs should be drafted during Sprint 1 or later:

ADR-TODO-001 — Exact Canonical Card Data Source

Decision needed:

Which external source provides canonical card facts for MVP?

Related backlog item:

K-001 — Choose Canonical Card Data Source

ADR-TODO-002 — Default MVP Mulligan Policy

Decision needed:

Which mulligan policy should simulations use by default?

Candidate options:

- no mulligan

- London mulligan

- one free mulligan then London

- Commander casual free mulligan

- custom per project

Related backlog item:

S-002 — Decide Default Mulligan Policy

ADR-TODO-003 — Tutor Modeling Boundary

Decision needed:

How should MVP simulations handle tutors?

Candidate options:

- ignore tutors

- tutor as access modifier

- full tutor sequencing

Likely MVP decision:

Support ignore_tutors and tutor_as_access_modifier.

Defer full tutor sequencing.

ADR-TODO-004 — MVP Functional Role Taxonomy

Decision needed:

What is the smallest useful role set for the first prototype?

Related backlog item:

K-003 — Define MVP Functional Role Taxonomy

ADR-TODO-005 — MVP User Persona

Decision needed:

Who is the first intended MVP user?

Candidate direction:

Power users / deckbuilding nerds first.

Reason:

They are more likely to tolerate structured briefs, analysis reports, versioning, and decision logs before the UI is polished.

ADR-TODO-006 — MVP Module Scope

Decision needed:

Which architecture modules are implemented in Sprint 1?

Likely MVP modules:

- Project Workspace

- Deck Parser

- Card Knowledge Base import

- Basic Deck Analysis

- Markdown Reporting

- Manual Recommendation Review

- Decision Log

- DeckVersion creation

Deferred:

- full UI

- full Reasoning Engine automation

- advanced Simulation Engine

- graph knowledge model

- automatic recommendation engine

### 8. ADR Maintenance Rules

8.1 Do Not Rewrite History

Accepted ADRs should not be silently edited to change their decision.

If a decision changes, create a new ADR and mark the old one as Superseded.

8.2 Keep ADRs Short Enough to Read

Each ADR should explain the decision clearly.

It should not become a full RFC.

8.3 Link ADRs to Backlog and RFCs

When an ADR creates work, that work should appear in the Backlog.

When an ADR depends on design principles, it should reference the relevant RFCs.

8.4 Prefer Explicit Trade-Offs

A good ADR should document not only what was chosen, but what was sacrificed.

8.5 Use ADRs to Prevent Drift

If the project starts drifting toward generic deckbuilding, shallow AI suggestions, or overbuilt infrastructure, the ADR should make the conflict visible.

### 9. Current Summary

The Workshop’s foundational decisions are:

- The root object is Project.

- AI is a reasoning layer, not the source of truth.

- Card knowledge must be structured and inspectable.

- Recommendations require context and explanation.

- Simulation tests hypotheses.

- DeckVersions are immutable.

- Decisions produce meaningful version changes.

- The MVP should likely start local-first.

- MVP storage should likely start with Markdown and JSON.

- Canonical card facts require an external source.

- The MVP should prove the engineering loop before building full UI.

- Popularity is evidence, never proof.

- User agency must be preserved.

- Accepted risks are first-class project knowledge.

- AI-suggested knowledge starts unvalidated.

These decisions protect The Workshop from becoming a generic deck builder.

They keep the product aligned with its core identity:

The Workshop is a Deck Engineering Platform.

## Part II — Current ADR Status Index

| ADR | Historical Status | Current Status |
| --- | --- | --- |
| ADR-001 through ADR-007 | Accepted in Sprint 0 | Accepted |
| ADR-008 | Proposed in v0.1 | Accepted in Sprint 1 |
| ADR-009 | Proposed in v0.1 | Accepted in Sprint 1 |
| ADR-010 | Proposed in v0.1 | Accepted in Sprint 1 |
| ADR-011 | Proposed in v0.1 | Accepted in Sprint 1 |
| ADR-012 through ADR-015 | Accepted in Sprint 0 | Accepted |
| ADR-016 | Not present in v0.1 | Added and Accepted in Sprint 1 |

## Part III — Sprint 1 Ratification and v0.2 Addendum

The v0.2 material below is an authorized ratification addendum to the preserved v0.1 ADR register. It does not rewrite the original proposal, context, alternatives, consequences, or revisit triggers.

### v0.2 Publication-State Record

Accepted product and architecture decisions after Sprint 1 certification.

| Field | v0.2 Publication-State Record |
| --- | --- |
| Last Updated | 13 July 2026 |
| Ratification change | ADR-008, ADR-009, ADR-010, and ADR-011 move from Proposed to Accepted. |
| New decision | ADR-016 is added to preserve certification integrity and exact reviewed-candidate identity. |
| Prior decisions | No previous accepted ADR is superseded or deprecated. |

### ADR-008 — Sprint 1 Ratification

Accepted in Sprint 1 through the local-first prototype implementation. The original proposal remains visible in the preserved v0.1 record; the implementation evidence and validation boundary are recorded in the v0.2 addendum and Sprint 1 ratification evidence.

### ADR-009 — Sprint 1 Ratification

Accepted in Sprint 1 through the Markdown/JSON structured artifact model. The original proposal remains visible in the preserved v0.1 record; the implementation evidence and validation boundary are recorded in the v0.2 addendum and Sprint 1 ratification evidence.

### ADR-010 — Sprint 1 Ratification

Accepted in Sprint 1 through the external-source-backed canonical Card Facts implementation. The original proposal remains visible in the preserved v0.1 record; the implementation evidence and validation boundary are recorded in the v0.2 addendum and Sprint 1 ratification evidence.

### ADR-011 — Sprint 1 Ratification

Accepted in Sprint 1 through delivery of the local core engineering loop before a full UI. The original proposal remains visible in the preserved v0.1 record; the implementation evidence and validation boundary are recorded in the v0.2 addendum and Sprint 1 ratification evidence.

### 1. Purpose

Architecture Decision Records preserve why The Workshop is built the way it is. They prevent implementation convenience, AI behavior, or short-term delivery pressure from silently changing the product constitution.

### 2. ADR Status Values

| Status | Meaning |
| --- | --- |
| Proposed | Decision is written but not yet ratified by evidence or explicit acceptance. |
| Accepted | Decision is active and governs current work. |
| Superseded | A later ADR replaces this decision while preserving historical context. |
| Deprecated | Decision is no longer recommended but still explains historical work. |
| Rejected | Alternative was explicitly considered and declined. |
| Deferred | Decision is important but intentionally postponed. |

### 3. ADR Index

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

### 4. Accepted Decisions

#### ADR-001 — Projects Are the Root Entity

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-000, RFC-001, RFC-002; The Myr Singularity project structure |

##### Context

A decklist cannot preserve design intent, constraints, history, evidence, decisions, versions, and accepted risks.

##### Decision

Project is the root entity. Decks, DeckVersions, briefs, analysis, recommendations, decisions, reports, notes, and backlog items belong to or are referenced by a Project.

##### Rationale

Deck engineering requires context and history. A project-first model prevents The Workshop from collapsing into a deck editor with attached AI suggestions.

##### Consequences

Serious analysis begins from a Project. Lightweight one-off tools may exist later but cannot replace the project workflow.

##### Revisit Trigger

Revisit only if a lightweight mode is added; serious work should remain project-aware.

#### ADR-002 — AI Is a Reasoning Layer, Not the Source of Truth

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-003, RFC-004; external Card Facts and structured review records |

##### Context

AI can explain and propose but is not reliable enough to own canonical card data, simulations, accepted decisions, or project history.

##### Decision

AI may interpret structured evidence, generate hypotheses, evaluate trade-offs, and prepare explanations. Canonical facts and stored state must come from controlled sources and explicit records.

##### Rationale

Trust requires separation between fact, interpretation, hypothesis, recommendation, decision, and evidence.

##### Consequences

AI output must remain attributable and reviewable. The product requires structured data and deterministic validation around AI-assisted work.

##### Revisit Trigger

Revisit tooling, not the separation principle, when future models become more reliable.

#### ADR-003 — Card Knowledge Must Be Structured and Inspectable

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-003; functional_roles.json and candidate metadata |

##### Context

The same card can serve different functions across projects. Freeform descriptions are insufficient for repeatable analysis and recommendation logic.

##### Decision

Separate Card Facts, derived data, general Card Knowledge, project-specific knowledge, relationship knowledge, and hypotheses. Track source, confidence, validation state, and scope.

##### Rationale

Structured knowledge enables role density, package fit, synergy, risk, and constraint reasoning without reducing decisions to popularity.

##### Consequences

MVP taxonomies must remain compact. Project overrides are allowed and must not corrupt global facts.

##### Revisit Trigger

Revisit storage representation when the knowledge model outgrows JSON, not before.

#### ADR-004 — Recommendations Require Context and Explanation

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | rec-001, rec-002, review-rec-002 |

##### Context

A card suggestion without project context, problem definition, trade-offs, and fit is not a Workshop recommendation.

##### Decision

Recommendations must link to a project, version, analysis or hypothesis, constraints, expected benefit, trade-off, risk, confidence, and suggested validation.

##### Rationale

Explainability preserves user agency and allows later decisions to be reconstructed.

##### Consequences

Recommendations cannot directly edit the deck. They move through Product Owner review and explicit decision records.

##### Revisit Trigger

Revisit only for deliberately lightweight product modes.

#### ADR-005 — Simulation Is Evidence for Hypotheses, Not a Perfect Game Model

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-005; Sprint 1 evidence boundary |

##### Context

Commander games are too complex and social for a first simulation system to produce a universal deck score or deterministic judgment.

##### Decision

Every SimulationRun must answer an explicit question, record assumptions and limitations, reference an immutable DeckVersion, and produce reproducible evidence.

##### Rationale

Focused probability evidence can improve decisions without pretending to model complete multiplayer games.

##### Consequences

Sprint 1 may remain valid without simulation. Unrun simulations must be recorded as not_run, not inferred from implementation.

##### Revisit Trigger

Revisit model scope when specific product questions justify additional complexity.

#### ADR-006 — DeckVersions Are Immutable Snapshots

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | DeckVersion v1.0 and v1.1 |

##### Context

Mutable deck state destroys comparison, reproducibility, and the ability to explain why a result changed.

##### Decision

A meaningful deck state is stored as an immutable DeckVersion linked to its parent and source decision. Current state points to a version; it does not rewrite history.

##### Rationale

Immutable versions create stable analysis and simulation targets and protect the baseline.

##### Consequences

Storage grows over time, but history remains reconstructable. Cleanup must not rewrite accepted versions.

##### Revisit Trigger

Revisit only the storage mechanism, not immutability.

#### ADR-007 — Decisions Produce Meaningful Deck Version Changes

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | decision-002, decision-003, decision-004; deck-change-design-v1.1 |

##### Context

Recommendations are advisory. Without a decision boundary, the system can silently optimize away the user’s intent.

##### Decision

Accepted, modified, rejected, deferred, and test-first outcomes must be recorded. Only approved decisions and design changes may produce a new DeckVersion.

##### Rationale

The user remains the designer. Decision records explain why changes happened and what was intentionally not changed.

##### Consequences

Version creation requires review and approval artifacts. Rejected and deferred candidates remain project knowledge.

##### Revisit Trigger

Revisit only if a future automatic mode is explicitly selected by the user.

#### ADR-008 — MVP Starts Local-First

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Certified Sprint 1 repository and merge commit 8d8be6db… |

##### Context

The first proof needed to validate product boundaries and traceability faster than a production web architecture could be justified.

##### Decision

The MVP begins as a repository-local workspace using files, scripts, tests, and version control.

##### Rationale

Local-first maximizes inspectability, fast iteration, and evidence quality while avoiding premature infrastructure.

##### Consequences

Multi-user collaboration, authentication, hosting, and production operations remain deferred. Local-first is a starting architecture, not the final product form.

##### Revisit Trigger

Revisit after the local workflow is stable and a user-facing multi-user need is concrete.

#### ADR-009 — MVP Storage Starts with Markdown and JSON

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | 25 Workshop JSON files; deterministic certification, backlog, and report renderers |

##### Context

The prototype requires human-readable reports and machine-verifiable structured sources without committing early to a database schema and migration layer.

##### Decision

Use JSON for structured artifacts and Markdown for readable projections. Generated Markdown must be reproducible from structured sources where applicable.

##### Rationale

This format is inspectable, versionable, portable, and sufficient for a single-user local proof.

##### Consequences

Concurrency, querying, permissions, and large-scale migration remain limited. Database adoption requires an explicit trigger.

##### Revisit Trigger

Revisit when file-based storage blocks collaboration, consistency, performance, or evolution.

#### ADR-010 — Canonical Card Facts Require an External Source

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | cards.json, candidate_cards.json, candidate import metadata |

##### Context

AI-authored oracle text, color identity, legality, mana values, and other canonical facts would make analysis untrustworthy.

##### Decision

Canonical Card Facts must be imported or referenced from an external authoritative data source. The current prototype uses Scryfall-derived card data and source metadata.

##### Rationale

External source identity separates factual game data from derived knowledge and AI interpretation.

##### Consequences

Imports require validation, identity checks, and provenance. Project knowledge may interpret facts but cannot replace them.

##### Revisit Trigger

Revisit the provider if coverage, licensing, reliability, or data requirements change.

#### ADR-011 — MVP Prioritizes the Core Engineering Loop Over Full UI

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Certified 15-stage product loop |

##### Context

A polished interface could hide an unproven workflow and encourage premature deck-editor behavior.

##### Decision

Prove Project → Brief → Version → Knowledge → Analysis → Recommendation → Review → Decision → Version → Report before implementing a full UI.

##### Rationale

The engineering loop is the product core. UI should expose and support it rather than define it accidentally.

##### Consequences

Sprint 1 remains repository-driven. Sprint 2 may select a narrow user-facing surface after the core loop is certified.

##### Revisit Trigger

Revisit now that Sprint 1 is certified, through an explicit Sprint 2 product decision.

#### ADR-012 — Popularity Data Is Evidence, Never Proof

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-000, RFC-003, RFC-004 |

##### Context

Common inclusion can indicate synergy, habit, budget, copying, or meta bias. Popularity alone cannot establish project fit.

##### Decision

Popularity may discover candidates but cannot justify a recommendation without project-specific reasoning and evidence.

##### Rationale

The Workshop optimizes for the Design Brief, identity, constraints, packages, risks, and user goals.

##### Consequences

MVP may omit popularity data entirely. Future integrations must label it as one weighted signal.

##### Revisit Trigger

Revisit when external popularity or metagame data is introduced.

#### ADR-013 — User Agency Must Be Preserved

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | Product Owner review and decision pipeline |

##### Context

Commander decks express personal philosophy, budget, variance, social goals, pet cards, and accepted trade-offs.

##### Decision

The user remains the designer. The system may analyze, explain, suggest, test, and document, but cannot silently change the deck or override intent.

##### Rationale

A technically stronger list may be a worse product outcome for the user.

##### Consequences

Review actions must include accept, reject, modify, defer, test-first, and accepted-risk outcomes.

##### Revisit Trigger

Revisit only for explicit automatic modes with clear user authorization.

#### ADR-014 — Accepted Risks Are First-Class Project Knowledge

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | RFC-002, RFC-003, RFC-004 |

##### Context

Not every weakness should be fixed. Repeatedly flagging intentional trade-offs makes the system noisy and untrustworthy.

##### Decision

Store accepted risks, intentional trade-offs, rejected concerns, and revisit triggers as durable project knowledge.

##### Rationale

This preserves intent and prevents repetitive recommendations.

##### Consequences

Accepted risks remain visible in briefs, decisions, reports, and reasoning context without being treated as unresolved defects.

##### Revisit Trigger

Revisit an accepted risk when its trigger, meta, strategy, or evidence changes.

#### ADR-015 — AI-Suggested Knowledge Starts Unvalidated

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 0 | Knowledge validation contracts |

##### Context

AI can infer useful roles and relationships but may be wrong, overly generic, or project-inappropriate.

##### Decision

AI-suggested knowledge begins as unvalidated and records source, scope, confidence, and validation status. Promotion requires controlled review or evidence.

##### Rationale

This allows assistance without converting guesses into canonical knowledge.

##### Consequences

Analysis and recommendations must distinguish validated knowledge from hypotheses.

##### Revisit Trigger

Revisit promotion workflows when knowledge editing becomes a user-facing feature.

#### ADR-016 — Certification Binds to an Exact Reviewed Commit

| Status | Accepted / Updated | Related Evidence |
| --- | --- | --- |
| Accepted | Sprint 1 | Sol APPROVE on c0de66c…; recording commit cded1e1…; certification validator |

##### Context

A later recording commit could otherwise repair or alter the artifact that an independent reviewer supposedly approved.

##### Decision

Certification records the exact reviewed commit. The completed record must structurally equal the reviewed pending candidate after projecting only permitted lifecycle fields: certification status, independent review, next action, and gate limitations.

##### Rationale

Independent approval is meaningful only when the reviewed artifact and recorded certification are provably the same substantive candidate.

##### Consequences

Review recording is limited to the certification JSON, generated certification Markdown, and structured review artifact. Material candidate changes require a new review.

##### Revisit Trigger

Revisit only if certification storage changes; exact candidate identity and substantive equivalence must remain.

### 5. Sprint 1 Ratification Evidence

| Decision | Evidence |
| --- | --- |
| ADR-008 Local-first | The complete product loop was executed and reviewed in a repository-local workspace. |
| ADR-009 Markdown/JSON | Structured JSON and deterministic Markdown projections passed validation and no-drift checks. |
| ADR-010 External facts | Card facts and candidate facts retain external source identity and validation boundaries. |
| ADR-011 Core loop before UI | A certified 15-stage loop exists without requiring a full application UI. |
| ADR-016 Exact reviewed commit | Full candidate equivalence and lifecycle-only recording changes were independently tested and approved. |

### 6. Decisions Still Needed

| Candidate ADR | Question |
| --- | --- |
| ADR-017 | What Commander mulligan policy and confidence model governs saved simulations? |
| ADR-018 | When must file-based state migrate to an append-only event model or database? |
| ADR-019 | What first user-facing surface should expose the certified engineering loop? |
| ADR-020 | What evidence threshold moves a needs_testing candidate into recommendation-ready state? |
| ADR-021 | What automation is permitted in recommendation generation without weakening user agency? |

### 7. ADR Maintenance Rules

- Do not rewrite an accepted ADR to make later implementation appear inevitable.

- Use Superseded when a new decision replaces an earlier one.

- Reference concrete artifacts, tests, or delivery evidence when a Proposed ADR becomes Accepted.

- Keep decisions separate from implementation detail unless the detail is itself a durable constraint.

- Record revisit triggers so accepted decisions remain challengeable without becoming unstable.

## Part IV — Evidence and History Boundaries

- Sprint 0 and Sprint 1 history is preserved rather than rewritten.
- Proposed decisions are not presented as though they were always Accepted; historical and current status transitions remain visible.
- Alternatives, consequences, and revisit triggers remain visible in the preserved v0.1 records.
- Later implementation evidence is appended as Sprint 1 ratification.
- No simulation or measured-performance claim is introduced.
- Krark-Clan Ironworks and Mana Echoes remain `needs_testing` and unimplemented.
- ADR-016 records the exact certification trust boundary, including reviewed-candidate equivalence and lifecycle-recording restriction.
- After merge, `/docs` remains the operational repository source.
