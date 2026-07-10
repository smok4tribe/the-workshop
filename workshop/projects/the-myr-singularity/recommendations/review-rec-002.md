# Product Owner Review Record - rec-002

## What this file is

This document (with its machine-readable companion `review-rec-002.json`) is
the **Product Owner review record** for `rec-002`, the first external
proposed recommendation candidate set (`cand-007` through `cand-011`).

**It records review states only.** The Product Owner has reviewed each
candidate and recorded an outcome, but:

**It does not change the deck.** No card enters or leaves the deck as a
result of this artifact.

**It does not create v1.1.** No deck version file is created or edited by
this artifact.

**It does not create a decision log.** No entry is added to
`workshop/projects/the-myr-singularity/decisions/` by this artifact.

- `accepted_for_decision` only means the candidate is **eligible for a
  future decision-log task**. It does not accept a deck change.
- `needs_testing` only means **testing is required before any decision-log
  task** for that candidate.

## Layer separation

- **Recommendation candidates** (`rec-002.json`) are generated, proposed,
  non-actionable artifacts. They are not edited by review and remain
  `proposed`, non-actionable, and undecided.
- **Product Owner review** (this artifact) records human review intent:
  where a candidate currently stands in the Product Owner's evaluation.
  `accepted_for_decision` here does **not** change the deck; it only means
  the candidate may proceed to a future decision log task.
- **Decision log** (`workshop/projects/the-myr-singularity/decisions/`)
  is a separate, later artifact that records an actual Product Owner
  decision once one is made. None exists yet.
- **Deck version** (`workshop/projects/the-myr-singularity/versions/`) is
  the only place an actual deck change is recorded, and only after a
  decision log entry exists. v1.1 has not been created.

## Review status values

`under_review`, `needs_testing`, `deferred`, `accepted_for_decision`,
`rejected`. See `review_schema.json` for the full contract and the explicit
distinction between `accepted_for_decision` and an authorized deck change.

## Review outcomes (recorded 2026-07-10)

Top-level review status: `in_progress`.

| candidate_id | candidate summary | review_status | testing_required | rationale summary | decision_log_required | creates_new_deck_version_if_accepted |
|---|---|---|---|---|---|---|
| cand-007 | City of Brass / Mana Confluence mana-fixing candidate. | accepted_for_decision | false | Baseline flags colored-cast consistency; these lands directly address colored access. | true | true |
| cand-008 | Urza's Saga utility/artifact land candidate. | accepted_for_decision | false | Aligned with the artifact-engine identity; supports artifact utility. | true | true |
| cand-009 | Krark-Clan Ironworks artifact engine candidate. | needs_testing | true | May significantly increase combo-engine explosiveness and shift the deck identity; test first. | true | true |
| cand-010 | Mana Echoes Myr typal burst candidate. | needs_testing | true | Highly synergistic with Myr density but may be board-dependent or win-more; test first. | true | true |
| cand-011 | Tezzeret the Seeker artifact planeswalker engine candidate. | accepted_for_decision | false | Aligned with the artifact-engine plan as tutor, untap engine, or artifact-scaling threat. | true | true |

## Testing notes

- **cand-009**: test whether KCI improves explosive turns without making
  the deck feel too deterministic or drifting away from the intended Myr
  artifact identity.
- **cand-010**: test whether Mana Echoes consistently creates meaningful
  Myr-driven mana bursts or only performs when the board is already
  developed.

## Boundary note

This artifact records Product Owner review states only. It does not accept
a deck change for any candidate. Every candidate that later advances still
requires a decision log entry and a new deck version file before any card
enters or leaves the deck. It does not edit `rec-002.json` or `rec-002.md`,
does not create a decision log entry, and does not create v1.1.
No deck change is authorized.
