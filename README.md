# The Workshop

The Workshop is a local-first Deck Engineering Platform for Commander. It is a structured workspace for deck analysis, recommendations, decisions, versions, reports, and evidence rather than a generic deck builder.

## Current Delivery State

- **Sprint 1** is completed and independently certified.
- **Sprint 2 — Evidence Loop Foundation** is active at kickoff.
- Sprint 1 certification covers local product-loop execution, structure, traceability, reproducibility, and evidence honesty. It does not claim simulation, gameplay validation, win rate, or measured deck performance.
- Krark-Clan Ironworks and Mana Echoes remain `needs_testing` and unimplemented.

## Repository Layout

- [`/docs`](docs/README.md) is the operational source for product, architecture, RFC, ADR, planning, delivery, and review documentation.
- [`/workshop`](workshop) contains the executable prototype and structured evidence.

## Storage Model

- JSON stores structured evidence and machine-validated artifacts.
- Markdown stores readable reports, notes, and synchronized RFC documentation.

The repository remains local-first. It is not a full web application, SaaS architecture, or production database deployment.
