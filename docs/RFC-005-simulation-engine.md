# RFC-005 — The Workshop Simulation Engine

Status: Draft Version: v0.2 Sprint: 0 Depends on: RFC-000 — Product Vision, RFC-001 — System Architecture, RFC-002 — Database / Data Model, RFC-003 — Knowledge Engine, RFC-004 — Reasoning Engine Document Type: Simulation Model / Architecture Architecture Owner: Software Architect / CTO Product Owner: Product Owner / Domain Expert

## 1. Purpose

This document defines the Simulation Engine for The Workshop.

The Simulation Engine is responsible for producing structured evidence that helps evaluate deckbuilding hypotheses.

The Simulation Engine does not attempt to perfectly reproduce a multiplayer Commander game.

It does not replace player judgment.

It does not decide which cards should be played.

It does not generate recommendations by itself.

Its purpose is to help The Workshop answer questions such as:

- How often does this deck keep a playable opening hand?

- How often does this deck hit its early land drops?

- How often can this deck produce required colors by a target turn?

- How often can this deck cast its commander on curve?

- How often does this deck access a key engine piece?

- How often does this deck find ramp, draw, protection, or interaction early enough?

- Does this proposed change materially improve the problem it claims to solve?

- Does the deck fail because of mana, access, density, speed, or unsupported engines?

- Is a gameplay complaint supported by repeatable evidence?

The Simulation Engine exists to turn deckbuilding arguments into testable questions.

## 2. Simulation Engine Thesis

Simulation is evidence for hypotheses.

It is not a generic deck score.

The Workshop should not ask:

“Is this deck good?”

It should ask:

“Given this deck version, this brief, this mulligan policy, this test configuration, and this hypothesis, what happens often enough to matter?”

A useful simulation does not need to model every opponent, every stack interaction, every political choice, or every possible game state.

A useful simulation needs to answer a concrete engineering question.

Example:

Bad simulation question:

“Is this deck powerful?”

Good simulation question:

“How often does DeckVersion v1.2 produce at least two white sources by turn six, assuming the deck wants to cast Organic Extinction in the midgame?”

The Simulation Engine should make uncertain reasoning more grounded.

It should not create false precision.

## 3. Scope

The Simulation Engine is responsible for:

- defining simulation test types

- accepting simulation questions

- selecting a target DeckVersion

- reading relevant deck, knowledge, and analysis data

- applying a test configuration

- running repeatable simulations

- producing metrics

- identifying failure patterns

- storing SimulationRuns

- storing SimulationResults

- exposing limitations

- supporting comparison between deck versions

- providing evidence to the Reasoning Engine

- supporting Recommendation and Decision workflows

The Simulation Engine is not responsible for:

- canonical card facts

- card role classification

- deck identity interpretation

- recommendation generation

- user decisions

- deck version creation

- final report writing

- full Commander game simulation

- perfect rules enforcement

- political gameplay modeling

- opponent behavior modeling in MVP

Those responsibilities belong to other modules.

## 4. Core Principle

The Simulation Engine must test specific hypotheses.

A SimulationRun should always have a test question.

A simulation without a test question is usually noise.

Correct:

“Test whether adding City of Brass and Mana Confluence improves white source availability by turn six.”

Incorrect:

“Run 100 games and tell me if the deck is better.”

The Simulation Engine should produce evidence that can be attached to:

- a Weakness

- a Hypothesis

- a Recommendation

- a Decision

- a Report

- a DeckVersion comparison

- a BacklogItem

If a simulation result cannot influence reasoning, recommendation, decision, or reporting, it should probably not be stored.

## 5. Position in the System

The Simulation Engine sits after analysis and reasoning.

The standard flow is:

User Input → Project Context → DeckVersion → Knowledge Retrieval → Deck Analysis → Reasoning Hypothesis → Simulation Question → SimulationRun → SimulationResult → Reasoning Interpretation → Recommendation / Decision / Report

The Simulation Engine does not decide what the result means in isolation.

The Reasoning Engine interprets simulation results against the Design Brief.

Example:

Simulation Result:

“The deck casts its commander by turn three in 41% of simulations.”

That result is not automatically good or bad.

Reasoning interpretation depends on context:

- For an explosive commander-centric deck, 41% may be too low.

- For a slower control deck, 41% may be acceptable.

- For a casual battlecruiser deck, commander-on-curve may not matter.

- For a deck where the commander is optional, the metric may be irrelevant.

Simulation produces evidence.

Reasoning creates judgment.

## 6. Inputs

The Simulation Engine consumes structured data from other modules.

6.1 Project Context

The Project provides:

- project id

- format

- commander

- current deck version

- design brief

- success criteria

- user constraints

- meta assumptions

- accepted risks

- previous decisions

- relevant notes

Simulation must respect project context.

A test that ignores the project brief may produce technically correct but useless evidence.

6.2 DeckVersion

Every SimulationRun must reference a specific DeckVersion.

The Simulation Engine must know exactly which decklist was tested.

Required DeckVersion inputs include:

- deck version id

- card list

- quantities

- zones

- commander

- categories

- project-specific role overrides

- included cards

- excluded cards

Simulation evidence is meaningless without the exact deck state tested.

6.3 Card Facts

The Simulation Engine consumes Card Facts from the Card Knowledge Base.

Relevant facts may include:

- mana cost

- mana value

- color identity

- card types

- produced mana

- oracle text

- keywords

- land status

- legality

- faces

- modal properties where available

The Simulation Engine should not invent card facts.

If a required card fact is missing, the simulation should either fail clearly or run with explicit limitations.

6.4 Card Knowledge

The Simulation Engine may consume Card Knowledge such as:

- ramp roles

- mana fixing roles

- tutor roles

- card draw roles

- card selection roles

- protection roles

- interaction roles

- engine piece tags

- combo piece tags

- payoff tags

- enabler tags

- package membership

- project-specific overrides

This allows simulations to test access to functional groups, not only named cards.

Example:

“How often does the deck access any engine piece by turn four?”

requires knowledge of which cards count as engine pieces in that specific project.

6.5 Analysis Reports

The Simulation Engine may consume prior AnalysisReport data, including:

- mana curve

- color pip pressure

- land count

- ramp density

- draw density

- role density

- package density

- detected weaknesses

- engine structure

Analysis can help define what needs to be simulated.

6.6 Reasoning Hypotheses

The Reasoning Engine may create a hypothesis that becomes a simulation request.

Example:

Hypothesis:

“The deck is not failing because it lacks payoffs. It is failing because it cannot reliably access mana acceleration early enough.”

Simulation Question:

“How often does the deck have ramp access by turn two or turn three?”

The Simulation Engine exists to test that kind of claim.

## 7. Outputs

The Simulation Engine produces SimulationRuns and SimulationResults.

7.1 SimulationRun

A SimulationRun stores the test setup.

It should answer:

- What question was tested?

- Which DeckVersion was tested?

- What simulation type was used?

- What assumptions were applied?

- How many iterations were run?

- What mulligan policy was used?

- What success criteria were used?

- What seed was used, if any?

- What status did the run finish with?

7.2 SimulationResult

A SimulationResult stores the test output.

It should include:

- summary

- metrics

- observations

- failure patterns

- confidence

- limitations

- created timestamp

The result should be both machine-readable and human-readable.

Raw metrics can be stored as JSON.

The interpreted summary should be understandable by the user.

## 8. Access, Castability, and Functional Availability

The Simulation Engine must distinguish between access, castability, and functional availability.

These are related but not equivalent.

8.1 Access

Access means the deck has seen, drawn, tutored, or otherwise reached a card, role, or package.

Example:

The deck has drawn Organic Extinction by turn six.

Access alone does not mean the card can be used.

8.2 Castability

Castability means the deck can pay the required mana cost and color requirements under the simulation assumptions.

Example:

The deck has Organic Extinction in hand and can produce two white mana by turn six.

Castability is especially important for:

- commanders

- color-intensive spells

- high mana value cards

- interaction that must be available on time

- engine pieces that must be deployed early

8.3 Functional Availability

Functional availability means the card, role, or engine can actually perform its intended function in the deck context.

Example:

Krark-Clan Ironworks is not functionally available as an artifact sacrifice mana engine if the deck has no artifact fuel.

Example:

An equipment payoff is not functionally available if the deck has no carrier, no equip line, or no relevant body.

Example:

A payoff is not functionally available if the deck has no enabler.

The Simulation Engine should avoid treating “card seen” as equivalent to “plan online.”

This distinction is critical for engine access, combo access, and goldfish testing.

## 9. MVP Simulation Types

The MVP should support a limited set of simulations that produce immediate deckbuilding value.

9.1 Opening Hand Simulation

Purpose:

Evaluate opening hand quality.

Possible questions:

- How often does this deck open a keepable hand?

- How often does it open with two or more lands?

- How often does it open with at least one ramp piece?

- How often does it open with early interaction?

- How often does it open with a dead high-cost-heavy hand?

Possible metrics:

- keepable hand rate

- zero-land hand rate

- one-land hand rate

- two-to-four-land hand rate

- five-plus-land hand rate

- ramp-in-opener rate

- early-play rate

- color-access-in-opener rate

- mulligan frequency

9.2 Land Drop Probability

Purpose:

Evaluate whether the deck naturally develops mana.

Possible questions:

- How often does the deck hit land drop one?

- How often does the deck hit land drop two?

- How often does the deck hit land drop three?

- How often does the deck hit land drop four?

- Does the deck consistently reach the mana needed for its key turns?

Possible metrics:

- land drop by turn

- missed land drop frequency

- average lands seen by turn

- probability of reaching X lands by turn Y

9.3 Mana Consistency

Purpose:

Evaluate whether the deck produces enough mana at the right time.

Possible questions:

- How often does the deck have three mana by turn three?

- How often does the deck have four mana by turn four?

- How often does ramp accelerate the deck ahead of natural land drops?

- Does cutting a ramp card materially hurt early development?

Possible metrics:

- available mana by turn

- ramp access by turn

- average mana production

- failure rate by target turn

9.4 Color Availability

Purpose:

Evaluate whether the deck can produce required colors.

Possible questions:

- How often does the deck have the required colors to cast its commander on curve?

- How often does the deck have double-white by turn six?

- How often does the deck have blue plus red by turn three?

- Does adding rainbow lands improve color availability enough to justify the cuts?

Possible metrics:

- source availability by turn

- color pair availability

- double-pip availability

- commander color availability

- failure rate for key color requirements

9.5 Ramp Access

Purpose:

Evaluate access to acceleration.

Possible questions:

- How often does the deck have ramp by turn two?

- How often does the deck have ramp by turn three?

- Does the deck have enough early development for its intended speed?

- Does adding fast mana improve explosiveness enough to matter?

Possible metrics:

- ramp-in-opener rate

- ramp-by-turn rate

- early-ramp density performance

- average acceleration turn

9.6 Engine Access

Purpose:

Evaluate whether the deck can access its core systems.

Engine access is not single-card access.

It is access to the minimum functional configuration required for an engine to begin operating.

Possible questions:

- How often does the deck see a core engine piece by turn four?

- How often does the deck have both enabler and payoff?

- How often does the deck draw payoff without support?

- How often does the deck access equipment carrier plus equipment?

- How often does the deck access artifact sacrifice outlet plus artifact fuel?

- How often does the deck access spell-chain support plus card flow?

- How often does the deck access recursion plus a meaningful graveyard target?

Possible metrics:

- engine piece access by turn

- enabler access

- payoff access

- enabler-plus-payoff rate

- minimum engine configuration rate

- partial engine access rate

- dead payoff rate

- unsupported engine rate

9.7 Win Condition Access

Purpose:

Evaluate whether the deck can find a way to win.

Possible questions:

- How often does the deck access at least one win condition by turn X?

- How often does the deck draw finishers without engine support?

- Does the deck have too many win conditions or too few?

- Are win conditions clogging early hands?

Possible metrics:

- win condition access by turn

- finisher-in-opening-hand rate

- unsupported finisher rate

- redundant finisher rate

9.8 Mulligan Quality

Purpose:

Evaluate whether mulligan rules materially change deck performance.

Possible questions:

- How often does the deck keep seven?

- How often does it need to mulligan?

- How much does one free mulligan improve opening hand quality?

- Does the deck rely too heavily on favorable mulligan policy?

Possible metrics:

- keep rate at seven

- keep rate after one mulligan

- average final hand size

- failed hand rate after mulligans

- hand quality distribution

9.9 Basic Goldfish Testing

Purpose:

Evaluate simplified solitaire development.

Goldfish simulation should be treated carefully.

It does not represent real Commander games.

It can still answer useful questions about:

- setup speed

- early sequencing

- engine access

- mana development

- average goldfish setup turn

- failure patterns

- dead draws

- clunky packages

Possible questions:

- How quickly does the deck establish its main engine?

- How often does the deck threaten a win under simplified assumptions?

- Does the modified version goldfish faster than the baseline?

- Is the deck failing because of speed, access, or mana?

Possible metrics:

- average setup turn

- average threat turn

- engine access turn

- fizzled run rate

- no-engine rate

- mana failure rate

- payoff-without-enabler rate

Goldfish should not overclaim.

Correct:

“In simplified goldfish assumptions, this version accesses an engine by turn four in 63% of runs.”

Incorrect:

“This deck wins on turn four 63% of the time.”

Goldfish results should always include limitations.

## 10. Goldfish Complexity Levels

Goldfish simulation should be introduced progressively.

The MVP should not attempt full gameplay simulation.

10.1 Level 1 — Draw / Access Goldfish

This level tracks what the deck sees by each turn.

It can answer questions such as:

- Did the deck see enough lands?

- Did the deck see ramp?

- Did the deck see an engine piece?

- Did the deck see payoff without enabler?

- Did the deck see a win condition?

This level does not attempt realistic sequencing.

10.2 Level 2 — Mana Development Goldfish

This level adds simplified land drop and mana development assumptions.

It can answer questions such as:

- How much mana is available by each turn?

- Can the commander be cast on curve?

- Can a color-intensive spell be cast by the target turn?

- Does early ramp improve development?

This should be the main MVP goldfish target.

10.3 Level 3 — Heuristic Sequencing Goldfish

This level attempts simplified play sequencing.

It may consider:

- playing ramp before payoff

- casting commander when available

- deploying engine pieces

- using simple card draw or selection

- attempting a known line when pieces are available

This level is useful but risky.

It should be experimental until the assumptions are transparent and reliable.

MVP should prioritize Level 1 and Level 2 before attempting Level 3.

## 11. Simulation Questions

A SimulationQuestion should be explicit.

Recommended fields:

- question

- hypothesis

- target DeckVersion

- simulation type

- metric

- success target

- assumptions

- related weakness

- related recommendation

- related decision

- expected interpretation

Example:

Question:

“How often does DeckVersion v1.3 produce two white sources by turn six?”

Hypothesis:

“The mana base does not reliably support Organic Extinction.”

Simulation Type:

color_availability

Metric:

double-white availability by turn six

Success Target:

At least 80%

Interpretation:

If below target, prioritize mana base changes before adding more white-intensive spells.

## 12. Simulation Configuration

Each simulation type should have a clear configuration.

Common configuration fields:

- iterations

- seed

- turn_limit

- mulligan_policy

- play_draw

- commander_cast_target_turn

- keep_rules

- success_conditions

- failure_conditions

- key_cards

- role_groups

- engine_groups

- package_groups

- assumptions

- excluded_cards

- special_rules

- limitations

MVP should keep configuration simple.

The system should prefer understandable assumptions over opaque complexity.

## 13. Mulligan Policy Model

Mulligan policy affects results heavily.

The Simulation Engine must make mulligan assumptions explicit.

Possible MVP policies:

- no_mulligan

- london_mulligan

- one_free_mulligan_then_london

- commander_casual_free_mulligan

- custom

The result must show which policy was used.

Example:

“This result assumes one free mulligan, then London mulligan.”

The same deck may look significantly different under a stricter policy.

## 14. Playability Rules

Opening hand simulations require keepability logic.

MVP keepability can start with simple rules.

Example keepable hand criteria:

- at least two lands

- at least one playable early spell or ramp source

- enough color access for early plays

- not overloaded with high mana value cards

- not missing all relevant action

Project-specific keep rules should be allowed.

Example:

A storm deck may keep a risky hand with fast mana and card draw.

A control deck may require interaction.

A commander-centric deck may require access to commander colors.

A graveyard deck may value discard outlets or self-mill.

Keepability is contextual.

The Simulation Engine should support default rules, then allow project overrides.

## 15. Engine Simulation Model

Engine simulation should focus on access, castability, and functional availability.

For MVP, the system should test whether the deck can reach the minimum functional configuration of an engine.

An EngineAccess test may define:

- core pieces

- enablers

- fuel

- converters

- payoffs

- outlets

- acceptable substitutes

- required combinations

- target turn

- success condition

Example:

Equipment Recursion Toolbox

Success condition by turn four:

- at least one equipment

- at least one carrier or access to commander

- enough mana to deploy relevant pieces

- recursion, tutor access, or reload path if required by the engine definition

Example:

Artifact Sacrifice Mana Engine

Success condition by turn five:

- artifact fuel

- sacrifice outlet

- payoff or mana sink

- enough mana to deploy the relevant pieces

Example:

Storm Spell-Chain Engine

Success condition by turn five:

- mana boost or cost reduction

- card flow

- sufficient spell density

- payoff, recovery, or reload path

The system should not pretend that engine access equals a won game.

It only means the deck found the required infrastructure.

## 16. Tutor Modeling Boundary

Tutors significantly affect access probabilities.

The Simulation Engine must handle tutors carefully because poor tutor modeling can create misleading results.

MVP may support three tutor modes.

16.1 Ignore Tutors

Tutors are treated as normal cards and do not increase access to their targets.

This is conservative but may underestimate consistency.

16.2 Tutor as Access Modifier

A tutor may count as access to a constrained group of valid targets if:

- the tutor is castable by the target turn

- the target group is explicitly defined

- the tutor restriction is known

- the simulation question allows this simplification

This is useful for engine access and combo access tests.

16.3 Full Tutor Sequencing

The simulator chooses tutor targets based on game state and strategic priority.

This is not required for MVP.

Full tutor sequencing should be deferred until the system has stronger card knowledge, validated target groups, and reliable sequencing rules.

All SimulationResults involving tutors must state how tutors were modeled.

## 17. Failure Pattern Detection

The Simulation Engine should identify recurring failure patterns.

Examples:

- zero-land hands

- one-land hands

- color screw

- missed third land drop

- ramp not found

- payoff without enabler

- enabler without payoff

- commander not castable

- commander accessible but not worth casting under assumptions

- too many high mana value cards early

- dead interaction in goldfish context

- win condition without setup

- engine access too late

- mana available but no action

- action available but wrong colors

- tutor found but target not castable

- engine piece found but not functionally available

Failure patterns are often more useful than aggregate success rates.

Example:

“The deck does not simply lack speed. In failed runs, the most common issue is drawing payoff cards before mana engines.”

That is actionable evidence.

## 18. Comparison Simulations

The Simulation Engine should support comparing DeckVersions.

Common comparisons:

- baseline vs proposed change

- current version vs test candidate

- paper budget version vs online no-budget version

- tutor package vs redundancy package

- utility land package vs rainbow fixing package

- high-power branch vs identity-preserving branch

Comparison should show:

- changed deck versions

- test question

- shared configuration

- metric deltas

- confidence

- limitations

- interpretation notes

Example:

DeckVersion v1.2:

Double-white by turn six: 58%

DeckVersion v1.3:

Double-white by turn six: 77%

Delta:

+19 percentage points

Interpretation:

The mana base change materially improves the tested problem, but still may be below target if the success criterion is 80%.

## 19. Simulation Result Interpretation

The Simulation Engine produces results.

The Reasoning Engine interprets them.

However, SimulationResult should include a basic readable summary.

Example:

Summary:

“Across 1,000 iterations, the deck produced double-white by turn six in 58% of runs. The most common failure pattern was opening with only one white-producing source and failing to find a second by the target turn.”

Limitations:

“This test does not account for opponent interaction, tutor sequencing, or gameplay decisions beyond basic draw and land-drop assumptions.”

Interpretation should remain cautious.

## 20. Confidence and Limitations

Every SimulationResult should expose limitations.

Possible limitation types:

- simplified sequencing

- no opponent interaction

- no stack interaction

- incomplete card behavior modeling

- unvalidated card roles

- small sample size

- incomplete mulligan model

- incomplete tutor modeling

- incomplete modal card modeling

- no politics

- no threat assessment

- assumes optimal land play

- assumes simple keep rules

The system should never hide simulation weakness behind precise numbers.

A number with bad assumptions is not strong evidence.

## 21. Simulation Invalidation and Staleness

Simulation evidence may become stale.

A SimulationRun should remain historically preserved, but it may no longer be valid as current evidence.

A simulation may become stale when:

- the tested DeckVersion is no longer current

- the decklist changes

- the commander changes

- relevant card facts are updated

- relevant card knowledge is corrected

- role tags or project overrides change

- engine definitions change

- package membership changes

- mulligan policy changes

- success criteria change

- the Design Brief changes

- meta assumptions change

- the simulation configuration changes

- the original test question is no longer relevant

Stale simulation results should not be deleted.

They should be marked as historical evidence.

The system should distinguish between:

- current evidence

- historical evidence

- superseded evidence

- invalid evidence

Example:

A color availability simulation for DeckVersion v1.2 remains useful for understanding why a mana base change was accepted.

It should not be used as evidence for DeckVersion v1.5 unless the relevant mana base is unchanged or the result is rerun.

## 22. Simulation Persistence Rules

Simulation should be persisted when it influences:

- a Recommendation

- a Decision

- a Report

- a Weakness

- a Hypothesis

- a DeckVersion comparison

- a future revisit item

Simulation does not need to be persisted when it is:

- casual exploration

- discarded

- invalid due to bad configuration

- not used for any decision

- obviously superseded before review

If saved, a SimulationRun and SimulationResult must be traceable to the exact DeckVersion tested.

## 23. Relationship with Knowledge Engine

The Knowledge Engine supplies the meaning needed for simulation.

It tells the Simulation Engine:

- which cards are lands

- which cards produce mana

- which cards are ramp

- which cards are draw

- which cards are tutors

- which cards are engine pieces

- which cards are payoffs

- which cards are enablers

- which cards are protection

- which cards belong to a package

- which cards are accepted substitutes

- which roles are project-specific

The Simulation Engine must not create trusted card knowledge by itself.

However, simulation results may create project-scoped evidence.

Example:

Simulation-derived project knowledge:

“DeckVersion v1.3 has confirmed white-source consistency risk under the tested configuration.”

This evidence is scoped to:

- project

- deck version

- simulation configuration

- assumptions

- sample size

- date

Simulation-derived knowledge is not universal card knowledge.

## 24. Relationship with Reasoning Engine

The Reasoning Engine defines what should be tested.

The Simulation Engine produces evidence.

The Reasoning Engine interprets that evidence.

Example:

Reasoning Hypothesis:

“The deck has enough win conditions, but not enough access to its engine.”

Simulation Question:

“How often does the deck access at least one core engine piece by turn four?”

Simulation Result:

“Engine access by turn four occurs in 46% of runs.”

Reasoning Interpretation:

“If the deck wants explosive early engine development, this supports adding redundancy, tutors, or card selection. If the deck is intended to be slower, this may be acceptable.”

Simulation does not make the decision.

It changes confidence.

## 25. Relationship with Recommendation Engine

The Recommendation Engine may request simulation before finalizing or presenting a recommendation.

Examples:

- Test mana base change before recommending cuts.

- Test ramp density before adding expensive top-end cards.

- Test engine access before adding more payoffs.

- Test opening hand quality before reducing land count.

- Test tutor package impact before increasing combo density.

A recommendation can include simulation evidence.

Example:

“Add two rainbow lands because the color availability simulation improves double-white access by turn six from 58% to 77%, with the trade-off of cutting two utility lands.”

A recommendation without evidence can still be valid, but high-impact or uncertain recommendations should prefer simulation when possible.

## 26. Relationship with Decision Log

Simulation evidence should support decisions.

A Decision may reference:

- SimulationRun

- SimulationResult

- tested DeckVersion

- compared DeckVersion

- key metric

- interpretation

- accepted risk

- reason for accepting, rejecting, modifying, or testing further

Example:

Decision:

Accept mana base change as experiment.

Evidence:

Color availability improved from 58% to 77% by turn six.

Risk Accepted:

Reduced utility land density.

Next Step:

Track real games to confirm whether the improved color access matters in practice.

The Decision Log turns simulation evidence into project memory.

## 27. MVP Simulation Model

The MVP Simulation Engine should be small and useful.

27.1 MVP Must Include

The MVP must support:

- SimulationRun entity

- SimulationResult entity

- simulation tied to DeckVersion

- explicit test question

- opening hand simulation

- land drop probability

- color availability

- mana consistency

- ramp access

- engine access

- basic mulligan policy

- basic goldfish Level 1 and Level 2

- failure pattern detection

- comparison between two DeckVersions

- readable result summaries

- JSON metrics

- explicit limitations

- stale / superseded result marking

27.2 MVP Should Prioritize

MVP should prioritize simulations that answer real deckbuilding questions:

- Can I keep hands?

- Can I cast my commander?

- Can I hit my colors?

- Can I access ramp?

- Can I access engines?

- Does this change actually improve the target problem?

27.3 MVP Should Not Include Yet

The MVP should not require:

- full Commander rules simulation

- multiplayer opponent modeling

- threat assessment

- political decision modeling

- combat optimization

- stack interaction modeling

- complete tutor sequencing

- complete modal card behavior

- full combo rules engine

- matchup simulation

- meta-specific opponent decks

- automated playtesting agent

- full heuristic sequencing goldfish as default behavior

The MVP should produce useful evidence, not fake omniscience.

## 28. Simulation Templates

28.1 Opening Hand Template

Test Question:

What opening hand quality question is being tested?

DeckVersion:

Which version is tested?

Mulligan Policy:

What mulligan assumptions are used?

Keep Criteria:

What counts as keepable?

Metrics:

- keepable hand rate

- land distribution

- ramp access

- color access

- early action access

Failure Patterns:

What caused unkeepable hands?

Limitations:

What does this test not model?

28.2 Color Availability Template

Test Question:

What color requirement is being tested?

DeckVersion:

Which version is tested?

Target Turn:

By what turn must the colors be available?

Required Colors:

What colors or pip requirements are required?

Metrics:

- availability percentage

- failure percentage

- source count

- common failure patterns

Interpretation:

How should the result affect the decision?

28.3 Engine Access Template

Test Question:

Which engine access question is being tested?

DeckVersion:

Which version is tested?

Engine:

What engine is being tested?

Required Components:

What cards, roles, or substitutes count?

Target Turn:

By what turn should the engine be accessible?

Metrics:

- core access rate

- enabler access rate

- payoff access rate

- minimum functional configuration rate

- partial engine access rate

- dead payoff rate

Failure Patterns:

Which missing component most often caused failure?

28.4 Goldfish Template

Test Question:

What simplified solitaire question is being tested?

DeckVersion:

Which version is tested?

Goldfish Level:

Level 1, Level 2, or Level 3.

Turn Limit:

How long is the simulation?

Success Condition:

What counts as success?

Sequencing Assumptions:

How are plays chosen?

Metrics:

- average setup turn

- average threat turn

- engine access turn

- mana failure rate

- fizzled run rate

- success rate

Limitations:

What gameplay realities are excluded?

28.5 Comparison Template

Test Question:

What change is being evaluated?

Baseline DeckVersion:

Which version is the control?

Candidate DeckVersion:

Which version is the test?

Shared Configuration:

What assumptions are held constant?

Metric Delta:

What changed?

Interpretation:

Did the candidate version improve the target problem enough to matter?

Trade-Off:

What was sacrificed?

## 29. Output Shape

A SimulationResult should be storable as JSON and renderable as Markdown.

Recommended MVP shape:

{

"simulation_type": "color_availability",

"test_question": "How often does the deck produce double-white by turn six?",

"deck_version_id": "deck_version_123",

"iterations": 1000,

"seed": 42,

"config": {

"target_turn": 6,

"required_colors": {

"W": 2

},

"mulligan_policy": "one_free_mulligan_then_london",

"tutor_mode": "ignore_tutors"

},

"summary": "The deck produced double-white by turn six in 58% of runs.",

"metrics": {

"success_rate": 0.58,

"failure_rate": 0.42

},

"failure_patterns": [

{

"pattern": "Only one white source found by turn six",

"frequency": 0.31

},

{

"pattern": "No white source in opening hand",

"frequency": 0.18

}

],

"confidence": "medium",

"evidence_status": "current",

"limitations": [

"Does not model tutors.",

"Assumes basic land play sequencing.",

"Does not model opponent interaction."

]

}

Readable summary:

“Across 1,000 iterations, the deck produced double-white by turn six in 58% of runs. The most common failure pattern was finding only one white source by the target turn. This supports the hypothesis that white-intensive spells are difficult to cast in the current version, but the result does not account for tutor sequencing or gameplay decisions.”

## 30. Future Extensions

Future Simulation Engine capabilities may include:

30.1 Advanced Goldfish Sequencing

Better heuristic sequencing for:

- ramp deployment

- card selection

- tutors

- commander casting

- engine assembly

- combo attempts

30.2 Tutor Modeling

Advanced modeling of tutor effects, including:

- target selection

- timing windows

- mana requirements

- strategic priority

- tutor chains

30.3 Card Selection Modeling

Model effects such as:

- scry

- surveil

- impulse draw

- looting

- cantrips

- wheels

- graveyard setup

30.4 Combo Assembly Simulation

Evaluate how often a defined combo line becomes available under simplified assumptions.

This requires curated combo knowledge.

AI-suggested combo lines should not be treated as simulation-ready unless validated.

30.5 Resilience Testing

Test simplified disruption assumptions:

- key piece removed

- commander delayed

- graveyard exiled

- artifact board wiped

- engine payoff removed

30.6 Meta-Specific Testing

Future simulations may include meta assumptions:

- expected removal density

- expected speed

- common hate pieces

- graveyard hate frequency

- artifact hate frequency

- counterspell density

30.7 Matchup Simulation

Long-term possibility only.

Not required for MVP.

Commander multiplayer matchup simulation is complex and should not be attempted before the core simulation model is trustworthy.

## 31. Open Questions

- What is the default mulligan policy for The Workshop simulations?

- Should the MVP assume one free Commander mulligan by default?

- How should keepability rules be defined per project?

- Should users be able to create custom keep rules?

- How much card sequencing should MVP goldfish attempt?

- Should tutors be ignored, approximated, or explicitly modeled in MVP?

- How should modal cards be handled in early simulations?

- How should MDFCs, split cards, adventures, and double-faced cards be represented?

- Should opening hand quality be scored numerically or categorically?

- Should simulation confidence be based on iterations, assumptions, or both?

- What minimum iteration count is acceptable for saved SimulationRuns?

- Should failed or invalid simulations be stored?

- Should SimulationRuns be automatically persisted or only saved when used?

- Should SimulationResults create project-scoped knowledge automatically?

- How should simulation compare versions with different card counts or zones?

- How should the system prevent users from over-trusting simplified goldfish results?

- Should simulation outputs be shown as charts, tables, or written reports in MVP?

- How should accepted risks affect future simulation suggestions?

- Should the system recommend simulation automatically when confidence is low?

- How should simulation results be invalidated when card knowledge changes?

- Should stale SimulationResults remain visible by default?

- Should Level 3 heuristic goldfish require explicit user opt-in?

- Should tutor modeling default to conservative mode?

- Should the Simulation Engine support project-defined success thresholds?

- Should SimulationResult confidence be qualitative, numeric, or both?

## 32. ADR Candidates

ADR-035 — Simulation Is Evidence, Not Judgment

Decision:

Simulation produces evidence for hypotheses but does not decide deck quality by itself.

Reason:

Simulation results require interpretation through the Design Brief, project context, and user goals.

ADR-036 — Every SimulationRun Must Reference a DeckVersion

Decision:

Every SimulationRun must reference one specific DeckVersion.

Reason:

Simulation evidence is meaningless without the exact deck state tested.

ADR-037 — Every SimulationRun Requires a Test Question

Decision:

A SimulationRun must have an explicit test question.

Reason:

Simulation should answer concrete engineering questions, not produce vague deck scores.

ADR-038 — MVP Prioritizes Simple High-Value Simulations

Decision:

MVP simulation should prioritize opening hands, land drops, color availability, mana consistency, ramp access, engine access, mulligan quality, and basic Level 1 / Level 2 goldfish.

Reason:

These simulations answer common deckbuilding questions without requiring full Commander gameplay modeling.

ADR-039 — Goldfish Results Must Expose Limitations

Decision:

Goldfish simulations must clearly state their assumptions, level, and limitations.

Reason:

Simplified solitaire testing is useful but can easily create false confidence.

ADR-040 — Simulation Results Are Interpreted by the Reasoning Engine

Decision:

The Simulation Engine produces results; the Reasoning Engine interprets those results in project context.

Reason:

The same metric may be good or bad depending on deck identity, bracket, meta, and success criteria.

ADR-041 — Simulation Can Support but Not Create Decisions

Decision:

Simulation evidence may support a Decision, but only a Decision entity can produce a new DeckVersion.

Reason:

The user remains the designer and simulation should not automatically modify decks.

ADR-042 — Simulation-Derived Knowledge Is Project-Scoped

Decision:

Findings from simulation may create project-scoped evidence but not universal card knowledge.

Reason:

A simulation result depends on deck version, configuration, assumptions, and project context.

ADR-043 — Access, Castability, and Functional Availability Are Separate

Decision:

The Simulation Engine must distinguish between seeing a card, being able to cast it, and being able to use it functionally.

Reason:

Card access alone can overstate deck performance, especially for color-intensive cards, engines, payoffs, and combos.

ADR-044 — Tutor Modeling Must Be Explicit

Decision:

SimulationResults involving tutors must state whether tutors were ignored, approximated as access modifiers, or fully sequenced.

Reason:

Tutors materially affect access probabilities and can create misleading results if modeled invisibly.

ADR-045 — Simulation Evidence Can Become Stale

Decision:

Simulation results should support current, historical, superseded, and invalid evidence states.

Reason:

Simulation evidence depends on deck version, configuration, knowledge, project context, and assumptions.

## 33. Foundational Simulation Principle

The Knowledge Engine tells The Workshop what cards can mean.

The Analysis Engine tells The Workshop what the deck currently contains.

The Reasoning Engine tells The Workshop what might be true.

The Simulation Engine tests whether that hypothesis survives contact with repeated evidence.

The Workshop should not say:

“This deck is better because the AI says so.”

It should say:

“This change appears justified because it was meant to solve this problem, tested against this DeckVersion, improved this metric, exposed these trade-offs, and produced this evidence under these assumptions.”

The decklist is the output.

The reasoning is the product.

The simulation is the evidence.
