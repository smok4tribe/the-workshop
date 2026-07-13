# RFC-002 — The Workshop Database / Data Model

Status: Draft Version: v0.2 Sprint: 0 Depends on: RFC-000 — Product Vision, RFC-001 — System Architecture Document Type: Data Model / Architecture Architecture Owner: Software Architect / CTO Product Owner: Product Owner / Domain Expert

## 1. Purpose

This document defines the conceptual and logical data model for The Workshop.

The goal is not to choose a final database technology.

The goal is to define the persistent model required to support The Workshop as a Deck Engineering Platform.

The Workshop must not only store decklists.

It must store:

- context

- intent

- constraints

- deck structure

- card knowledge

- analysis

- hypotheses

- recommendations

- simulations

- decisions

- reports

- versions

- reasoning history

The data model must support the core engineering loop:

Brief → Analyze → Recommend → Test → Decide → Version

The model must answer:

- What is the user trying to build?

- What does the current deck actually do?

- What problems were found?

- What changes were recommended?

- Why were those changes recommended?

- What tests were run?

- What decision did the user make?

- What deck version resulted?

- Can the user understand and reverse the process later?

## 2. Data Model Thesis

The Workshop is not organized around cards.

The Workshop is not organized around decklists.

The Workshop is organized around Projects.

A Project represents the full engineering workspace around a deckbuilding effort.

A decklist is only one artifact inside a Project.

Therefore:

Project is the root entity of The Workshop.

The model must enforce the product philosophy:

- Context before analysis.

- Analysis before recommendation.

- Evidence before optimization.

- Decision before versioning.

- Reasoning before output.

A recommendation should not exist as a naked card suggestion.

A decision should not exist without rationale.

A simulation should not exist without a specific deck version.

A report should not float without knowing what project state generated it.

The database exists to preserve engineering accountability.

## 3. Core Data Domains

The data model is divided into six ownership domains.

Project Data

Card Data

Knowledge Data

Analysis Data

Recommendation / Reasoning Data

Simulation Data

These domains should remain conceptually separate even if the MVP stores some of them in simple files or JSON.

## 4. Root Model

4.1 Root Entity

The root entity is:

Project

A Project owns or references every meaningful artifact in the workspace.

Project

├── DesignBrief

├── UserConstraints

├── Deck

│ └── DeckVersions

│ └── DeckCards

├── AnalysisReports

├── Recommendations

├── Decisions

├── SimulationRuns

├── Reports

├── Notes

└── BacklogItems

4.2 Project vs Deck vs DeckVersion

These three entities must not be collapsed.

Project

The full engineering workspace.

It contains:

- brief

- deck

- versions

- notes

- analysis

- recommendations

- simulations

- decisions

- reports

- backlog

The Project answers:

“What are we trying to engineer?”

Deck

The conceptual deck inside the Project.

Usually one Project has one Deck in the MVP.

The Deck answers:

“What deck concept belongs to this Project?”

DeckVersion

An immutable snapshot of the decklist at a point in time.

The DeckVersion answers:

“What exactly did the deck look like at this moment?”

## 5. MVP Entity Map

This is the practical v0.2 entity map.

| Entity | Domain | Required for MVP | Persistent | Versioned | Notes |
| --- | --- | --- | --- | --- | --- |
| Project | Project Data | Yes | Yes | No | Root entity |
| DesignBrief | Project Data | Yes | Yes | Soft | Defines what “better” means |
| UserConstraint | Project Data | Yes | Yes | Soft | Budget, meta, philosophy, restrictions |
| Deck | Project Data | Yes | Yes | No | Conceptual deck |
| DeckVersion | Project Data | Yes | Yes | Yes | Immutable deck snapshot |
| DeckCard | Project Data | Yes | Yes | Through DeckVersion | Card inside a specific version |
| Card | Card Data | Yes | Yes | External refresh | Canonical card identity |
| CardPrinting | Card Data | Partial | Yes | External refresh | Can be lightweight in MVP |
| CardKnowledge | Knowledge Data | Yes | Yes | Later | Functional interpretation |
| Tag | Knowledge Data | Yes | Yes | No | Lightweight classification |
| FunctionalRole | Knowledge Data | Yes | Yes | No | More structured than tag |
| Synergy | Knowledge Data | Partial | Yes/JSON | Later | Can start semi-structured |
| Combo | Knowledge Data | Partial | Yes/JSON | Later | Can start semi-structured |
| EngineInstance | Analysis Data | Yes | Yes if reported | Per DeckVersion | Detected engine in a version |
| PackageInstance | Analysis Data | Yes | Yes if reported | Per DeckVersion | Detected package in a version |
| Weakness | Analysis Data | Yes | Yes | Per DeckVersion | Structural problem |
| AnalysisReport | Analysis Data | Yes | Yes | Per DeckVersion | Snapshot analysis |
| Recommendation | Recommendation Data | Yes | Yes | Status-tracked | Engineering proposal |
| RecommendationChange | Recommendation Data | Yes | Yes | No | Add/cut/move/change |
| Decision | Project Data | Yes | Yes | No | User/system decision record |
| SimulationRun | Simulation Data | Yes | Yes if saved | Per DeckVersion | Test configuration |
| SimulationResult | Simulation Data | Yes | Yes if saved | Per DeckVersion | Test output |
| Report | Project Data | Yes | Yes | Snapshot | Human-readable output |
| Note | Project Data | Yes | Yes | No | User/system notes |
| BacklogItem | Project Data | Yes | Yes | No | Future project work |

## 6. Entity Responsibilities

6.1 Project

The Project is the root entity.

It stores the full deck engineering context.

Required fields:

id

name

status

format

commander_name

current_deck_version_id

summary

identity_statement

created_at

updated_at

archived_at

Responsibilities:

- owns the workspace

- groups all project artifacts

- defines the current active deck version

- preserves long-term history

MVP requirement:

Project is mandatory.

6.2 DesignBrief

The DesignBrief defines what “better” means for the Project.

Required fields:

id

project_id

format

commander

strategy

design_philosophy

desired_play_pattern

bracket_target

budget

meta_context

success_criteria

anti_goals

created_at

updated_at

Responsibilities:

- captures user intent

- defines constraints for analysis and recommendation

- prevents generic optimization

- anchors reasoning

MVP storage:

Can be stored as structured fields plus flexible JSON.

Recommended MVP shape:

DesignBrief

├── core fields

└── brief_json

The JSON can hold evolving fields such as:

- table context

- disliked patterns

- desired experience

- bracket notes

- meta notes

- personal philosophy

6.3 UserConstraint

UserConstraint represents explicit constraints that affect recommendations.

Required fields:

id

project_id

type

value

severity

source

created_at

updated_at

Constraint types:

budget

card_availability

proxy_policy

power_level

bracket

meta

theme

tutor_limit

combo_limit

color_requirement

disliked_card

required_card

play_pattern

Severity values:

hard

soft

preference

note

Responsibilities:

- protects user intent

- blocks bad recommendations

- explains why some powerful options are rejected

Rule:

Hard constraints must be checked before a recommendation is considered valid.

6.4 Deck

Deck represents the conceptual deck inside a Project.

Required fields:

id

project_id

name

format

commander_card_id

partner_commander_card_id

status

created_at

updated_at

Responsibilities:

- groups all deck versions

- stores commander identity

- represents the deck concept, not a single list

MVP rule:

One Project should usually contain one Deck.

Future:

A Project may support multiple Decks later for paper/online/budget/high-power branches.

6.5 DeckVersion

DeckVersion is an immutable snapshot of a decklist.

Required fields:

id

project_id

deck_id

version_number

label

parent_version_id

status

change_summary

created_at

created_by

source

Responsibilities:

- stores exact historical deck state

- supports comparison

- supports reversibility

- anchors analysis

- anchors simulation

- anchors reports

- anchors recommendations

DeckVersion status values:

draft

active

test_candidate

archived

rejected

paper_current

online_current

Rules:

- Do not mutate meaningful DeckVersions.

- Create a new DeckVersion for meaningful changes.

- A SimulationRun must reference one DeckVersion.

- An AnalysisReport must reference one DeckVersion.

- A Recommendation should reference the DeckVersion it was created against.

6.6 DeckCard

DeckCard represents a card inside a specific DeckVersion.

DeckCard is not the same as Card.

Required fields:

id

deck_version_id

card_id

printing_id

quantity

zone

category

user_category

is_commander

role_override

notes

included_by_decision_id

removed_by_decision_id

Zones:

commander

main

sideboard

maybeboard

considering

Responsibilities:

- stores card quantity in a deck version

- stores card zone

- stores project-specific card role

- stores user category

- links inclusion/removal to decisions

Important principle:

Card is global. DeckCard is contextual.

Example:

A card may globally be known as “removal”, but in one deck it may function as:

- combo piece

- protection layer

- sacrifice outlet

- storm enabler

- political tool

- artifact count enabler

This contextual meaning belongs on DeckCard, not Card.

6.7 Card

Card represents canonical card identity and rules text.

Required fields:

id

external_id

name

normalized_name

oracle_text

mana_cost

mana_value

type_line

color_identity

colors

keywords

legalities

layout

faces

produced_mana

created_at

updated_at

Responsibilities:

- stores factual card data

- prevents hallucinated card facts

- supports analysis and legality checks

- supports deck parsing

Rule:

The AI must not be the source of truth for Card data.

MVP:

Use one canonical external source, but do not decide the integration inside this RFC.

6.8 CardPrinting

CardPrinting represents a specific printed version of a Card.

Required fields for MVP:

id

card_id

external_printing_id

set_code

collector_number

rarity

image_url

language

price_data

Responsibilities:

- supports imports/exports

- supports price context

- supports collection context later

- supports exact printing selection

MVP:

Lightweight support is enough.

Full collection-grade printing support can wait.

6.9 CardKnowledge

CardKnowledge represents structured interpretation of a Card.

It is not raw oracle text.

Required fields:

id

card_id

summary

role_tags

synergy_tags

archetype_tags

risk_tags

notes

confidence

source

created_at

updated_at

Responsibilities:

- stores functional understanding

- supports recommendation quality

- supports analysis

- supports reasoning

- exposes uncertainty

Source values:

imported

curated

user_defined

ai_suggested

simulation_supported

manually_verified

MVP:

Store as semi-structured JSON.

Later:

Normalize role tags, synergy tags, archetype tags, and risk tags if they become heavily queried.

6.10 Tag

Tag is a lightweight reusable classification label.

Required fields:

id

scope

name

description

parent_tag_id

created_at

updated_at

Scopes:

global_card

project

deck_card

synergy

role

weakness

report

Responsibilities:

- supports filtering

- supports analysis

- supports card grouping

- supports user-defined organization

Rule:

Avoid tag spam. A tag should help reasoning, filtering, reporting, or explanation.

6.11 FunctionalRole

FunctionalRole represents what a card does functionally.

It is more structured than Tag.

Required fields:

id

name

description

role_family

default_weight

Examples:

ramp

mana_fixing

card_draw

card_selection

removal

board_wipe

protection

recursion

tutor

combo_piece

payoff

enabler

outlet

finisher

cost_reduction

token_generation

sacrifice_outlet

stax_piece

Responsibilities:

- supports role density analysis

- supports package analysis

- supports recommendation logic

- supports contextual card evaluation

Important:

- Card may have default FunctionalRoles.

- DeckCard may override them in a specific Project.

6.12 Synergy

Synergy represents a meaningful interaction that is not necessarily deterministic.

Required MVP fields:

id

name

description

synergy_type

participants_json

conditions

payoff

confidence

source

Synergy types:

card_to_card

card_to_role

card_to_tag

package_synergy

engine_synergy

project_specific

Responsibilities:

- captures soft interactions

- supports engine detection

- supports recommendation explanation

MVP:

Store participants as JSON.

Normalize later if synergy search becomes central.

6.13 Combo

Combo represents a deterministic or semi-deterministic line.

Required MVP fields:

id

name

description

required_card_ids

optional_card_ids

result

setup_requirements

failure_points

disruption_points

mana_required

confidence

source

Responsibilities:

- stores known combo lines

- supports win condition analysis

- supports risk and bracket analysis

- supports recommendation checks

Important:

Combo is stricter than Synergy.

A synergy can be broad.

A combo must have a defined line and result.

6.14 EngineInstance

EngineInstance represents a detected or user-defined engine inside a specific DeckVersion.

Required fields:

id

project_id

deck_version_id

name

description

engine_type

core_deck_card_ids

support_deck_card_ids

payoff_deck_card_ids

missing_pieces

strength

consistency

fragility

notes

Engine types:

mana

draw

recursion

storm

equipment

graveyard

sacrifice

token

tutor

control

lock

combat

Responsibilities:

- makes engines first-class

- supports “reason about engines before individual cards”

- supports reports

- supports recommendations

MVP:

EngineInstance can be stored as analysis output.

Global EngineDefinition can wait.

6.15 PackageInstance

PackageInstance represents a group of cards serving a deckbuilding purpose in a specific DeckVersion.

Required fields:

id

project_id

deck_version_id

name

package_type

deck_card_ids

target_density

actual_density

evaluation

notes

Package types:

mana_base

ramp

draw

interaction

protection

win_condition

engine_support

tutor

recursion

meta_answer

flex

Responsibilities:

- supports density analysis

- supports package-level recommendations

- avoids judging cards only one by one

MVP:

PackageInstance should exist.

Global PackageDefinition can wait.

6.16 Weakness

Weakness represents a structural problem detected by analysis or declared by the user.

Required fields:

id

project_id

deck_version_id

analysis_report_id

type

severity

description

evidence

suggested_tests

status

created_at

updated_at

Weakness types:

mana_inconsistency

color_requirement_issue

low_card_access

low_interaction

low_protection

fragile_engine

slow_clock

under_supported_theme

over_supported_package

dead_cards

curve_issue

bracket_mismatch

budget_issue

meta_vulnerability

Status values:

open

under_review

recommendation_created

decision_made

resolved

accepted_risk

Responsibilities:

- captures analysis findings

- creates targets for recommendations

- tracks whether problems are solved or accepted

6.17 AnalysisReport

AnalysisReport is a snapshot of analysis performed on a DeckVersion.

Required fields:

id

project_id

deck_version_id

analysis_type

summary

metrics_json

findings_json

assumptions_json

confidence

created_at

generated_by

Analysis types:

baseline_audit

mana_report

curve_report

engine_report

weakness_report

package_report

interaction_report

protection_report

win_condition_report

Responsibilities:

- stores analysis output

- anchors Recommendations

- anchors Reports

- preserves historical deck understanding

Rule:

AnalysisReports should not silently mutate when the deck changes.

If the deck changes, create a new AnalysisReport.

6.18 Recommendation

Recommendation represents an engineering proposal.

Required fields:

id

project_id

deck_version_id

weakness_id

title

summary

recommendation_type

status

rationale_json

expected_benefit

trade_offs

confidence

created_at

created_by

Recommendation types:

add_cut

package_adjustment

mana_base_change

role_density_change

meta_adjustment

budget_adjustment

identity_preservation

test_request

Statuses:

proposed

under_review

accepted

rejected

deferred

testing

superseded

Responsibilities:

- proposes changes

- explains why

- connects to Weakness, AnalysisReport, or user request

- stores trade-offs

- supports Decision creation

Rule:

A Recommendation does not modify the deck.

Only a Decision can produce a new DeckVersion.

6.19 RecommendationChange

RecommendationChange stores the concrete proposed modification.

Required fields:

id

recommendation_id

change_type

card_id

from_zone

to_zone

quantity

cut_card_id

add_card_id

reason

Change types:

add

cut

swap

move_zone

change_quantity

change_category

tag_override

role_override

Responsibilities:

- makes add/cut proposals structured

- supports review

- supports modified acceptance

- supports changelog generation

Example:

A single Recommendation may include:

Cut Urza's Mine

Cut Urza's Power Plant

Cut Urza's Tower

Add City of Brass

Add Mana Confluence

Add Urza's Saga

This is one recommendation with multiple RecommendationChanges.

6.20 Decision

Decision records what the user actually chose.

Required fields:

id

project_id

deck_version_id

recommendation_id

decision_type

title

rationale

user_comment

accepted_changes_json

rejected_changes_json

expected_outcome

risk_accepted

evidence_links_json

resulting_deck_version_id

created_at

Decision types:

accept

reject

defer

modify

test_first

accept_as_experiment

revert

mark_as_known_risk

Responsibilities:

- records user agency

- tracks why changes happened

- links Recommendations to DeckVersions

- supports reversibility

- preserves project memory

Important:

A Decision is not the same as a Recommendation.

Recommendation:

“I propose this.”

Decision:

“We chose this, for this reason.”

6.21 SimulationRun

SimulationRun represents a specific test against a DeckVersion.

Required fields:

id

project_id

deck_version_id

recommendation_id

decision_id

simulation_type

test_question

config_json

seed

iterations

status

created_at

Simulation types:

opening_hand

mana_consistency

color_availability

land_drop_probability

ramp_access

engine_access

win_condition_access

goldfish

mulligan_quality

resilience

custom

Responsibilities:

- stores test setup

- anchors simulation evidence

- connects tests to recommendations and decisions

Rule:

SimulationRun must always reference a DeckVersion.

6.22 SimulationResult

SimulationResult stores the output of a SimulationRun.

Required fields:

id

simulation_run_id

summary

metrics_json

observations_json

failure_patterns_json

confidence

limitations

created_at

Responsibilities:

- stores simulation evidence

- supports decision-making

- supports historical comparison

- supports report generation

MVP:

Raw metrics can be JSON.

Interpreted summary should be human-readable.

6.23 Report

Report is a human-readable artifact generated from project data.

Required fields:

id

project_id

deck_version_id

report_type

title

content_markdown

source_analysis_report_ids

source_simulation_run_ids

source_decision_ids

created_at

updated_at

Report types:

deck_audit

mana_report

engine_report

recommendation_report

simulation_report

primer

changelog

play_pattern_guide

decision_summary

Responsibilities:

- communicates system understanding

- summarizes analysis and reasoning

- produces reusable user-facing documents

MVP:

Markdown content is acceptable.

Metadata must be structured.

6.24 Note

Note stores user or system-authored comments.

Required fields:

id

project_id

target_type

target_id

author_type

content

tags

created_at

updated_at

Target types:

project

deck_version

deck_card

card

recommendation

decision

simulation_run

report

Responsibilities:

- captures observations

- stores informal reasoning

- supports workflow without polluting structured entities

6.25 BacklogItem

BacklogItem represents future work inside a Project.

Required fields:

id

project_id

title

description

status

priority

related_card_ids

related_recommendation_id

related_weakness_id

created_at

updated_at

Statuses:

open

in_progress

blocked

done

dismissed

Responsibilities:

- tracks future tests

- tracks unresolved ideas

- tracks deckbuilding tasks

- supports project continuity

## 7. Relationship Model

7.1 Project Relationships

Project 1 ── 1 DesignBrief

Project 1 ── many UserConstraints

Project 1 ── many Notes

Project 1 ── many BacklogItems

Project 1 ── many Reports

Project 1 ── many Decisions

Project 1 ── many Recommendations

Project 1 ── many SimulationRuns

Project 1 ── many AnalysisReports

Project 1 ── many Decks

MVP:

Use one Deck per Project.

7.2 Deck Relationships

Deck 1 ── many DeckVersions

DeckVersion 1 ── many DeckCards

DeckCard many ── 1 Card

DeckCard many ── 0/1 CardPrinting

Important:

DeckVersion is the snapshot boundary.

DeckCard belongs to one DeckVersion only.

7.3 Analysis Relationships

DeckVersion 1 ── many AnalysisReports

AnalysisReport 1 ── many Weaknesses

AnalysisReport 1 ── many EngineInstances

AnalysisReport 1 ── many PackageInstances

Weaknesses must point back to the DeckVersion where they were detected.

7.4 Recommendation Relationships

DeckVersion 1 ── many Recommendations

Recommendation 1 ── many RecommendationChanges

Recommendation many ── 0/1 Weakness

Recommendation many ── 0/1 AnalysisReport

Recommendation 1 ── 0/1 Decision

A Recommendation may exist without a Decision.

A Decision may reject, modify, defer, or accept it.

7.5 Decision Relationships

Decision many ── 1 Project

Decision many ── 1 source DeckVersion

Decision many ── 0/1 Recommendation

Decision many ── 0/1 resulting DeckVersion

Decision many ── many evidence links

Evidence links may include:

AnalysisReport

Weakness

SimulationRun

SimulationResult

Note

Report

7.6 Simulation Relationships

DeckVersion 1 ── many SimulationRuns

SimulationRun 1 ── 1 SimulationResult

SimulationRun many ── 0/1 Recommendation

SimulationRun many ── 0/1 Decision

SimulationRun many ── 0/1 Weakness

Simulation is attached to the deck state it tested.

Not to the abstract deck.

## 8. Persistence Rules

8.1 Must Persist

These must always be persistent:

Project

DesignBrief

Deck

DeckVersion

DeckCard

Card

Recommendation

RecommendationChange

Decision

Report

Reason:

They are essential to the engineering loop.

8.2 Should Persist When Saved or Used

These should persist when they influence user-facing output or decisions:

AnalysisReport

Weakness

SimulationRun

SimulationResult

EngineInstance

PackageInstance

Note

BacklogItem

Rule:

If it influenced a Recommendation, Decision, or Report, persist it.

8.3 Can Be Recomputed

These can be recomputed unless used historically:

mana curve

land count

color pip pressure

role density

card type counts

package density

average mana value

basic probability metrics

Rule:

Recompute for current working state.

Persist when attached to:

- AnalysisReport

- Recommendation

- Decision

- Report

8.4 Can Start as JSON

These can start semi-structured in MVP:

DesignBrief details

UserConstraint value

CardKnowledge

Synergy participants

Combo requirements

Analysis metrics

Reasoning rationale

Simulation config

Simulation metrics

Decision evidence links

Accepted/rejected change details

Reason:

These areas will evolve quickly during prototype development.

Premature normalization would slow down iteration.

## 9. Versioning Model

9.1 Versioning Principle

Deckbuilding changes are engineering events.

Every meaningful change should be:

- traceable

- explainable

- reversible

- comparable

- linked to a reason

9.2 Immutable DeckVersions

DeckVersions should be immutable after creation.

Corrections or changes create a new DeckVersion.

This enables:

- rollback

- comparison

- simulation traceability

- recommendation traceability

- changelog generation

9.3 Parent Version

Each DeckVersion may have a parent_version_id.

Example:

v1.0 Baseline Import

├── v1.1 Mana Fixing Test

│ └── v1.2 Accepted Mana Fixing

└── v1.1b High-Power Proxy Branch

9.4 Revert Model

A revert should create a new DeckVersion.

It should not delete history.

Example:

v1.4 Revert Tezzeret Package

This preserves:

- the original experiment

- the failed result

- the decision to revert

- the new state

## 10. Decision Log Model

10.1 Decision Log Principle

The Decision Log is the engineering memory of the Project.

It records:

- what was proposed

- what was tested

- what was accepted

- what was rejected

- what was deferred

- what was reverted

- why the choice was made

- what version resulted

10.2 Decision Lifecycle

Weakness detected

→ Recommendation created

→ Optional SimulationRun

→ User reviews trade-offs

→ Decision recorded

→ New DeckVersion created

→ Future results attached

10.3 Required Decision Questions

A Decision should answer:

What changed?

Why?

What problem was being solved?

What benefit was expected?

What trade-off was accepted?

What evidence supported it?

What deck version resulted?

Should this be tested again?

10.4 Accepted Risk

Accepted risk should be first-class.

Example:

Weakness:

Low graveyard hate.

Decision:

Mark as accepted risk.

Rationale:

Current meta does not require dedicated graveyard hate.

Deck identity and slot pressure matter more for now.

This prevents the system from repeatedly flagging the same intentional weakness as unresolved.

## 11. Reasoning Data Model

11.1 Reasoning Principle

Reasoning must be structured enough to be useful later.

Do not store reasoning only as long chat transcripts.

A Recommendation should store reasoning as:

rationale_json

├── problem

├── hypothesis

├── evidence

├── expected_benefit

├── trade_offs

├── uncertainty

├── alternatives_considered

└── test_suggestion

11.2 Reasoning Persistence Rule

Persist reasoning when it supports:

- Recommendation

- Decision

- AnalysisReport

- Report

- Simulation interpretation

Do not persist every transient thought.

11.3 Reasoning Boundary

The AI may produce reasoning.

The database must store the useful structured result.

The database should not treat raw AI output as truth.

## 12. Knowledge Data Model

12.1 Knowledge Principle

Knowledge comes before AI.

The system should reason over structured, inspectable knowledge.

12.2 Card Facts vs Card Knowledge

Card Facts:

oracle text

mana cost

type line

color identity

legalities

rulings

printings

Card Knowledge:

functional role

synergy role

combo role

archetype relevance

risk notes

replacement candidates

package relevance

engine relevance

Card Facts are imported or refreshed.

Card Knowledge is curated, inferred, edited, or user-defined.

12.3 MVP Knowledge Shape

MVP should support:

Card

CardPrinting

CardKnowledge

Tag

FunctionalRole

Synergy as JSON

Combo as JSON

Do not overbuild a complete knowledge graph in MVP.

Start with enough structure to support:

- role counting

- synergy explanation

- package detection

- engine detection

- recommendation rationale

## 13. Simulation Data Model

13.1 Simulation Principle

Simulation is evidence for hypotheses.

It is not a generic deck score.

A SimulationRun must have a test question.

Examples:

How often does this version keep a playable opening hand?

How often can this version cast the commander on curve?

How often does this version have two white sources by turn six?

How often does this version access an engine piece by turn four?

Does this mana base change improve color availability?

13.2 MVP Simulation Types

MVP should support:

opening_hand

mana_consistency

color_availability

land_drop_probability

ramp_access

engine_access

goldfish

Advanced gameplay simulation can wait.

13.3 Simulation Storage

SimulationRun stores:

test question

deck version

configuration

iterations

seed

status

SimulationResult stores:

summary

metrics

observations

failure patterns

limitations

Raw output may be JSON.

Interpreted findings should be readable.

## 14. Recommendation Data Model

14.1 Recommendation Principle

A Recommendation is an engineering proposal.

It is not:

Add Card X because it is good.

It should be:

Add Card X because it improves Y,

supports Z,

solves weakness W,

and trades off Q.

14.2 Recommendation Validity

A Recommendation should be considered valid only if it references at least one of:

DesignBrief

UserConstraint

AnalysisReport

Weakness

SimulationResult

User request

Project Note

14.3 Recommendation Output

A complete Recommendation should include:

problem

proposed change

affected engine/package

expected benefit

trade-off

confidence

test suggestion

14.4 Recommendation to Decision

Recommendations do not change deck state.

Only Decisions can produce new DeckVersions.

Recommendation proposed

→ Decision accepted / modified / rejected / deferred

→ New DeckVersion created if needed

## 15. MVP Data Model

The MVP must prove the product loop.

It does not need full database complexity.

15.1 MVP Core Loop

The MVP must support:

Create Project

→ Define lightweight DesignBrief

→ Import Decklist

→ Create DeckVersion

→ Parse DeckCards

→ Load Card facts

→ Apply basic CardKnowledge

→ Run AnalysisReport

→ Detect Weaknesses

→ Create Recommendation

→ Review RecommendationChanges

→ Record Decision

→ Create new DeckVersion

→ Optional SimulationRun

→ Generate Report

15.2 MVP Required Entities

Required:

Project

DesignBrief

UserConstraint

Deck

DeckVersion

DeckCard

Card

CardPrinting

CardKnowledge

Tag

FunctionalRole

AnalysisReport

Weakness

EngineInstance

PackageInstance

Recommendation

RecommendationChange

Decision

SimulationRun

SimulationResult

Report

Note

BacklogItem

15.3 MVP Deferred Entities

Can wait:

UserCollection

OwnedPrinting

Advanced Combo Graph

Global EngineDefinition

Global PackageDefinition

Advanced Synergy Graph

Collaborative Comments

External Account Integration

Price History

Meta Profiles

Matchup Profiles

15.4 MVP Normalized

Normalize from the start:

Project

Deck

DeckVersion

DeckCard

Card

Recommendation

RecommendationChange

Decision

SimulationRun

SimulationResult

Report

15.5 MVP Semi-Structured

Allow JSON initially:

DesignBrief extended fields

UserConstraint value

CardKnowledge

Synergy

Combo

Analysis metrics

Reasoning rationale

Simulation config

Simulation metrics

Decision evidence

EngineInstance card groups

PackageInstance card groups

15.6 MVP Reports

Reports can be Markdown documents with structured metadata.

This keeps implementation simple while preserving useful output.

## 16. Future Extensions

16.1 User Collection

Future entities:

UserCollection

OwnedPrinting

AcquisitionStatus

Use cases:

- paper availability

- budget recommendations

- owned cards

- proxy decisions

16.2 Multi-Deck Project

Future support:

Project

├── Deck: Paper Budget

├── Deck: Online No-Budget

└── Deck: High-Power Branch

Use cases:

- different budgets

- different metas

- online vs paper

- proxy vs owned cards

16.3 Advanced Knowledge Graph

Future graph support:

Card → Synergy → Card

Card → Engine → Package

Card → Combo → WinCondition

Card → ReplacementCandidate → Card

Use cases:

- hidden gem discovery

- synergy search

- replacement reasoning

- combo mapping

16.4 Advanced Simulation

Future simulation support:

matchup simulation

resilience testing

removal pressure

meta-specific tests

mulligan policy testing

play pattern simulation

16.5 External Integrations

Future integrations:

Moxfield

Archidekt

Scryfall

EDHREC

price providers

Tabletop Simulator

collection trackers

16.6 Collaborative Projects

Future support:

multi-user projects

comments

review states

shared decisions

change approvals

## 17. Open Questions

- Should MVP storage start as Markdown/JSON files, or as a lightweight database?

- Should DesignBrief be stored as mostly JSON at first, or normalized earlier?

- Should user-defined tags and global system tags share the same table?

- Should CardKnowledge be manually curated first, AI-assisted, or imported from structured sources?

- Should EngineInstance and PackageInstance exist only as analysis outputs in MVP?

- Should every DeckVersion require a Decision, or only meaningful changes?

- Should Reports be immutable snapshots or editable documents?

- Should rejected Recommendations remain visible by default?

- Should confidence be qualitative, numeric, or both?

- Should price data be stored as current-only or historical snapshots?

- Should accepted risk suppress future Weakness warnings?

- Should SimulationRuns be saved automatically or only when user marks them as relevant?

- How should branch merging work between divergent DeckVersions?

- Should project chat history be stored at all, or only distilled Notes, Decisions, and Reports?

- What is the minimum CardKnowledge required before recommendations become trustworthy?

## 18. ADR Candidates

ADR-001 — Project Is the Root Entity

Decision:

Project is the root entity of The Workshop.

Reason:

The product stores context, reasoning, versions, decisions, tests, and reports, not only decklists.

ADR-002 — DeckVersion Is Immutable

Decision:

DeckVersions are immutable snapshots.

Reason:

Immutability supports traceability, comparison, simulation, reversibility, and changelog generation.

ADR-003 — Card and DeckCard Are Separate

Decision:

Card and DeckCard are separate entities.

Reason:

Card stores global facts. DeckCard stores contextual use inside a specific DeckVersion.

ADR-004 — Recommendation Does Not Modify Deck State

Decision:

Recommendations do not modify decks directly.

Reason:

The user remains the designer. Only Decisions produce new DeckVersions.

ADR-005 — SimulationRun Must Reference DeckVersion

Decision:

Every SimulationRun must reference a specific DeckVersion.

Reason:

Simulation evidence is meaningless without knowing the exact deck state tested.

ADR-006 — Reasoning Is Structured

Decision:

Reasoning should be stored as structured assumptions, hypotheses, evidence, trade-offs, and uncertainty.

Reason:

Structured reasoning is searchable, explainable, and reusable.

ADR-007 — MVP Allows JSON for Evolving Structures

Decision:

MVP may use JSON for DesignBrief details, CardKnowledge, Synergies, Combos, Analysis metrics, Simulation config, and reasoning rationale.

Reason:

These structures will evolve quickly during prototype work.

ADR-008 — Persist Analysis Only When It Matters

Decision:

Analysis should be persisted when it influences a Recommendation, Decision, Report, or historical comparison.

Reason:

Avoid storing noise while preserving engineering accountability.

ADR-009 — Decision Log Is First-Class

Decision:

Decision is a first-class entity.

Reason:

The Decision Log is the memory of the engineering process.

ADR-010 — Accepted Risk Is First-Class

Decision:

Accepted risk should be represented as a Decision outcome.

Reason:

Some weaknesses are intentional trade-offs. The system must not repeatedly treat them as unresolved mistakes.

## 19. Foundational Data Principle

A decklist answers:

What cards are in the deck?

The Workshop must answer:

Why are these cards here?

What system do they create?

What problems remain?

What did we test?

What did we decide?

What changed?

What should we revisit later?

The list is the output.

The reasoning, evidence, and decision history are the product.
