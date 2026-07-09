# Baseline Structural Analysis — The Myr Singularity v1.0

## What this analysis is

This is the first baseline structural analysis for deck version v1.0 of The
Myr Singularity. It describes the deck's structure as it exists today, using
only the project brief, the imported v1.0 decklist, canonical Card Facts, and
the first-pass Functional Role assignments. All counts are computed from
those files; the machine-readable version of this analysis is
`baseline_v1.0.json`.

## What this analysis is not

This document makes no recommendations. It contains no card cuts, adds,
swaps, replacements, upgrade or budget suggestions, no price or popularity
claims, no simulation or matchup results, no power score, and no verdict. It
changes no decklist, version, knowledge, or card-data files. Recommendations
are a separate, later task.

## Deck identity

- **Commander:** Urtet, Remnant of Memnarch (five-color identity)
- **Stated identity:** an artifact combo-control engine disguised as a Myr
  tribal deck; Myr and artifact bodies are used as resources, not merely as
  attackers.
- **Sprint 1 goals:** preserve the Myr identity; improve explosiveness,
  consistency, mana fixing, and resilience.

### Composition (playable 100: commander + 99 main-deck cards)

| Fact | Count |
|---|---|
| Lands | 34 |
| Nonland cards | 66 |
| Artifact cards | 50 |
| Creature cards | 24 |
| Myr typal cards | 14 |
| Nonland cards with colored costs | 23 |
| Average nonland mana value | 3.0 |
| Imported SIDEBOARD cards (counted separately) | 7 |

Nonland mana value curve: 0 → 1 card, 1 → 6, 2 → 22, 3 → 20, 4 → 8, 5 → 4,
6+ → 5. The main deck contains two copies of Island; all other names are
unique.

## Role category distribution

Counting basis: the two card columns count distinct cards in the playable
100; the role-assignments column counts role assignments, so a card with two
roles in the same category contributes twice there.

| Category | Cards with any role | Cards with a primary role | Role assignments |
|---|---|---|---|
| Lands and Mana Base | 34 | 34 | 66 |
| Mana Development | 28 | 22 | 47 |
| Board Presence | 24 | 2 | 26 |
| Utility and Support | 20 | 9 | 26 |
| Selection and Tutoring | 16 | 13 | 20 |
| Interaction | 15 | 12 | 16 |
| Engine and Scaling | 14 | 11 | 24 |
| Card Advantage | 11 | 6 | 11 |
| Protection and Resilience | 8 | 5 | 11 |
| Combo and Win Conditions | 5 | 5 | 6 |
| Recursion and Recovery | 5 | 4 | 5 |

## Section overviews

**Mana development.** 28 cards touch this layer, carrying 47 in-category
role assignments concentrated in artifact-based acceleration: 14 mana rocks,
14 ramp effects, 9 cost reducers, 5 mana fixers, 5 utility-land mana
contributions. No card carries `land_ramp` or `ritual_or_burst_mana`;
acceleration is almost entirely permanent-based.

**Card advantage and selection.** 11 cards provide card advantage (4
repeatable draw, 2 burst draw, 4 impulse/selection, 1 graveyard access); 16
cards provide selection and tutoring across 20 role assignments (7 artifact
tutors, 5 broad tutors, 4 filtering, 3 topdeck manipulation, 1 land tutor).
Selection is weighted toward finding specific artifacts rather than
accumulating raw cards.

**Interaction.** 15 cards across 16 role assignments: 4 counterspells, 4
board wipes, 2 targeted removal, 2 bounce, 2 stax/hate pieces, 2 graveyard
hate. The suite leans toward stack answers and mass removal, with few
single-target permanent answers.

**Protection and resilience.** 8 playable cards across 11 role assignments:
4 broad protection, 3 indestructible/regeneration, 2 hexproof/shroud, 2
pillowfort. No playable card carries `anti_wipe_protection`; the only card
with that role (Darksteel Forge) is in the imported SIDEBOARD.

**Recursion and recovery.** 5 cards, all artifact-directed. The deck has no
tagged recursion for non-artifact cards.

**Engine and scaling.** 14 cards across 24 role assignments: 6 tap-untap
engines, 6 scaling threats, 5 payoff engines, 3 artifact engines, 3 mana
engines, 1 token engine. The deck appears structurally dense in repeatable
artifact-driven value loops, consistent with its stated engine identity.

**Combo and win conditions.** 5 cards across 6 role assignments: 5 damage
payoffs and 1 combo payoff (Aetherflux Reservoir, which carries both). No
card currently carries `combo_piece`,
`combo_enabler`, `finisher`, or `alternate_win_condition`. Given the stated
combo-control archetype, this gap between the archetype description and the
tagged win-condition structure is a primary area to investigate — it may
reflect first-pass Knowledge coverage rather than the deck's actual
structure.

**Board presence.** 24 cards, almost entirely `creature_body` (23) plus 3
token producers (two of which are also creature bodies). No evasive
threats, dedicated blockers, or
commander-support cards are tagged; board presence reads as functional mass
rather than combat pressure, consistent with bodies-as-resources.

**Lands and mana base.** 34 lands for a five-color identity, carrying 66
land-role assignments: 21 colored sources, 19 colorless sources, 12 fixing
lands, 7 playable utility lands, 6 artifact lands, 1 fetch/search land, and
the three Urza lands. Only 7 lands are basics, while 23 nonland cards have
colored costs.

**Sideboard.** The imported SIDEBOARD holds 7 cards skewing toward defense
and disruption. Commander play typically has no sideboard, so the intended
relationship of these cards to the 100-card deck is an open question.

## Structural strengths

- High artifact density (50/100) structurally supporting the deck's engines,
  cost reducers, improvise costs, and artifact-count payoffs.
- A deep mana development layer (28 cards carrying 47 mana-development role
  assignments) built on redundant rocks and cost reduction, matching the
  explosiveness goal.
- Dedicated artifact tutoring (7 cards) plus broad tutors (5) giving
  structural access to specific engine pieces.
- Redundant untap effects (6 tap-untap engines) that can reuse rocks and
  activated abilities.
- An artifact recursion package (5 cards) for recovering the deck's primary
  resource type.
- A low, engine-oriented curve (average nonland mana value 3.0; 49 of 66
  nonland cards at mana value 3 or less).

## Structural pressure points (areas to investigate)

- Win-condition structure is under-described in current Knowledge: no
  finisher, combo piece, or combo enabler is tagged despite the combo-control
  archetype. Knowledge coverage gap or structural gap — to be determined.
- The card advantage layer is comparatively small (11 cards), relevant to
  the consistency goal.
- Colored-cast consistency for a five-color identity is unverified: 23
  colored nonland cards against 21 colored sources and 12 fixing lands.
- Anti-wipe resilience is absent from the playable 100, relevant to the
  resilience goal for a board-dependent engine deck.
- Recursion is exclusively artifact-directed.
- Targeted removal is a small share of interaction (2 of 15 interaction
  cards).
- Myr typal density (14/100) versus the commander's Myr-focused triggers is
  untested.
- The 7-card SIDEBOARD has no defined role in Commander play.

## Open questions for later testing

1. Which card combinations constitute the intended combo lines, and which
   cards would carry `combo_piece`/`combo_enabler` once synergy mapping
   exists?
2. Does Aetherflux Reservoir have sufficient structural support as a win
   route, and which cards feed it?
3. How often can the 23 colored nonland cards be cast on curve? (Simulation,
   later.)
4. How frequently do the commander's Myr triggers find targets with 14 Myr
   typal cards?
5. Is the absence of land ramp and burst mana a deliberate identity or an
   artifact of the current list?
6. What is the SIDEBOARD's intended function in this project's workflow?
7. Do the 13 medium-confidence role assignments hold up under focused
   review?

## Boundary note

Recommendations come in a later task. Nothing in this analysis
pre-authorizes any deck change, and no statement here should be read as a
suggestion to alter the decklist.
