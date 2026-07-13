# RFC-003 — The Workshop Knowledge Engine

Status: Draft Version: v0.2 Sprint: 0 Depends on: RFC-000 — Product Vision, RFC-001 — System Architecture, RFC-002 — Database / Data Model Document Type: Knowledge Model / Architecture Architecture Owner: Software Architect / CTO Product Owner: Product Owner / Domain Expert

## 1. Purpose

This document defines the conceptual and logical model for the Knowledge Engine of The Workshop.

The Knowledge Engine is responsible for how The Workshop knows, organizes, enriches, validates, and uses knowledge about cards, deck components, engines, packages, combos, archetypes, risks, constraints, and project-specific context.

The goal is not to choose a specific implementation technology.

This RFC does not decide:

- vector database

- graph database

- embedding strategy

- LLM pipeline

- specific storage engine

- final ingestion infrastructure

The goal is to define the knowledge model that allows The Workshop to reason from structured, inspectable, updateable information rather than from vague card suggestions or AI hallucination.

The Workshop is a Deck Engineering Platform.

Therefore, the Knowledge Engine must support the core product loop:

Brief → Analyze → Recommend → Test → Decide → Version

The Knowledge Engine exists to make that loop trustworthy.

## 2. Knowledge Engine Thesis

Knowledge comes before AI.

The AI is not the source of truth.

The AI is a reasoning layer that operates on structured knowledge, project context, analysis results, and simulation evidence.

The Knowledge Engine must answer questions such as:

- What does this card objectively say?

- What does this card usually do?

- What role does this card perform in this specific deck?

- What engine does it support?

- What package does it belong to?

- What synergies does it create?

- What risks does it introduce?

- What constraints does it violate?

- What assumptions are being made?

- What is fact, what is interpretation, and what is hypothesis?

- What knowledge is global?

- What knowledge is project-specific?

- What knowledge was defined by the user?

The Workshop must be able to say:

“This is a card fact from canonical data.”

or:

“This is an internal functional classification.”

or:

“This is project-specific interpretation.”

or:

“This is a user-defined constraint.”

or:

“This is a reasoning hypothesis that needs validation.”

The Knowledge Engine should make recommendations better by making them more grounded, not by making the system more complicated.

## 3. Scope

The Knowledge Engine manages knowledge about:

- Card Facts

- Card Metadata

- Oracle Text

- Legalities

- Color Identity

- Mana Value

- Type Line

- Prices

- Printings

- Rulings

- Functional Roles

- Strategic Roles

- Synergy Tags

- Engine Tags

- Package Membership

- Combo Relationships

- Archetype Relationships

- Risk Tags

- Constraint Tags

- User Notes

- Project-Specific Overrides

- Confidence Levels

- Source Tracking

- Knowledge Validation Status

The Knowledge Engine does not own:

- Project lifecycle

- DeckVersion lifecycle

- Recommendation decisions

- Simulation execution

- Report generation

- UI state

Those belong to other modules.

However, the Knowledge Engine supplies the structured knowledge those modules rely on.

## 4. Core Principle

The Knowledge Engine should not maximize the number of tags.

It should maximize the usefulness of knowledge.

A knowledge item is useful only if it helps at least one of these actions:

- analyze a deck

- explain a card’s role

- detect a weakness

- identify an engine

- identify a package

- validate a combo

- generate a better recommendation

- reject a bad recommendation

- test a hypothesis

- explain a trade-off

- preserve deck identity

- respect user constraints

- generate a better report

If a tag, relation, or annotation does not help any of those, it is noise.

## 5. Knowledge Types

The Knowledge Engine distinguishes between different types of knowledge.

Not all knowledge has the same source, reliability, scope, or purpose.

5.1 Card Facts

Card Facts are objective data about a card.

Examples:

- name

- oracle text

- mana cost

- mana value

- type line

- card types

- supertypes

- subtypes

- color identity

- colors

- power/toughness

- loyalty

- defense

- keywords

- produced mana

- legalities

- layout

- faces

- printings

- rulings

- price data

Card Facts should come from reliable external sources.

The AI must not author Card Facts.

Card Facts answer:

“What is this card according to the game data?”

5.2 Derived Card Data

Derived Card Data is computed from Card Facts.

Examples:

- is_creature

- is_artifact

- is_enchantment

- is_land

- is_legendary

- is_commander_legal

- has_activated_ability

- has_triggered_ability

- mentions_graveyard

- mentions_token

- mentions_sacrifice

- mentions_draw

- color_count

- pip_intensity

- mana_value_bucket

- produced_mana_colors

Derived Card Data should be reproducible.

It may be generated through deterministic parsing, rules, or lightweight classifiers.

Derived Card Data answers:

“What can we infer mechanically from the card data?”

5.3 Card Knowledge

Card Knowledge is structured interpretation of what a card does in deckbuilding terms.

Examples:

- ramp

- card draw

- tutor

- removal

- protection

- recursion

- sacrifice outlet

- payoff

- enabler

- combo piece

- win condition

- engine support

- mana fixing

- graveyard hate

- board wipe

- cost reduction

- token producer

Card Knowledge answers:

“How can this card function inside deckbuilding systems?”

Card Knowledge is not always universal.

A card may have a default global role, but its actual role inside a project may be different.

Example:

- A card can be generic ramp globally.

- In a specific deck, it can be artifact count support.

- In another deck, it can be a combo piece.

- In another deck, it can be off-plan filler.

5.4 Project-Specific Knowledge

Project-Specific Knowledge describes how a card, package, engine, or combo functions inside one Project.

Examples:

- “This Myr deck uses Myr as resources, not attackers.”

- “This Zur deck accepts risky aura lines because brinkmanship is part of its identity.”

- “This Emry deck is not generic Voltron; equipment is a recursion toolbox.”

- “This card is powerful, but it makes the deck less itself.”

- “This combo is legal, but rejected because it violates the table experience.”

- “This card is a pet card and should not be recommended as a cut unless explicitly requested.”

- “This weakness is accepted because the meta does not punish it.”

Project-Specific Knowledge is first-class.

The Workshop does not optimize decks in the abstract.

It improves a specific deck, for a specific player, under a specific brief.

5.5 User-Defined Knowledge

User-Defined Knowledge is knowledge explicitly provided or approved by the user.

Examples:

- custom card tags

- pet cards

- cards the user dislikes

- budget constraints

- proxy policy

- tutor tolerance

- combo tolerance

- preferred play patterns

- meta notes

- accepted risks

- cards marked “do not cut”

- cards marked “testing”

- user explanations

User-Defined Knowledge is authoritative for user intent.

It cannot override canonical rules text or legality.

It can override recommendation logic inside a project.

Example:

Global knowledge:

Demonic Tutor is an efficient tutor.

User-defined project constraint:

Avoid tutor-heavy gameplay.

Recommendation impact:

Do not recommend Demonic Tutor unless the user changes that constraint.

5.6 Relationship Knowledge

Relationship Knowledge describes how entities connect.

Examples:

- card supports role

- card supports engine

- card belongs to package

- card synergizes with card

- card enables combo

- card pays off archetype

- card conflicts with constraint

- card increases risk

- card replaces another card

- card is redundant with another card

Relationship Knowledge is central to The Workshop.

The platform should reason about interactions before individual card power.

5.7 Reasoning Hypotheses

Reasoning Hypotheses are tentative conclusions produced by analysis or reasoning.

Examples:

- “The deck may lack enough early ramp.”

- “The deck may be overcommitted to graveyard lines.”

- “This card is strong but likely outside the intended deck identity.”

- “This package appears under-supported.”

- “The mana base may not support double-white costs reliably.”

- “The deck may need more protection before adding more payoff cards.”

Hypotheses are not facts.

They should be validated through:

- user review

- analysis

- simulation

- gameplay notes

- accepted or rejected decisions

Reasoning Hypotheses should not silently become permanent global knowledge.

## 6. Source of Truth Model

The Knowledge Engine must track source and trust level.

A single card may have:

- canonical facts

- derived properties

- curated roles

- heuristic tags

- AI-suggested classifications

- user notes

- project overrides

- simulation-supported findings

These must not be mixed into one undifferentiated blob.

6.1 Source Categories

| Source Category | Description | Scope | Trust |
| --- | --- | --- | --- |
| Canonical External | Oracle text, legalities, official metadata, rulings | Global | Highest |
| External Volatile | Prices, availability, popularity data | Global | High but time-sensitive |
| Internal Deterministic | Parsed or computed fields | Global | High if parser is correct |
| Internal Curated | Manually maintained roles, combos, archetype data | Global | Medium/High |
| Internal Heuristic | Rule-based inferred tags | Global or Project | Medium |
| AI-Suggested | AI-proposed classification, relation, or note | Draft | Low until validated |
| User-Defined | User preference, note, tag, constraint | Project/User | Authoritative for intent |
| Project Override | Context-specific reinterpretation | Project | Authoritative in project |
| Simulation-Derived | Finding supported by test result | DeckVersion/Project | Evidence-based |

6.2 Source Tracking Requirements

Every non-trivial knowledge item should be able to answer:

- What is the claim?

- What entity does it apply to?

- What type of knowledge is it?

- What is the source?

- Is it global or project-specific?

- Is it curated, computed, user-defined, or AI-suggested?

- What is the confidence level?

- What is the validation status?

- When was it created?

- When was it updated?

- Is it stale, deprecated, accepted, rejected, or under review?

This allows The Workshop to expose uncertainty instead of hiding it.

## 7. Card Facts vs Card Knowledge

The Workshop must strictly separate Card Facts from Card Knowledge.

7.1 Card Facts

Card Facts answer:

“What does the card say and what is its official game identity?”

Examples:

- oracle text

- mana cost

- type line

- color identity

- legality

- rulings

- printings

Card Facts are imported or refreshed.

They are not authored by the AI.

7.2 Card Knowledge

Card Knowledge answers:

“How is this card useful, risky, or relevant inside deckbuilding systems?”

Examples:

- functional role

- synergy role

- combo role

- archetype relevance

- package relevance

- engine relevance

- risk notes

- replacement candidates

- contextual weaknesses

Card Knowledge may be:

- curated

- inferred

- user-defined

- project-specific

- simulation-supported

- AI-suggested but unvalidated

7.3 Card vs DeckCard Context

A global Card is not the same as a card inside a deck.

The global Card stores objective and default knowledge.

A DeckCard can override or specialize that knowledge inside a specific DeckVersion.

Example:

Card:

Skullclamp

Global Card Knowledge:

- card draw

- sacrifice synergy

- token payoff

DeckCard in Token Deck:

- primary draw engine

- core engine piece

DeckCard in Equipment Deck:

- weak off-plan draw piece

- likely cut candidate

DeckCard in Artifact Combo Deck:

- artifact count support

- token-to-card converter

The card is the same.

The role is contextual.

## 8. Functional Role Model

Functional Roles describe what a card does.

They are more structured than freeform tags.

They should be controlled, understandable, and useful for analysis.

8.1 Functional Role Principles

Functional Roles should be:

- limited

- clear

- user-readable

- useful for role density analysis

- useful for recommendation logic

- overridable at DeckCard level

- explainable

- confidence-scored

Functional Roles should not become tag spam.

A role exists because it helps the system reason about deck structure.

8.2 Role Families

The MVP should use a compact role taxonomy.

Recommended role families:

Resource Development

- ramp

- mana_fixing

- cost_reduction

- ritual

- treasure_generation

Card Access

- card_draw

- card_selection

- tutor

- impulse_draw

- recursion

Interaction

- removal

- board_wipe

- counterspell

- graveyard_hate

- stax_piece

Protection

- commander_protection

- board_protection

- spell_protection

- recovery

Engine Structure

- enabler

- payoff

- outlet

- converter

- redundancy_piece

- engine_glue

Win Conditions

- combat_win

- combo_win

- drain_win

- mill_win

- alternate_win

Deck Support

- token_producer

- sacrifice_outlet

- discard_outlet

- equipment_carrier

- artifact_count_support

- enchantment_count_support

This taxonomy should stay intentionally small for MVP.

New roles should be added only when a real analysis or recommendation need appears.

8.3 Role Assignment

A role assignment should include:

- card_id or deck_card_id

- role

- role_family

- scope

- source

- confidence

- is_primary

- explanation

- conditions

Example:

Card: Krark-Clan Ironworks

Role: sacrifice_outlet

Scope: Global

Source: Internal Curated

Confidence: High

Primary: true

Explanation: Allows artifacts to be sacrificed repeatedly for mana.

Card: Krark-Clan Ironworks

Role: mana_engine

Scope: Project-Specific

Source: Project Override

Confidence: High

Primary: true

Explanation: In this artifact deck, KCI converts artifact bodies and tokens into explosive mana.

8.4 Primary, Secondary, and Incidental Roles

The system must distinguish between:

- primary role

- secondary role

- incidental role

- project role

This prevents bad role counting.

Example:

Solemn Simulacrum

Primary:

- ramp

Secondary:

- card_draw

Incidental:

- artifact_count_support

Project-specific:

- sacrifice_fodder in decks that can exploit death triggers

A card should not inflate every density count equally.

8.5 Role Weight

For analysis, not every role should count as 1.

A role assignment may have a weight.

Example:

Card: Rhystic Study

Role: card_draw

Weight: 1.0

Card: Solemn Simulacrum

Role: card_draw

Weight: 0.25

Role weight helps avoid false analysis.

A card that can technically draw one card should not count the same as a dedicated draw engine.

MVP can start with simple qualitative weights:

- full

- partial

- incidental

Numeric weighting can come later.

## 9. Synergy Model

A synergy is a meaningful positive interaction.

A synergy is not merely two cards sharing a type, color, or keyword.

9.1 Synergy Definition

A synergy exists when one element materially improves the usefulness, efficiency, consistency, payoff, or resilience of another.

Examples:

- token producer + sacrifice outlet

- equipment + evasive carrier

- graveyard recursion + self-mill

- artifact bodies + artifact sacrifice outlet

- enchantment tutor + silver bullet aura

- cost reducer + spell chain

- commander protection + commander-centric engine

- lifegain trigger + life payment engine

9.2 Synergy Object

A synergy should include:

- name

- synergy_type

- participants

- directionality

- conditions

- payoff

- strength

- scope

- confidence

- source

- explanation

- risk_notes

Example:

Name: Token-to-Card Conversion

Participants:

- Skullclamp

- 1-toughness token producers

Directionality:

Token producers enable Skullclamp.

Payoff:

Repeatable card draw.

Strength:

Strong

Scope:

Pattern / Project-Specific

Risk:

Weak if token density is low.

9.3 Directionality

Synergy may be directional.

Example:

A tutor finds a combo piece.

The combo piece does not tutor the tutor.

A token producer supports Skullclamp.

Skullclamp does not support all token producers equally.

The model should not assume all relationships are symmetrical.

9.4 Synergy Strength

Suggested values:

- weak

- medium

- strong

- critical

Meaning:

| Strength | Meaning |
| --- | --- |
| weak | Minor interaction, useful but not structural |
| medium | Meaningful support |
| strong | Important interaction that affects deck performance |
| critical | The deck or engine may depend on it |

9.5 Anti-Spam Rule

The system should not create synergies automatically just because:

- both cards are artifacts

- both cards mention creatures

- both cards are in the same color

- both cards are popular in the same archetype

- both cards share a broad tag

A synergy must help explain something.

If it does not help analysis, recommendation, simulation, or reporting, it should not be stored.

## 10. Engine Model

An Engine is a repeatable or structurally important subsystem that converts resources into advantage, pressure, control, or a win path.

The Workshop should reason about engines before individual cards.

10.1 Engine Definition

An Engine has:

- purpose

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

- failure modes

- setup cost

- speed

- resilience

- deck identity relevance

Examples:

- artifact sacrifice mana engine

- graveyard recursion engine

- enchantment tutor engine

- equipment recursion toolbox

- token-to-mana engine

- storm spell-chain engine

- blink value engine

- aristocrats drain engine

- commander damage aura engine

- stax lock engine

10.2 Engine Components

| Component Type | Description |
| --- | --- |
| Enabler | Allows the engine to function |
| Fuel | Resource consumed by the engine |
| Converter | Turns one resource into another |
| Payoff | Rewards engine activity |
| Outlet | Allows repeated use or conversion |
| Redundancy Piece | Increases consistency |
| Protection Piece | Protects the engine |
| Recovery Piece | Rebuilds the engine |
| Finisher | Converts the engine into a win |

10.3 Engine Definition vs Engine Instance

The Knowledge Engine may eventually support global EngineDefinitions.

For MVP, the system should prioritize EngineInstances inside Projects and DeckVersions.

Reason:

Global engine modeling can become huge quickly.

Project-level engine detection is more immediately useful.

10.4 EngineInstance

An EngineInstance exists inside a specific DeckVersion.

It should include:

- project_id

- deck_version_id

- name

- engine_type

- description

- core_deck_cards

- support_deck_cards

- payoff_deck_cards

- missing_pieces

- strength

- consistency

- fragility

- speed

- resilience

- role_in_deck_identity

- notes

Example:

Engine: Myr Artifact Sacrifice Engine

Scope: Project-Specific

DeckVersion: v1.2

Input:

- Myr tokens

- artifact bodies

Converters:

- Krark-Clan Ironworks

- Ashnod's Altar

Outputs:

- mana

- death triggers

- explosive turns

Payoffs:

- combo finish

- large artifact turns

Weaknesses:

- artifact hate

- graveyard hate

- board wipes

Role in Deck Identity:

Core

10.5 Engine Evaluation

An engine should be evaluated by:

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

The Knowledge Engine provides the engine structure.

The Analysis Engine evaluates whether the deck supports it.

The Reasoning Engine decides what it means.

The Simulation Engine may test access, speed, or consistency.

## 11. Package Model

A Package is a modular group of cards included to solve a specific problem or support a plan.

Packages are smaller and more optional than Engines.

11.1 Package Definition

A Package has:

- purpose

- members

- target density

- actual density

- expected benefit

- opportunity cost

- related roles

- related engines

- risks

- constraints

- evaluation

Examples:

- fast mana package

- cheap interaction package

- graveyard hate package

- artifact protection package

- tutor package

- equipment carrier package

- mana fixing land package

- recursion package

- board wipe package

- meta answer package

11.2 Package vs Engine

| Concept | Engine | Package |
| --- | --- | --- |
| Function | Core subsystem | Modular solution |
| Dependency | Often structural | Often optional |
| Size | Can span many cards | Usually smaller |
| Purpose | Generates repeated value, control, or win path | Solves a deckbuilding problem |
| Question | “Does this deck function through it?” | “Is this worth the slots?” |

11.3 PackageInstance

For MVP, packages should primarily exist as PackageInstances inside a DeckVersion.

Fields:

- project_id

- deck_version_id

- name

- package_type

- deck_card_ids

- target_density

- actual_density

- evaluation

- risks

- notes

Example:

Package: Artifact Protection Package

Type: protection

Target Density: 4-6 pieces

Actual Density: 3 pieces

Evaluation:

Under target for an artifact-heavy meta.

Risk:

Adding more protection may reduce proactive engine density.

## 12. Combo Relationship Model

A Combo is a specific interaction pattern that produces a decisive, repeated, or deterministic outcome.

A combo is stricter than a synergy.

12.1 Combo Definition

A Combo should include:

- name

- required pieces

- optional pieces

- result

- setup requirements

- mana required

- zones required

- timing requirements

- loop description

- disruption points

- failure points

- confidence

- source

- scope

- legality notes

- bracket/power risk

12.2 Combo Types

Suggested combo types:

- infinite_mana

- infinite_draw

- infinite_damage

- infinite_tokens

- infinite_life

- infinite_mill

- infinite_death_triggers

- deterministic_win

- soft_lock

- hard_lock

- repeated_value_loop

- storm_finish

- commander_damage_kill

- alternate_win

12.3 Exact Combo vs Pattern Combo

The Workshop should distinguish:

| Type | Description |
| --- | --- |
| Exact Combo | Specific named cards create a known line |
| Pattern Combo | A class of cards can create a line |
| Project Combo | A combo recognized inside a specific deck |
| Hypothetical Combo | A possible line requiring validation |
| Rejected Combo | A known line intentionally excluded |

This is important because The Workshop must not overstate uncertain combo knowledge.

12.4 MVP Combo Rule

For MVP:

- exact combos can be stored if curated or user-defined

- project combos can be stored when detected or accepted

- pattern combos can exist as notes or semi-structured records

- AI-suggested combos must remain unvalidated until reviewed

The system should not pretend to be a full rules engine in MVP.

## 13. Archetype Relationship Model

An Archetype is a broad strategic pattern.

Examples:

- artifacts

- aristocrats

- spellslinger

- storm

- blink

- reanimator

- enchantress

- Voltron

- stax

- tokens

- tribal

- lands

- graveyard combo

- equipment toolbox

- control-combo

- pillowfort

- wheels

- lifegain

13.1 Archetype Relevance

A card can relate to an archetype as:

- staple

- enabler

- payoff

- support card

- role-player

- niche tech

- budget alternative

- meta answer

- risky inclusion

- off-plan trap

The system should not say:

“This card is good in artifacts.”

It should say:

“This card is relevant to artifact decks because it converts artifact permanents into mana, which supports sacrifice-based artifact engines.”

13.2 Archetype Is Not Deck Identity

Archetype labels are useful but insufficient.

A Project’s identity may bend or reject archetype expectations.

Example:

Archetype:

Myr Tribal

Project Identity:

Artifact combo-control engine disguised as Myr tribal.

Archetype:

Equipment

Project Identity:

Emry recursion-based equipment toolbox.

Archetype:

Enchantments

Project Identity:

Zur forbidden-aura brinkmanship engine.

The Knowledge Engine provides archetype context.

The Project Workspace and Reasoning Engine determine deck identity.

## 14. Risk Tags and Constraint Tags

The Knowledge Engine must track downsides, not only strengths.

A card recommendation is incomplete if it cannot explain risk.

14.1 Risk Tags

Risk Tags describe possible downsides introduced by a card, package, engine, or combo.

Examples:

- high_mana_value

- color_intensive

- graveyard_dependent

- commander_dependent

- board_dependent

- low_floor

- win_more

- table_threat_signal

- combo_stigma

- budget_risk

- bracket_risk

- nonbo_risk

- slow_setup

- vulnerable_to_artifact_hate

- vulnerable_to_graveyard_hate

- weak_without_density

- redundant

- conflicts_with_identity

14.2 Constraint Tags

Constraint Tags describe conflicts with explicit project or user constraints.

Examples:

- exceeds_budget

- violates_no_tutor_preference

- violates_no_infinite_combo_rule

- too_strong_for_bracket

- too_slow_for_meta

- off_theme

- low_originality

- proxy_only

- not_format_legal

- unavailable_in_collection

- disliked_by_user

14.3 Risk Is Contextual

A card is not risky in a vacuum.

Risk depends on:

- deck strategy

- bracket target

- meta

- budget

- play pattern

- user preference

- support density

- table tolerance

- current weaknesses

Example:

Card:

Demonic Tutor

Global:

Efficient tutor.

Risk in Project A:

None. High-power combo accepted.

Risk in Project B:

Violates low-tutor philosophy.

Risk in Project C:

Raises table threat perception.

## 15. Project-Specific Overrides

Project-Specific Overrides allow a Project to reinterpret global knowledge without modifying global facts.

15.1 Override Rules

A project override may:

- change a card’s project role

- mark a card as core

- mark a card as replaceable

- mark a card as off-plan

- mark a card as pet card

- mark a card as accepted risk

- mark a package as accepted/rejected

- mark a combo as accepted/rejected

- adjust confidence inside the project

- explain why global advice does not apply

A project override may not:

- change oracle text

- change legality

- change official card metadata

- rewrite canonical facts

15.2 Override Example

Global Card Knowledge:

Rhystic Study is a strong card draw engine.

Project Override:

Rejected for this deck because it pushes the list toward generic blue goodstuff and damages originality.

Impact:

Do not recommend unless the user asks for raw power upgrades.

15.3 Accepted Risk

Accepted Risk is a special project-specific decision.

Example:

Weakness:

Low graveyard hate.

Decision:

Accepted risk.

Rationale:

Current meta does not require dedicated graveyard hate, and slot pressure is high.

Impact:

Do not repeatedly flag this as unresolved unless meta assumptions change.

Accepted Risk prevents the system from nagging the user about intentional trade-offs.

## 16. Confidence & Uncertainty Model

The Knowledge Engine must represent confidence explicitly.

16.1 Confidence Levels

Recommended levels:

| Level | Meaning |
| --- | --- |
| certain | Canonical, verified, or directly sourced |
| high | Curated or strongly supported |
| medium | Reasonable but contextual |
| low | Weak inference or incomplete data |
| unknown | Not enough information |
| disputed | Conflicting sources or interpretations |

16.2 Validation Status

Recommended statuses:

- imported

- computed

- curated

- ai_suggested

- user_defined

- project_override

- user_accepted

- user_rejected

- simulation_supported

- validated

- deprecated

- needs_review

16.3 Required Metadata

Knowledge records should include:

- source

- confidence

- validation_status

- scope

- created_at

- updated_at

- explanation

- optional evidence references

16.4 Uncertainty Behavior

Correct behavior:

This card appears to support sacrifice synergies based on its text, but the role has not been curated yet.

Incorrect behavior:

This is definitely a core combo card.

The system should expose uncertainty instead of hiding it behind confident prose.

## 17. Knowledge Ingestion Model

Knowledge ingestion is the process of bringing information into the Knowledge Engine.

17.1 Ingestion Sources

Possible sources:

- canonical card database

- oracle text

- legalities

- rulings

- printings

- price data

- manually curated tags

- internal heuristics

- user notes

- project notes

- accepted recommendations

- rejected recommendations

- decisions

- simulation results

- gameplay observations

17.2 Ingestion Flow

Conceptual pipeline:

Raw Source

→ Normalize

→ Identify Source Type

→ Extract Facts

→ Compute Derived Data

→ Attach Source Metadata

→ Validate

→ Store

→ Expose to Analysis / Reasoning / Simulation

17.3 AI-Assisted Ingestion

AI may assist with:

- proposing functional roles

- proposing risk tags

- detecting possible synergies

- summarizing card function

- proposing combo candidates

- identifying possible project overrides

- suggesting archetype relationships

But AI-assisted ingestion creates draft knowledge.

It does not create trusted knowledge by default.

AI-suggested knowledge should be:

- scoped to project, or

- marked low confidence, or

- reviewed before becoming global curated knowledge

## 18. Knowledge Validation Model

Validation prevents the Knowledge Engine from becoming polluted.

18.1 Validation Types

| Type | Purpose |
| --- | --- |
| Source Validation | Confirms source reliability |
| Schema Validation | Confirms required fields exist |
| Rules Validation | Confirms facts match canonical data |
| Heuristic Validation | Confirms inferred classification matches rules |
| Curator Validation | Human/system owner approves knowledge |
| User Validation | User accepts knowledge inside a project |
| Simulation Validation | Test result supports or weakens a hypothesis |
| Decision Validation | Accepted/rejected decision changes project knowledge |

18.2 Knowledge Decay

Some knowledge becomes stale.

Examples:

- prices change

- legalities change

- new printings appear

- new cards create new synergies

- bracket expectations evolve

- project goals change

- user preferences change

- meta assumptions change

The Knowledge Engine should support:

- updated_at

- stale flags

- deprecated status

- refresh strategy in future phases

MVP does not need advanced refresh automation.

It does need timestamps and source metadata.

## 19. Relationship with Deck Analysis Engine

The Deck Analysis Engine uses Knowledge Engine data to understand what a DeckVersion contains.

The Knowledge Engine provides:

- card facts

- functional roles

- role weights

- synergy tags

- risk tags

- combo relationships

- archetype relationships

- project overrides

- user constraints

The Deck Analysis Engine produces:

- role density

- package density

- engine detection

- weakness detection

- unsupported card detection

- over-supported package detection

- structural findings

The Knowledge Engine knows what cards can mean.

The Analysis Engine determines what the current deck actually does.

## 20. Relationship with Reasoning Engine

The Reasoning Engine consumes knowledge.

It does not own truth.

The Reasoning Engine uses the Knowledge Engine to answer:

- What does this card do?

- What role does it perform here?

- What engine does it support?

- What package does it belong to?

- What risks does it introduce?

- What constraints does it violate?

- Is this card strong but wrong for this project?

- Is this weakness real or accepted?

- What uncertainty remains?

- What should be tested?

The Reasoning Engine may output:

- assumptions

- hypotheses

- trade-off analysis

- project-specific interpretations

- candidate recommendations

- uncertainty statements

- draft tags

- suggested tests

These outputs should be stored as reasoning data, project notes, recommendations, or hypotheses.

They should not automatically become global knowledge.

## 21. Relationship with Recommendation Engine

The Recommendation Engine uses Knowledge Engine data to create structured proposals.

A good recommendation should include:

- problem

- proposed add/cut/change

- affected role

- affected engine

- affected package

- expected benefit

- trade-off

- risk

- constraint check

- confidence

- test suggestion

The Recommendation Engine should reject or downgrade candidates when:

- they violate hard user constraints

- they damage deck identity

- they solve the wrong problem

- they duplicate an already over-supported role

- they increase an accepted risk without benefit

- they are globally strong but project-wrong

- their knowledge confidence is too low

A recommendation is valid only if it can explain why it belongs in this project.

## 22. Relationship with Simulation Engine

The Simulation Engine uses knowledge to define testable questions.

It should not test vague deck quality.

It should test specific hypotheses.

22.1 Simulation Knowledge Inputs

The Simulation Engine may use:

- mana value

- color requirements

- land types

- ramp roles

- tutor roles

- draw roles

- engine pieces

- combo pieces

- package members

- key cards

- acceptable substitutes

- opening hand criteria

- mulligan rules

- project success criteria

22.2 Example Simulation Questions

- How often does the deck open with enough mana?

- How often can the deck cast its commander on curve?

- How often does the deck access an engine piece by turn four?

- How often does the deck draw payoff without enabler?

- Does adding two rainbow lands improve color availability?

- Does cutting one ramp card hurt early development?

- Does the deck have enough equipment carriers?

- How often does a combo line assemble under defined assumptions?

22.3 Simulation Feedback

Simulation results may create or update project-scoped knowledge.

Example:

Hypothesis:

The deck lacks enough white sources for double-white spells.

Simulation:

Double-white availability by turn six is below target.

Project Knowledge:

White pip intensity risk confirmed for DeckVersion v1.3.

Simulation-derived knowledge must remain scoped to:

- project

- deck version

- test configuration

- assumptions

- sample size

- date

Simulation is evidence.

It is not universal truth.

## 23. MVP Knowledge Model

The MVP must prove that structured knowledge improves analysis and recommendations.

It should not attempt to model every possible Magic interaction.

23.1 MVP Must Include

Card Facts

- name

- oracle text

- mana cost

- mana value

- type line

- color identity

- colors

- keywords

- legalities

- basic printings

- basic prices if available

Derived Data

- card type flags

- color count

- pip intensity

- mana value bucket

- produced mana

- basic text pattern flags

Functional Roles

A compact role set:

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

Risk Tags

- high_mana_value

- color_intensive

- commander_dependent

- graveyard_dependent

- board_dependent

- low_floor

- win_more

- combo_risk

- budget_risk

- off_theme

- weak_without_support

- table_threat_signal

Project-Specific Overrides

- core card

- replaceable card

- pet card

- off-plan card

- testing card

- accepted package

- rejected package

- accepted combo

- rejected combo

- accepted risk

EngineInstances

- name

- type

- core cards

- support cards

- payoff cards

- missing pieces

- strength

- fragility

- notes

PackageInstances

- name

- type

- member cards

- target density

- actual density

- evaluation

Confidence & Source

At minimum:

- source

- confidence

- validation_status

- scope

23.2 MVP Can Use JSON For

The MVP may store these as semi-structured JSON:

- CardKnowledge

- synergy participants

- combo requirements

- reasoning rationale

- analysis metrics

- simulation configuration

- simulation results

- project-specific overrides

- engine card groups

- package card groups

This matches the Data Model principle that evolving structures can start semi-structured before normalization.

23.3 MVP Should Not Include Yet

The MVP should not require:

- full graph database

- complete combo library

- complete archetype ontology

- advanced embedding search

- automated ruling interpretation

- full EDH metagame model

- popularity-driven recommendation logic

- community knowledge contribution

- advanced collection tracking

- perfect Commander gameplay simulation

The MVP should be smaller, sharper, and useful.

23.4 MVP Success Criteria

The MVP Knowledge Engine is successful if The Workshop can:

- load reliable card facts

- classify basic functional roles

- distinguish Card from DeckCard meaning

- distinguish global knowledge from project-specific knowledge

- explain why a card matters

- explain why a strong card may be wrong

- identify basic engines

- identify basic packages

- expose uncertainty

- support deck analysis

- support recommendation rationale

- support basic simulation questions

- preserve user intent

## 24. Future Extensions

Future versions may add:

24.1 Global EngineDefinitions

Reusable engine templates across projects.

Examples:

- artifact sacrifice engine

- enchantress draw engine

- graveyard recursion engine

- storm spell-chain engine

- blink value engine

24.2 Global PackageDefinitions

Reusable package templates.

Examples:

- artifact protection package

- graveyard hate package

- cheap interaction package

- equipment carrier package

24.3 Advanced Knowledge Graph

Future graph relationships:

Card → Role

Card → Engine

Card → Package

Card → Combo

Card → Replacement

Card → Risk

Card → Archetype

Card → Constraint

This should come after MVP, not before.

24.4 Embedding-Based Retrieval

Embeddings may help with:

- semantic card search

- similar effect discovery

- hidden gem discovery

- replacement candidates

- clustering cards by function

- finding non-obvious synergy candidates

Embeddings should complement structured knowledge.

They should not replace it.

24.5 Curated Combo Library

Future combo data may include:

- exact combos

- pattern combos

- required zones

- mana requirements

- deterministic status

- failure points

- disruption points

- bracket risk

- ruling references

24.6 Meta-Aware Knowledge

Future meta knowledge may include:

- local meta threats

- common hate pieces

- expected speed

- removal density

- table tolerance

- bracket expectations

24.7 Collection-Aware Knowledge

Future collection knowledge may include:

- owned cards

- owned printings

- acquisition status

- proxy policy

- budget upgrades

- paper vs online availability

24.8 Learning From Decisions

The system may learn from:

- accepted recommendations

- rejected recommendations

- accepted risks

- repeated user preferences

- successful tests

- failed tests

- reverted changes

This learning must remain inspectable and editable.

## 25. Open Questions

- What should be the canonical external card source for MVP?

- Should popularity data be excluded from MVP to avoid bias?

- What is the smallest useful curated FunctionalRole set?

- Should role weights be qualitative or numeric in MVP?

- Should AI-suggested tags be project-only by default?

- How should global tags and user-defined tags interact?

- Should project overrides hide global knowledge or annotate it?

- What is the minimum useful combo model for MVP?

- Should pattern combos wait until after exact/project combos?

- How should accepted risks affect future weakness detection?

- How should stale price/legalities knowledge be refreshed?

- How should confidence be displayed without overwhelming the user?

- Should EngineDefinitions wait until multiple projects show repeated patterns?

- Should PackageDefinitions wait until after PackageInstances are validated?

- How much manual curation is acceptable before automation?

- What review process should promote AI-suggested knowledge to curated knowledge?

- How should rulings be connected to combo validation?

- How should The Workshop handle newly released cards with incomplete knowledge?

## 26. ADR Candidates

ADR-011 — Card Facts and Card Knowledge Are Separate

Decision: The system separates objective Card Facts from interpretive Card Knowledge.

Reason: Oracle text, legalities, and metadata must not be mixed with functional interpretation or AI-generated assumptions.

ADR-012 — AI-Suggested Knowledge Is Draft Until Validated

Decision: AI-suggested roles, synergies, combos, and risks are not trusted global knowledge until validated.

Reason: The AI is a reasoning layer, not the source of truth.

ADR-013 — Functional Roles Use a Controlled Taxonomy

Decision: Functional Roles are controlled and structured, not arbitrary freeform tag spam.

Reason: Role data must support analysis, recommendation, and reporting.

ADR-014 — DeckCard Can Override Global Card Knowledge

Decision: A DeckCard may have project-specific role overrides.

Reason: A card’s meaning depends on the deck system it belongs to.

ADR-015 — Project-Specific Knowledge Cannot Override Canonical Facts

Decision: Project overrides can reinterpret role, priority, and fit, but cannot alter oracle text, legality, or official card facts.

Reason: User intent is authoritative for deckbuilding, not for rules truth.

ADR-016 — Synergies Must Be Meaningful Engineering Relationships

Decision: The system stores synergies only when they help analysis, recommendation, simulation, or explanation.

Reason: Automatic keyword-based synergy spam would reduce trust and usefulness.

ADR-017 — MVP Prioritizes EngineInstances Over Global EngineDefinitions

Decision: MVP should model engines primarily inside DeckVersions before building a global engine ontology.

Reason: Project-specific engine understanding is more immediately useful and avoids premature abstraction.

ADR-018 — MVP Prioritizes PackageInstances Over Global PackageDefinitions

Decision: MVP should model packages primarily inside DeckVersions before building global package templates.

Reason: Package needs vary heavily by project, bracket, meta, and user philosophy.

ADR-019 — Combo Knowledge Must Distinguish Exact, Pattern, Project, Hypothetical, and Rejected Combos

Decision: The system must not collapse all combo knowledge into one category.

Reason: Combo certainty, scope, and user acceptance materially affect recommendations.

ADR-020 — Confidence and Source Are Required for Knowledge Records

Decision: Knowledge records must track source, confidence, validation status, and scope.

Reason: The system must expose uncertainty instead of hallucinating certainty.

ADR-021 — Accepted Risk Is Knowledge

Decision: Accepted risks are stored as project-specific knowledge.

Reason: Some weaknesses are intentional trade-offs and should not be repeatedly treated as unresolved errors.

ADR-022 — Popularity Is Candidate Discovery, Not Recommendation Justification

Decision: Popularity data may help discover candidates, but cannot justify inclusion by itself.

Reason: The Workshop optimizes for project fit, not generic popularity.

## 27. Foundational Knowledge Principle

A card database tells The Workshop what a card says.

The Knowledge Engine tells The Workshop what that card can mean.

A Project tells The Workshop what that card means here.

The AI explains why that meaning matters.

The Workshop should not merely say:

“This card is good.”

It should say:

“This card fits this project because it performs this role, supports this engine, solves this weakness, respects these constraints, introduces these risks, and is supported by this evidence.”

That is the difference between a card suggestion tool and a Deck Engineering Platform.

The list is the output.

The reasoning is the product.
