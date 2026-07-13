# RFC-004 — The Workshop Reasoning Engine

Status: Draft Version: v0.2 Sprint: 0 Depends on: RFC-000 — Product Vision, RFC-001 — System Architecture, RFC-002 — Database / Data Model, RFC-003 — Knowledge Engine Document Type: Reasoning Model / Architecture Architecture Owner: Software Architect / CTO Product Owner: Product Owner / Domain Expert

## 1. Purpose

This document defines the Reasoning Engine for The Workshop.

The Reasoning Engine is responsible for transforming structured project context, deck analysis, card knowledge, user constraints, simulation evidence, and project history into explainable engineering reasoning.

The Reasoning Engine does not own card facts.

The Reasoning Engine does not execute simulations.

The Reasoning Engine does not directly modify deck state.

The Reasoning Engine does not decide what the user must play.

Its purpose is to help The Workshop answer:

- What is this deck trying to be?

- What does the current deck actually do?

- Where is the gap between intent and reality?

- Which problems matter?

- Which problems are accepted risks?

- What hypotheses explain the observed weaknesses?

- What changes could solve those problems?

- What trade-offs would those changes introduce?

- What should be tested before deciding?

- What recommendation is justified by the available evidence?

The Reasoning Engine is the layer where The Workshop interprets meaning.

The goal is not to make the AI sound smart.

The goal is to make deck engineering decisions explainable, contextual, testable, reversible, and aligned with the user’s intent.

## 2. Reasoning Engine Thesis

The Workshop does not optimize decks in the abstract.

It improves a specific deck, for a specific player, under a specific brief.

Therefore, reasoning must always be project-aware.

The Reasoning Engine must never ask only:

What is the best card?

It must ask:

Given this project, this deck identity, this strategy, this budget, this meta, this bracket, this user philosophy, and this current deck state, what change actually improves the system — and why?

The Reasoning Engine exists after knowledge and analysis.

The correct sequence is:

Design Brief

+ User Constraints

+ DeckVersion

+ Card Knowledge

+ Deck Analysis

+ Project History

+ Simulation Evidence

↓

Reasoning Engine

↓

Assumptions

Hypotheses

Trade-Off Analysis

Candidate Evaluation

Clarifying Questions

Test Suggestions

Recommendation Rationale

Decision Support

The Reasoning Engine exists to protect The Workshop from becoming a generic recommendation machine.

A shallow system says:

Add Rhystic Study because it is strong.

The Workshop should say:

Rhystic Study would improve card access, but in this project it may damage originality, increase table threat perception, and move the deck toward generic blue goodstuff. If the objective is raw power, it is a candidate. If the objective is identity preservation, it should probably be rejected.

That is reasoning.

## 3. Scope

The Reasoning Engine is responsible for:

- interpreting the Design Brief

- interpreting user constraints

- comparing deck intent against deck reality

- identifying reasoning gaps

- making assumptions explicit

- deciding when clarification is needed

- generating hypotheses

- evaluating trade-offs

- evaluating candidate solution directions

- evaluating candidate cards, packages, engines, or changes

- distinguishing real problems from accepted risks

- identifying project-fit failures

- challenging weak assumptions

- suggesting tests

- preparing recommendation rationale

- supporting decisions

- producing reasoning summaries for reports

The Reasoning Engine is not responsible for:

- storing canonical card facts

- parsing decklists

- running simulations

- generating final deck versions

- executing user decisions

- replacing user taste

- acting as a full Commander rules engine

- producing popularity-based rankings

- deciding universally what a “good deck” is

Those responsibilities belong to other modules.

## 4. Core Principle

The Reasoning Engine must reason from context.

A recommendation is invalid if it is only justified by generic card strength.

A reasoning output is useful only if it explains at least one of the following:

- what problem exists

- why the problem matters

- what evidence supports the problem

- what assumption is being made

- what trade-off is involved

- what project constraint applies

- what engine or package is affected

- what alternative exists

- what uncertainty remains

- what test would reduce uncertainty

- why a strong card may still be wrong

- why a weaker card may be the better fit

If the Reasoning Engine cannot explain why something matters in this project, it should not present it as a serious recommendation.

## 5. Reasoning Position in the System

The Reasoning Engine sits between analysis and recommendation.

The high-level system flow is:

User Input

→ Project Context

→ Structured Knowledge Retrieval

→ Deck Analysis

→ Reasoning

→ Hypothesis / Trade-Off / Test Suggestion

→ Recommendation

→ Decision

→ Version

The Reasoning Engine does not replace the other modules.

It interprets their outputs.

5.1 Module Boundary Summary

Knowledge Engine

Knows what cards can mean.

Deck Analysis Engine

Determines what the current DeckVersion contains and how it behaves structurally.

Simulation Engine

Tests specific hypotheses against a DeckVersion.

Reasoning Engine

Interprets what the knowledge, analysis, history, constraints, and evidence mean.

Recommendation Engine

Turns justified reasoning into structured proposals.

Decision Log

Records what the user chose and why.

This boundary is foundational.

If the Reasoning Engine becomes the source of card facts, the system becomes unreliable.

If the Reasoning Engine directly modifies decks, the user loses agency.

If the Reasoning Engine skips analysis, recommendations become shallow.

## 6. Inputs

The Reasoning Engine consumes data from several modules.

6.1 Design Brief

The Design Brief is the primary reasoning anchor.

It defines what “better” means for the Project.

Relevant fields include:

- format

- commander

- strategy

- design philosophy

- desired play pattern

- bracket target

- budget

- meta context

- success criteria

- anti-goals

- table experience

- personal constraints

The Reasoning Engine must interpret every serious recommendation through the Design Brief.

Without a Design Brief, serious reasoning is incomplete.

If the brief is missing or thin, the Reasoning Engine may still proceed, but it must state assumptions clearly.

Example:

Assumption:

Because no budget was specified, I am treating this as an online/no-budget analysis.

or:

Assumption:

Because no bracket target was specified, I am avoiding cEDH-style optimizations unless explicitly requested.

The goal is not bureaucracy.

The goal is alignment.

6.2 User Constraints

User Constraints represent explicit limits or preferences.

Examples:

- budget ceiling

- no proxies

- proxies allowed

- avoid tutors

- avoid infinite combos

- keep pet cards

- maintain theme density

- preserve weirdness

- avoid generic staples

- optimize for online play

- target a specific meta

- respect bracket expectations

Hard constraints must be treated as blockers.

Soft constraints must be treated as trade-off factors.

Preferences must be considered, but may be challenged when appropriate.

Example:

Constraint:

Low tutor usage.

Reasoning impact:

Do not recommend Demonic Tutor as a default consistency fix. If tutoring is the cleanest solution, present it as a power trade-off, not as the default answer.

6.3 DeckVersion

The Reasoning Engine must reason against a specific DeckVersion.

It should not reason against a vague idea of the deck.

Relevant DeckVersion data includes:

- exact decklist

- commander

- current card categories

- current roles

- current engine structure

- current packages

- current mana base

- current win conditions

- current known weaknesses

- current accepted risks

Reasoning must be version-aware because a recommendation that was correct for one version may become wrong after changes.

6.4 Card Knowledge

The Reasoning Engine consumes Card Knowledge from the Knowledge Engine.

This includes:

- functional roles

- role weights

- synergy relationships

- combo relationships

- archetype relevance

- risk tags

- constraint tags

- project-specific overrides

- confidence levels

- validation status

- source metadata

The Reasoning Engine may use this knowledge, but it must not silently promote uncertain knowledge into fact.

Correct:

This appears to function as recursion support in this deck, but the role has not been validated yet.

Incorrect:

This is definitely a core recursion engine.

6.5 Analysis Reports

The Deck Analysis Engine provides structural findings.

The Reasoning Engine interprets those findings.

Inputs may include:

- mana curve

- land count

- color pressure

- ramp density

- draw density

- interaction density

- protection density

- win condition density

- engine detection

- package density

- unsupported cards

- over-supported roles

- fragile engines

- structural weaknesses

The Analysis Engine answers:

What is happening?

The Reasoning Engine answers:

What does that mean?

6.6 Simulation Evidence

Simulation results provide evidence for or against hypotheses.

The Reasoning Engine uses simulation evidence to update confidence.

Examples:

- opening hand quality

- land drop probability

- color availability

- ramp access

- engine access

- goldfish speed

- mulligan quality

- combo access

- failure patterns

Simulation does not automatically decide the recommendation.

It informs reasoning.

Example:

Simulation finding:

Double-white availability by turn six is below target.

Reasoning interpretation:

Organic Extinction is structurally difficult to cast in this version unless the mana base changes or the deck reduces double-white dependency.

6.7 Project History

Project history includes:

- previous recommendations

- accepted decisions

- rejected decisions

- deferred ideas

- accepted risks

- reverted experiments

- user notes

- gameplay observations

- previous reports

- backlog items

The Reasoning Engine must use history to avoid repeating bad advice.

Example:

Previous Decision:

Rejected Rhystic Study because it damaged deck originality.

Reasoning impact:

Do not recommend Rhystic Study again as a generic draw upgrade unless the user changes the project objective.

Project memory is part of reasoning quality.

## 7. Reasoning Tasks

The Reasoning Engine should not run as one generic “think about this deck” process.

It should operate through explicit ReasoningTasks.

A ReasoningTask defines:

- what question is being answered

- what context is required

- what output shape is expected

- whether the result can become a Recommendation, SimulationRun, Decision, Report, or Note

7.1 ReasoningTask Types

Recommended MVP task types:

deck_audit_reasoning

weakness_interpretation

candidate_evaluation

add_cut_rationale

trade_off_comparison

simulation_interpretation

simulation_request

decision_support

accepted_risk_review

revert_review

identity_fit_review

constraint_fit_review

recommendation_readiness_check

7.2 ReasoningTask Fields

A ReasoningTask should include:

id

project_id

deck_version_id

task_type

question

input_context

related_card_ids

related_deck_card_ids

related_engine_ids

related_package_ids

related_weakness_ids

related_recommendation_ids

related_simulation_run_ids

required_output_type

created_at

created_by

MVP can store ReasoningTasks as lightweight JSON records or as part of AnalysisReport / Recommendation metadata.

The important point is conceptual:

The system should know what kind of reasoning it is performing.

## 8. Outputs

The Reasoning Engine may produce several types of output.

8.1 Assumptions

Assumptions are explicit temporary beliefs used to continue reasoning when context is incomplete.

Examples:

Assumption:

The deck is aiming for high-power casual, not cEDH.

Assumption:

The user values explosiveness more than table friendliness.

Assumption:

The current meta contains meaningful artifact hate.

Assumption:

The user prefers testing owned cards before expensive upgrades.

Assumptions must be visible.

They should not be hidden inside confident prose.

8.2 Clarifying Questions

Clarifying questions are used when missing context materially affects the answer.

The Reasoning Engine should ask a question when:

- the recommendation would change significantly depending on the answer

- a hard constraint is unknown

- the deck identity is ambiguous

- the user’s tolerance for power, tutors, combos, or proxies is unclear

- the requested analysis would be misleading without missing context

However, The Workshop should not over-question the user.

If the missing detail is minor, the Reasoning Engine should proceed with stated assumptions.

Correct:

I can proceed assuming this is online/no-budget. If this is paper-budget instead, the recommendation changes.

Incorrect:

I cannot continue until every field of the Design Brief is complete.

8.3 Hypotheses

A hypothesis is a testable explanation of a problem or opportunity.

Examples:

Hypothesis:

The deck is not failing because it lacks payoffs. It is failing because it cannot reliably access its engines early enough.

Hypothesis:

The mana base is the real bottleneck, not the top-end card selection.

Hypothesis:

The deck has enough combo finishers but not enough protection to survive until the combo turn.

Hypothesis:

The equipment package is underperforming because the carrier density is too low.

Hypothesis:

The deck looks tribal, but its real identity is artifact combo-control.

Hypotheses should connect:

- problem

- evidence

- affected engine/package

- expected test

- confidence

- uncertainty

A hypothesis should not be treated as a final conclusion until supported.

8.4 Trade-Off Analysis

Trade-off analysis is central to The Workshop.

The Reasoning Engine must compare the cost and benefit of possible decisions.

Common trade-offs include:

- speed vs resilience

- tutors vs variance

- power vs table friendliness

- budget vs efficiency

- protection vs proactive development

- theme density vs interaction density

- explosiveness vs consistency

- originality vs staples

- engine density vs answer density

- high ceiling vs low floor

- commander dependency vs redundancy

- combo density vs play experience

- mana greed vs card quality

A good trade-off analysis should not simply say which option is stronger.

It should explain which option better serves the project objective.

Example:

Option A:

Add more tutors.

Benefit:

Improves access to core engines and win lines.

Trade-off:

Reduces variance and may make games feel more repetitive. Also increases perceived power level.

Fit:

Good if the project prioritizes consistency and combo execution.

Bad if the project wants organic gameplay and lower tutor density.

8.5 Candidate Solution Directions

Before generating exact card recommendations, the Reasoning Engine may propose solution directions.

Examples:

Solution Direction:

Improve color fixing before adding more expensive white spells.

Solution Direction:

Increase protection density instead of adding another payoff.

Solution Direction:

Cut off-plan value cards to increase engine redundancy.

Solution Direction:

Add more cheap equipment carriers before adding more equipment.

Solution Direction:

Reduce top-end cards and improve early development.

This prevents the system from jumping directly to card names.

The Reasoning Engine should identify the engineering problem before choosing the component.

8.6 Candidate Evaluation

Candidate evaluation assesses a possible card, package, engine, or change before it becomes a recommendation.

A candidate should be checked for:

- problem fit

- engine fit

- package fit

- identity fit

- constraint fit

- role density impact

- risk impact

- trade-off

- alternatives

- confidence

- test need

Example:

Candidate:

Mox Opal

Fit:

Strong for artifact-heavy explosive builds.

Benefit:

Improves fast mana and artifact count.

Risk:

High budget cost and possible power-level increase.

Constraint Impact:

Invalid if paper budget is strict.

Valid if online/no-budget or proxy allowed.

Reasoning:

Excellent card for the system, but not automatically correct if budget matters.

A globally strong card may be downgraded or rejected if it is project-wrong.

8.7 Recommendation Rationale

The Reasoning Engine prepares the rationale used by the Recommendation Engine.

A complete rationale should include:

- problem

- hypothesis

- evidence

- affected role

- affected engine

- affected package

- proposed direction

- expected benefit

- trade-off

- risk

- constraint check

- alternatives considered

- confidence

- uncertainty

- test suggestion

Example:

Problem:

The deck struggles to cast double-white spells on time.

Hypothesis:

The current mana base does not provide enough reliable white sources by the relevant turn window.

Evidence:

Analysis shows low white source density relative to white pip requirements.

Gameplay notes mention Organic Extinction being stranded in hand.

Proposed Direction:

Improve rainbow/five-color fixing before adding more white-intensive cards.

Expected Benefit:

Higher castability of key spells and smoother development.

Trade-Off:

May reduce utility land count or increase financial cost.

Test Suggestion:

Run color availability simulation before and after the mana base changes.

8.8 Test Suggestions

The Reasoning Engine should suggest tests when evidence would materially improve the decision.

Examples:

Test:

Run 100 opening hand simulations to compare keepable hands before and after the land changes.

Test:

Run engine access probability by turn four with and without the tutor package.

Test:

Goldfish 50 games to compare average win turn before and after cutting the high-mana-value package.

Test:

Track 10 real games and record whether the deck loses because of lack of protection or lack of payoff.

Not every question needs simulation.

The Reasoning Engine should suggest tests when the decision is uncertain, high-impact, or evidence-sensitive.

8.9 Decision Support

The Reasoning Engine supports decisions but does not override the user.

It may recommend:

- accept

- reject

- defer

- test first

- accept as experiment

- mark as accepted risk

- modify recommendation

- revert previous decision

Example:

Suggested Decision:

Test first.

Reason:

The proposed mana base change is likely correct, but the current evidence is mostly anecdotal. A color availability simulation would make the decision stronger.

Decision support should preserve user agency.

The user remains the designer.

## 9. ReasoningOutput Model

The Reasoning Engine should produce structured outputs.

Reasoning should not exist only as raw chat.

A ReasoningOutput should be both:

- machine-readable enough to persist

- human-readable enough to review

9.1 ReasoningOutput Fields

Recommended MVP fields:

id

project_id

deck_version_id

task_type

summary

assumptions

clarifying_questions

hypotheses

evidence

trade_offs

candidate_evaluations

constraint_checks

identity_checks

risks

uncertainty

confidence

recommendation_readiness

suggested_tests

decision_support

readable_markdown

created_at

generated_by

MVP can store this inside:

- AnalysisReport

- Recommendation.rationale_json

- Decision.evidence_links_json

- Report metadata

- Note

- dedicated ReasoningOutput record if needed later

9.2 Example ReasoningOutput JSON

{

"task_type": "weakness_interpretation",

"summary": "The deck appears to have a white source consistency issue.",

"assumptions": [

"The deck wants to cast Organic Extinction by the midgame."

],

"hypotheses": [

{

"problem": "White-intensive spells are difficult to cast.",

"hypothesis": "The mana base does not provide enough reliable white sources.",

"confidence": "medium"

}

],

"evidence": [

"Gameplay note: Organic Extinction was stranded in hand.",

"Analysis: white source density appears low relative to pip requirements."

],

"trade_offs": [

"Adding rainbow lands improves color access but may reduce utility land count.",

"Adding expensive lands may violate paper budget constraints."

],

"suggested_tests": [

"Run color availability simulation by turn six."

],

"recommendation_readiness": "needs_simulation",

"confidence": "medium",

"uncertainty": [

"No simulation has confirmed the exact failure rate yet."

]

}

## 10. Reasoning Modes

The Reasoning Engine should support multiple operating modes.

Each mode changes depth, input requirements, and output expectations.

10.1 Quick Advice Mode

Used for lightweight user questions.

Examples:

Is this card good here?

Should I cut this?

Does this package make sense?

Behavior:

- use available context

- state assumptions

- avoid heavy formalism

- do not require complete Design Brief

- do not create full recommendation unless needed

- expose uncertainty

Output:

- short explanation

- project-fit judgment

- main trade-off

- optional next step

10.2 Deep Audit Mode

Used for serious deck analysis.

Behavior:

- require or infer Design Brief

- use DeckVersion

- use Knowledge Engine data

- use Analysis Reports

- identify structural issues

- generate hypotheses

- distinguish problems from accepted risks

- prepare candidate solution directions

- recommend tests where useful

Output:

- assumptions

- deck identity interpretation

- key hypotheses

- weakness interpretation

- trade-offs

- recommended next engineering steps

10.3 Candidate Evaluation Mode

Used when evaluating a specific card, package, engine, or change.

Behavior:

- check problem fit

- check identity fit

- check constraints

- compare alternatives

- identify risk

- determine recommendation readiness

Output:

- candidate fit

- benefit

- risk

- trade-off

- verdict

- confidence

- test suggestion if needed

10.4 Recommendation Review Mode

Used before proposing add/cut changes.

Behavior:

- verify problem clarity

- verify candidate fit

- check constraints

- check accepted risks

- check project history

- prepare rationale

- decide whether recommendation is ready

Output:

- ready_to_recommend

- needs_clarification

- needs_analysis

- needs_simulation

- needs_user_review

- reject_candidate

- defer

10.5 Simulation Interpretation Mode

Used after a SimulationRun.

Behavior:

- read test question

- read simulation configuration

- read result

- compare against success criteria

- interpret evidence in project context

- update hypothesis confidence

- suggest decision

Output:

- result interpretation

- confidence update

- decision support

- next test if needed

10.6 Decision Support Mode

Used when the user must choose.

Behavior:

- summarize options

- explain expected benefit

- explain trade-off

- explain risk

- explain uncertainty

- connect to evidence

- suggest decision type

Output may include:

- accept

- reject

- defer

- test first

- accept as experiment

- mark as accepted risk

- modify recommendation

- revert

## 11. Clarification Policy

The Reasoning Engine should ask clarifying questions only when needed.

11.1 Ask When Missing Context Is Material

Ask when the answer would change significantly depending on the missing context.

Examples:

Are proxies allowed?

Are infinite combos acceptable?

Is this meant for paper budget or online no-budget?

Is the goal to preserve theme or maximize power?

Are tutors acceptable in this bracket?

11.2 Proceed When Assumptions Are Enough

If the system can proceed productively, it should state assumptions and continue.

Example:

I will assume this is a high-power casual Commander deck and avoid cEDH-only recommendations unless the brief says otherwise.

11.3 Avoid Bureaucracy

The Workshop should support lightweight reasoning.

A complete brief improves quality, but the system should not block basic analysis just because some fields are missing.

11.4 Escalate From Assumption to Clarification

The system should move from assumption to clarification when:

- confidence is low

- a hard constraint is unknown

- the recommendation would be expensive

- the recommendation would change deck identity

- the recommendation would increase bracket/power level

- the recommendation would introduce controversial play patterns

- the user seems uncertain about the deck’s direction

## 12. Hypothesis Model

A Reasoning Hypothesis should include:

id

project_id

deck_version_id

title

problem

hypothesis

evidence

affected_engine_ids

affected_package_ids

affected_card_ids

confidence

uncertainty

suggested_tests

status

created_at

updated_at

Suggested statuses:

proposed

under_review

supported_by_analysis

supported_by_simulation

supported_by_gameplay

rejected

accepted_as_risk

converted_to_recommendation

resolved

Example:

Title:

Mana base may not support white-intensive spells.

Problem:

White spells with multiple white pips are difficult to cast on curve.

Hypothesis:

The deck has too few reliable white sources relative to its white pip requirements.

Evidence:

User gameplay note: Organic Extinction was repeatedly stranded.

Analysis: white source density appears low.

Suggested Test:

Color availability simulation by turn six.

Confidence:

Medium.

Status:

Proposed.

Hypotheses are first-class because The Workshop should reason before recommending.

## 13. Trade-Off Model

A Trade-Off Analysis should include:

decision_context

option_a

option_b

affected_objective

benefit_a

cost_a

benefit_b

cost_b

constraint_impact

identity_impact

risk_impact

recommendation

confidence

uncertainty

Example:

Decision Context:

Improve deck consistency.

Option A:

Add tutors.

Benefit:

Higher access to core engines.

Cost:

More repetitive gameplay and higher perceived power.

Option B:

Add redundancy pieces.

Benefit:

Improves consistency while preserving more organic gameplay.

Cost:

May be slower and less precise than tutors.

Recommendation:

Prefer redundancy if the user wants high-power casual with lower tutor density.

Prefer tutors if the user prioritizes maximum consistency.

The goal is not to choose the strongest option.

The goal is to explain which option best fits the brief.

## 14. Candidate Evaluation Model

When evaluating a candidate card, package, engine, or change, the Reasoning Engine should check several gates.

14.1 Fit Checks

- Does it solve a real problem?

- Does it support a core engine?

- Does it improve an under-supported role?

- Does it respect the Design Brief?

- Does it preserve deck identity?

- Does it fit the bracket?

- Does it fit the budget?

- Does it fit the desired play pattern?

- Does it improve the deck more than alternatives?

14.2 Rejection Checks

A candidate should be rejected or downgraded if:

- it violates a hard constraint

- it damages deck identity

- it solves the wrong problem

- it duplicates an over-supported role

- it increases a risk without meaningful benefit

- it is only justified by popularity

- it is too slow for the stated meta

- it is too strong for the bracket

- it creates unwanted repetitive gameplay

- its knowledge confidence is too low

- it requires unsupported infrastructure

14.3 Candidate Output

Candidate evaluation should produce:

candidate

fit_rating

problem_solved

affected_engine

affected_package

identity_impact

constraint_impact

benefits

risks

trade_offs

alternatives

confidence

recommendation_readiness

test_suggestion

## 15. Recommendation Readiness

The Reasoning Engine should decide whether a recommendation is ready.

A recommendation is ready when:

- the problem is clear

- the objective is clear

- the candidate solves that problem

- the trade-off is understood

- constraints have been checked

- confidence is sufficient

- uncertainty is acceptable or testable

A recommendation is not ready when:

- the problem is vague

- the objective is ambiguous

- the candidate is only generically strong

- the recommendation violates constraints

- the engine impact is unclear

- there is insufficient evidence

- the change should be tested first

Possible readiness states:

ready_to_recommend

needs_clarification

needs_analysis

needs_simulation

needs_user_review

reject_candidate

defer

The Recommendation Engine should not create serious proposals from candidates that fail readiness checks.

## 16. Uncertainty Handling

The Reasoning Engine must expose uncertainty clearly.

16.1 Confidence Levels

Recommended levels:

certain

high

medium

low

unknown

disputed

16.2 Uncertainty Sources

Uncertainty may come from:

- incomplete Design Brief

- missing card knowledge

- unvalidated AI-suggested tags

- thin analysis

- no simulation evidence

- conflicting gameplay notes

- unknown meta

- unclear user philosophy

- newly released cards

- volatile price data

- ambiguous deck identity

16.3 Correct Uncertainty Behavior

Correct:

This looks like a mana consistency issue, but I would confirm it with color availability testing before cutting spells.

Incorrect:

The mana base is definitely wrong.

Correct:

This card appears off-plan unless the deck is intentionally moving toward a higher-power combo shell.

Incorrect:

Cut this card.

The Reasoning Engine should be confident when evidence supports confidence, and careful when it does not.

## 17. Accepted Risk Reasoning

Some weaknesses are intentional.

The Reasoning Engine must distinguish between:

unresolved problem

intentional trade-off

accepted risk

rejected concern

deferred issue

Example:

Weakness:

Low graveyard hate.

Reasoning:

In a graveyard-heavy meta, this is a serious problem.

In the current stated meta, this may be acceptable.

Decision Support:

Mark as accepted risk and revisit if meta assumptions change.

Accepted risks should prevent repetitive warnings.

However, accepted risks should be revisited when:

- meta changes

- deck strategy changes

- new evidence appears

- user asks for a fresh audit

- the risk starts causing repeated losses

Accepted risk is not denial.

It is documented engineering intent.

## 18. Project Identity Protection

The Reasoning Engine must protect deck identity.

A technically correct recommendation may still be wrong.

Examples:

Adding more tutors may improve consistency but damage the intended variance.

Adding generic staples may improve raw power but make the deck less original.

Adding more tribal lords may make a Myr deck more tribal but worse at its actual artifact-combo identity.

Adding stronger Voltron equipment may be wrong if the Emry deck is really an equipment recursion toolbox.

The Reasoning Engine should flag identity risk when a recommendation would make the deck less itself.

Identity protection does not mean refusing optimization.

It means optimizing toward the stated identity.

## 19. Reasoning Workflow

The default reasoning workflow should be:

## 1. Receive ReasoningTask

## 2. Identify task type

## 3. Load Project Context

## 4. Load Design Brief

## 5. Load User Constraints

## 6. Load target DeckVersion

## 7. Load relevant Knowledge Engine data

## 8. Load relevant Analysis Reports

## 9. Load relevant Project History

## 10. Load relevant Simulation Evidence if available

## 11. Identify assumptions

## 12. Identify missing context

## 13. Decide whether clarification is required

## 14. Generate hypotheses

## 15. Evaluate trade-offs

## 16. Evaluate candidates or solution directions

## 17. Check constraints

## 18. Check identity fit

## 19. Assess uncertainty and confidence

## 20. Decide recommendation readiness

## 21. Suggest tests if needed

## 22. Produce ReasoningOutput

## 23. Route output to Recommendation, Simulation, Decision, Report, Note, or Backlog

The Reasoning Engine should not skip directly from decklist to recommendation unless the user explicitly asks for a lightweight answer.

## 20. Reasoning Persistence Rules

Reasoning should be persisted when it supports:

- Recommendation

- Decision

- AnalysisReport

- Report

- Simulation interpretation

- accepted risk

- rejected recommendation

- project-specific override

- future revisit item

Reasoning does not need to be persisted when it is:

- casual chat

- transient exploration

- low-impact speculation

- redundant with existing records

- not used for any decision or report

20.1 What to Persist

Persist structured reasoning, not raw hidden thought.

Useful persisted reasoning includes:

- assumptions

- problem framing

- hypothesis

- evidence

- trade-offs

- uncertainty

- alternatives considered

- confidence

- test suggestion

- decision support

20.2 Where to Persist

Depending on use, reasoning may be stored in:

- Recommendation.rationale_json

- Decision.rationale

- AnalysisReport.assumptions_json

- AnalysisReport.findings_json

- SimulationResult.observations_json

- Report.content_markdown

- Note

- BacklogItem

- future ReasoningOutput entity

The MVP does not need a dedicated ReasoningOutput table if reasoning is stored cleanly inside existing entities.

However, the system should preserve a consistent ReasoningOutput shape.

## 21. Relationship with Knowledge Engine

The Knowledge Engine knows what cards can mean.

The Reasoning Engine decides what that meaning implies in this project.

The Reasoning Engine consumes:

- card facts

- card knowledge

- role assignments

- synergies

- combos

- archetype relationships

- risk tags

- project overrides

- source metadata

- confidence levels

The Reasoning Engine may produce:

- reasoning hypotheses

- project-specific interpretations

- draft role suggestions

- uncertainty statements

- candidate tests

- recommendation rationale

The Reasoning Engine must not automatically write global knowledge.

AI-suggested knowledge remains draft until validated.

## 22. Relationship with Deck Analysis Engine

The Analysis Engine produces findings.

The Reasoning Engine interprets findings.

Example:

Analysis Finding:

The deck has 7 ramp pieces.

Reasoning:

For a commander with high setup dependency and a desired explosive game plan, 7 ramp pieces may be below target.

The same analysis finding may mean different things in different projects.

Example:

Finding:

Low interaction density.

Possible interpretations:

- serious weakness in a control deck

- accepted risk in a glass-cannon combo deck

- bracket mismatch in a hostile meta

- reasonable choice in a casual battlecruiser deck

Analysis is not judgment.

Reasoning creates judgment through context.

## 23. Relationship with Simulation Engine

The Reasoning Engine defines what should be tested.

The Simulation Engine produces evidence.

The Reasoning Engine interprets that evidence.

Example:

Reasoning Hypothesis:

The deck cannot reliably cast its commander on curve.

Simulation Question:

How often does DeckVersion v1.2 cast the commander by turn three under the selected mulligan policy?

Simulation Result:

Commander cast on curve in 41% of runs.

Reasoning Interpretation:

If the project target is explosive commander-centric gameplay, this is below target and supports increasing early ramp or color fixing.

Simulation should answer specific reasoning questions.

It should not produce abstract deck scores.

## 24. Relationship with Recommendation Engine

The Reasoning Engine prepares recommendation logic.

The Recommendation Engine structures the proposal.

The Reasoning Engine provides:

- problem framing

- hypothesis

- trade-off analysis

- candidate evaluation

- constraint check

- risk analysis

- confidence

- test suggestion

The Recommendation Engine outputs:

- add/cut/change proposal

- affected cards

- affected packages

- affected engines

- expected benefit

- trade-off

- status

- review path

A recommendation without reasoning is invalid.

A recommendation without user decision does not change deck state.

## 25. Relationship with Decision Log

The Decision Log stores what the user chose and why.

The Reasoning Engine supports decisions by explaining:

- what changed

- why it was proposed

- what benefit was expected

- what risk was accepted

- what evidence supported the decision

- what alternatives were rejected

- what should be tested later

Reasoning should be persisted when it supports a Recommendation, Decision, Report, or Simulation interpretation.

Do not persist every transient thought.

Persist the useful structured result.

## 26. MVP Reasoning Model

The MVP Reasoning Engine should be simple but disciplined.

26.1 MVP Must Include

The MVP must support:

- ReasoningTask types

- Design Brief interpretation

- assumption generation

- basic clarification policy

- hypothesis generation

- trade-off analysis

- constraint checking

- identity fit checking

- candidate evaluation

- recommendation readiness

- test suggestion

- uncertainty statements

- structured rationale output

26.2 MVP Reasoning Templates

The MVP should use structured templates for:

- Deck Audit Reasoning

- Weakness Interpretation

- Candidate Evaluation

- Add/Cut Rationale

- Trade-Off Comparison

- Simulation Request

- Simulation Interpretation

- Decision Support

- Accepted Risk

- Revert Reasoning

- Identity Fit Review

- Constraint Fit Review

26.3 MVP Output Shape

A reasoning output should be storable as JSON plus readable Markdown.

Example:

{

"problem": "The deck struggles to cast white-intensive spells.",

"hypothesis": "The mana base does not provide enough reliable white sources.",

"evidence": [

"Gameplay note: Organic Extinction was stranded in hand.",

"Analysis: white source density appears low."

],

"affected_package": "mana_base",

"candidate_direction": "increase rainbow/five-color fixing",

"expected_benefit": "higher castability of key spells",

"trade_offs": [

"reduced utility land count",

"possible budget increase"

],

"uncertainty": "Needs color availability simulation.",

"confidence": "medium",

"test_suggestion": "Run color availability test by turn six."

}

26.4 MVP Should Not Include Yet

The MVP should not require:

- autonomous long-term agent behavior

- full natural language memory as source of truth

- hidden chain-of-thought storage

- complex multi-agent debate

- automatic deck modification

- automatic global knowledge updates

- perfect Commander strategy modeling

- final authority over user decisions

The MVP should reason clearly, not magically.

## 27. Reasoning Templates

27.1 Weakness Interpretation Template

Weakness:

What structural issue was detected?

Evidence:

What analysis, gameplay note, or simulation supports it?

Context:

Why does this matter under the Design Brief?

Hypothesis:

What is the likely cause?

Affected System:

Which engine, package, role, or constraint is involved?

Severity:

How important is this problem?

Trade-Off:

What might be sacrificed to solve it?

Next Step:

Recommend, test, clarify, defer, or mark as accepted risk.

27.2 Candidate Evaluation Template

Candidate:

What card, package, or change is being evaluated?

Problem Solved:

What issue does it address?

System Fit:

Which engine, package, or role does it support?

Identity Fit:

Does it preserve or damage deck identity?

Constraint Check:

Does it violate budget, bracket, tutor tolerance, combo tolerance, or other constraints?

Benefit:

What improves?

Risk:

What gets worse?

Alternatives:

What else could solve the same problem?

Confidence:

How certain is the fit?

Recommendation Readiness:

Ready, test first, clarify, defer, or reject.

27.3 Trade-Off Template

Decision:

What choice is being evaluated?

Option A:

What is the first path?

Option B:

What is the second path?

Benefit A:

What does A improve?

Cost A:

What does A sacrifice?

Benefit B:

What does B improve?

Cost B:

What does B sacrifice?

Project Fit:

Which option better matches the Design Brief?

Recommendation:

Which path is preferred and why?

27.4 Accepted Risk Template

Weakness:

What issue exists?

Reason Accepted:

Why is this acceptable in the current project?

Conditions:

Under what assumptions is it acceptable?

Revisit Trigger:

What would make this worth revisiting?

Decision Impact:

Suppress repeated warnings unless conditions change.

27.5 Simulation Request Template

Hypothesis:

What claim needs evidence?

Test Question:

What specific question should simulation answer?

DeckVersion:

Which exact deck version should be tested?

Metric:

What should be measured?

Success Target:

What result would count as acceptable?

Interpretation:

How should the result affect the decision?

27.6 Decision Support Template

Decision Context:

What choice does the user need to make?

Options:

What are the realistic options?

Evidence:

What supports each option?

Trade-Off:

What does each option sacrifice?

Risk:

What can go wrong?

Uncertainty:

What is still unknown?

Suggested Decision:

Accept, reject, modify, test first, defer, revert, or mark as accepted risk.

Reason:

Why does this decision fit the project?

## 28. Prompting Principles

If LLM prompts are used inside the Reasoning Engine, they should follow strict rules.

28.1 Prompt Inputs Must Be Structured

Prompts should receive:

- ReasoningTask

- project summary

- Design Brief

- constraints

- DeckVersion summary

- analysis findings

- relevant card knowledge

- project history

- simulation evidence

- explicit task

Prompts should not receive a raw decklist and be asked to “make it better.”

28.2 Prompt Outputs Must Be Structured

The model should output:

- assumptions

- hypotheses

- trade-offs

- risks

- uncertainty

- recommendation readiness

- test suggestions

- rationale JSON

- readable summary

28.3 The AI Must Not Invent Facts

If card data, rulings, prices, legality, or exact rules interactions are missing, the model must say so.

Correct:

I do not have validated card knowledge for this interaction yet.

Incorrect:

This combo definitely works.

28.4 The AI Must Respect Project Memory

If a card, package, or strategy was previously rejected, the model must not reintroduce it without explaining why the context changed.

## 29. Future Extensions

Future Reasoning Engine capabilities may include:

29.1 Reasoning Profiles

Different reasoning profiles for different user philosophies.

Examples:

- high-power optimizer

- casual identity protector

- combo engineer

- budget upgrader

- anti-staple brewer

- bracket compliance reviewer

- meta predator

- originality-first brewer

29.2 Multi-Option Recommendation Trees

The system may present several paths:

Path A:

Maximum consistency.

Path B:

More explosive, higher variance.

Path C:

More resilient, slower.

Path D:

More thematic, lower raw power.

29.3 Automatic Revisit Triggers

Accepted risks or deferred decisions may be reopened when:

- simulation contradicts assumptions

- gameplay notes show repeated failure

- meta changes

- deck version changes

- new card knowledge appears

- user changes the brief

29.4 Reasoning Evaluation

The system may score reasoning quality by checking:

- did it cite a real problem?

- did it respect constraints?

- did it explain trade-offs?

- did it avoid unsupported claims?

- did it offer testable hypotheses?

- did the user accept, reject, or modify the suggestion?

- did gameplay results support the reasoning?

29.5 Learning From Decisions

The system may learn project-specific preferences from:

- accepted recommendations

- rejected recommendations

- accepted risks

- reverted changes

- repeated user comments

- gameplay results

This learning must remain inspectable and editable.

The system must not silently decide that a user “likes” or “dislikes” something without traceable evidence.

## 30. Open Questions

- What is the minimum Design Brief required for serious reasoning?

- Should the Reasoning Engine always produce assumptions explicitly?

- Should hypotheses be persisted by default or only when promoted?

- Should every Recommendation require a formal hypothesis?

- How should confidence be represented: qualitative, numeric, or both?

- How should the system decide when to ask clarifying questions?

- How should accepted risks suppress future warnings?

- Should rejected recommendations be used as negative project knowledge?

- Should user corrections automatically create project overrides?

- How should the Reasoning Engine handle conflicting evidence?

- How much project history should be included in each reasoning pass?

- Should there be different reasoning modes for quick advice vs deep audit?

- Should the MVP expose reasoning JSON to the user or only readable summaries?

- How should the system evaluate whether reasoning was successful?

- How should reasoning templates evolve without becoming too rigid?

- Should the Reasoning Engine be deterministic where possible, or mostly LLM-assisted?

- Should the system support multiple recommendation philosophies in parallel?

- How should the Reasoning Engine handle newly released cards with weak knowledge?

- What level of explanation is enough before a recommendation feels bloated?

- When should the system challenge the user’s stated preference?

- Should ReasoningOutput become a first-class persisted entity or remain embedded in existing entities during MVP?

- Should ReasoningTask be explicitly stored, or inferred from user action and report type?

- Should reasoning modes be user-visible, system-internal, or both?

## 31. ADR Candidates

ADR-023 — Reasoning Engine Consumes Knowledge, It Does Not Own Truth

Decision: The Reasoning Engine consumes card knowledge, project context, analysis, and simulation evidence, but does not own canonical truth.

Reason: The AI is a reasoning layer, not the source of truth.

ADR-024 — Serious Recommendations Require Explicit Reasoning

Decision: A serious recommendation must include problem, evidence, expected benefit, trade-off, risk, confidence, and project fit.

Reason: The Workshop must avoid shallow card suggestions.

ADR-025 — Assumptions Must Be Explicit

Decision: When context is incomplete, the Reasoning Engine must either ask a clarifying question or state its assumption.

Reason: Hidden assumptions create bad recommendations and reduce trust.

ADR-026 — Clarifying Questions Are Used Only When Material

Decision: The Reasoning Engine should ask clarifying questions only when missing context would materially change the answer.

Reason: The Workshop should be structured without becoming bureaucratic.

ADR-027 — Hypotheses Are First-Class Reasoning Objects

Decision: The Reasoning Engine should represent important conclusions as hypotheses before converting them into recommendations.

Reason: Deck engineering should be testable and reversible.

ADR-028 — Trade-Off Analysis Is Required for Meaningful Changes

Decision: Meaningful recommendations must explain trade-offs.

Reason: The best card is not always the best fit.

ADR-029 — Identity Fit Is a Recommendation Gate

Decision: Recommendations must be checked against deck identity and user philosophy.

Reason: Improvement must not become homogenization.

ADR-030 — Accepted Risk Suppresses Repeated Warnings

Decision: If a user accepts a risk, the Reasoning Engine should not repeatedly flag it as unresolved unless conditions change.

Reason: Some weaknesses are intentional engineering trade-offs.

ADR-031 — Simulation Is Requested When Reasoning Needs Evidence

Decision: The Reasoning Engine should request simulation when a hypothesis is important, uncertain, and testable.

Reason: Simulation exists to support decisions, not to create abstract deck scores.

ADR-032 — Recommendations Do Not Become Decisions

Decision: The Reasoning Engine may support a decision, but only a Decision entity can produce a new DeckVersion.

Reason: The user remains the designer.

ADR-033 — ReasoningTask Defines the Type of Reasoning Being Performed

Decision: The Reasoning Engine should operate through explicit task types such as weakness interpretation, candidate evaluation, simulation interpretation, and decision support.

Reason: Different reasoning tasks require different inputs, depth, and output structures.

ADR-034 — ReasoningOutput Should Be Structured

Decision: The Reasoning Engine should produce structured outputs that can be stored as JSON and rendered as readable Markdown.

Reason: Structured reasoning is searchable, reusable, reviewable, and easier to connect to recommendations, decisions, and reports.

## 32. Foundational Reasoning Principle

The Knowledge Engine tells The Workshop what cards can mean.

The Analysis Engine tells The Workshop what the deck currently does.

The Simulation Engine tells The Workshop what happens under test.

The Reasoning Engine tells The Workshop what it all means.

The Workshop should not say:

Add this card because it is good.

It should say:

This card is a justified candidate because it solves this problem, supports this engine, respects this brief, improves this metric, introduces this trade-off, and should be tested in this way.

The decklist is the output.

The reasoning is the product.
