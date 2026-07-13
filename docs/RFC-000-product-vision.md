# RFC-000 — The Workshop Product Vision

Status

Draft Sprint 0 Document Owner: Product Owner / Domain Expert Architecture Owner: Software Architect / CTO

## 1. Mission

The Workshop is not a deck builder.

The Workshop is a Deck Engineering Platform.

Its purpose is not to automatically generate Commander decks.

Its purpose is to help players engineer better decks through structured analysis, explainable reasoning, iteration, testing, and documentation.

The Workshop treats a deck as an engineered system, not as a pile of individually powerful cards.

A deck is not just a list.

A deck is a system.

The Workshop exists to understand, improve, and document that system.

## 2. Core Product Thesis

Most deckbuilding tools answer the question:

“What cards should I add?”

The Workshop answers a better question:

“Given this player, this commander, this strategy, this budget, this meta, and this philosophy, what changes actually make the deck better — and why?”

The Workshop does not optimize decks in the abstract.

It improves a specific deck, for a specific player, under a specific brief.

A recommendation that is powerful in general but wrong for the user’s context is not a good recommendation.

## 3. Product Philosophy

The Workshop does not assume a universal definition of a “good deck”.

A deck can be optimized for:

- power

- consistency

- explosiveness

- resilience

- theme

- budget

- originality

- table experience

- bracket compliance

- online play with no budget limits

- low tutor usage

- high combo density

- casual pacing

- specific play patterns

Because of this, every serious project begins with a Design Brief.

The Design Brief defines what “better” means for that specific deck.

Without context, optimization is guesswork.

## 4. The Design Brief

Every serious deck engineering project should define:

- Format

- Commander

- Strategy

- Design Philosophy

- Bracket / Power Target

- Budget

- Meta

- Personal Constraints

- Desired Play Pattern

- Success Criteria

The Design Brief is required for meaningful engineering analysis, but it does not need to be heavy at the start.

The Workshop should support both:

- a lightweight brief for quick iteration

- a complete brief for deeper analysis and long-term project work

The goal is not bureaucracy.

The goal is alignment.

The system must know what kind of deck the user is trying to build before judging whether a change is good.

## 5. Deck Identity

The Workshop must preserve the intended identity of a deck while improving its structure.

A deck is not defined only by its commander or colors.

It is defined by its intended experience, engines, constraints, and personality.

For example:

- A Myr deck may not really be “artifact tribal”; it may be a combo-control engine disguised as tribal.

- An Emry equipment deck may not be generic Voltron; it may be a recursion-based equipment toolbox.

- A Zur deck may not be a normal enchantment deck; it may be a risk-heavy forbidden-aura engine built around brinkmanship.

The Workshop must avoid technically correct recommendations that make the deck less itself.

Improvement must not become homogenization.

## 6. Product Model

The Workshop is organized around Projects, not isolated decklists.

A Project represents the full engineering context around a deck.

A Project may contain:

- Design Brief

- Current Decklist

- Card Pool / Collection Context

- Components

- Engines

- Packages

- Mana Base

- Interaction Suite

- Protection Suite

- Win Conditions

- Weaknesses

- Engineering Reports

- Simulation Results

- Versions

- Notes

- Decisions

- Backlog

A decklist is only one artifact inside a Project.

The Project is the real unit of work.

## 7. Analysis Before Recommendation

The Workshop separates analysis from recommendation.

Before suggesting changes, the system should first explain what is happening inside the deck.

Analysis answers questions like:

- What is the deck trying to do?

- What are its main engines?

- What are its win paths?

- What resources does it need?

- Where does it fail?

- What is too slow?

- What is inconsistent?

- What is under-supported?

- What is over-supported?

- Which cards are structurally important?

- Which cards are replaceable?

Only after analysis should the system recommend changes.

This prevents the platform from becoming a generic “add these staples” machine.

## 8. Engineering Principles

The Workshop must follow these principles.

8.1 Always Explain Why

A recommendation without reasoning is incomplete.

The system must explain:

- what problem the change solves

- what role the card plays

- what synergy it supports

- what trade-off it introduces

- what kind of hand, board state, or engine it improves

8.2 Popularity Is Evidence, Never Proof

Popularity data can suggest candidates.

It cannot justify inclusion by itself.

A card being commonly played does not mean it belongs in this project.

8.3 No Generic Best-in-Slot by Default

The Workshop should avoid generic best-in-slot recommendations unless they directly serve the project’s brief.

A strong card can still be wrong if it damages:

- deck identity

- budget

- bracket target

- play pattern

- originality

- table experience

- user preference

8.4 Evaluate Interactions Before Individual Power

A card is valuable because of what it does inside the system.

The Workshop should prioritize relationships between cards, not isolated card quality.

8.5 Reason About Engines Before Individual Cards

The platform should identify and evaluate:

- mana engines

- card draw engines

- recursion engines

- tutor chains

- protection layers

- combo lines

- pressure plans

- lock pieces

- win conditions

- recovery plans

The deck should be understood as a set of interacting subsystems.

8.6 Analyze Consistency Before Optimization

A powerful line that rarely happens is not automatically better than a weaker line that consistently appears.

The Workshop must care about:

- opening hands

- mana availability

- color requirements

- curve

- redundancy

- card access

- setup cost

- fail states

- recovery after disruption

8.7 Respect the User’s Philosophy

The Workshop must not force a player into a deckbuilding philosophy they do not want.

It should not turn:

- a casual deck into a tutor-heavy combo deck

- a combo deck into fair midrange

- a theme deck into generic goodstuff

- a budget deck into a proxy-only pile

- a weird personal brew into an EDHREC average list

The user defines the target.

The system helps engineer toward that target.

8.8 Explain Trade-Offs

When multiple solutions satisfy the same objective, The Workshop must explain the trade-offs.

For example:

- speed vs resilience

- tutors vs variance

- power vs table friendliness

- budget vs efficiency

- protection vs proactive development

- theme density vs interaction density

- explosiveness vs consistency

The best recommendation is not always the strongest card.

It is the best fit for the stated objective.

## 9. Versioning and Reversibility

Every meaningful deck change should be traceable, reversible, and tied to a stated hypothesis.

The Workshop should track:

- what changed

- why it changed

- what problem the change was meant to solve

- what risk the change introduced

- what test or observation justified the change

- whether the change succeeded, failed, or needs more data

Deckbuilding should become an iterative engineering loop:

Hypothesis → Change → Test → Result → Decision

The user should be able to understand not only what the deck looks like now, but how it got there.

## 10. Simulation Philosophy

Simulation is a progressive capability.

The Workshop should not treat simulation as one monolithic feature.

Simulation may include:

- opening hand analysis

- mana consistency checks

- curve analysis

- color availability checks

- goldfish testing

- engine access probability

- win-condition access probability

- mulligan quality checks

- resilience testing

- advanced gameplay simulation

Early simulation can be simple.

It is still useful if it answers a concrete deckbuilding question.

The goal of simulation is not to perfectly reproduce Commander gameplay.

The goal is to generate evidence that helps evaluate deckbuilding hypotheses.

## 11. AI Role

The AI is not the source of truth.

The AI is a reasoning layer.

Its role is to:

- interpret the Design Brief

- identify systems inside the deck

- ask useful clarifying questions

- make explicit assumptions when needed

- reason about trade-offs

- explain recommendations

- propose alternatives

- challenge weak assumptions

- document decisions

- help the user iterate

The AI should ask clarifying questions when missing context materially affects the recommendation.

Otherwise, it should state its assumptions clearly and let the user correct them.

The AI should behave like an experienced deck engineer, not like a random card suggestion engine.

It collaborates with the user.

It does not dictate the final deck.

## 12. Knowledge Philosophy

Knowledge comes before AI.

The Workshop should rely on structured, inspectable knowledge whenever possible.

Relevant knowledge may include:

- card database

- oracle text

- color identity

- legality

- card types

- mana value

- prices

- card availability

- synergy tags

- functional roles

- combo relationships

- rulings

- user collection

- deck history

- prior decisions

- project notes

- simulation results

AI should reason over this knowledge.

AI should not hallucinate it.

When structured knowledge is incomplete, the system must expose uncertainty instead of inventing facts.

The correct behavior is:

“I do not have enough reliable information to assert this.”

Not:

“I will pretend to know.”

## 13. User Experience Vision

The Workshop should feel like entering an engineering studio for Commander decks.

The experience should be structured, but not sterile.

The user should feel that the system understands:

- what they are trying to build

- why they enjoy that kind of deck

- what constraints matter

- what trade-offs they are willing to accept

- what kind of table experience they want

- what kind of recommendations would ruin the deck for them

The Workshop should help the user move from:

“Here is my decklist.”

to:

“Here is the system I am building, here is what it does well, here is where it fails, and here is the next engineering step.”

The product should make the user a better deckbuilder, not just produce a better list.

## 14. Internal Operating Model

The Workshop project uses clear internal roles.

Product Owner / Domain Expert

Responsible for:

- Commander domain judgment

- player needs

- deckbuilding taste

- UX expectations

- project priorities

- evaluation of recommendations

- defining what “good” means per project

Software Architect / CTO

Responsible for:

- system architecture

- data model

- reasoning model

- documentation structure

- technical decisions

- implementation strategy

- ADR discipline

Software Engineer

Responsible for:

- implementation

- code quality

- database work

- integrations

- testing

- automation

- tooling

These roles exist to keep the project organized.

They are not user-facing product roles.

## 15. Documentation Model

The Workshop uses documentation as a product asset.

The documentation structure is:

- 📘 000 - Product Vision

- 📘 001 - Architecture

- 📘 002 - Database

- 📘 003 - Knowledge Engine

- 📘 004 - Reasoning Engine

- 📘 005 - Simulation Engine

- 📘 006 - UI & UX

- 📘 007 - Sprint Log

- 📘 008 - Backlog

- 📘 009 - ADR

- 📘 010 - Testing

Each document has one purpose.

The goal is to avoid one chaotic mega-chat and instead build a readable, reconstructable product history.

Six months from now, the team should be able to understand the entire project by reading the documentation.

## 16. Non-Goals

The Workshop is not trying to be:

- a generic deck generator

- an EDHREC clone

- a popularity scraper

- a chatbot that casually suggests cards

- a cEDH-only optimizer

- a casual-only deck helper

- a universal judge of what Commander should be

- a replacement for player taste

The Workshop is also not trying to remove the user from deckbuilding.

The player remains the designer.

The system is the engineering assistant.

## 17. Success Criteria

The Workshop is successful if it can:

- understand a player’s deckbuilding intent

- analyze a deck in context

- preserve deck identity

- identify structural weaknesses

- explain recommendations clearly

- avoid generic best-in-slot suggestions

- compare alternatives through trade-offs

- simulate relevant play patterns

- track versions and decisions

- support different deck philosophies

- avoid hallucinated card knowledge

- produce useful engineering reports

- help the user make better deckbuilding decisions

The final test is simple:

After using The Workshop, the user should understand their deck better than before.

## 18. Foundational Principle

The Workshop does not build decks for the user.

The Workshop engineers decks with the user.

The list is the output.

The reasoning is the product.
