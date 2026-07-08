# Card Data

## Card Facts Checkpoint

Scryfall is the canonical card facts source for Sprint 1.

`cards.json` currently contains canonical imported facts for all 106 cards in The Myr Singularity fixture. Exact-name matching is preferred for card fact import. Scryfall `flavor_name` aliases may be resolved only when the alias is explicitly verified from Scryfall metadata.

When a decklist name differs from the canonical card name, the original decklist name must be preserved through fields such as `original_decklist_name` and `display_name`.

Card Facts are not Card Knowledge. Card Facts must not include functional roles, strategic tags, synergy interpretation, analysis, or recommendations.
