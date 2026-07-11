# Decision decision-003 - Urza's Saga (pending deck-change design)

## Source candidate

- **Recommendation set:** rec-002
- **Candidate:** cand-008 (add_candidate)
- **Review record:** `review-rec-002.json` (Product Owner review, 2026-07-10)

## Current status

`implemented_as_v1.1` — this decision has been implemented as part of
DeckVersion v1.1 (implemented at 2026-07-10T21:32:00Z) through the
Product-Owner-approved `deck-change-design-v1.1`.

**Implementation summary:**

- Incoming: Urza's Saga
- Outgoing: Urza's Tower
- Implementation rationale: approved artifact land / utility update from v1.1 design.
- `deck/current.txt` reflects v1.1; `versions/v1.1.json` records the
  implemented version.
- Trace: candidate -> review -> decision scaffold -> design -> Product
  Owner approval -> v1.1 implementation.

## Candidate summary

Urza's Saga utility/artifact land candidate: land-slot artifact selection,
Construct board presence scaling with the deck's artifact count, and
colorless mana.

## Rationale

Product Owner accepted Urza's Saga for the decision path because it is
strongly aligned with the artifact-engine identity and may improve
utility, selection, and board development.

## Incoming cards under consideration

- Urza's Saga

## Outgoing cards

Cuts were deferred at scaffold time and later selected in the approved
deck-change design: Urza's Tower (implemented in v1.1).

## Unresolved design questions

- Which land or utility slot should Urza's Saga replace?
- Does Urza's Saga require additional one-mana artifact targets to
  maximize value?
- Does the Saga line improve consistency without making the deck feel like
  generic artifact goodstuff?

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
