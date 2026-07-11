# Validation

The Sprint 1 validation suite separates data-layer checks from project-pipeline
checks. Every validator is read-only and uses only the Python standard library.

## Validator boundaries

| Validator | Responsibility |
| --- | --- |
| `validate_knowledge_layer.py` | Canonical Card Facts, role taxonomy, and functional-role assignments |
| `validate_candidate_card_facts.py` | External candidate Card Facts intake and facts-only boundaries |
| `validate_recommendation_schema.py` | Recommendation candidate schema, references, and non-actionable candidate records |
| `validate_recommendation_review.py` | Product Owner candidate-review artifacts and review-state transitions only |
| `validate_decision_pipeline.py` | Recommendation, review, decisions, deck-change design, and Product Owner approval |
| `validate_deck_versions.py` | Current deck, parent/child DeckVersions, quantity-aware diffs, and implementation integrity |

`validate_recommendation_review.py` intentionally does not validate decisions,
designs, approval, implementation, DeckVersions, or `deck/current.txt`.

## Run the positive validators

From the repository root:

```bash
python workshop/tests/validation/validate_knowledge_layer.py
python workshop/tests/validation/validate_candidate_card_facts.py
python workshop/tests/validation/validate_recommendation_schema.py
python workshop/tests/validation/validate_recommendation_review.py
python workshop/tests/validation/validate_decision_pipeline.py
python workshop/tests/validation/validate_deck_versions.py
```

The recommendation validator defaults to `rec-001`. Validate `rec-002` in
PowerShell with:

```powershell
$env:WORKSHOP_RECOMMENDATION_JSON = "workshop/projects/the-myr-singularity/recommendations/rec-002.json"
$env:WORKSHOP_RECOMMENDATION_MD = "workshop/projects/the-myr-singularity/recommendations/rec-002.md"
python workshop/tests/validation/validate_recommendation_schema.py
Remove-Item Env:\WORKSHOP_RECOMMENDATION_JSON
Remove-Item Env:\WORKSHOP_RECOMMENDATION_MD
```

## Knowledge Layer validation

`validate_knowledge_layer.py` checks that:

- `cards.json`, `role_taxonomy.json`, and `functional_roles.json` parse.
- The Sprint 1 Card Facts and assignment populations remain one-to-one by
  Scryfall ID.
- Role IDs exist in the taxonomy.
- Primary and secondary roles are disjoint subsets whose union equals `roles`.
- Confidence, source type, evidence, and Card Facts/Card Knowledge boundaries
  are valid.

It does not analyze decks or produce recommendations.

## Candidate Card Facts validation

`validate_candidate_card_facts.py` checks the six-card Sprint 1 external intake,
its Scryfall provenance, metadata counts, required canonical fields, unique
identities, facts-only status, and non-actionable boundary.

It does not import, recommend, or implement cards.

## Recommendation validation

`validate_recommendation_schema.py` checks schema-only and candidate-set modes,
candidate lifecycle fields, evidence, project traceability, qualified card
references, Commander legality, color identity, and non-actionable boundaries.

Card references use Scryfall IDs as stable identity. A historical
`candidate:scryfall:<id>` reference resolves from candidate staging or canonical
Card Facts after promotion. If both stores contain the ID, their canonical facts
must agree; conflicting or duplicate identities fail validation. Moving a facts
record between lifecycle stores therefore does not invalidate history.

Legacy bare `scryfall:<id>` references remain limited to `rec-001`.

## Recommendation Review validation

`validate_recommendation_review.py` checks only the Product Owner review layer:

- Review schema and artifact structure.
- One review entry per recommendation candidate.
- Controlled review statuses and coherent top-level progression.
- Rationale, timestamps, and testing disposition for progressed entries.
- Concrete testing notes for `needs_testing`.
- Preservation of decision-log and new-version gates.
- A non-authorizing review boundary.
- Unmodified proposed recommendation candidates.
- Review Markdown coverage.

It does not inspect `decisions/`, `versions/`, designs, approvals, implementation,
or the current deck.

## Decision Pipeline validation

`validate_decision_pipeline.py` validates:

```text
Recommendation
-> Product Owner Review
-> Decisions
-> Deck-change Design
-> Product Owner Approval
```

It resolves the target version from artifact metadata. Implemented status names
are derived from that target, so later versions do not require a source-code
version literal.

Checks include:

- Recommendation and review references resolve.
- Review outcomes remain distinct.
- Decisions reference only `accepted_for_decision` candidates.
- Decision state matches the target version and implementation source.
- Design additions and removals exactly match and map to decisions.
- Rejected, deferred, and `needs_testing` candidates cannot enter the design.
- Product Owner approval and design status are coherent.

## DeckVersion validation

`validate_deck_versions.py` resolves the current version from
`project.json.current_version_id`. It then checks:

- The current and parent DeckVersions exist and have coherent identity.
- Commander, main-deck, and total quantities are exactly 1, 99, and 100.
- Quantities are positive integers and singleton rules are quantity-aware.
- The commander is not duplicated in the main deck.
- `deck/current.txt` exactly matches the resolved current DeckVersion.
- Sideboard names and quantities remain unchanged without an approved
  sideboard change.
- The exact quantity-aware parent/child diff matches the design, decisions, and
  DeckVersion change metadata.
- Unapproved candidate changes are absent.
- Cards outside the approved diff remain unchanged.

Card names use deterministic Unicode NFKC, whitespace, and case normalization
for comparisons. Card Facts aliases are used only to identify singleton
exceptions such as basic lands.

## Regression tests

Run the committed mutation suite with:

```bash
python -m unittest discover -s workshop/tests/validation -p "test_*.py" -v
```

The tests use isolated temporary repository copies. They prove that validation:

- Rejects divergence between `current.txt` and the current DeckVersion.
- Rejects quantity-only main-deck corruption.
- Rejects a same-count sideboard replacement.
- Rejects a `needs_testing` candidate inserted into the design.
- Preserves historical candidate references after canonical Card Facts
  promotion.

No regression test mutates committed project data.
