# RFC-010 — The Workshop Testing Strategy

Status: Draft Version: v0.2 Sprint: 0 / Sprint 1 Planning Depends on: RFC-000, RFC-001, RFC-002, RFC-003, RFC-004, RFC-005, RFC-006, RFC-007, RFC-008, RFC-009 Document Type: Testing / Quality Strategy Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

## 1. Purpose

This document defines the testing strategy for The Workshop.

The goal is not only to test whether the software works.

The goal is to test whether The Workshop behaves like a Deck Engineering Platform.

The Workshop must be tested against its core product promise:

- Project-first workflow

- Context before analysis

- Analysis before recommendation

- Evidence before optimization

- Decision before versioning

- AI as reasoning layer, not source of truth

- Recommendations as explainable proposals

- Simulation as evidence for hypotheses

- User agency preserved

- Project history preserved

Testing must protect the system from drifting into:

- a generic deck builder

- a chatbot with card suggestions

- an automatic optimizer

- an opaque simulator

- a raw statistics dashboard

- an untraceable recommendation machine

The Testing Strategy exists to make quality explicit, repeatable, and connected to the product thesis.

## 2. Testing Thesis

The Workshop should be tested as an engineering system, not only as an application.

A normal deckbuilder can be tested by asking:

“Does the decklist import work?”

The Workshop must also ask:

“Did the system understand what the user is trying to build?”

“Did the analysis explain the deck before recommending changes?”

“Did the recommendation respect the Design Brief?”

“Did the recommendation explain the trade-off?”

“Did the simulation test a specific hypothesis?”

“Did the decision create a traceable DeckVersion?”

“Can the user understand why the deck changed?”

A feature is not complete just because it executes.

A feature is complete when it supports the core engineering loop:

Brief → Analyze → Recommend → Test → Decide → Version

## 3. Scope

The Testing Strategy covers:

- Product Loop Testing

- Data Model Testing

- Deck Parser Testing

- Card Knowledge Testing

- Analysis Engine Testing

- Reasoning Engine Testing

- Recommendation Testing

- Simulation Testing

- Decision / Versioning Testing

- Report Testing

- UI / UX Testing

- Regression Testing

- Test Fixtures

- MVP Quality Gates

This RFC does not define the final test framework, CI platform, or implementation tooling.

Those should be decided during implementation.

This RFC defines what must be tested and why.

## 4. Core Testing Principle

The Workshop must test behavior against product principles.

A test should not only verify that an output exists.

It should verify that the output is valid under The Workshop philosophy.

Example:

Bad test:

“System recommends Rhystic Study.”

Better test:

“Given a project that prioritizes originality and avoids generic staples, the system should not recommend Rhystic Study only because it is strong.”

Example:

Bad test:

“Simulation returns a percentage.”

Better test:

“Simulation result includes test question, DeckVersion, assumptions, mulligan policy, metric, failure patterns, and limitations.”

Example:

Bad test:

“Recommendation created.”

Better test:

“Recommendation includes problem, proposed change, expected benefit, trade-off, risk, confidence, constraint check, and suggested test when useful.”

The Workshop is only trustworthy if the process is tested, not just the output.

## 5. Quality Gates

The Workshop should use quality gates to prevent invalid outputs from moving forward.

A quality gate is a required check before a workflow can progress.

5.1 Project Gate

Before serious analysis, the system must have:

- Project

- commander or deck concept

- format

- baseline DeckVersion

- at least a lightweight Design Brief

If the Design Brief is incomplete, the system may proceed, but missing fields must become explicit assumptions.

5.2 Analysis Gate

Before serious recommendations, the system must have:

- parsed DeckVersion

- card facts loaded

- basic role knowledge available

- baseline analysis generated

- at least one finding, weakness, or user question to reason about

The system should not jump from raw decklist to add/cut suggestions unless the user explicitly requests lightweight advice.

5.3 Reasoning Gate

Before a candidate becomes a Recommendation, the system must know:

- what problem is being solved

- why that problem matters

- which engine, package, role, weakness, or constraint is affected

- what trade-off is introduced

- what uncertainty remains

- whether a test is useful before deciding

A candidate that is only “good in general” fails the Reasoning Gate.

5.4 Recommendation Gate

Before a Recommendation is reviewable, it must include:

- problem solved

- proposed change

- affected engine or package

- expected benefit

- trade-off

- risk

- constraint check

- identity check

- confidence

- rationale

- suggested test when useful

A Recommendation must not modify the deck.

It is a proposal.

5.5 Simulation Gate

Before a SimulationRun can be saved, it must include:

- test question

- target DeckVersion

- simulation type

- configuration

- assumptions

- success criteria

- mulligan policy when relevant

- limitations

A simulation without a test question is not valid Workshop evidence.

5.6 Decision Gate

Before a meaningful new DeckVersion is created, there must be a Decision.

The Decision must record:

- source DeckVersion

- decision type

- rationale

- accepted changes

- rejected changes when applicable

- expected outcome

- risk accepted when applicable

- resulting DeckVersion when applicable

DeckVersion changes without Decision history should be treated as temporary edits or invalid workflow.

5.7 Report Gate

Before a report is considered useful, it must include:

- summary

- findings

- evidence

- assumptions

- confidence

- relevant DeckVersion

- next actions or decision context

A report that is only raw metrics or raw JSON is not enough.

## 6. Test Categories

6.1 Product Loop Tests

Product Loop Tests verify that the full system flow works from project creation to versioned decision.

The MVP must be able to complete this loop:

- Create Project

- Define lightweight Design Brief

- Import decklist

- Create baseline DeckVersion

- Load card facts

- Apply basic card knowledge

- Generate baseline analysis

- Identify structural weakness

- Produce explainable recommendation

- Record user decision

- Create new DeckVersion when appropriate

- Generate readable report

Product Loop Acceptance Criteria

A successful Product Loop Test must prove that:

- Project is the root workspace.

- The decklist is stored as part of a Project.

- Design Brief is preserved.

- DeckVersion is created before analysis.

- Analysis runs before serious recommendation.

- Recommendation does not modify the deck.

- Decision records what was accepted, rejected, deferred, or modified.

- New DeckVersion is created only after a meaningful Decision.

- Report can explain what happened.

Example Product Loop Test

Given:

- A Project with a Commander decklist

- A lightweight Design Brief

- A baseline DeckVersion

When:

- The system runs baseline analysis

- The system detects a mana consistency weakness

- The system proposes a mana base recommendation

- The user accepts the change as an experiment

Then:

- Recommendation remains a proposal until accepted

- Decision records the rationale

- New DeckVersion is created

- Source DeckVersion remains unchanged

- Report explains the problem, change, trade-off, and expected test

6.2 Data Model Tests

Data Model Tests verify that The Workshop preserves structure, traceability, and ownership boundaries.

Required Data Model Tests

Project:

- can be created with required fields

- owns or references brief, deck, versions, reports, decisions, notes, and backlog

- points to current DeckVersion

DesignBrief:

- stores strategy, philosophy, bracket, budget, constraints, success criteria, anti-goals

- supports missing fields without breaking lightweight usage

- distinguishes hard constraints from soft preferences

DeckVersion:

- is immutable after creation

- contains exact deck state

- references parent version when applicable

- can be compared to another version

DeckCard:

- belongs to one DeckVersion

- stores contextual category and role override

- does not overwrite global Card knowledge

Recommendation:

- stores rationale

- stores proposed changes

- stores confidence, trade-offs, risks, and status

- does not directly modify DeckVersion

Decision:

- records accepted, rejected, deferred, modified, or test-first choices

- links to source recommendation when applicable

- can create resulting DeckVersion

- stores rationale and expected outcome

SimulationRun:

- always references a DeckVersion

- always has a test question

- stores configuration and assumptions

SimulationResult:

- stores metrics, observations, failure patterns, confidence, and limitations

Data Model Acceptance Criteria

The data model passes testing if:

- no meaningful artifact floats without Project context

- no SimulationRun exists without DeckVersion

- no AnalysisReport silently mutates after deck changes

- no Recommendation directly edits the deck

- no Decision loses its rationale

- no DeckVersion is overwritten by later changes

6.3 Deck Parser Tests

Deck Parser Tests verify that raw decklists become structured DeckVersions.

Parser Test Cases

The parser should handle:

- plain text decklists

- commander section

- main deck section

- categories when provided

- sideboard / maybeboard when provided

- duplicate card names

- quantities

- unknown card names

- malformed lines

- extra whitespace

- Moxfield-style exports

- future import formats

Parser Acceptance Criteria

The parser must:

- identify commander where possible

- normalize card names

- preserve quantities

- assign cards to zones

- preserve user categories when available

- flag unknown or ambiguous cards

- avoid silently dropping cards

- create a valid baseline DeckVersion

The parser should not perform deep deck analysis.

Its job is normalization.

6.4 Card Knowledge Tests

Card Knowledge Tests verify that the system separates facts from interpretation.

Required Knowledge Tests

Card Facts:

- imported from canonical external source

- not authored by AI

- include name, oracle text, mana cost, mana value, type line, color identity, legality where available

Derived Card Data:

- reproducible from card facts

- does not overwrite canonical facts

Card Knowledge:

- stores functional roles

- stores source

- stores confidence

- stores validation status

- can be global or project-specific

Project Overrides:

- can reinterpret a card inside a specific deck

- do not modify global card facts

- can mark cards as core, replaceable, pet card, testing, off-plan, accepted risk, do not cut

Knowledge Acceptance Criteria

The system must be able to say:

- this is a canonical card fact

- this is derived data

- this is curated card knowledge

- this is AI-suggested and unvalidated

- this is user-defined

- this is project-specific

If the system cannot identify source or confidence, the knowledge should not be treated as reliable.

6.5 Analysis Engine Tests

Analysis Engine Tests verify that the system can explain what the deck currently is.

Required Analysis Areas

The MVP should test analysis for:

- land count

- mana curve

- color requirements

- ramp density

- draw density

- interaction density

- protection density

- win condition density

- basic package detection

- basic engine detection

- unsupported cards

- over-supported roles

- under-supported roles

- structural weaknesses

Analysis Acceptance Criteria

An AnalysisReport must include:

- summary

- key findings

- evidence

- affected components

- assumptions

- confidence

- weaknesses

- suggested next steps

The Analysis Engine answers:

“What is happening inside this DeckVersion?”

It must not jump directly to:

“Add this card.”

6.6 Reasoning Engine Tests

Reasoning Engine Tests verify that The Workshop interprets analysis through project context.

Required Reasoning Tests

The Reasoning Engine should be tested for:

- Design Brief interpretation

- constraint handling

- assumption generation

- clarification policy

- hypothesis generation

- trade-off analysis

- candidate evaluation

- identity fit review

- constraint fit review

- accepted risk handling

- recommendation readiness

- decision support

Reasoning Acceptance Criteria

A ReasoningOutput should include:

- summary

- assumptions

- hypotheses

- evidence

- trade-offs

- candidate evaluations when relevant

- constraint checks

- identity checks

- risks

- uncertainty

- confidence

- suggested tests

- recommendation readiness

- decision support

The Reasoning Engine must not:

- invent card facts

- skip the Design Brief for serious recommendations

- treat popularity as proof

- recommend generic staples without project fit

- modify decks directly

- hide uncertainty

Example Reasoning Test

Given:

- A deck with low tutor tolerance in the Design Brief

- A weakness related to inconsistent engine access

When:

- The system evaluates Demonic Tutor as a candidate solution

Then:

- The system may identify it as powerful

- The system must flag conflict with low tutor tolerance

- The system must explain the trade-off

- The system should consider redundancy-based alternatives

- The system must not recommend it as a default fix

6.7 Recommendation Tests

Recommendation Tests verify that proposals are contextual, explainable, and reviewable.

Required Recommendation Tests

A Recommendation must include:

- problem solved

- proposed change

- affected engine or package

- expected benefit

- trade-off

- risk

- constraint check

- identity check

- confidence

- rationale

- suggested test when useful

- status

Recommendation Acceptance Criteria

A valid serious recommendation must satisfy:

- problem is clear

- objective is clear

- proposed change addresses the problem

- trade-off is explained

- constraints are checked

- identity fit is considered

- confidence is stated

- uncertainty is exposed

- recommendation does not automatically modify deck

- user can accept, reject, defer, modify, or test first

Invalid recommendation examples:

- “Add this because it is popular.”

- “Add this because it is strong.”

- “Cut this without explaining what role is lost.”

- “Automatically update the deck.”

- “Ignore budget, bracket, or user philosophy.”

6.8 Simulation Tests

Simulation Tests verify that simulations produce evidence for hypotheses without false certainty.

Required Simulation Types for MVP

The MVP should test:

- opening hand simulation

- land drop probability

- mana consistency

- color availability

- ramp access

- mulligan quality

- basic goldfish Level 1

- basic goldfish Level 2

Engine access simulation can be added after the role and engine data are reliable enough.

SimulationRun Acceptance Criteria

Every SimulationRun must include:

- test question

- target DeckVersion

- simulation type

- configuration

- iterations

- seed when relevant

- mulligan policy

- assumptions

- success conditions

- limitations

- status

SimulationResult Acceptance Criteria

Every SimulationResult must include:

- readable summary

- metrics

- observations

- failure patterns

- confidence

- limitations

- created timestamp

Simulation Quality Rules

The Simulation Engine must distinguish:

- access

- castability

- functional availability

The system must not claim:

“This deck wins 63% of the time.”

Preferred:

“Under simplified goldfish assumptions, this DeckVersion accesses a minimum engine configuration by turn four in 63% of runs.”

Simulation should support reasoning.

It should not replace judgment.

Example Simulation Test

Given:

- A DeckVersion with white-intensive spells

- A hypothesis that the mana base cannot support double-white by turn six

When:

- The system runs a color availability simulation

Then:

- The SimulationRun includes the test question

- The result reports double-white availability by turn six

- The result includes failure patterns

- The result includes assumptions and limitations

- The Reasoning Engine interprets the result before any final recommendation

6.9 Decision and Versioning Tests

Decision and Versioning Tests verify that project history remains traceable and reversible.

Required Decision Tests

The system should support Decision types:

- accept

- reject

- defer

- modify

- test first

- accept as experiment

- revert

- mark as accepted risk

Decision Acceptance Criteria

A Decision must record:

- source DeckVersion

- source Recommendation when applicable

- decision type

- title

- rationale

- accepted changes

- rejected changes

- expected outcome

- accepted risk when relevant

- resulting DeckVersion when relevant

- user comment when provided

- created timestamp

Versioning Acceptance Criteria

A meaningful deck change must:

- create a new DeckVersion

- preserve parent version

- preserve change summary

- preserve source Decision

- not mutate historical versions

- allow comparison between versions

- allow later revert through a new Decision

Example Versioning Test

Given:

- DeckVersion v1.0

- A Recommendation to add two mana fixing lands

- A user Decision to accept as experiment

When:

- The Decision is applied

Then:

- DeckVersion v1.1 is created

- DeckVersion v1.0 remains unchanged

- v1.1 references v1.0 as parent

- the Decision links to both source and resulting version

- changelog can explain what changed and why

6.10 Report Tests

Report Tests verify that The Workshop produces readable user-facing artifacts.

Required MVP Reports

The MVP should support:

- baseline deck audit

- mana report

- recommendation report

- simulation report

- changelog

- decision summary

- project report

Report Acceptance Criteria

A Report must include:

- title

- project

- DeckVersion

- summary

- findings

- reasoning

- evidence

- assumptions

- confidence

- recommendations or next actions when relevant

- source analysis, simulation, recommendation, or decision references

Reports should be readable.

They should not be raw JSON dumps.

Structured metadata should exist, but the user-facing content should explain what matters.

6.11 UI / UX Tests

UI / UX Tests verify that the product experience preserves The Workshop philosophy.

Required UI Tests

The UI should make clear that:

- Project is the primary workspace

- Design Brief appears before serious recommendations

- decklist is one artifact inside a Project

- recommendations are proposals

- simulation results have assumptions and limitations

- only Decisions create meaningful DeckVersions

- trade-offs are visible

- accepted risks are visible but not noisy

- user agency is preserved

UI Acceptance Criteria

The MVP UI or local workflow must allow the user to:

- view project identity

- view current DeckVersion

- view brief

- view analysis summary

- review recommendation

- inspect rationale

- accept, reject, defer, modify, or test first

- view decision history

- view version history

- view reports

Even if the MVP is local-first and file-based, the workflow should still be testable as a user experience.

## 7. Test Fixtures

The Workshop should maintain a small set of test deck projects.

These fixtures should represent different product challenges.

The goal is not to test every Commander archetype.

The goal is to test whether The Workshop can preserve deck identity, reason from context, and avoid generic recommendations.

7.1 Myr Artifact Combo-Control Fixture

Purpose:

Test whether the system can avoid treating a deck as simple tribal when its real identity is combo-control.

Expected identity:

Artifact combo-control engine disguised as Myr tribal.

Useful tests:

- artifact count analysis

- mana fixing analysis

- engine detection

- combo support

- artifact hate vulnerability

- recommendation identity preservation

- simulation for color availability and engine access

Failure case to catch:

The system recommends generic Myr tribal payoffs while ignoring artifact sacrifice engines, mana fixing, and combo-control identity.

7.2 Emry Equipment Toolbox Fixture

Purpose:

Test whether the system can distinguish equipment recursion toolbox from generic Voltron.

Expected identity:

Mono-blue recursion-based equipment toolbox.

Useful tests:

- equipment package analysis

- carrier density analysis

- graveyard recursion support

- artifact hate resilience

- protection package evaluation

- goldfish setup speed

Failure case to catch:

The system recommends generic Voltron damage upgrades while ignoring recursion, artifact loops, and carrier/package density.

7.3 Zur Forbidden-Aura Fixture

Purpose:

Test whether the system can preserve risky deck identity instead of normalizing into generic enchantment control.

Expected identity:

Risk-heavy forbidden-aura brinkmanship engine.

Useful tests:

- aura package analysis

- commander dependency

- protection density

- accepted risk handling

- identity-fit rejection of generic recommendations

- shroud / hexproof rules dependency on canonical facts

Failure case to catch:

The system removes the risky aura plan because it is fragile, instead of recognizing that risk is part of the deck identity.

7.4 Izzet Spellslinger / Storm Fixture

Purpose:

Test whether the system can reason about spell-chain engines, rituals, card flow, and payoff density.

Expected identity:

Mana fraud / storm engine.

Useful tests:

- ramp vs ritual distinction

- card flow density

- payoff without enabler

- goldfish Level 1 / Level 2

- tutor modeling boundary

- explosiveness vs consistency trade-off

Failure case to catch:

The system treats rituals as normal ramp or recommends generic draw spells without evaluating spell-chain function.

## 8. Regression Testing

Regression tests protect The Workshop from becoming worse over time.

A regression occurs when the system starts violating a core principle that previously held.

Required Regression Areas

The system should fail tests if:

- AI authors canonical card facts

- recommendation appears without rationale

- recommendation modifies deck directly

- simulation runs without test question

- DeckVersion mutates after creation

- Decision is missing for meaningful version change

- accepted risk is repeatedly flagged as unresolved

- card popularity is treated as proof

- project-specific role override modifies global card knowledge

- reports omit assumptions or confidence

- simulation results omit limitations

- generic staples are recommended despite conflicting constraints

- a rejected recommendation is suggested again without new context

- a previous user constraint is ignored

- a new DeckVersion loses parent history

Regression testing should include both technical checks and product behavior checks.

## 9. MVP Testing Priorities

Sprint 1 should prioritize tests that prove the core product loop.

9.1 P0 Testing Priorities

Required before MVP foundation can be considered valid:

- Project creation test

- Design Brief schema test

- Deck import / parser test

- DeckVersion immutability test

- Card facts import test

- Basic role taxonomy test

- Baseline analysis report test

- Recommendation structure test

- Decision creates DeckVersion test

- Report generation test

9.2 P1 Testing Priorities

Important for first useful prototype:

- Opening hand simulation test

- Color availability simulation test

- Recommendation readiness test

- Constraint handling test

- Accepted risk test

- Version comparison test

- Changelog test

- Project-specific role override test

9.3 P2 Testing Priorities

Useful after core loop works:

- Engine access simulation test

- Tutor modeling test

- Goldfish Level 2 test

- UI dashboard test

- Recommendation review UI test

- Decision log UI test

- Multi-version project history test

## 10. Testing Non-Goals

The MVP testing strategy does not require:

- perfect Commander rules simulation

- full multiplayer gameplay simulation

- complete card knowledge coverage

- exhaustive combo database validation

- production-grade UI automation

- full database migration testing

- performance testing at scale

- every possible deck archetype

- exact pricing validation

- complete import support for every external deck platform

These are valid future concerns, but they are not required to prove the MVP.

The MVP must prove that The Workshop’s structure is correct.

## 11. Definition of Done for MVP Features

A feature is done only when it satisfies three levels of quality.

11.1 Functional Done

The feature executes without obvious failure.

Example:

Decklist import creates a DeckVersion.

11.2 Structural Done

The feature stores data in the correct model and preserves ownership boundaries.

Example:

DeckVersion contains DeckCards, but Card Facts remain global.

11.3 Product Done

The feature supports The Workshop philosophy.

Example:

The imported deck can be analyzed as part of a Project, and later recommendations can reference its exact DeckVersion.

A feature that is only functionally done is not enough.

The Workshop needs structural and product correctness.

## 12. MVP Testing Workflow

Sprint 1 testing should follow this sequence:

- Validate file / storage structure

- Validate Project schema

- Validate Design Brief schema

- Validate DeckVersion schema

- Validate deck import

- Validate card fact lookup

- Validate role tagging

- Validate baseline analysis

- Validate weakness detection

- Validate reasoning output

- Validate recommendation format

- Validate decision record

- Validate new DeckVersion creation

- Validate report generation

- Validate regression checks against core principles

This order matters.

Testing recommendations before Project, Brief, DeckVersion, and Analysis exist would recreate the shallow behavior The Workshop is designed to avoid.

## 13. Testing Artifacts

The Workshop should store testing artifacts alongside the project.

Recommended local-first structure:

/tests /fixtures /decks /projects /briefs /expected /golden analysis_reports recommendations simulation_results decision_logs /regression product_principles data_model reasoning simulation /scripts run_parser_tests run_analysis_tests run_simulation_tests run_regression_tests

Golden files should be used carefully.

They should verify structure, required fields, and product behavior.

They should not make the system brittle by requiring every sentence of a generated report to remain identical forever.

## 14. Acceptance Criteria for RFC-010

This RFC is acceptable if it defines:

- why testing matters for The Workshop

- what categories of testing are required

- how testing connects to the core engineering loop

- what quality gates protect the system

- what must be tested in Sprint 1

- how to test recommendations

- how to test simulations

- how to test decisions and versioning

- how to avoid false certainty

- how to use real deck fixtures

- what is explicitly out of scope for MVP testing

- what “done” means for MVP features

## 15. Summary

Testing in The Workshop is not only about preventing bugs.

It is about protecting the product identity.

The system must be tested to ensure that it remains:

- project-first

- context-aware

- analysis-driven

- evidence-supported

- explainable

- reversible

- user-directed

- honest about uncertainty

The Workshop should not merely pass technical tests.

It should pass engineering behavior tests.

A test suite that only verifies code execution is insufficient.

The Workshop must prove that it can help a player understand, improve, test, and document a deck as an engineered system.
