# RFC-011 — The Workshop Sprint 1 Plan

Status: Draft Version: v0.1 Sprint: 1 Depends on: RFC-000, RFC-001, RFC-002, RFC-003, RFC-004, RFC-005, RFC-006, RFC-007, RFC-008, RFC-009, RFC-010 Document Type: Sprint Plan / Execution Plan Owner: Product Owner / Domain Expert Technical Owner: Software Architect / CTO

## 1. Purpose

This document defines the execution plan for Sprint 1 of The Workshop.

Sprint 0 established the product and architecture foundation.

Sprint 1 begins the transition from documentation to a working prototype.

The goal is not to build the final application.

The goal is to prove that The Workshop can operate as a local Deck Engineering Platform using real project files, structured data, readable reports, and traceable decisions.

Sprint 1 should answer one core question:

Can The Workshop complete its core engineering loop on one real Commander deck project?

The core loop is:

Project → Brief → Deck Import → DeckVersion → Card Facts → Basic Knowledge → Analysis → Weakness → Recommendation → Decision → New DeckVersion → Report

If Sprint 1 proves this loop, The Workshop stops being only documentation and becomes an executable product model.

## 2. Sprint Name

Sprint 1 — Local Prototype Foundation

## 3. Sprint Goal

Create a minimal local prototype of The Workshop that proves the core product loop with real files.

By the end of Sprint 1, the project should be able to:

- create a local Workshop project

- store a lightweight Design Brief

- import a Commander decklist

- create an immutable baseline DeckVersion

- load or reference canonical card facts

- apply basic functional role knowledge

- generate a baseline analysis report

- identify at least one structural weakness

- draft one structured recommendation

- record one user decision

- create one new DeckVersion from that decision

- generate a readable project report

The prototype can be rough.

It must be structurally correct.

## 4. Sprint Thesis

Sprint 1 is not a UI sprint.

Sprint 1 is not an AI automation sprint.

Sprint 1 is not a full simulation sprint.

Sprint 1 is a product-loop proof sprint.

The Workshop must first prove that its architecture can be executed locally before building a polished interface, a full database, advanced simulation, or automatic recommendations.

The most important Sprint 1 success condition is not beauty.

It is traceability.

At the end of Sprint 1, the system should be able to answer:

- What project are we working on?

- What is the deck trying to be?

- What exact deck version was analyzed?

- What card facts were used?

- What basic roles were assigned?

- What did the analysis find?

- What weakness was identified?

- What recommendation was proposed?

- What did the user decide?

- What new deck version resulted?

- What report explains the process?

If these questions can be answered from local files, Sprint 1 is successful.

## 5. Sprint Scope

5.1 Must Have

Sprint 1 must deliver the minimum structure required to run the core loop.

Product / Workflow

- Define the MVP product loop step by step.

- Define required input and output for each step.

- Select one real Commander deck as the first test project.

- Define the first lightweight Design Brief format.

- Define what counts as a successful Sprint 1 project run.

Architecture

- Confirm local-first prototype direction.

- Confirm Markdown/JSON storage direction.

- Define the local project folder structure.

- Define MVP module boundaries.

- Decide which modules are real in Sprint 1 and which remain manual or conceptual.

Data Model

Create MVP schemas for:

- Project

- DesignBrief

- DeckVersion

- DeckCard

- AnalysisReport

- Recommendation

- Decision

- Report

- BacklogItem or Note

These schemas may be JSON files.

They do not need to be database tables yet.

Deck Import

- Support one plain-text decklist import format.

- Parse card quantity and card name.

- Identify commander manually or through a simple field.

- Preserve categories if present.

- Flag unknown or malformed lines instead of silently dropping them.

- Create a baseline DeckVersion from the import.

Card Facts

- Choose canonical card data source for MVP.

- Define card import strategy.

- Load or reference basic card facts:

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

Card facts must not be authored by AI.

Basic Knowledge

- Define MVP FunctionalRole taxonomy.

- Create first role tag file.

- Support global roles and project-specific role overrides.

- Mark role source and confidence.

- Keep role taxonomy compact.

Analysis

Generate one baseline analysis report that includes:

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

The analysis should explain what the deck currently is.

It should not jump directly to card recommendations.

Recommendation

Create one structured recommendation manually or semi-automatically.

The recommendation must include:

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

Decision

Record one decision.

The decision must include:

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

Versioning

- Preserve baseline DeckVersion unchanged.

- Create a new DeckVersion after accepted or modified decision.

- Link new DeckVersion to parent version.

- Store change summary.

- Preserve source decision.

Reporting

Generate one readable Markdown report.

The report must explain:

- project identity

- current version

- brief summary

- analysis findings

- weakness identified

- recommendation proposed

- decision made

- resulting version

- next action

5.2 Should Have

These are important if Must Have work is stable.

- Basic changelog generation.

- Basic project README.

- First project backlog file.

- First note format.

- Basic package grouping:

- mana base

- ramp

- draw

- interaction

- protection

- win conditions

- flex

- Basic role density output.

- Basic weakness status:

- open

- under review

- recommendation created

- decision made

- resolved

- accepted risk

- Basic recommendation review Markdown template.

- Basic decision log Markdown template.

- First regression checklist against Workshop principles.

5.3 Could Have

These are optional stretch items.

- Opening hand simulation prototype.

- Color availability simulation prototype.

- Simple land-drop probability script.

- Simple goldfish Level 1 draw/access script.

- Markdown report renderer.

- CLI command for project creation.

- CLI command for deck import.

- CLI command for analysis report generation.

- JSON schema validation script.

- First golden test fixture.

These should not block the sprint.

5.4 Should Not Have Yet

Sprint 1 should explicitly not build:

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

If one of these becomes tempting during Sprint 1, it should be moved to the Backlog or Future scope.

## 6. Sprint 1 MVP Module Scope

6.1 Implemented in Sprint 1

These modules should exist in minimal local form:

Project Workspace

Implemented as local project folders and metadata files.

Owns:

- project metadata

- Design Brief

- deck versions

- reports

- decisions

- notes

- backlog

Deck Parser

Implemented as a simple parser for one supported decklist format.

Owns:

- raw decklist normalization

- card name extraction

- quantity extraction

- zone/category preservation where possible

- unknown card warnings

Card Knowledge Base

Implemented as local card data files or imported canonical data.

Owns:

- canonical card facts

- basic card lookup

- basic role tag file

Deck Analysis Engine

Implemented as scripts or manual/semi-automatic report generation.

Owns:

- land count

- curve

- role density

- package density

- basic findings

- weakness list

Reporting Engine

Implemented as Markdown report templates.

Owns:

- baseline audit report

- recommendation report

- decision summary

- changelog or project summary

Versioning & Decision Log

Implemented as JSON/Markdown files.

Owns:

- immutable DeckVersions

- decision records

- version parent links

- change summaries

6.2 Manual or Semi-Manual in Sprint 1

These modules may be represented by templates rather than full automation:

Reasoning Engine

Sprint 1 should not attempt full reasoning automation.

It should define and use structured reasoning templates:

- weakness interpretation

- candidate evaluation

- add/cut rationale

- trade-off comparison

- decision support

The reasoning may be authored manually or with AI assistance, but stored as structured output.

Recommendation Engine

Sprint 1 does not need automatic recommendation generation.

It only needs structured recommendation records.

A recommendation may be manually created as long as it follows the required format.

Simulation Engine

Sprint 1 may include optional prototype scripts, but simulation is not required to prove the first loop.

If simulation is included, every result must have:

- test question

- target DeckVersion

- assumptions

- configuration

- limitations

6.3 Deferred Modules

These remain conceptual or future scope:

- full UI

- advanced Reasoning Engine automation

- automatic Recommendation Engine

- advanced Simulation Engine

- graph knowledge model

- full rules engine

- multiplayer gameplay simulation

- collection integration

- external sharing

- collaboration features

## 7. Proposed Local Folder Structure

Sprint 1 should use a local-first project structure.

Recommended root:

/workshop

/card-data

cards.json

card_import_metadata.json

/knowledge

functional_roles.json

role_taxonomy.json

project_override_schema.json

/projects

/project-slug

project.json

README.md

/brief

brief.json

brief.md

/deck

current.txt

/versions

v1.0.json

v1.1.json

/analysis

baseline_v1.0.json

baseline_v1.0.md

/recommendations

rec-001.json

rec-001.md

/decisions

decision-001.json

decision-001.md

/reports

project_report_v1.0.md

changelog.md

/notes

notes.md

backlog.md

/tests

/fixtures

/decks

/projects

/briefs

/expected

/analysis_reports

/recommendations

/decision_logs

/regression

product_principles.md

data_model.md

reasoning.md

simulation.md

This structure is not final product architecture.

It is the first executable form of the product model.

## 8. Sprint 1 Work Items

8.1 Product Work

S1-P-001 — Define MVP Product Loop

Priority: P0 Status: open

Deliverable:

- step-by-step MVP flow

- input/output per step

- manual vs automated step classification

Acceptance Criteria:

- flow includes Project, Brief, DeckVersion, AnalysisReport, Recommendation, Decision, and Report

- flow avoids automatic deck modification

- flow can be executed on one real deck project

S1-P-002 — Select First Test Deck Project

Priority: P0 Status: open

Deliverable:

- one real Commander deck selected as Sprint 1 fixture

- lightweight brief written for that deck

- baseline decklist available in supported format

Acceptance Criteria:

- deck has enough complexity to test roles, packages, weaknesses, and recommendations

- deck is not so complex that it blocks the prototype

- deck can produce at least one meaningful recommendation and decision

Recommended candidates:

- Myr artifact combo-control deck

- Emry equipment recursion toolbox

- Zur forbidden-aura brinkmanship deck

- Izzet spellslinger / storm deck

S1-P-003 — Define Sprint 1 Success Criteria

Priority: P0 Status: open

Deliverable:

- success checklist

Acceptance Criteria:

Sprint 1 is successful if one project can complete:

Project → Brief → Deck Import → DeckVersion → Analysis → Recommendation → Decision → New DeckVersion → Report

8.2 Architecture Work

S1-A-001 — Accept or Revise Local-First ADR

Priority: P0 Status: open

Deliverable:

- ADR-008 accepted, revised, or rejected

Acceptance Criteria:

- implementation strategy selected

- trade-offs documented

- Sprint 1 build path clear

S1-A-002 — Accept or Revise Markdown/JSON Storage ADR

Priority: P0 Status: open

Deliverable:

- ADR-009 accepted, revised, or rejected

Acceptance Criteria:

- storage model selected

- file structure sketched

- migration path acknowledged

S1-A-003 — Define MVP Module Boundaries

Priority: P0 Status: open

Deliverable:

- module scope document or section

Acceptance Criteria:

- Sprint 1 modules listed

- deferred modules listed

- manual/semi-manual modules identified

- ownership boundaries preserved

S1-A-004 — Define Project Folder Structure

Priority: P0 Status: open

Deliverable:

- local folder layout

Acceptance Criteria:

- supports Project, Brief, DeckVersion, Analysis, Recommendation, Decision, Report, Notes, and Backlog

- human-readable

- migration-friendly

8.3 Data Model Work

S1-D-001 — Create Project Schema

Priority: P0 Status: open

Required fields:

- id

- name

- status

- format

- commander_name

- current_deck_version_id

- summary

- identity_statement

- created_at

- updated_at

S1-D-002 — Create Design Brief Schema

Priority: P0 Status: open

Required fields:

- format

- commander

- strategy

- design_philosophy

- desired_play_pattern

- bracket_target

- budget

- proxy_policy

- meta_context

- success_criteria

- anti_goals

- hard_constraints

- soft_preferences

- accepted_risks

S1-D-003 — Create DeckVersion Schema

Priority: P0 Status: open

Required fields:

- id

- project_id

- deck_id

- version_number

- label

- parent_version_id

- status

- change_summary

- source

- created_at

- created_by

- cards

S1-D-004 — Create DeckCard Schema

Priority: P0 Status: open

Required fields:

- card_name

- quantity

- zone

- category

- user_category

- is_commander

- role_override

- status

- notes

- related_decision_id

S1-D-005 — Create AnalysisReport Schema

Priority: P0 Status: open

Required fields:

- id

- project_id

- deck_version_id

- analysis_type

- summary

- metrics

- findings

- weaknesses

- assumptions

- confidence

- created_at

- generated_by

S1-D-006 — Create Recommendation Schema

Priority: P1 Status: open

Required fields:

- id

- project_id

- deck_version_id

- title

- problem

- summary

- proposed_changes

- expected_benefit

- trade_offs

- risks

- constraint_check

- identity_check

- confidence

- status

- test_suggestion

- rationale

S1-D-007 — Create Decision Schema

Priority: P1 Status: open

Required fields:

- id

- project_id

- source_deck_version_id

- recommendation_id

- decision_type

- title

- rationale

- accepted_changes

- rejected_changes

- expected_outcome

- risk_accepted

- resulting_deck_version_id

- user_comment

- created_at

8.4 Knowledge Work

S1-K-001 — Choose Canonical Card Data Source

Priority: P0 Status: open

Deliverable:

- selected canonical external card data source

- import method

- refresh strategy

- ADR update if required

Acceptance Criteria:

- AI is not used as source for card facts

- source supports core card facts required for parsing and analysis

- limitations are documented

S1-K-002 — Define MVP Card Import Pipeline

Priority: P0 Status: open

Deliverable:

- import plan or script

Acceptance Criteria:

Pipeline supports:

- name

- normalized name

- oracle text

- mana cost

- mana value

- type line

- color identity

- colors

- legalities

- produced mana where available

S1-K-003 — Define MVP Functional Role Taxonomy

Priority: P0 Status: open

Recommended MVP roles:

- ramp

- mana_fixing

- card_draw

- card_selection

- tutor

- removal

- board_wipe

- counterspell

- protection

- recursion

- token_producer

- sacrifice_outlet

- payoff

- enabler

- outlet

- combo_piece

- win_condition

- graveyard_hate

- cost_reduction

Acceptance Criteria:

- each role has a short definition

- roles are grouped by family

- role spam is avoided

- project-specific overrides are supported

S1-K-004 — Create First Role Tag File

Priority: P1 Status: open

Deliverable:

- functional_roles.json

Acceptance Criteria:

- covers cards from the first test deck

- roles include source, confidence, and validation status

- AI-suggested roles are marked unvalidated

- user/project overrides remain separate from global roles

8.5 Analysis Work

S1-AN-001 — Define Baseline Analysis Report Template

Priority: P0 Status: open

Deliverable:

- baseline_analysis_template.md

- baseline_analysis_schema.json

Acceptance Criteria:

Report includes:

- summary

- deck identity assumption

- land count

- curve summary

- role density

- package density

- strengths

- weaknesses

- assumptions

- confidence

- suggested next steps

S1-AN-002 — Generate First Baseline Analysis Report

Priority: P0 Status: open

Deliverable:

- baseline report for first test deck

Acceptance Criteria:

- report references exact DeckVersion

- report identifies at least three meaningful findings

- report identifies at least one weakness

- report does not make unsupported recommendations

- report is readable by a human

8.6 Reasoning and Recommendation Work

S1-R-001 — Define MVP Reasoning Templates

Priority: P0 Status: open

Templates:

- weakness interpretation

- candidate evaluation

- add/cut rationale

- trade-off comparison

- simulation request

- decision support

- accepted risk

- identity fit review

- constraint fit review

Acceptance Criteria:

- each template has required fields

- each template can render as Markdown

- each template can be stored as JSON

- each template includes uncertainty and confidence

S1-R-002 — Create First Structured Recommendation

Priority: P1 Status: open

Deliverable:

- one Recommendation JSON

- one Recommendation Markdown review

Acceptance Criteria:

- recommendation solves a stated problem

- proposed change is explicit

- affected role/package/engine is named

- trade-off is explained

- confidence is stated

- recommendation does not modify deck

8.7 Decision and Versioning Work

S1-V-001 — Define Decision Log Format

Priority: P0 Status: open

Deliverable:

- decision schema

- decision Markdown template

Acceptance Criteria:

- supports accept, reject, defer, modify, test first, accept as experiment, revert, accepted risk

- links to Recommendation and DeckVersion

- preserves rationale

S1-V-002 — Create New DeckVersion From Decision

Priority: P0 Status: open

Deliverable:

- DeckVersion v1.1 created from Decision

Acceptance Criteria:

- v1.0 remains unchanged

- v1.1 links to v1.0 as parent

- decision explains why v1.1 exists

- project current_deck_version_id updates only after decision

8.8 Reporting Work

S1-REP-001 — Create Project Report Template

Priority: P0 Status: open

Deliverable:

- project_report_template.md

Acceptance Criteria:

Report includes:

- project identity

- brief summary

- current DeckVersion

- analysis findings

- recommendation summary

- decision summary

- version change summary

- next actions

S1-REP-002 — Generate First Project Report

Priority: P0 Status: open

Deliverable:

- report for first test project

Acceptance Criteria:

- readable without opening raw JSON

- references source DeckVersion

- explains what changed and why

- includes next engineering step

8.9 Testing Work

S1-T-001 — Define Sprint 1 Quality Checklist

Priority: P0 Status: open

Deliverable:

- Sprint 1 testing checklist

Acceptance Criteria:

Checklist verifies:

- Project exists

- Brief exists

- DeckVersion exists

- DeckVersion is immutable

- card facts are sourced externally

- roles are source-tracked

- analysis runs before recommendation

- recommendation does not modify deck

- decision creates new version

- report explains the process

S1-T-002 — Create First Test Fixtures

Priority: P1 Status: open

Deliverable:

- fixture decklist

- fixture brief

- expected project files

- expected report structure

Acceptance Criteria:

- fixture can be reused in later parser, analysis, recommendation, and decision tests

- fixture is realistic enough to expose product behavior

## 9. Sprint Exit Criteria

Sprint 1 is complete only if all of the following are true:

- A local project folder exists.

- Project metadata exists.

- A lightweight Design Brief exists.

- A decklist has been imported.

- A baseline DeckVersion exists.

- The baseline DeckVersion is not mutated after creation.

- Card facts are loaded or referenced from an external source.

- Basic functional roles exist for the test deck.

- A baseline analysis report exists.

- The analysis identifies at least one structural weakness.

- A structured recommendation exists.

- The recommendation includes problem, benefit, trade-off, risk, confidence, and rationale.

- A decision exists.

- The decision records what was accepted, rejected, deferred, or modified.

- A new DeckVersion exists if the decision changes the deck.

- The new DeckVersion links to the previous version.

- A readable project report exists.

- The process is reproducible on the same fixture deck.

- Sprint findings are added to the Sprint Log.

- Any major implementation decisions are recorded or updated in ADR.

## 10. Definition of Done

A Sprint 1 feature is not done just because it runs.

It must satisfy three levels.

10.1 Functional Done

The feature executes.

Example:

Deck import creates a DeckVersion.

10.2 Structural Done

The feature stores the correct data in the correct place.

Example:

DeckVersion contains DeckCards, but global Card Facts remain separate.

10.3 Product Done

The feature supports The Workshop philosophy.

Example:

The imported deck can be analyzed inside a Project, and later recommendations can reference the exact DeckVersion.

Functional Done alone is not enough.

The Workshop must be structurally and philosophically correct from the start.

## 11. Sprint Risks

11.1 Scope Creep

Risk:

Sprint 1 expands into UI, automation, simulation, database design, or full app architecture.

Mitigation:

Keep Sprint 1 focused on the local product loop.

Anything outside the loop goes to Backlog.

11.2 Over-Modeling

Risk:

Knowledge and data schemas become too complex before the first project works.

Mitigation:

Use compact roles, JSON files, and project-level overrides.

Normalize later only when needed.

11.3 False Progress

Risk:

The system produces nice Markdown but does not preserve structured data.

Mitigation:

Every report must reference structured source files.

Readable output is not enough.

11.4 Shallow AI Behavior

Risk:

The prototype becomes a chatbot workflow that suggests cards without analysis.

Mitigation:

Require AnalysisReport before serious Recommendation.

Require Recommendation rationale.

Require Decision before DeckVersion change.

11.5 Simulation Distraction

Risk:

Sprint 1 spends too much time on goldfish or color simulations before project structure works.

Mitigation:

Simulation is optional for Sprint 1.

If included, it must test a specific question.

11.6 Card Data Complexity

Risk:

Choosing and importing card data becomes a rabbit hole.

Mitigation:

Choose one canonical source.

Import only required fields first.

Document limitations.

## 12. Open Questions for Sprint 1

These questions should be answered during Sprint 1 or moved to future backlog.

Product

- Which deck becomes the first real test project?

- Is Sprint 1 targeting power users / deckbuilding nerds only?

- How much brief information is required before baseline analysis?

- How much recommendation depth is required for the first prototype?

Architecture

- Should ADR-008 local-first be accepted as-is?

- Should ADR-009 Markdown/JSON storage be accepted as-is?

- Should Sprint 1 include CLI commands or manual file creation?

- Should schemas be formal JSON Schema or lightweight examples first?

Knowledge

- What is the canonical external card source?

- Is popularity data excluded from Sprint 1?

- What is the final MVP FunctionalRole set?

- Are AI-suggested roles project-only by default?

Reasoning

- Should every Recommendation require an explicit Hypothesis in Sprint 1?

- Should rejected recommendations become negative project knowledge immediately?

- Should user corrections create project overrides immediately?

- How strict is the recommendation readiness gate in Sprint 1?

Simulation

- Is simulation entirely deferred?

- If not deferred, is opening hand or color availability first?

- What mulligan policy is assumed?

- What minimum iteration count is acceptable for saved results?

UI / Reporting

- Are Markdown reports enough for Sprint 1?

- Should the first project report behave like a dashboard substitute?

- Should accepted risks appear in the first report?

- Should deck editing be represented through decisions only?

## 13. Expected Sprint 1 Artifacts

Sprint 1 should produce:

Product Artifacts

- MVP product loop document

- first test project brief

- Sprint 1 success checklist

Architecture Artifacts

- local folder structure

- MVP module scope

- accepted or revised ADR-008

- accepted or revised ADR-009

- accepted or revised ADR-010 if card source is selected

Data Artifacts

- project.json

- brief.json

- DeckVersion JSON

- DeckCard schema

- AnalysisReport schema

- Recommendation schema

- Decision schema

- Report metadata shape

Knowledge Artifacts

- role_taxonomy.json

- functional_roles.json

- card import metadata

- project override format

Execution Artifacts

- imported decklist

- baseline DeckVersion

- baseline analysis report

- one recommendation

- one decision

- one resulting DeckVersion

- one final project report

Testing Artifacts

- fixture deck

- fixture brief

- expected file structure

- Sprint 1 quality checklist

## 14. Sprint 1 Non-Goals

Sprint 1 does not need to prove:

- production scalability

- final database design

- polished UX

- full automation

- full card knowledge coverage

- advanced combo recognition

- accurate gameplay simulation

- price accuracy

- collection support

- public sharing

- mobile experience

- multiplayer modeling

- full external deck platform integration

Sprint 1 only needs to prove that The Workshop can execute its core loop as a local engineering system.

## 15. Recommended Sprint 1 Execution Order

- Accept or revise ADR-008 and ADR-009.

- Choose first test deck.

- Define local project folder structure.

- Define Project and Brief schemas.

- Create local project manually.

- Define DeckVersion and DeckCard schemas.

- Import decklist into baseline DeckVersion.

- Choose canonical card data source.

- Load or reference card facts.

- Define FunctionalRole taxonomy.

- Tag enough cards for first deck.

- Define baseline analysis template.

- Generate baseline analysis report.

- Identify one weakness.

- Create one structured recommendation.

- Record one decision.

- Create new DeckVersion.

- Generate project report.

- Run Sprint 1 quality checklist.

- Update Sprint Log and Backlog.

- Record implementation decisions in ADR.

This order matters.

Building recommendations before Project, Brief, DeckVersion, card facts, roles, and analysis exist would recreate the shallow behavior The Workshop is explicitly designed to avoid.

## 16. Sprint 1 Success Statement

Sprint 1 is successful if The Workshop can take one real Commander deck and turn it into a traceable local engineering project.

The final output should not be merely:

“Here is an improved decklist.”

The final output should be:

“Here is the project, the brief, the baseline version, the analysis, the weakness, the recommendation, the decision, the resulting version, and the report explaining why the change happened.”

That is the difference between a deck builder and a Deck Engineering Platform.

## 17. Summary

Sprint 0 created the foundation.

Sprint 1 must prove execution.

The Workshop should now build the smallest local prototype that demonstrates:

- project-first workflow

- context before judgment

- analysis before recommendation

- structured knowledge before AI reasoning

- recommendation before decision

- decision before versioning

- reports as readable engineering artifacts

- user agency preserved

- project history preserved

The sprint should stay narrow.

The goal is not to build everything.

The goal is to make the product loop real.
