# RFC-012 — The Workshop Sprint 1 Kickoff

Status: Draft Version: v0.1 Sprint: 1 Depends on: RFC-000, RFC-001, RFC-002, RFC-003, RFC-004, RFC-005, RFC-006, RFC-007, RFC-008, RFC-009, RFC-010, RFC-011 Document Type: Sprint Kickoff / Execution Start Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

## 1. Purpose

This document officially opens Sprint 1 of The Workshop.

Sprint 0 created the product and architecture foundation.

Sprint 1 begins execution.

The purpose of this kickoff is to align the sprint around a single operational goal:

Prove that The Workshop can execute its core deck engineering loop locally, using real project files, structured data, readable reports, and traceable decisions.

Sprint 1 is not about building the final product.

Sprint 1 is about proving that the product model works.

If Sprint 1 succeeds, The Workshop will no longer be only documentation.

It will become an executable local Deck Engineering Platform prototype.

## 2. Sprint Name

Sprint 1 — Local Prototype Foundation

## 3. Sprint Status

Active / Kickoff

## 4. Sprint Goal

Create the first minimal local prototype of The Workshop.

The prototype must prove that one real Commander deck can move through the core engineering loop:

Project → Brief → Deck Import → DeckVersion → Card Facts → Basic Knowledge → Analysis → Weakness → Recommendation → Decision → New DeckVersion → Report

The prototype can be rough.

It does not need a polished UI.

It does not need full automation.

It does not need advanced simulation.

It must be structurally correct.

## 5. Sprint Thesis

Sprint 1 is a product-loop proof sprint.

It is not a UI sprint.

It is not a full app sprint.

It is not a simulation sprint.

It is not an AI automation sprint.

The central question is:

Can The Workshop take one real Commander deck and turn it into a traceable engineering project?

The output should not merely be:

“Here is an improved decklist.”

The output should be:

“Here is the project, the brief, the baseline deck version, the analysis, the weakness, the recommendation, the decision, the resulting version, and the report explaining why the change happened.”

That is the difference between a deck builder and a Deck Engineering Platform.

## 6. Kickoff Decisions

Sprint 1 begins with the following working decisions.

These decisions may be refined through ADR updates during the sprint.

6.1 Prototype Direction

The Sprint 1 prototype starts local-first.

Reason:

A local-first prototype allows the team to prove the product loop quickly using folders, JSON, Markdown, scripts, and real deck files.

A web-first implementation is deferred until the core loop has been proven.

6.2 Storage Direction

Sprint 1 starts with Markdown and JSON.

Structured data lives in JSON files.

Human-readable outputs live in Markdown files.

Reason:

Markdown and JSON are readable, inspectable, easy to version, easy to edit manually, and migration-friendly.

The goal is not to avoid databases forever.

The goal is to avoid premature database complexity before the product loop works.

6.3 UI Direction

Sprint 1 does not implement the full UI.

The first project report may act as a dashboard substitute.

Reason:

If the core loop does not work in structured files and readable reports, a polished UI will not save the product.

6.4 Recommendation Direction

Sprint 1 does not require automatic recommendations.

A recommendation may be manually or semi-manually authored as long as it follows the structured recommendation format.

Reason:

The goal is to prove recommendation traceability, not recommendation automation.

6.5 Simulation Direction

Simulation is optional in Sprint 1.

If included, it must test a specific question.

Reason:

Simulation must not distract from project structure, deck import, analysis, recommendation, decision, and versioning.

## 7. Sprint 1 First Test Project

Sprint 1 needs one real Commander deck as its first fixture.

Candidate decks:

- Myr artifact combo-control deck

- Emry equipment recursion toolbox

- Zur forbidden-aura brinkmanship deck

- Izzet spellslinger / storm deck

Recommended first fixture:

Myr artifact combo-control deck.

Reason:

The Myr deck is a strong first test because it clearly exercises the core Workshop concepts:

- deck identity is non-obvious

- the deck looks tribal but functions as an artifact combo-control engine

- card roles are contextual

- mana fixing matters

- artifact engines matter

- protection and resilience matter

- recommendations can easily become wrong if they ignore deck identity

- simulation questions can later be concrete and useful

The Myr project should be used only if a clean current decklist is available.

If the Myr decklist is not ready, Emry equipment recursion toolbox is the fallback fixture.

## 8. Sprint 1 Operating Rule

Sprint 1 must avoid false progress.

A pretty Markdown report is not enough.

A generated decklist is not enough.

A card suggestion is not enough.

Every meaningful artifact must be traceable to structured project data.

The sprint should preserve this order:

- Project

- Brief

- DeckVersion

- Card Facts

- Basic Knowledge

- Analysis

- Weakness

- Recommendation

- Decision

- New DeckVersion

- Report

If the sprint jumps directly from decklist to recommendation, it has failed the product philosophy.

## 9. Sprint 1 Must-Have Deliverables

9.1 Product / Workflow

Sprint 1 must produce:

- MVP product loop definition

- input/output map for each loop step

- first test deck project selection

- lightweight Design Brief for the test deck

- Sprint 1 success checklist

9.2 Architecture

Sprint 1 must produce:

- accepted or revised local-first ADR

- accepted or revised Markdown/JSON storage ADR

- MVP module boundary definition

- local folder structure

- migration-friendly file organization

9.3 Data Model

Sprint 1 must create MVP schemas for:

- Project

- DesignBrief

- DeckVersion

- DeckCard

- AnalysisReport

- Recommendation

- Decision

- Report

- Note or BacklogItem

These may be JSON examples first.

Formal JSON Schema can come later if lightweight examples are faster.

9.4 Deck Import

Sprint 1 must support one decklist import path.

Minimum requirements:

- plain-text decklist support

- quantity parsing

- card name parsing

- commander identification through field or section

- category preservation where possible

- malformed line warnings

- unknown card warnings

- baseline DeckVersion creation

The parser should not silently drop cards.

9.5 Card Facts

Sprint 1 must choose one canonical external card data source.

Minimum required fields:

- name

- normalized name

- oracle text

- mana cost

- mana value

- type line

- color identity

- colors

- legalities where available

- produced mana where available

AI must not author canonical card facts.

9.6 Basic Knowledge

Sprint 1 must define:

- MVP FunctionalRole taxonomy

- role families

- role source metadata

- confidence field

- validation status

- project-specific override format

The role taxonomy must stay compact.

The goal is useful analysis, not tag spam.

9.7 Analysis

Sprint 1 must generate one baseline analysis report.

Minimum report sections:

- summary

- land count

- mana curve

- color requirements

- ramp density

- draw density

- interaction density

- protection density

- win condition density

- basic package grouping

- basic weakness list

- assumptions

- confidence

- suggested next steps

The analysis must explain what the deck currently is.

It must not jump directly to card recommendations.

9.8 Recommendation

Sprint 1 must create one structured recommendation.

Minimum fields:

- problem solved

- proposed change

- affected role, engine, or package

- expected benefit

- trade-off

- risk

- constraint check

- identity check

- confidence

- rationale

- suggested test if useful

- status

The recommendation must not modify the deck.

9.9 Decision

Sprint 1 must record one decision.

Minimum fields:

- source DeckVersion

- source Recommendation

- decision type

- rationale

- accepted changes

- rejected changes if relevant

- expected outcome

- risk accepted if relevant

- resulting DeckVersion if applicable

- user comment if provided

- created timestamp

Only a Decision may create a meaningful new DeckVersion.

9.10 Versioning

Sprint 1 must preserve:

- baseline DeckVersion unchanged

- resulting DeckVersion after accepted or modified decision

- parent version link

- change summary

- source decision reference

Reverts should create new versions rather than deleting history.

9.11 Reporting

Sprint 1 must generate one readable Markdown project report.

Minimum sections:

- project identity

- current version

- brief summary

- analysis findings

- weakness identified

- recommendation proposed

- decision made

- resulting version

- next action

The report must reference structured source files.

## 10. Sprint 1 Should-Have Deliverables

If the must-have work is stable, Sprint 1 should also produce:

- basic changelog

- project README

- first project backlog file

- notes format

- recommendation review Markdown template

- decision log Markdown template

- basic role density output

- basic package grouping

- first regression checklist against Workshop principles

## 11. Sprint 1 Could-Have Deliverables

Optional stretch items:

- opening hand simulation prototype

- color availability simulation prototype

- land-drop probability script

- goldfish Level 1 draw/access script

- Markdown report renderer

- CLI command for project creation

- CLI command for deck import

- CLI command for analysis report generation

- JSON validation script

- first golden test fixture

These must not block the sprint.

## 12. Sprint 1 Explicit Non-Goals

Sprint 1 should not build:

- full web UI

- full deck editor

- login/auth

- SaaS architecture

- real-time collaboration

- public profiles

- marketplace features

- full graph knowledge model

- full Commander rules engine

- full combo database

- full multiplayer gameplay simulation

- automatic deck generation

- automatic recommendation engine

- popularity-based recommendation ranking

- advanced AI agent workflow

- production database

- complete Moxfield / Archidekt integration

- complete price tracking

- collection management

If one of these becomes tempting, move it to the Backlog.

Do not build it in Sprint 1.

## 13. Sprint 1 Execution Order

Sprint 1 should execute in this order:

- Accept or revise ADR-008.

- Accept or revise ADR-009.

- Choose the first test deck.

- Define local project folder structure.

- Define Project schema.

- Define DesignBrief schema.

- Create local project manually.

- Define DeckVersion schema.

- Define DeckCard schema.

- Import decklist into baseline DeckVersion.

- Choose canonical card data source.

- Load or reference card facts.

- Define FunctionalRole taxonomy.

- Tag enough cards for the first deck.

- Define baseline analysis template.

- Generate baseline analysis report.

- Identify one structural weakness.

- Create one structured recommendation.

- Record one decision.

- Create one resulting DeckVersion.

- Generate final project report.

- Run Sprint 1 quality checklist.

- Update Sprint Log.

- Update Backlog.

- Record implementation decisions in ADR.

This order matters.

Building recommendations before Project, Brief, DeckVersion, Card Facts, Roles, and Analysis exist would recreate the shallow behavior The Workshop is designed to avoid.

## 14. Sprint 1 Quality Gates

14.1 Project Gate

Before serious analysis, the system must have:

- Project

- commander or deck concept

- format

- baseline DeckVersion

- lightweight Design Brief

If the brief is incomplete, assumptions must be visible.

14.2 Analysis Gate

Before serious recommendations, the system must have:

- parsed DeckVersion

- card facts loaded or referenced

- basic role knowledge available

- baseline analysis generated

- at least one finding, weakness, or user question

14.3 Recommendation Gate

Before a Recommendation is reviewable, it must include:

- problem solved

- proposed change

- expected benefit

- trade-off

- risk

- constraint check

- identity check

- confidence

- rationale

A Recommendation must not modify the deck.

14.4 Decision Gate

Before a meaningful new DeckVersion is created, there must be a Decision.

The Decision must record:

- source DeckVersion

- decision type

- rationale

- accepted changes

- rejected changes when applicable

- expected outcome

- resulting DeckVersion when applicable

14.5 Report Gate

Before the sprint output is considered useful, the report must include:

- summary

- findings

- evidence

- assumptions

- confidence

- relevant DeckVersion

- decision context

- next action

A report that is only raw metrics or raw JSON is not enough.

## 15. Sprint Risks

15.1 Scope Creep

Risk:

Sprint 1 expands into UI, automation, simulation, database design, or full app architecture.

Mitigation:

Keep Sprint 1 focused on the local product loop.

Anything outside the loop goes to Backlog.

15.2 Over-Modeling

Risk:

Knowledge and data schemas become too complex before the first project works.

Mitigation:

Use compact roles, JSON files, and project-level overrides.

Normalize later only when needed.

15.3 False Progress

Risk:

The system produces nice Markdown but does not preserve structured data.

Mitigation:

Every report must reference structured source files.

Readable output is not enough.

15.4 Shallow AI Behavior

Risk:

The prototype becomes a chatbot workflow that suggests cards without analysis.

Mitigation:

Require AnalysisReport before serious Recommendation.

Require Recommendation rationale.

Require Decision before DeckVersion change.

15.5 Simulation Distraction

Risk:

Sprint 1 spends too much time on goldfish or color simulations before project structure works.

Mitigation:

Simulation is optional.

If included, it must test a specific question.

15.6 Card Data Rabbit Hole

Risk:

Choosing and importing card data becomes too large.

Mitigation:

Choose one canonical source.

Import only required fields first.

Document limitations.

## 16. Sprint 1 Success Criteria

Sprint 1 is successful if one real Commander deck can complete this loop:

- Project created.

- Lightweight Design Brief stored.

- Decklist imported.

- Baseline DeckVersion created.

- Card facts loaded or referenced.

- Basic roles assigned.

- Baseline analysis generated.

- At least one structural weakness identified.

- One structured recommendation created.

- One decision recorded.

- One new DeckVersion created from that decision.

- One readable project report generated.

- Baseline version remains unchanged.

- Recommendation does not directly modify the deck.

- Decision explains why the change happened.

- Report explains the process in human-readable form.

- Structured data exists behind readable reports.

- Sprint findings are added to the Sprint Log.

- Major implementation decisions are recorded or updated in ADR.

- Deferred ideas are moved to Backlog.

## 17. Kickoff Backlog Selection

Sprint 1 starts with the following priority items.

Must Start Immediately

- S1-P-001 — Define MVP Product Loop

- S1-P-002 — Select First Test Deck Project

- S1-P-003 — Define Sprint 1 Success Criteria

- S1-A-001 — Accept or Revise Local-First ADR

- S1-A-002 — Accept or Revise Markdown/JSON Storage ADR

- S1-A-003 — Define MVP Module Boundaries

- S1-A-004 — Define Project Folder Structure

- S1-D-001 — Create Project Schema

- S1-D-002 — Create Design Brief Schema

- S1-D-003 — Create DeckVersion Schema

- S1-D-004 — Create DeckCard Schema

- S1-K-001 — Choose Canonical Card Data Source

- S1-K-003 — Define MVP FunctionalRole Taxonomy

Start After Project Structure Exists

- S1-D-005 — Create AnalysisReport Schema

- S1-D-006 — Create Recommendation Schema

- S1-D-007 — Create Decision Schema

- S1-I-001 — Create Repository Structure

- S1-I-002 — Implement Decklist Parser MVP

- S1-I-003 — Implement Baseline Analysis Script

- S1-I-004 — Generate Markdown Analysis Report

- S1-I-005 — Implement Manual Recommendation Template

- S1-I-006 — Implement Decision Log File

Optional Stretch

- S1-S-001 — Define MVP Simulation Configuration Format

- S1-S-002 — Decide Default Mulligan Policy

- S1-S-003 — Implement Opening Hand Simulation

- S1-S-004 — Implement Color Availability Simulation

## 18. Sprint 1 Working Assumptions

The sprint begins with these assumptions:

- The first prototype is local-first.

- MVP storage uses Markdown and JSON.

- Full UI is deferred.

- The first project report acts as a dashboard substitute.

- Card facts come from one canonical external source.

- AI may assist reasoning, but does not author card facts.

- Recommendations are manually reviewable proposals.

- Decisions create meaningful DeckVersion changes.

- Simulation is optional.

- The first user is a power user / deckbuilding nerd, not a casual mainstream user.

- The first deck fixture should be complex enough to test the model, but not so complex that it blocks implementation.

These assumptions should be validated or revised during Sprint 1.

## 19. Immediate Next Actions

The first execution block is:

- Accept ADR-008 as the working local-first decision.

- Accept ADR-009 as the working Markdown/JSON storage decision.

- Choose the first test deck.

- Create the repository / folder skeleton.

- Create project.json.

- Create brief.json and brief.md.

- Import the first decklist into v1.0.json.

- Confirm the exact minimum card facts needed for analysis.

- Select the canonical card data source.

- Define the MVP role taxonomy.

Only after those are done should analysis and recommendation work begin.

## 20. Sprint 1 Kickoff Statement

Sprint 0 proved that The Workshop has a coherent product vision and architecture.

Sprint 1 must prove that the architecture can execute.

The team should now stop expanding the conceptual model and start producing the first local working artifact.

The guiding principle for this sprint is:

Make the loop real.

Not perfect.

Real.

By the end of Sprint 1, The Workshop should be able to take one Commander deck and show:

- what the user is trying to build

- what exact deck version was analyzed

- what the deck currently does

- what weakness was found

- what change was proposed

- why that change was proposed

- what the user decided

- what new version resulted

- what report explains the process

That is the Sprint 1 target.

That is the first real proof of The Workshop.

## 21. Summary

RFC-012 officially kicks off Sprint 1.

Sprint 1 is focused on the Local Prototype Foundation.

The work should remain narrow, practical, and traceable.

The sprint succeeds only if The Workshop completes its first real project loop using structured local files and readable reports.

The Workshop is now moving from product architecture to executable product behavior.
