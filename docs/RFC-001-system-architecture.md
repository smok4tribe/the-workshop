# RFC-001 — The Workshop System Architecture

Status: Draft

Sprint: 0

Depends on: RFC-000 — Product Vision

Document Type: Architecture

Architecture Owner: Software Architect / CTO

## 1. Purpose

Define the first system architecture for The Workshop.

This document translates the Product Vision into a concrete technical model:

- core modules

- system boundaries

- data ownership

- reasoning flow

- knowledge flow

- simulation flow

- project lifecycle

- implementation phases

The goal is not to over-engineer.

The goal is to create a stable architecture that can grow without becoming chaotic.

## 2. Architectural Thesis

The Workshop is not a chatbot with deckbuilding features.

The Workshop is a structured deck engineering system with an AI reasoning layer on top.

Therefore, the architecture must separate:

- product context

- structured card knowledge

- deck/project data

- reasoning logic

- simulation logic

- user interface

- documentation/history

The AI must not be the database.

The AI must not be the rules engine.

The AI must not be the source of truth.

The AI reasons over structured knowledge, project context, and simulation evidence.

## 3. Core Architectural Principle

Knowledge first.

Reasoning second.

Recommendation third.

The system flow should be:

User Input

→ Project Context

→ Structured Knowledge Retrieval

→ Deck Analysis

→ Hypothesis Generation

→ Simulation / Validation

→ Recommendation

→ Versioned Decision

The Workshop should never jump directly from user input to card suggestion unless the task is explicitly lightweight.

## 4. Core System Modules

The first architecture is divided into the following modules:

## 1. Project Workspace

## 2. Card Knowledge Base

## 3. Deck Parser

## 4. Deck Analysis Engine

## 5. Reasoning Engine

## 6. Simulation Engine

## 7. Recommendation Engine

## 8. Versioning & Decision Log

## 9. Reporting Engine

## 10. User Interface

Each module has a clear responsibility.

No module should become a dumping ground.

## 5. Module Responsibilities

### 5.1 Project Workspace

The Project Workspace is the main unit of work.

It stores:

- Design Brief

- decklist

- commander

- format

- budget

- bracket / power target

- meta assumptions

- user constraints

- notes

- reports

- versions

- decisions

- test results

A decklist is not the product root.

A Project is the product root.

### 5.2 Card Knowledge Base

The Card Knowledge Base stores structured card information.

It includes:

- card name

- oracle text

- mana cost

- mana value

- color identity

- type line

- legalities

- formats

- prices

- printings

- rulings

- functional tags

- synergy tags

- combo relationships

- role classifications

This module exists to prevent hallucinated card knowledge.

The system should reason from inspectable data whenever possible.

### 5.3 Deck Parser

The Deck Parser converts raw decklists into structured data.

It should support sources such as:

- pasted text

- Moxfield export

- Archidekt export

- future API/import integrations

The parser identifies:

- commander

- main deck

- sideboard / maybeboard when available

- categories if provided

- card counts

- format legality issues

- missing or unknown cards

The parser should not analyze the deck deeply.

Its job is to normalize input.

### 5.4 Deck Analysis Engine

The Deck Analysis Engine explains what the deck currently is.

It identifies:

- mana curve

- color requirements

- land count

- ramp density

- draw density

- interaction density

- protection density

- win conditions

- engines

- packages

- combo lines

- redundant effects

- unsupported cards

- structural weaknesses

This module answers:

“What is happening inside this deck?”

It must run before serious recommendations.

### 5.5 Reasoning Engine

The Reasoning Engine interprets the deck through the Design Brief.

It compares:

- what the deck is trying to be

- what the deck currently does

- where the deck fails

- what trade-offs are acceptable

- what changes align with the user’s philosophy

The Reasoning Engine is where AI is most useful.

It should:

- ask clarifying questions when needed

- make assumptions explicit

- explain trade-offs

- challenge weak assumptions

- propose engineering hypotheses

The Reasoning Engine does not own card facts.

It consumes facts from the Knowledge Base.

### 5.6 Simulation Engine

The Simulation Engine produces evidence.

Early simulation may include:

- opening hand tests

- land drop probability

- color availability

- ramp availability

- key engine access

- goldfish speed

- mulligan quality

- win-condition access

- failure pattern detection

The Simulation Engine does not need to perfectly simulate Commander.

Its purpose is to test specific hypotheses.

Example:

“Does adding two rainbow lands materially improve the chance of casting Organic Extinction?”

That is a valid simulation question.

### 5.7 Recommendation Engine

The Recommendation Engine proposes changes.

A recommendation should include:

- proposed add

- proposed cut

- reason

- affected engine/package

- expected benefit

- trade-off

- confidence level

- test suggestion

Recommendations should be generated only after context, analysis, and reasoning.

A recommendation is not just:

“Add Card X.”

It should be:

“Add Card X because it improves Y, supports Z, and trades off W.”

### 5.8 Versioning & Decision Log

Every meaningful change should be traceable.

The system should track:

- deck version

- date

- changes

- hypothesis

- reason

- expected outcome

- test result

- final decision

The user should be able to answer:

- Why did I add this card?

- What did I cut for it?

- Did the change work?

- Should I revert it?

- What was I trying to solve?

### 5.9 Reporting Engine

The Reporting Engine generates human-readable outputs.

Possible reports:

- deck audit

- mana report

- consistency report

- engine report

- weakness report

- recommendation report

- version changelog

- primer

- play pattern guide

- goldfish report

Reports should be readable, not just technical dumps.

The goal is to make the user understand the deck better.

### 5.10 User Interface

The UI should feel like an engineering studio.

Core surfaces:

- Project Dashboard

- Design Brief

- Decklist View

- Component Map

- Engine View

- Analysis Reports

- Simulation Results

- Recommendation Review

- Version History

- Decision Log

- Notes / Backlog

The UI should help the user think clearly.

It should not bury them under raw data.

## 6. High-Level System Flow

### 6.1 New Project Flow

1. User creates a Project.

2. User imports or pastes a decklist.

3. User defines a lightweight Design Brief.

4. System parses the decklist.

5. System loads card data.

6. System performs baseline analysis.

7. System identifies deck identity, engines, and weaknesses.

8. User reviews or corrects assumptions.

9. System proposes next engineering steps.

### 6.2 Deck Audit Flow

1. Load Project.

2. Read Design Brief.

3. Read current decklist.

4. Retrieve structured card knowledge.

5. Analyze deck components.

6. Identify structural weaknesses.

7. Generate findings.

8. Suggest possible hypotheses.

9. Recommend changes only when justified.

### 6.3 Recommendation Flow

1. Identify problem.

2. Define objective.

3. Generate candidate solutions.

4. Check candidates against brief.

5. Compare trade-offs.

6. Suggest add/cut pairs.

7. Record recommendation rationale.

8. Optionally run simulation.

9. Save accepted decision.

### 6.4 Simulation Flow

1. Define test question.

2. Select deck version.

3. Select simulation type.

4. Run test.

5. Collect results.

6. Interpret results against the brief.

7. Attach evidence to decision log.

## 7. Data Ownership Boundaries

### Project Data

Owned by: Project Workspace

Includes:

- brief

- decklist

- versions

- decisions

- notes

- reports

- simulation results

### Card Data

Owned by: Card Knowledge Base

Includes:

- oracle text

- legality

- card metadata

- prices

- tags

- rulings

- combos

### Analysis Data

Owned by: Deck Analysis Engine

Includes:

- computed metrics

- role counts

- curve

- density analysis

- package detection

### Reasoning Data

Owned by: Reasoning Engine

Includes:

- assumptions

- hypotheses

- trade-off analysis

- recommendation rationale

### Simulation Data

Owned by: Simulation Engine

Includes:

- test configuration

- run results

- probability outputs

- observed failure patterns

## 8. AI Boundary

The AI is allowed to:

- interpret user intent

- summarize deck identity

- reason about trade-offs

- explain recommendations

- generate reports

- ask clarifying questions

- propose hypotheses

- document decisions

The AI is not allowed to be the only source for:

- oracle text

- legality

- prices

- exact card rules

- simulation results

- stored project history

- accepted decisions

When the AI lacks reliable data, it must expose uncertainty.

## 9. Minimum Viable Architecture

The first useful version of The Workshop does not need every module fully automated.

A practical MVP architecture could include:

## 1. Manual Project creation

## 2. Decklist parser

## 3. Local card database

## 4. Basic tagging system

## 5. Deck analysis reports

## 6. AI-assisted reasoning

## 7. Manual recommendation review

## 8. Version notes

## 9. Basic goldfish scripts

## 10. Markdown/JSON project storage

The MVP should prove the product loop before building a complex application.

The core product loop is:

Brief → Analyze → Recommend → Test → Decide → Version

## 10. Implementation Phases

### Phase 0 — Documentation Foundation

Goal:

Define product, architecture, data model, and engineering principles.

Outputs:

- RFC-000 Product Vision

- RFC-001 Architecture

- RFC-002 Database

- RFC-003 Knowledge Engine

- RFC-004 Reasoning Engine

- RFC-005 Simulation Engine

### Phase 1 — Local Prototype

Goal:

Create a local working system that can parse decks and generate structured reports.

Includes:

- project folders

- decklist import

- card database import

- basic analysis scripts

- markdown reports

- version notes

### Phase 2 — Knowledge Engine

Goal:

Build a structured card knowledge layer.

Includes:

- card metadata

- role tags

- synergy tags

- functional tags

- combo relationships

- ruling references

- price data where possible

### Phase 3 — Reasoning Layer

Goal:

Connect AI reasoning to structured project and card knowledge.

Includes:

- project-aware prompts

- context retrieval

- structured analysis templates

- recommendation templates

- uncertainty handling

### Phase 4 — Simulation Layer

Goal:

Add evidence-based testing.

Includes:

- opening hand simulation

- mana consistency

- goldfish testing

- engine access probability

- hypothesis testing

### Phase 5 — UI Layer

Goal:

Create the user-facing engineering studio.

Includes:

- dashboard

- deck view

- brief editor

- analysis reports

- simulation results

- recommendation review

- version history

## 11. Architectural Non-Goals

The architecture should not initially optimize for:

- full gameplay simulation

- real-time multiplayer testing

- automatic deck generation

- complete replacement of human judgment

- perfect Commander rule modeling

- immediate full SaaS complexity

- social networking features

- marketplace features

Those may become future expansions.

They are not needed to prove the core product.

## 12. Key Architecture Decisions To Formalize

The following decisions should become ADRs:

- ADR-001: Projects are the root entity, not decklists.

- ADR-002: AI is a reasoning layer, not the source of truth.

- ADR-003: Card knowledge must be structured and inspectable.

- ADR-004: Recommendations require context and explanation.

- ADR-005: Simulation is evidence for hypotheses, not a perfect game model.

- ADR-006: Versioning is required for meaningful deck engineering.

- ADR-007: Markdown/JSON may be used for the first local prototype before database complexity.

- ADR-008: The system separates analysis from recommendation.

## 13. Open Questions

- Should the first prototype be local-first or web-first?

- Should Project storage begin as file-based Markdown/JSON or immediately as a database?

- Which card source should be canonical for the local card database?

- How should user-defined tags interact with global system tags?

- How much of the Design Brief is required before analysis?

- Should simulation be implemented before UI?

- Should the first product experience target power users only?

- How should deck identity be represented in data?

- How should confidence levels be calculated or expressed?

- How should accepted and rejected recommendations be stored?

## 14. Foundational Architecture Principle

The Workshop architecture exists to protect the product philosophy.

The system must make it difficult to produce shallow recommendations.

The architecture should force the correct sequence:

Context before analysis.

Analysis before recommendation.

Evidence before optimization.

Decision before versioning.

Reasoning before output.

The Workshop is not built around card suggestions.

It is built around deck understanding.
