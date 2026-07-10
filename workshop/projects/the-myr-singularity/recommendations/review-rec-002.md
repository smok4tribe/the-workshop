# Product Owner Review Scaffold - rec-002

## What this file is

This document (with its machine-readable companion `review-rec-002.json`) is
a **Product Owner review scaffold** for `rec-002`, the first external
proposed recommendation candidate set (`cand-007` through `cand-011`).

**It does not accept, reject, defer, or approve any candidate yet.** Every
review entry starts neutral, at `review_status: "under_review"`.

**It does not change the deck.** No card enters or leaves the deck as a
result of this artifact.

**It does not create v1.1.** No deck version file is created or edited by
this artifact.

**It does not create a decision log.** No entry is added to
`workshop/projects/the-myr-singularity/decisions/` by this artifact.

It exists so the Product Owner has a structured place to review each rec-002
candidate over time: recording notes, rationale, testing needs, and an
eventual review conclusion, separately from the recommendation candidate
records themselves.

## Layer separation

- **Recommendation candidates** (`rec-002.json`) are generated, proposed,
  non-actionable artifacts. They are not edited by review.
- **Product Owner review** (this artifact) records human review intent:
  where a candidate currently stands in the Product Owner's evaluation.
  `accepted_for_decision` here does **not** change the deck; it only means
  the candidate may proceed to a future decision log task.
- **Decision log** (`workshop/projects/the-myr-singularity/decisions/`)
  is a separate, later artifact that records an actual Product Owner
  decision once one is made.
- **Deck version** (`workshop/projects/the-myr-singularity/versions/`) is
  the only place an actual deck change is recorded, and only after a
  decision log entry exists.

## Review status values

`under_review`, `needs_testing`, `deferred`, `accepted_for_decision`,
`rejected`. See `review_schema.json` for the full contract and the explicit
distinction between `accepted_for_decision` and an authorized deck change.

## Candidate review entries

| candidate_id | candidate summary | review_status | testing_required | decision_log_required | creates_new_deck_version_if_accepted |
|---|---|---|---|---|---|
| cand-007 | Mana-fixing candidate using City of Brass and Mana Confluence. | under_review | null | true | true |
| cand-008 | Utility/artifact land candidate using Urza's Saga. | under_review | null | true | true |
| cand-009 | Artifact engine candidate using Krark-Clan Ironworks. | under_review | null | true | true |
| cand-010 | Combo engine candidate using Mana Echoes. | under_review | null | true | true |
| cand-011 | Planeswalker/artifact engine candidate using Tezzeret the Seeker. | under_review | null | true | true |

## Boundary note

This artifact creates a review scaffold only. It does not accept, reject,
defer, or approve `cand-007` through `cand-011`. It does not edit
`rec-002.json` or `rec-002.md`. It does not create a decision log entry or a
new deck version. No deck change is authorized.
