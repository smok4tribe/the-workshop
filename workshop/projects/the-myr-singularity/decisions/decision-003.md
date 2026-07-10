# Decision decision-003 - Urza's Saga (pending deck-change design)

## Source candidate

- **Recommendation set:** rec-002
- **Candidate:** cand-008 (add_candidate)
- **Review record:** `review-rec-002.json` (Product Owner review, 2026-07-10)

## Current status

`pending_deck_change_design` — the Product Owner accepted this candidate
for the decision-log path, but the exact deck change has not been designed
yet. This is **not** a final accepted deck change, **not** an implemented
change, and it does **not** authorize deck mutation.

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

None selected yet. Choosing cuts is deliberately deferred to the
deck-change design task.

## Unresolved design questions

- Which land or utility slot should Urza's Saga replace?
- Does Urza's Saga require additional one-mana artifact targets to
  maximize value?
- Does the Saga line improve consistency without making the deck feel like
  generic artifact goodstuff?

## Boundary statement

This decision scaffold does not change the deck. It does not create v1.1.
It does not select outgoing cuts. It does not mark the recommendation
candidate as implemented. A future task must design the actual deck change
and create a new deck version before implementation.

## Required next step

`deck_change_design_before_v1.1`
