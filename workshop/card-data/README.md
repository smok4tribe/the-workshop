# Card Data

## Card Facts Checkpoint

Scryfall is the canonical card facts source for Sprint 1.

`cards.json` currently contains canonical imported facts for the 106-card v1.0 fixture and the four implemented v1.1 incoming cards. Exact-name matching is preferred for card fact import. Scryfall `flavor_name` aliases may be resolved only when the alias is explicitly verified from Scryfall metadata.

When a decklist name differs from the canonical card name, the original decklist name must be preserved through fields such as `original_decklist_name` and `display_name`.

Card Facts are not Card Knowledge. Card Facts must not include functional roles, strategic tags, synergy interpretation, analysis, or recommendations.

## Candidate Card Facts

Deck Card Facts remain in `cards.json`. That file contains the canonical facts
for the imported deck and sideboard only.

Active external candidate Card Facts live in `candidate_cards.json`, with intake
metadata in `candidate_card_import_metadata.json`. The stable intake manifest
also retains promoted identities so prior `candidate:scryfall:<id>` references
remain resolvable through canonical facts without treating promoted cards as
active candidate records.

The intake manifest is authoritative for the original candidate identity set.
Active status comes from `candidate_cards.json`; promoted storage comes from
canonical `cards.json`. Both metadata files carry a validated summary of the
same promoted name-to-ID records and do not independently define lifecycle
state.

Candidate Card Facts are not recommendations. They do not authorize deck
changes, create recommendation candidates, modify deck versions, or record
decisions. Future recommendation candidates can reference candidate facts only
when the recommendation validator supports candidate Card Facts references.
