# RFC-006 — The Workshop UI & UX

Status: Draft Version: v0.2 Sprint: 0 Depends on: RFC-000 — Product Vision, RFC-001 — System Architecture, RFC-002 — Database / Data Model, RFC-003 — Knowledge Engine, RFC-004 — Reasoning Engine, RFC-005 — Simulation Engine Document Type: Product Experience / UX Architecture Architecture Owner: Software Architect / CTO Product Owner: Product Owner / Domain Expert

## 1. Purpose

This document defines the user experience model for The Workshop.

The goal of RFC-006 is to describe how users interact with The Workshop as a Deck Engineering Platform.

The UI must translate the system modules into usable product surfaces:

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

The Workshop is not a generic deck builder.

It is an engineering studio for Commander decks.

Therefore, the UI should not feel like:

- a card search page

- a chatbot window

- a raw statistics dashboard

- a decklist editor with AI bolted on

- a generic suggestion feed

It should feel like a structured workspace where the user can understand:

- what they are building

- why the deck works

- where it fails

- what options exist

- what each change improves

- what trade-off each change introduces

- what evidence supports a decision

- how the deck evolved over time

The UI should help the user move from:

“Here is my decklist.”

to:

“Here is the system I am engineering, here is what it does well, here is where it fails, and here is the next justified step.”

## 2. UX Thesis

The Workshop UI exists to make deck engineering visible.

The core UX thesis is:

The user should never feel like they are receiving random card suggestions.

They should feel like they are working through an engineering process.

The UI should guide the user through the core product loop:

Project → Brief → Deck Import → Baseline Analysis → Component Understanding → Engine Understanding → Weakness Identification → Recommendation Review → Optional Simulation → Decision → New Version → Report / Backlog

This loop must be visible without becoming bureaucratic.

The UI should be structured enough to create trust, but light enough to preserve flow.

## 3. Core UX Principles

3.1 Project First

The primary object in the UI is the Project.

The user does not simply open a decklist.

The user opens a Project workspace.

A Project contains:

- Design Brief

- current deck version

- deck identity

- components

- engines

- analysis

- recommendations

- simulations

- decisions

- reports

- notes

- backlog

The UI should constantly reinforce that the decklist is only one artifact inside a wider engineering context.

3.2 Context Before Judgment

The UI must not judge a deck before understanding the user’s intent.

The Design Brief should appear early in the project flow.

The user should be able to create a lightweight brief quickly, then enrich it over time.

The UI should support both:

- Quick Brief

- Full Engineering Brief

The goal is not form completion.

The goal is alignment.

3.3 Analysis Before Recommendation

Recommendations should not appear as a generic suggestion feed.

Before showing add/cut proposals, the UI should show:

- what the deck is trying to do

- what the deck currently does

- what engines were detected

- what packages exist

- what weaknesses were found

- what assumptions were made

Only then should the system present recommendations.

This protects The Workshop from becoming a shallow “add these cards” tool.

3.4 Explain Why by Default

Every important UI surface should answer “why?”

A weakness should show:

- what the problem is

- what evidence supports it

- which engine or package it affects

- why it matters under the brief

- what could be done next

A recommendation should show:

- proposed add/cut/change

- problem solved

- expected benefit

- trade-off

- affected engine/package

- confidence

- test suggestion

- decision options

A simulation result should show:

- test question

- deck version tested

- assumptions

- key metric

- failure patterns

- limitations

- interpretation

The UI should never hide reasoning behind a confident final answer.

3.5 Preserve User Agency

The user remains the designer.

The UI must make clear that:

- Recommendations do not modify the deck automatically.

- Simulation does not decide deck quality.

- AI does not dictate the final list.

- Only a Decision can produce a new DeckVersion.

- Rejected, deferred, modified, and accepted recommendations remain part of project history.

The product should feel collaborative, not authoritarian.

3.6 Progressive Disclosure

The Workshop contains a lot of structured information.

The UI must avoid overwhelming the user.

Each surface should show:

- clear summary

- expandable reasoning

- detailed evidence

- raw metadata only when useful

Default view should be readable.

Expanded view should provide engineering detail.

Advanced view may expose structured data, assumptions, metrics, and confidence.

3.7 Make Trade-Offs Visible

The Workshop should not present changes as pure upgrades.

The UI should show trade-offs clearly.

Examples:

- speed vs resilience

- tutors vs variance

- power vs table friendliness

- budget vs efficiency

- protection vs proactive development

- theme density vs interaction density

- explosiveness vs consistency

- originality vs staples

- mana greed vs utility lands

The user should be able to compare options without decoding hidden assumptions.

3.8 Show Evidence, Not False Certainty

The UI should distinguish:

- fact

- interpretation

- hypothesis

- simulation evidence

- accepted decision

- accepted risk

- uncertainty

Simulation results should always show limitations.

Reasoning outputs should show confidence.

AI-suggested knowledge should not look like verified truth.

## 4. Primary Navigation Model

The Workshop should use a Project Workspace layout.

Recommended full navigation:

- Dashboard

- Brief

- Deck

- Components

- Engines

- Reports

- Simulations

- Recommendations

- Decisions

- Versions

- Notes / Backlog

MVP navigation can be simpler:

- Overview

- Brief

- Deck

- Analysis

- Recommendations

- Simulations

- Decisions / Versions

- Notes

The UI should support growth without forcing every surface into MVP.

## 5. Project Dashboard

5.1 Purpose

The Project Dashboard is the home screen of a deck engineering project.

It should answer:

- What is this project?

- What is the deck trying to be?

- What is the current version?

- What is the current engineering state?

- What needs attention next?

- What changed recently?

- What decisions are pending?

The dashboard should be an executive summary for the deck project, not a raw data dump.

5.2 Dashboard Sections

Project Identity

Shows:

- project name

- commander

- format

- bracket / power target

- budget mode

- deck identity statement

- current DeckVersion

- status

Example:

Project: The Myr Singularity Commander: Urtet, Remnant of Memnarch Identity: Artifact combo-control engine disguised as Myr tribal Current Version: v1.4 — Mana Fixing Test Status: Testing

Current Engineering Summary

Shows:

- main engines

- primary win paths

- major strengths

- active weaknesses

- accepted risks

- current recommendation state

Next Best Actions

Shows suggested next steps:

- complete missing brief fields

- review baseline audit

- run simulation

- review pending recommendation

- record decision

- update gameplay notes after testing

Recent Activity

Shows recent project events:

- deck version created

- recommendation proposed

- simulation completed

- decision accepted/rejected

- report generated

- note added

Open Questions

Shows unresolved issues:

- Is the deck paper-budget or online no-budget?

- Are tutors acceptable?

- Is graveyard hate an accepted risk?

- Should the deck optimize for explosiveness or consistency?

5.3 MVP Dashboard

MVP dashboard should include:

- project identity

- current deck version

- brief completion state

- latest analysis summary

- open weaknesses

- pending recommendations

- recent decisions

- next suggested action

## 6. Design Brief UI

6.1 Purpose

The Design Brief defines what “better” means for the project.

The UI must make the brief easy to create, edit, and revisit.

The brief should not feel like bureaucracy.

It should feel like aligning the engineering target.

6.2 Brief Modes

Quick Brief

Used for fast project start:

- format

- commander

- strategy

- bracket / power target

- budget / proxy policy

- desired play pattern

- hard constraints

- success criteria

Full Brief

Used for deeper engineering:

- deck identity

- design philosophy

- meta context

- table experience

- anti-goals

- pet cards

- disliked cards

- tutor tolerance

- combo tolerance

- theme requirements

- originality requirements

- budget ceiling

- paper vs online mode

- accepted risks

- testing goals

6.3 Brief UX Rules

The UI should:

- allow incomplete briefs

- show assumptions when fields are missing

- highlight fields that materially affect recommendations

- distinguish hard constraints from preferences

- allow users to change philosophy over time

- track major brief changes as project events

A missing brief field should not block basic usage.

Serious recommendations should show when assumptions are being made.

## 7. Deck View

7.1 Purpose

The Deck View displays the current DeckVersion.

It should do more than show a list of cards.

It should show the deck as an engineered system.

The Deck View should answer:

- What cards are in this version?

- What role does each card play?

- Which cards are core?

- Which cards are replaceable?

- Which cards are being tested?

- Which cards are linked to decisions?

- Which cards are tied to engines or packages?

- Which cards have project-specific role overrides?

7.2 Deck View Modes

List View

Traditional decklist grouped by:

- commander

- lands

- ramp

- draw

- interaction

- protection

- engines

- payoffs

- win conditions

- flex

- maybeboard

Role View

Groups cards by functional role:

- ramp

- mana fixing

- card draw

- tutor

- removal

- board wipe

- protection

- recursion

- enabler

- payoff

- outlet

- win condition

Package View

Groups cards by package:

- mana base

- ramp package

- draw package

- interaction suite

- protection suite

- combo package

- recursion package

- meta answers

- flex slots

Status View

Groups cards by workflow status:

- core

- replaceable

- testing

- recently added

- recently cut

- accepted risk

- do not cut

- possible cut

- needs review

7.3 Card Panel

Each card should be clickable.

A card panel should show:

- card name

- mana value

- type line

- current role in this project

- default global role

- project-specific override if any

- engine/package membership

- synergies

- risks

- related recommendations

- related decisions

- notes

- status

The UI should clearly distinguish global card knowledge from project-specific meaning.

Example:

Global Role: card draw Project Role: artifact count support / sacrifice fodder Project Note: kept because it supports artifact density and KCI lines

7.4 Deck View MVP

MVP should include:

- current decklist

- card categories

- functional role labels

- project role override

- card status

- link to related recommendation/decision

- simple filters

## 8. Component Map

8.1 Purpose

The Component Map shows the deck as a system of functional parts.

It helps the user understand:

- what packages exist

- what roles are over-supported

- what roles are under-supported

- what cards connect multiple systems

- what packages compete for slots

- where the deck is structurally fragile

This surface is one of the clearest ways The Workshop differs from normal deck builders.

8.2 Component Groups

Example component groups:

- Mana Development

- Card Access

- Interaction

- Protection

- Main Engine

- Secondary Engine

- Win Conditions

- Recovery

- Meta Answers

- Flex Slots

Each group can show:

- member cards

- target density

- actual density

- health status

- related weaknesses

- related recommendations

8.3 Component Health

Each component may show a status:

- strong

- acceptable

- under-supported

- over-supported

- fragile

- untested

- accepted risk

- needs review

Example:

Protection Suite Status: Under-supported Evidence: 3 protection pieces detected; project is commander-centric and artifact-hate meta is expected. Suggested Next Step: Review protection package before adding more payoffs.

8.4 Component Map MVP

MVP can start as a structured component board.

It does not need to be a graph at first.

MVP should include:

- package cards grouped visually

- role density summary

- weak/strong labels

- links to reports and recommendations

## 9. Engine View

9.1 Purpose

The Engine View shows the deck’s main engines.

The Workshop should reason about engines before individual cards.

The Engine View should answer:

- What are the deck’s engines?

- What does each engine consume?

- What does each engine produce?

- What cards are core?

- What cards are support?

- What are the payoffs?

- What are the missing pieces?

- How fragile is the engine?

- How fast is the engine?

- How important is it to deck identity?

9.2 Engine Layout

Each engine should display:

- name

- description

- engine type

- role in deck identity

- input resources

- output resources

- enablers

- fuel

- converters

- payoffs

- outlets

- redundancy pieces

- protection pieces

- recovery pieces

- finishers

- missing pieces

- failure modes

Example:

Engine: Artifact Sacrifice Mana Engine Input: artifact bodies, Myr tokens Converter: Krark-Clan Ironworks, Ashnod’s Altar Output: mana, explosive turns, combo access Payoffs: large artifact turns, combo finishers Failure Modes: artifact hate, low artifact fuel, payoff without outlet Identity Role: Core

9.3 Engine Evaluation

Each engine may be evaluated on:

- density

- access

- redundancy

- setup cost

- payoff quality

- protection

- recovery

- speed

- fragility

- identity fit

- constraint fit

These should be shown as readable labels, not only numeric scores.

Example:

Access: Medium Fragility: High Identity Fit: Core Recommendation: Increase protection before adding another payoff.

9.4 Engine View MVP

MVP should include:

- detected engine list

- core/support/payoff card groups

- missing pieces

- fragility notes

- links to simulation questions

- links to recommendations

## 10. Analysis Reports UI

10.1 Purpose

Analysis Reports explain what the deck currently is.

They should not be raw technical dumps.

They should make the deck understandable.

Reports may include:

- baseline deck audit

- mana report

- curve report

- color report

- engine report

- package report

- weakness report

- protection report

- interaction report

- win condition report

10.2 Report Structure

Each report should include:

- Summary

- Key Findings

- Evidence

- Affected Components

- Assumptions

- Confidence

- Weaknesses

- Suggested Next Steps

Example:

Finding: The deck may have a white source consistency issue. Evidence: White-intensive spells are present, but white source density appears below target. Affected Package: Mana Base Suggested Test: Run color availability by turn six. Confidence: Medium

10.3 Report UX Rules

Reports should:

- explain findings in plain language

- link to affected cards

- link to affected engines/packages

- distinguish issue from accepted risk

- show assumptions

- show confidence

- suggest next action

- avoid overwhelming the user with raw metrics first

10.4 Report MVP

MVP should support Markdown-style reports with structured metadata.

This is enough for:

- deck audit

- mana report

- engine report

- recommendation report

- simulation report

- changelog

- primer

## 11. Simulation Results UI

11.1 Purpose

Simulation Results show evidence from tests.

They should help the user decide whether a hypothesis survived testing.

They should not pretend to perfectly predict Commander gameplay.

A simulation result should answer:

- What was tested?

- Why was it tested?

- Which DeckVersion was tested?

- What assumptions were used?

- What happened?

- What failed most often?

- What are the limitations?

- What decision does this evidence support?

11.2 Simulation Result Card

Each SimulationResult should show:

- simulation type

- test question

- target DeckVersion

- iterations

- mulligan policy

- key metric

- failure patterns

- confidence

- limitations

- linked hypothesis

- linked recommendation

- linked decision if any

Example:

Test Question: How often does the deck produce double-white by turn six? DeckVersion: v1.3 Result: 58% success rate Main Failure Pattern: Only one white source found by target turn Limitations: Does not model tutors or opponent interaction Suggested Interpretation: Supports the hypothesis that white-intensive spells are difficult to cast in this version.

11.3 Comparison View

The UI should support comparing simulations across versions.

Example:

Metric: Double-white by turn six

- v1.2 Baseline: 58%

- v1.3 Mana Base Test: 77%

- Delta: +19 percentage points

Interpretation:

The mana base change materially improves the tested problem, but may still be below the target if the success threshold is 80%.

11.4 Simulation UX Rules

Simulation UI must always show:

- test question

- assumptions

- limitations

- deck version

- interpretation status

The UI must avoid vague claims like:

“This deck wins 63% of the time.”

Preferred:

“Under simplified goldfish assumptions, this version accesses a minimum engine configuration by turn four in 63% of runs.”

11.5 Simulation MVP

MVP should support result cards for:

- opening hand

- land drops

- color availability

- mana consistency

- ramp access

- engine access

- mulligan quality

- basic goldfish Level 1 / Level 2

- version comparison

## 12. Recommendation Review UI

12.1 Purpose

Recommendation Review is where proposed changes become user decisions.

This is a critical UX surface.

The UI must make clear that a recommendation is a proposal, not an automatic deck change.

A recommendation should be:

- reviewable

- explainable

- modifiable

- rejectable

- testable

- traceable

12.2 Recommendation Card

A Recommendation card should include:

- title

- status

- problem solved

- proposed changes

- affected engine/package

- expected benefit

- trade-off

- risks

- confidence

- evidence

- assumptions

- alternatives considered

- suggested test

- decision actions

Example:

Recommendation: Improve five-color fixing Problem: White-intensive spells are difficult to cast on time.

Proposed Changes:

- Cut utility land A

- Cut utility land B

- Add City of Brass

- Add Mana Confluence

Expected Benefit: Better access to required colors by midgame. Trade-Off: Lower utility land density and possible budget increase. Suggested Test: Run color availability comparison before accepting.

12.3 Recommendation Actions

The UI should support:

- Accept

- Reject

- Modify

- Defer

- Test First

- Accept as Experiment

- Mark as Accepted Risk

- Convert to Backlog Item

- Ask for Alternatives

Each action should create or update project history.

12.4 Recommendation Statuses

Recommended statuses:

- proposed

- under review

- needs clarification

- needs analysis

- needs simulation

- testing

- accepted

- rejected

- modified

- deferred

- superseded

12.5 Add/Cut Review

For add/cut recommendations, the UI should show proposed changes as structured rows:

- Add Card X

- Cut Card Y

- Reason

- Affected role

- Affected package

- Risk

- User action

The user should be able to accept a recommendation partially.

Example:

Accept:

- Add City of Brass

- Add Mana Confluence

Reject:

- Cut Darksteel Citadel

Modify:

- Cut different land instead

Partial acceptance should create a Decision of type “modify.”

12.6 Recommendation MVP

MVP should include:

- recommendation cards

- add/cut list

- rationale

- trade-offs

- confidence

- status

- accept/reject/defer/test-first actions

- decision creation

## 13. Decision Log UI

13.1 Purpose

The Decision Log is the engineering memory of a Project.

It should answer:

- What did we change?

- Why did we change it?

- What problem was it meant to solve?

- What evidence supported it?

- What risk did we accept?

- What version resulted?

- Did it work?

- Should we revisit it?

Normal deckbuilders show the current list.

The Workshop shows how the list got there.

13.2 Decision Entry

A Decision entry should include:

- decision type

- title

- source recommendation

- source DeckVersion

- resulting DeckVersion

- accepted changes

- rejected changes

- rationale

- evidence links

- expected outcome

- risk accepted

- user comment

- revisit trigger

- created timestamp

Example:

Decision: Accept as Experiment Title: Test Rainbow Mana Base Source Version: v1.2 Resulting Version: v1.3 Reason: Organic Extinction and other white-intensive spells were repeatedly stranded. Evidence: Color availability concern from mana report. Risk Accepted: Reduced utility land density. Revisit Trigger: If real games still show color issues after 10 games.

13.3 Decision Filters

The UI should allow filtering by:

- accepted

- rejected

- deferred

- modified

- test first

- reverted

- accepted risk

- related card

- related engine

- related package

- related DeckVersion

13.4 Accepted Risk UI

Accepted risk should be visible but not noisy.

Example:

Accepted Risk: Low graveyard hate Reason: Current meta does not require dedicated graveyard hate. Revisit if: Meta shifts toward graveyard decks or repeated losses occur.

The system should not repeatedly flag accepted risks as unresolved unless conditions change.

13.5 Decision Log MVP

MVP should include:

- chronological decision list

- decision detail card/page

- links to recommendation

- links to resulting version

- rationale

- accepted/rejected changes

- accepted risk marker

## 14. Version History UI

14.1 Purpose

Version History shows how the deck evolved.

It should answer:

- What did each version contain?

- Why was each version created?

- What changed from the previous version?

- Which decision produced it?

- What simulations or reports were attached?

- Can the user compare or revert?

14.2 Version Entry

Each DeckVersion should show:

- version number

- label

- status

- parent version

- change summary

- created timestamp

- source decision

- card changes

- attached reports

- attached simulations

- notes

Example:

v1.4 — Protection Test Parent: v1.3 Status: Test Candidate Changes: +2 protection pieces, -2 flex payoffs Source Decision: Accept Protection Package as Experiment Attached Simulation: Engine access comparison Current Result: Under testing

14.3 Version Comparison

The UI should support comparing two versions.

Comparison should show:

- added cards

- removed cards

- role density changes

- package density changes

- mana changes

- simulation deltas

- decision rationale

14.4 Revert UX

Reverting should not delete history.

The UI should create a new DeckVersion based on a previous version.

Example:

v1.6 — Revert Tezzeret Package

This preserves:

- the original experiment

- the failed result

- the decision to revert

- the new state

14.5 Version MVP

MVP should include:

- version list

- version detail

- simple diff

- resulting decision link

- current version marker

- revert-as-new-version action

## 15. Notes and Backlog UI

15.1 Purpose

Not everything belongs in a formal report or decision.

The Notes and Backlog surfaces allow the user to capture informal thoughts, future tests, gameplay observations, and unresolved ideas.

15.2 Notes

Notes may attach to:

- project

- deck version

- card

- recommendation

- decision

- simulation

- report

Examples:

- “Organic Extinction stranded in hand twice.”

- “Table is heavy on artifact hate lately.”

- “Do not cut this pet card unless we fully rebuild the deck.”

- “This card felt dead in three games.”

- “Try more protection before adding more payoffs.”

Notes should be lightweight but linkable.

15.3 Backlog

Backlog items represent future work.

Examples:

- Test mana base after 10 games.

- Review graveyard hate package.

- Find budget replacement for Mox Opal.

- Compare tutor package vs redundancy package.

- Write primer after list stabilizes.

- Revisit accepted risk if meta changes.

Backlog statuses:

- open

- in progress

- blocked

- done

- dismissed

15.4 Notes / Backlog MVP

MVP should include:

- project notes

- card notes

- recommendation notes

- backlog items

- status

- priority

- related cards / recommendations / weaknesses

## 16. Main User Flows

16.1 New Project Flow

- User creates a Project.

- User enters commander and format.

- User imports or pastes decklist.

- User completes Quick Brief.

- System parses decklist.

- System creates baseline DeckVersion.

- System loads card facts and basic knowledge.

- System generates baseline analysis.

- User reviews deck identity and assumptions.

- System suggests first engineering steps.

UX goal:

The user should reach a useful project dashboard quickly.

16.2 Deck Audit Flow

- User opens Project.

- User selects current DeckVersion.

- User runs or opens baseline analysis.

- UI shows deck identity, components, engines, packages, weaknesses.

- User expands findings that matter.

- User chooses next step:

- review recommendation

- run simulation

- mark accepted risk

- add note

- create backlog item

UX goal:

The user should understand the deck better before changing it.

16.3 Recommendation Flow

- User selects weakness or asks for improvement.

- System frames the problem.

- System proposes solution direction.

- System generates recommendation.

- UI shows add/cut/change proposal.

- User reviews benefit, trade-off, risk, confidence.

- User chooses:

- accept

- reject

- modify

- defer

- test first

- Decision is recorded.

- New DeckVersion is created only if needed.

UX goal:

The user should understand the recommendation and remain in control.

16.4 Simulation Flow

- User or system identifies hypothesis.

- UI creates Simulation Question.

- User selects DeckVersion and configuration.

- Simulation runs.

- Result is shown with metrics, failure patterns, and limitations.

- Reasoning interpretation is attached.

- User can connect result to:

- recommendation

- decision

- report

- backlog item

UX goal:

Simulation should feel like evidence, not magic.

16.5 Decision Flow

- User reviews recommendation, report, or simulation.

- UI asks what decision to record.

- User chooses decision type.

- User can add comment.

- System records rationale, evidence, accepted/rejected changes.

- New DeckVersion is created if the decision changes deck state.

- Dashboard updates.

UX goal:

The project should remember why the deck changed.

16.6 Version Review Flow

- User opens Version History.

- User compares current version with previous version.

- UI shows changes and reasons.

- User reviews attached decisions and evidence.

- User may:

- keep current version

- revert as new version

- branch

- mark experiment successful

- mark experiment failed

UX goal:

The user should never lose track of how the deck evolved.

## 17. Information Hierarchy

The UI should follow this hierarchy:

- Summary

- Why it matters

- Evidence

- Trade-off

- Action

- Details

Example:

Summary: The mana base may not support white-intensive spells.

Why it matters: The deck wants to cast Organic Extinction in the midgame.

Evidence: Gameplay note and color source analysis indicate low double-white availability.

Trade-off: Improving fixing may require cutting utility lands.

Action: Run color availability simulation or review mana base recommendation.

Details: Source counts, affected cards, assumptions, confidence.

## 18. Visual Language

The Workshop should feel like an engineering studio.

Recommended visual tone:

- calm

- structured

- readable

- professional

- slightly tactical

- not sterile

Avoid:

- casino-style score explosions

- fake deck power ratings

- excessive badges

- unexplained AI confidence meters

- generic “best card” rankings

- cluttered dashboards

Use visual labels for:

- core

- testing

- replaceable

- accepted risk

- needs review

- under-supported

- over-supported

- fragile

- strong

- untested

## 19. Confidence and Status Display

The UI should show confidence without overwhelming the user.

Recommended confidence values:

- Certain

- High

- Medium

- Low

- Unknown

- Disputed

Confidence should appear on:

- card knowledge

- analysis findings

- reasoning hypotheses

- recommendations

- simulation interpretation

Status should appear on:

- recommendations

- decisions

- simulations

- reports

- weaknesses

- backlog items

- deck versions

The UI should make uncertainty normal and trustworthy.

## 20. AI Interaction Model

The AI should appear as an engineering consultant inside the UI.

It should not be the whole product interface.

Recommended AI interaction surfaces:

- Ask about this project

- Explain this weakness

- Compare these options

- Why was this recommended?

- What should I test next?

- Summarize this version

- Turn this into a report

- Draft a primer

- Review this decision

- Suggest next engineering step

The AI should operate over the current Project context.

It should not behave like a generic chat detached from the workspace.

## 21. MVP UI Scope

The MVP UI should prove the core product loop.

It does not need every advanced visualization.

21.1 MVP Must Include

- Project Dashboard

- Quick Design Brief

- Deck Import / Deck View

- Basic role/category display

- Baseline Analysis Report

- Weakness list

- Recommendation Review

- Decision Log

- Version History

- Simulation Result display

- Notes / Backlog

- Markdown report rendering

21.2 MVP Can Be Simple

The MVP may use:

- tables

- cards

- accordions

- markdown reports

- simple filters

- structured panels

- basic comparison views

It does not require:

- complex graph visualization

- drag-and-drop deckbuilding

- full SaaS navigation polish

- real-time collaboration

- advanced animations

- perfect mobile UX

- public profile pages

- social features

21.3 MVP Success Criteria

The MVP UI is successful if a user can:

- Create a project.

- Define a lightweight brief.

- Import a decklist.

- Understand the deck’s components and engines.

- Review analysis findings.

- See weaknesses in context.

- Review recommendations with trade-offs.

- Run or inspect a simulation result.

- Accept/reject/modify a recommendation.

- Create a new deck version.

- Understand why the deck changed.

- Generate or read a useful report.

## 22. Future UI Extensions

Future versions may include:

22.1 Graph Component Map

A visual graph of:

- engines

- packages

- cards

- synergies

- dependencies

- failure points

22.2 Branching Version Tree

Support for:

- paper branch

- online no-budget branch

- high-power branch

- budget branch

- experimental branch

22.3 Advanced Simulation Dashboards

Charts for:

- opening hand quality

- color availability

- land drops

- engine access

- goldfish setup turns

- version deltas

22.4 Recommendation Comparison Matrix

Compare options by:

- benefit

- trade-off

- budget

- identity fit

- power impact

- simulation need

- confidence

22.5 Primer Builder

Generate user-facing deck primers from:

- project identity

- engine view

- win conditions

- play patterns

- accepted decisions

- final deck version

22.6 Collection-Aware UI

Future support for:

- owned cards

- missing cards

- acquisition status

- proxy policy

- paper vs online versions

- budget upgrade paths

22.7 Collaboration

Possible future support:

- shared project review

- comments

- external reviewer notes

- approval states

- playgroup feedback

## 23. Open Questions

- Should the MVP UI be local-first, file-based, or web-based?

- Should the first prototype prioritize dashboard/report UX or deck editing UX?

- Should the Project Dashboard be the default landing surface or the Deck View?

- How much of the Design Brief should be required before baseline analysis?

- Should the UI expose reasoning JSON or only readable summaries?

- How should confidence be displayed without making the product feel over-engineered?

- Should simulations be launched from the Simulation tab, Recommendation Review, or both?

- Should accepted risks appear on the Dashboard or only in the Decision Log?

- Should rejected recommendations remain visible by default?

- Should version branching exist in MVP or wait until later?

- Should the Component Map start as cards/tables before becoming a graph?

- Should card search exist inside MVP, or should MVP focus on project review?

- How much deck editing should the MVP support directly?

- Should reports be editable after generation or immutable snapshots?

- Should the AI chat be global, project-scoped, or surface-specific?

- Should the user be able to manually override roles and packages in the UI?

- How should project-specific overrides be displayed without confusing users?

- Should the MVP support mobile, or focus on desktop/tablet first?

- How should the UI distinguish “recommendation” from “decision” visually?

- Should the UI support lightweight casual mode and advanced engineering mode?

## 24. ADR Candidates

ADR-046 — Project Workspace Is the Primary UI Root

Decision: The UI is organized around Projects, not decklists.

Reason: The Workshop stores context, reasoning, decisions, versions, reports, and simulations. A decklist alone is not the product root.

ADR-047 — Design Brief Appears Before Serious Analysis

Decision: The UI should ask for a lightweight Design Brief before serious analysis and recommendation.

Reason: The system needs project intent before judging whether a change is good.

ADR-048 — Recommendations Are Reviewable Proposals

Decision: Recommendations are presented as reviewable proposals, not automatic deck edits.

Reason: The user remains the designer, and only Decisions produce new DeckVersions.

ADR-049 — Decision Log Is a First-Class UI Surface

Decision: The Decision Log must be visible as a primary project surface.

Reason: The Workshop’s value depends on preserving why the deck changed, not only what changed.

ADR-050 — Simulation Results Must Show Assumptions and Limitations

Decision: Simulation UI must show test question, assumptions, deck version, metrics, failure patterns, and limitations.

Reason: Simulation is evidence, not judgment, and simplified results can create false confidence if shown without context.

ADR-051 — Component Map Starts Simple

Decision: The MVP Component Map may start as structured cards/tables rather than a graph visualization.

Reason: The value is in making deck structure visible. Advanced graph UI can wait.

ADR-052 — Engine View Is a Core Product Surface

Decision: The UI should expose detected engines as a first-class surface.

Reason: The Workshop reasons about engines before individual cards, so users need to see engines clearly.

ADR-053 — UI Uses Progressive Disclosure

Decision: The UI should show summaries first, then expandable reasoning and details.

Reason: The system contains complex data, but the user experience must remain readable and usable.

ADR-054 — Accepted Risk Is Visible but Not Noisy

Decision: Accepted risks should remain visible in the project but should not repeatedly appear as unresolved warnings unless conditions change.

Reason: Some weaknesses are intentional trade-offs and part of the deck’s engineering history.

ADR-055 — Reports Are Human-Readable Artifacts

Decision: Reports should render as readable Markdown-style documents with structured metadata behind them.

Reason: Reports are meant to help users understand the deck, not merely inspect system output.

## 25. Foundational UX Principle

The Workshop UI should not ask:

“What card do you want to add?”

It should ask:

“What system are you building, what is it trying to do, what is currently failing, what evidence do we have, what trade-off are you willing to accept, and what decision should we record?”

The decklist is the output.

The reasoning is the product.

The UI is the workshop where that reasoning becomes usable.
