# RFC-009 - Architecture Decision Records

## ADR-010 - Canonical Card Facts Require an External Source

Status: Accepted

### Decision

Scryfall bulk/oracle data is the MVP canonical source for card facts.

### Rationale

Card facts must come from an external canonical source. AI must not author card facts, because generated card data can introduce incorrect mana costs, oracle text, type lines, colors, legalities, prices, tags, roles, or synergies.

The current `workshop/card-data/cards.json` file contains unresolved placeholder records only. Each record identifies a card name and marks that external card data is still required.

Actual card fact enrichment will happen in a later task after the Scryfall bulk/oracle data import path is defined.
