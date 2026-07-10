# Deck-Change Design for v1.1 - Accepted rec-002 Decisions

## Status

`product_owner_approved` — the Product Owner **approved this design as
proposed** on 2026-07-10. The approval covers the exact IN/OUT sets below.

Even with approval, this artifact remains **non-implementing**: no deck
change is implemented in this task, `deck/current.txt` remains unchanged,
and `versions/v1.1.json` is not created or populated yet. Approval
authorizes the next task to create DeckVersion v1.1; it does not itself
change the deck.

## Approved IN / OUT

| IN | slot | OUT | slot |
|---|---|---|---|
| City of Brass | land | Urza's Mine | land |
| Mana Confluence | land | Urza's Power Plant | land |
| Urza's Saga | land | Urza's Tower | land |
| Tezzeret the Seeker | nonland | Nevinyrral's Disk | nonland |

## Approval rationale

The Product Owner approves the design because it directly addresses
colored mana consistency, removes the low-consistency Tron package, adds
artifact-aligned utility and tutoring, preserves Myr identity, keeps
Walking Ballista, keeps land count stable, and removes the most
self-destructive board wipe rather than cutting core engine/ramp pieces.

## Source decisions

- `decision-002` (cand-007): City of Brass + Mana Confluence
- `decision-003` (cand-008): Urza's Saga
- `decision-004` (cand-011): Tezzeret the Seeker

cand-009 (Krark-Clan Ironworks) and cand-010 (Mana Echoes) remain
`needs_testing` and are **not** part of this design.

## Proposed v1.1 design summary

Keep the land count at 34 by swapping the three Urza's Tron lands for the
three incoming lands, and make a single nonland swap for Tezzeret the
Seeker. Four cards in, four cards out.

## Why these incoming cards

- **City of Brass / Mana Confluence**: the baseline flags colored-cast
  consistency as a structural pressure point (23 colored nonland cards
  against 21 colored sources). Two any-color lands raise colored sources
  to 23 and ease historically hard casts such as Organic Extinction's
  double white. The life cost is the accepted price of full fixing.
- **Urza's Saga**: converts a land slot into artifact selection (0-1
  mana-value targets include Walking Ballista, Skullclamp, and six
  artifact lands), Construct board presence scaling with 50 artifacts,
  and colorless mana. It is itself an Urza's land, so Urza's Cave can
  still fetch it after Tron leaves.
- **Tezzeret the Seeker**: battlefield artifact tutoring (mana value X or
  less), a repeatable two-artifact untap that reuses the deck's 14 mana
  rocks, and an artifact-scaling threat — all proactive engine roles the
  Product Owner flagged as wanted.

## Why these outgoing cards

- **Urza's Mine / Power Plant / Tower**: incomplete Tron is a
  low-consistency assembly in singleton Commander, and all three pieces
  produce only colorless mana in a deck whose defining mana problem is
  colored access. Cutting the trio removes the incomplete-Tron failure
  mode entirely; the deck's explosiveness plan is artifact-based, not
  land-based.
- **Nevinyrral's Disk**: of the three board wipes, it is the only one
  that destroys the deck's own artifact board (and enters tapped). The
  remaining wipes are better aligned: All Is Dust spares the deck's
  mostly colorless permanents, and Organic Extinction becomes more
  castable with the new fixing.

## Alternative cuts considered

- **Propaganda** — less aligned with the proactive plan, but it is the
  only `defensive_pillowfort` effect in the playable 100 and resilience
  is a stated project goal. Swap it for the Disk cut if the Product Owner
  prefers keeping three wipes.
- **Prismatic Lens** — the weakest of five fixing rocks once land-level
  fixing improves, but it is a cheap Tezzeret untap target and cutting it
  would lower rock/ramp density alongside a curve-topping addition. Swap
  it for the Disk cut if the Product Owner prefers preserving interaction
  count. Whether the Lens stays worth its slot after v1.1 is flagged as a
  future review question.

## Mana-base impact

- Land count: 34 → 34.
- Colored sources: 21 → 23; fixing lands: 12 → 14.
- Colorless-only sources: 19 → 17 (colorless needs remain well covered).
- The rare assembled-Tron burst is given up in exchange for consistent
  colored access.
- New incremental life pressure from the two painlands, flagged for
  testing observation.

## Artifact-engine impact

- Artifact tutoring rises from 7 toward 9 effective sources (Saga
  chapters + Tezzeret), with Tezzeret putting targets directly onto the
  battlefield.
- Tezzeret's +1 reinforces the 6 existing untap engines and reuses the 14
  mana rocks.
- Urza's Saga adds scaling Construct board presence from the mana base.
- No engine piece is cut; the outgoing nonland was interaction.

## Identity impact

- No Myr card is touched; the Myr typal plan is unchanged.
- The artifact-engine identity is strengthened; the cut wipe was the
  deck's only self-destructive artifact effect.
- Walking Ballista is not cut and gains value as a Saga/Tezzeret target.
- The commander is untouched and no sideboard card is used as a main-deck
  cut.

## Risk assessment

- Board-wipe density drops from 3 to 2 (alternatives listed if that is
  too low).
- Painland life loss accumulates in longer games.
- Tezzeret the Seeker (5 mana value on a 3.0 curve) may not survive a
  turn cycle; its rock-untap floor limits the downside.
- Urza's Saga self-sacrifices after chapter III, effectively lowering the
  land count by one over time.
- The Tron trio carried 3 of 5 `utility_land_mana` tags; land-based ramp
  texture drops slightly, with the 14 mana rocks remaining the primary
  acceleration.

## Boundary statement

This design has Product Owner approval, but the deck change is approved
and **not implemented**. This artifact still does not modify the deck: no
deck change is implemented in this task. `deck/current.txt` remains
unchanged. `versions/v1.1.json` remains an empty, unpopulated placeholder.
A future task must create DeckVersion v1.1 before any implementation
exists. This design does not mark any decision as implemented, does not
mark any recommendation candidate as accepted or implemented, and does
not promote candidate card facts into deck card facts.

## Required next step

`create_deck_version_v1.1` — create DeckVersion v1.1 in a future task.
