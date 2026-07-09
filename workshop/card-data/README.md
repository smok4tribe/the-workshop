# Card Data

## Card Facts Checkpoint

Scryfall is the canonical card facts source for Sprint 1.

`cards.json` currently contains canonical imported facts for all 106 cards in The Myr Singularity fixture. Exact-name matching is preferred for card fact import. Scryfall `flavor_name` aliases may be resolved only when the alias is explicitly verified from Scryfall metadata.

When a decklist name differs from the canonical card name, the original decklist name must be preserved through fields such as `original_decklist_name` and `display_name`.

Card Facts are not Card Knowledge. Card Facts must not include functional roles, strategic tags, synergy interpretation, analysis, or recommendations.

## Candidate Card Facts

Deck Card Facts remain in `cards.json`. That file contains the canonical facts
for the imported deck and sideboard only.

External candidate Card Facts live in `candidate_cards.json`, with intake
metadata in `candidate_card_import_metadata.json`. These records are sourced
from Scryfall and are kept separate from the deck Card Facts layer so future
recommendation candidates can reference external cards without modifying the
current deck facts.

Candidate Card Facts are not recommendations. They do not authorize deck
changes, create recommendation candidates, modify deck versions, or record
decisions. Future recommendation candidates can reference candidate facts only
when the recommendation validator supports candidate Card Facts references.
