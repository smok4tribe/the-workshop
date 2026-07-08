# Knowledge

Local structured knowledge files for Sprint 1.

## Boundary

Card Facts are canonical external data. For Sprint 1, Scryfall is the canonical source for Card Facts.

Functional Roles are project-independent Card Knowledge. Roles describe what a card can do in deck construction terms, such as ramp, interaction, recursion, or combo support.

Functional Roles are not recommendations, not analysis, and not deck-specific importance scores. A card may eventually have multiple roles, but this layer defines the controlled vocabulary only.

Project-specific role weighting, role overrides, or context-sensitive interpretation belongs later in `project_override_schema.json` or project-level knowledge, not in this taxonomy.

## Files

- `role_taxonomy.json`: controlled functional role vocabulary grouped by category.
- `functional_roles.json`: reserved for future card-to-role assignments; Task 10 does not assign roles to cards.
- `project_override_schema.json`: reserved for future project-specific role weighting or overrides.

## Task 10 Scope

Task 10 starts the Card Knowledge layer by defining the functional role taxonomy. It does not assign roles to specific cards, add synergy maps, produce recommendations, perform analysis, run simulations, or modify Card Facts.
