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
| `validate_project_reports.py` | Structured project reports, source traceability, exact DeckVersion deltas, evidence status, and deterministic Markdown |

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
python workshop/tests/validation/validate_project_reports.py
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

`validate_candidate_card_facts.py` checks the active Sprint 1 external intake,
its stable intake manifest, promoted canonical identities, metadata counts,
required canonical fields, unique identities, facts-only status, and
non-actionable boundary.

The candidate validator owns the active/promoted partition and the promoted
name-to-ID mapping. The Knowledge validator owns the canonical metadata summary
and verifies that it exactly agrees with the candidate lifecycle mapping and
canonical Card Facts.

It does not import, recommend, or implement cards.

## Recommendation validation

`validate_recommendation_schema.py` checks schema-only and candidate-set modes,
candidate lifecycle fields, evidence, project traceability, qualified card
references, Commander legality, color identity, and non-actionable boundaries.

Card references use Scryfall IDs as stable identity. A
`candidate:scryfall:<id>` reference resolves from active candidate staging, or
from canonical Card Facts only when the ID is retained in the candidate intake
manifest after promotion. An arbitrary canonical-only ID is not a candidate
reference. If both stores contain the ID, their canonical facts must agree;
conflicting or duplicate identities fail validation. Moving a known intake facts
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
- Parent/child additions and removals are matched by commander, main-deck, and
  sideboard zones, with quantities preserved in every zone.
- Sideboard names and quantities remain unchanged without an approved
  sideboard change; approved sideboard additions and removals must match exactly.
- The exact zone-aware, quantity-aware parent/child diff matches the design,
  decisions, and DeckVersion change metadata.
- Unapproved candidate changes are absent.
- Cards outside the approved diff remain unchanged.

Card names use deterministic Unicode NFKC, whitespace, and case normalization
for comparisons. Card Facts aliases are used only to identify singleton
exceptions such as basic lands.

## Project report validation

`workshop/scripts/render_project_report.py` renders each committed
`project_report_v*.json` document to its same-name Markdown file. The renderer
is deterministic: a clean render must leave the committed Markdown unchanged.

`validate_project_reports.py` discovers reports under project metadata rather
than assuming a particular project. `WORKSHOP_PROJECT_ID` may focus validation
on one project. It validates each referenced source by identity and relationship,
parses the referenced current decklist using the DeckVersion parser, compares all
three zones and quantities with the resulting version, and derives the exact
parent/child delta.

The report validator also verifies per-card decision attribution, decision
summaries, source-derived candidate dispositions, canonical Card Facts,
Functional Knowledge, and retained candidate provenance. Evidence entries use a
generic status/source model: unmeasured states have no evidence source, while
completed, validated, or measured states must resolve to matching structured
post-implementation evidence. It verifies implementation and traceability only;
it does not certify Sprint 1.

The renderer uses only report JSON. Version headings, delta counts, candidate
groups, evidence status, and next actions are all data-driven and deterministic.

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
- Rejects a canonical-only ID masquerading as a candidate reference.
- Preserves historical candidate references after canonical Card Facts
  promotion.
- Accepts an approved sideboard replacement and rejects an unapproved sideboard
  quantity change.
- Requires promoted candidate identities to exist in canonical facts, rejects
  conflicting duplicate facts, and verifies canonical role-assignment coverage.
- Rejects invalid report DeckVersion references, incorrect reported deltas,
  measured-outcome claims without evidence, candidate disposition drift,
  Markdown drift, and missing required source artifacts.
- Rejects current-deck divergence, false decision attribution, decision-summary
  drift, wrong existing source types, false Knowledge/provenance claims, and
  missing implemented Knowledge cards.
- Proves relationship-driven candidate IDs, dynamic renderer labels/counts/
  candidate groups, and valid future evidence references in isolated fixtures.

No regression test mutates committed project data.
