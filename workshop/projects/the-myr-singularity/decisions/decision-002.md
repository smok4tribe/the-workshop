# Decision decision-002 - City of Brass / Mana Confluence (pending deck-change design)

## Source candidate

- **Recommendation set:** rec-002
- **Candidate:** cand-007 (mana_base_adjustment_candidate)
- **Review record:** `review-rec-002.json` (Product Owner review, 2026-07-10)

## Current status

`implemented_as_v1.1` — this decision has been implemented as part of
DeckVersion v1.1 (implemented at 2026-07-10T21:32:00Z) through the
Product-Owner-approved `deck-change-design-v1.1`.

**Implementation summary:**

- Incoming: City of Brass, Mana Confluence
- Outgoing: Urza's Mine, Urza's Power Plant
- Implementation rationale: approved mana fixing update from v1.1 design.
- `deck/current.txt` reflects v1.1; `versions/v1.1.json` records the
  implemented version.
- Trace: candidate -> review -> decision scaffold -> design -> Product
  Owner approval -> v1.1 implementation.

## Candidate summary

City of Brass / Mana Confluence mana-fixing candidate: increase any-color
land sources for a five-color identity whose colored-cast consistency the
baseline flags as unverified.

## Rationale

Product Owner accepted the mana-fixing candidate for the decision path
because the baseline analysis identified colored-cast consistency as a
structural pressure point, and City of Brass / Mana Confluence directly
address colored access.

## Incoming cards under consideration

- City of Brass
- Mana Confluence

## Outgoing cards

Cuts were deferred at scaffold time and later selected in the approved
deck-change design: Urza's Mine, Urza's Power Plant (implemented in v1.1).

## Unresolved design questions

- Which lands should be cut if City of Brass and Mana Confluence advance
  to v1.1?
- Should both lands be added together or staged separately?
- How much life-loss/pain-land pressure is acceptable for the deck?

## Boundary statement

Historical scaffold boundary (superseded by implementation): the scaffold
itself did not change the deck, create v1.1, select cuts, or mark the
candidate as implemented. As of 2026-07-10 this decision has been
implemented as DeckVersion v1.1 via the approved deck-change-design-v1.1.
The originating rec-002 candidate record remains proposed in its
historical artifact and was not modified; Card Facts were not manually
authored.

## Required next step

`post_implementation_validation_or_report`
