# Decision decision-004 - Tezzeret the Seeker (pending deck-change design)

## Source candidate

- **Recommendation set:** rec-002
- **Candidate:** cand-011 (add_candidate)
- **Review record:** `review-rec-002.json` (Product Owner review, 2026-07-10)

## Current status

`implemented_as_v1.1` — this decision has been implemented as part of
DeckVersion v1.1 (implemented at 2026-07-10T21:32:00Z) through the
Product-Owner-approved `deck-change-design-v1.1`.

**Implementation summary:**

- Incoming: Tezzeret the Seeker
- Outgoing: Nevinyrral's Disk
- Implementation rationale: approved artifact-engine nonland update from v1.1 design.
- `deck/current.txt` reflects v1.1; `versions/v1.1.json` records the
  implemented version.
- Trace: candidate -> review -> decision scaffold -> design -> Product
  Owner approval -> v1.1 implementation.

## Candidate summary

Tezzeret the Seeker artifact planeswalker engine candidate: battlefield
artifact tutoring, a repeatable two-artifact untap, and an
artifact-scaling threat in the planeswalker slot.

## Rationale

Product Owner accepted Tezzeret the Seeker for the decision path because
it is aligned with the artifact-engine plan and can function as tutor,
untap engine, or artifact-scaling threat.

## Incoming cards under consideration

- Tezzeret the Seeker

## Outgoing cards

Cuts were deferred at scaffold time and later selected in the approved
deck-change design: Nevinyrral's Disk (implemented in v1.1).

## Unresolved design questions

- Which noncreature spell or engine slot should Tezzeret the Seeker
  compete with?
- Is Tezzeret primarily a tutor, untap engine, or alternate
  artifact-scaling threat in this deck?
- Is five mana acceptable for the expected role?

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
