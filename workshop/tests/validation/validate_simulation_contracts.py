#!/usr/bin/env python3
"""Validate the Sprint 2 Task 30 simulation policy and contracts.

Read-only, standard-library only. Verifies the Simulation Policy, the
project-scoped card semantics, the SimulationQuestion / SimulationRun /
SimulationResult / ComparisonResult contracts, the failure-pattern taxonomy,
and the documented (not executed) first evidence question. It also recomputes
the deck-content fingerprints from the immutable DeckVersions and proves that
no production simulation run or result artifact exists.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unicodedata
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ID = os.environ.get("WORKSHOP_PROJECT_ID", "the-myr-singularity")
PROJECT_DIR = REPO_ROOT / "workshop" / "projects" / PROJECT_ID
SIM_DIR = PROJECT_DIR / "simulation"
CONTRACTS_DIR = SIM_DIR / "contracts"
QUESTIONS_DIR = SIM_DIR / "questions"
VERSIONS_DIR = PROJECT_DIR / "versions"
CARDS_PATH = REPO_ROOT / "workshop" / "card-data" / "cards.json"

POLICY_VERSION = "sim-policy-v1"
FINGERPRINT_ALGORITHM_ID = "deck-content-sha256-v1"
SEED_ALGORITHM_ID = "sim-seed-sha256-v1"

REQUIRED_OVERRIDE_CARDS = {
    "City of Brass": {
        "counts_as_land_drop": True,
        "produces_colors": ["W", "U", "B", "R", "G"],
        "produces_colorless": False,
        "counts_as_five_color_source": True,
    },
    "Mana Confluence": {
        "counts_as_land_drop": True,
        "produces_colors": ["W", "U", "B", "R", "G"],
        "produces_colorless": False,
        "counts_as_five_color_source": True,
    },
    "Urza's Saga": {
        "counts_as_land_drop": True,
        "produces_colors": [],
        "produces_colorless": True,
        "counts_as_five_color_source": False,
    },
}

FORBIDDEN_CLAIM_PHRASES = [
    "win rate",
    "win probability",
    "average win turn",
    "gameplay performance",
    "matchup performance",
    "generic deck quality",
    "the deck is better",
]

INSTANCE_ARTIFACT_TYPES = {"simulation_run", "simulation_result", "comparison_result"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_identity(value):
    return " ".join(unicodedata.normalize("NFKC", str(value)).split())


def zone_counter(version, source_field):
    counter = Counter()
    if source_field == "commander":
        obj = version.get("commander")
        if isinstance(obj, dict) and obj.get("name"):
            counter[normalize_identity(obj["name"])] += int(obj.get("quantity", 1))
        return counter
    for entry in version.get(source_field, []):
        if isinstance(entry, dict) and entry.get("name"):
            counter[normalize_identity(entry["name"])] += int(entry.get("quantity", 1))
    return counter


def deck_content_fingerprint(version):
    """Implements deck-content-sha256-v1 exactly as defined in the policy."""
    blocks = []
    for zone_label, source_field in (("commander", "commander"), ("library", "main_deck")):
        counter = zone_counter(version, source_field)
        card_lines = [f"{counter[name]} {name}" for name in sorted(counter)]
        blocks.append(zone_label + "\n" + "\n".join(card_lines))
    serialized = "\n\x1e\n".join(blocks)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{FINGERPRINT_ALGORITHM_ID}:{digest}"


def derive_seed(question_id, policy_version, deck_content_fp, run_role):
    """Implements sim-seed-sha256-v1 exactly as defined in the policy."""
    payload = "\x1f".join([question_id, policy_version, deck_content_fp, run_role])
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def require_fields(obj, fields, label):
    if not isinstance(obj, dict):
        return [f"{label} is not an object"]
    return [f"{label} is missing required field {field!r}" for field in fields if field not in obj]


def find_forbidden(text):
    lowered = str(text).casefold()
    return [phrase for phrase in FORBIDDEN_CLAIM_PHRASES if phrase in lowered]


def report(checks):
    failed = 0
    for description, errors in checks:
        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {description}")
        for error in errors:
            print(f"       - {error}")
        failed += bool(errors)
    print()
    if failed:
        print(f"FAIL: {failed} of {len(checks)} simulation-contract checks failed.")
        return 1
    print(f"PASS: all {len(checks)} simulation-contract checks passed.")
    return 0


def main():
    checks = []

    def check(description, errors):
        checks.append((description, errors))

    # ---- artifacts exist and parse -------------------------------------------
    expected_files = {
        "policy": SIM_DIR / "simulation_policy.json",
        "policy_md": SIM_DIR / "simulation_policy.md",
        "card_semantics": SIM_DIR / "card_semantics.json",
        "question": QUESTIONS_DIR / "question-001-mana-color.json",
        "question_md": QUESTIONS_DIR / "question-001-mana-color.md",
        "question_contract": CONTRACTS_DIR / "simulation_question.contract.json",
        "run_contract": CONTRACTS_DIR / "simulation_run.contract.json",
        "result_contract": CONTRACTS_DIR / "simulation_result.contract.json",
        "comparison_contract": CONTRACTS_DIR / "comparison_result.contract.json",
        "taxonomy": CONTRACTS_DIR / "failure_pattern_taxonomy.json",
    }
    documents = {}
    errors = []
    for key, path in expected_files.items():
        if not path.is_file():
            errors.append(f"missing artifact: {path.relative_to(REPO_ROOT)}")
            continue
        if path.suffix == ".json":
            try:
                documents[key] = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(REPO_ROOT)} does not parse: {exc}")
    check("all simulation artifacts exist and parse", errors)
    if errors:
        return report(checks)

    policy = documents["policy"]
    semantics = documents["card_semantics"]
    question = documents["question"]
    taxonomy = documents["taxonomy"]

    # ---- policy: top-level ownership -----------------------------------------
    errors = require_fields(
        policy,
        [
            "artifact_type", "policy_id", "policy_version", "project_id", "references",
            "commander_scenario", "turn_semantics", "mulligan_policy", "keep_rule",
            "bottoming_rule", "sequencing_semantics", "card_behavior_boundary",
            "randomness_policy", "iteration_policy", "uncertainty_policy",
            "deck_fingerprint_policy", "metric_catalog", "commander_castability_policy",
            "evidence_language_boundary", "lifecycle_boundary", "explicit_boundary",
        ],
        "policy",
    )
    if policy.get("artifact_type") != "simulation_policy":
        errors.append("policy artifact_type must be 'simulation_policy'")
    if policy.get("policy_version") != POLICY_VERSION:
        errors.append(f"policy_version must be {POLICY_VERSION!r}")
    check("policy declares the universal ownership fields", errors)

    # ---- policy: commander scenario / turn semantics -------------------------
    errors = []
    scenario = policy.get("commander_scenario", {})
    if scenario.get("format") != "Commander":
        errors.append("commander_scenario.format must be 'Commander'")
    if scenario.get("table") != "multiplayer":
        errors.append("commander_scenario.table must be 'multiplayer'")
    if scenario.get("seat") != "first_player":
        errors.append("commander_scenario.seat must be 'first_player'")
    if scenario.get("first_turn_draw") is not True:
        errors.append("commander_scenario.first_turn_draw must be true (draw on turn 1)")
    if scenario.get("opening_hand_size") != 7:
        errors.append("commander_scenario.opening_hand_size must be 7")
    turns = policy.get("turn_semantics", {})
    if turns.get("observation_horizon_turn") != 6:
        errors.append("turn_semantics.observation_horizon_turn must be 6")
    if turns.get("turn_indexing") != "one_based":
        errors.append("turn_semantics.turn_indexing must be 'one_based'")
    check("policy commander scenario and turn semantics match the agreed decisions", errors)

    # ---- policy: mulligan -----------------------------------------------------
    errors = []
    mull = policy.get("mulligan_policy", {})
    if mull.get("policy_name") != "one_free_mulligan_then_london":
        errors.append("mulligan_policy.policy_name must be 'one_free_mulligan_then_london'")
    if mull.get("free_mulligans") != 1:
        errors.append("mulligan_policy.free_mulligans must be 1")
    if mull.get("subsequent_mulligan_rule") != "london":
        errors.append("mulligan_policy.subsequent_mulligan_rule must be 'london'")
    check("policy encodes the one-free-mulligan-then-London workflow", errors)

    # ---- policy: keep rule ----------------------------------------------------
    errors = []
    keep = policy.get("keep_rule", {})
    base = keep.get("base_rule", {})
    land_range = base.get("keep_land_count_range", {})
    if land_range.get("min_keep") != 2 or land_range.get("max_keep") != 5:
        errors.append("keep_rule base land range must be 2 through 5")
    if base.get("zero_land_hands") != "reject":
        errors.append("keep_rule must reject zero-land hands")
    if base.get("six_or_seven_land_hands") != "reject":
        errors.append("keep_rule must reject six-or-seven-land hands")
    one_land = base.get("one_land_exception", {})
    condition = str(one_land.get("condition", "")).casefold()
    if "two mana" not in condition or "turn 2" not in condition:
        errors.append("keep_rule one-land exception must require at least two mana by turn 2")
    not_evaluated = set(keep.get("explicitly_not_evaluated", []))
    for required in ("combo quality", "interaction quality", "generic hand strength", "matchup quality"):
        if required not in not_evaluated:
            errors.append(f"keep_rule must not evaluate {required!r}")
    invariants = keep.get("project_extension_points", {}).get("non_overridable_invariants", [])
    if not any("zero-land" in str(item).casefold() for item in invariants):
        errors.append("keep_rule must record zero-land rejection as a non-overridable invariant")
    check("policy base keep rule and project extension points are correct", errors)

    # ---- policy: bottoming ----------------------------------------------------
    errors = []
    priority = policy.get("bottoming_rule", {}).get("priority_order", [])
    selectors = [entry.get("selector") for entry in priority]
    expected_selectors = [
        "highest_mana_value_nonland",
        "remaining_high_mana_value_nonlands",
        "lands_above_three",
        "stable_normalized_card_identity_tiebreak",
    ]
    if selectors != expected_selectors:
        errors.append(f"bottoming priority order must be {expected_selectors}, found {selectors}")
    ranks = [entry.get("rank") for entry in priority]
    if ranks != [1, 2, 3, 4]:
        errors.append("bottoming priority ranks must be 1..4 in order")
    check("policy deterministic bottoming priority is exact", errors)

    # ---- policy: randomness ---------------------------------------------------
    errors = []
    rng = policy.get("randomness_policy", {})
    if rng.get("rng_id") != "pcg32-v1":
        errors.append("randomness_policy.rng_id must be 'pcg32-v1'")
    if rng.get("seed_type") != "unsigned_64_bit":
        errors.append("randomness_policy.seed_type must be 'unsigned_64_bit'")
    derivation = rng.get("canonical_seed_derivation", {})
    if derivation.get("algorithm_id") != SEED_ALGORITHM_ID:
        errors.append(f"seed derivation algorithm_id must be {SEED_ALGORITHM_ID!r}")
    if derivation.get("inputs_in_order") != ["question_id", "policy_version", "deck_content_fingerprint", "run_role"]:
        errors.append("seed derivation inputs_in_order must be question_id, policy_version, deck_content_fingerprint, run_role")
    if derivation.get("byte_encoding") != "UTF-8":
        errors.append("seed derivation byte_encoding must be UTF-8")
    check("policy randomness identity and seed derivation are versioned and unambiguous", errors)

    # ---- policy: full RNG algorithm specification ----------------------------
    errors = []
    algorithm = rng.get("rng_algorithm", {})
    required_algorithm_fields = [
        "variant", "state_width_bits", "output_width_bits", "multiplier",
        "increment_rule", "stream_selector", "unsigned_overflow_behavior",
        "state_transition", "output_permutation", "state_initialization",
        "bounded_integer_generation", "shuffle_algorithm", "known_answer_test_vector",
    ]
    missing_algorithm = [field for field in required_algorithm_fields if field not in algorithm]
    if missing_algorithm:
        errors.append(f"rng_algorithm is missing required parameters: {missing_algorithm}")
    if algorithm.get("multiplier") != 6364136223846793005:
        errors.append("rng_algorithm.multiplier must be the pcg32 constant 6364136223846793005")
    if algorithm.get("state_width_bits") != 64 or algorithm.get("output_width_bits") != 32:
        errors.append("rng_algorithm must be 64-bit state / 32-bit output")
    vector = algorithm.get("known_answer_test_vector", {})
    for field in ("seed_initstate", "first_5_u32_outputs", "shuffle_input", "shuffle_result"):
        if field not in vector:
            errors.append(f"known_answer_test_vector is missing {field!r}")
    if not isinstance(vector.get("first_5_u32_outputs"), list) or len(vector.get("first_5_u32_outputs", [])) < 1:
        errors.append("known_answer_test_vector must record at least one raw RNG output")
    reproducibility = rng.get("reproducibility", {})
    declares = reproducibility.get("declares_reproducibility") or reproducibility.get("requires_versioned_rng_algorithm")
    if declares and missing_algorithm:
        errors.append("policy declares reproducibility but omits versioned RNG algorithm parameters")
    check("policy freezes a complete, reproducible pcg32-v1 algorithm with a test vector", errors)

    # ---- policy: modeled deck zones exclude the sideboard --------------------
    errors = []
    zones = policy.get("modeled_deck_zones", {})
    if zones.get("included") != ["commander", "main_deck"]:
        errors.append("modeled_deck_zones.included must be commander and main_deck only")
    if "sideboard" not in zones.get("excluded", []):
        errors.append("modeled_deck_zones must exclude the sideboard")
    if zones.get("commander_count") != 1 or zones.get("library_count") != 99:
        errors.append("modeled_deck_zones must record 1 commander and 99 library cards")
    check("policy models only the commander plus the 99-card library and excludes other zones", errors)

    # ---- policy: time-dependent card semantics consumption -------------------
    errors = []
    time_dependent = policy.get("time_dependent_card_semantics", {})
    if time_dependent.get("model") != "controller_turn_window":
        errors.append("time_dependent_card_semantics.model must be 'controller_turn_window'")
    obligations = " ".join(time_dependent.get("engine_obligations", [])).casefold()
    if "never extend availability" not in obligations and "never assumed to be a permanent" not in obligations:
        errors.append("time_dependent_card_semantics must forbid extending availability beyond the window")
    if "permanent land through" not in str(time_dependent.get("horizon_interaction", "")).casefold():
        errors.append("time_dependent_card_semantics must forbid treating a windowed land as permanent through the horizon")
    check("policy defines deterministic consumption of time-dependent card semantics", errors)

    # ---- policy: iteration and uncertainty -----------------------------------
    errors = []
    iters = policy.get("iteration_policy", {})
    if iters.get("minimum_saved_iterations") != 10000:
        errors.append("iteration_policy.minimum_saved_iterations must be 10000")
    if iters.get("canonical_comparative_iterations") != 100000:
        errors.append("iteration_policy.canonical_comparative_iterations must be 100000")
    unc = policy.get("uncertainty_policy", {})
    if unc.get("confidence_presentation") != "wilson_95":
        errors.append("uncertainty_policy.confidence_presentation must be 'wilson_95'")
    if unc.get("confidence_level") != 0.95:
        errors.append("uncertainty_policy.confidence_level must be 0.95")
    for field in ("raw_count", "sample_size", "probability", "confidence_interval", "absolute_delta"):
        if field not in unc.get("required_reported_fields", []):
            errors.append(f"uncertainty_policy must require reported field {field!r}")
    rel = unc.get("relative_delta_rule", {})
    if rel.get("status") != "secondary" or "non-zero" not in str(rel.get("valid_only_when", "")).casefold():
        errors.append("uncertainty_policy relative delta must be secondary and require non-zero baseline")
    check("policy iteration and uncertainty policy match the agreed decisions", errors)

    # ---- policy: fingerprint definition + recomputation ----------------------
    errors = []
    fp_policy = policy.get("deck_fingerprint_policy", {})
    if fp_policy.get("algorithm_id") != FINGERPRINT_ALGORITHM_ID:
        errors.append(f"deck_fingerprint_policy.algorithm_id must be {FINGERPRINT_ALGORITHM_ID!r}")
    if "sideboard" not in fp_policy.get("excluded_from_fingerprint", []):
        errors.append("deck fingerprint must exclude the sideboard")
    serialization = fp_policy.get("canonical_serialization", {})
    if "DeckVersion" not in str(fp_policy.get("excluded_note", "")):
        errors.append("deck fingerprint must exclude the DeckVersion ID from content")
    reference_fps = fp_policy.get("reference_fingerprints", {})
    recomputed = {}
    for version_id in ("v1.0", "v1.1"):
        version_path = VERSIONS_DIR / f"{version_id}.json"
        if not version_path.is_file():
            errors.append(f"DeckVersion {version_id} missing at {version_path.relative_to(REPO_ROOT)}")
            continue
        version_document = load_json(version_path)
        recomputed[version_id] = deck_content_fingerprint(version_document)
        commander_total = sum(zone_counter(version_document, "commander").values())
        library_total = sum(zone_counter(version_document, "main_deck").values())
        if commander_total != 1:
            errors.append(f"{version_id} commander total is {commander_total}, expected 1")
        if library_total != 99:
            errors.append(f"{version_id} library total is {library_total}, expected 99")
        if reference_fps.get(version_id) != recomputed[version_id]:
            errors.append(
                f"policy reference fingerprint for {version_id} does not match recomputation: "
                f"recorded={reference_fps.get(version_id)!r} recomputed={recomputed[version_id]!r}"
            )
    if recomputed.get("v1.0") and recomputed.get("v1.0") == recomputed.get("v1.1"):
        errors.append("v1.0 and v1.1 fingerprints must differ")
    check("deck-content fingerprint recomputes to the recorded reference values", errors)

    # ---- policy: metric catalog + castability --------------------------------
    errors = []
    catalog = {m.get("metric_id"): m for m in policy.get("metric_catalog", {}).get("metrics", [])}
    if "five_color_availability_by_turn" not in catalog:
        errors.append("metric_catalog must define five_color_availability_by_turn")
    castability = policy.get("commander_castability_policy", {})
    if castability.get("is_success_criterion") is not False:
        errors.append("commander castability must not be a success criterion")
    if castability.get("is_primary_five_color_metric") is not False:
        errors.append("commander castability must not be a primary five-color metric")
    cast_metric = catalog.get("commander_castability_by_turn", {})
    if cast_metric.get("kind") != "optional_sanity":
        errors.append("commander_castability_by_turn must be an optional_sanity metric")
    check("policy metric catalog treats commander castability as an optional sanity metric", errors)

    # ---- policy: card-behavior boundary + separation -------------------------
    errors = []
    boundary = policy.get("card_behavior_boundary", {})
    unsupported = boundary.get("unsupported_behavior_handling", {})
    if "never silently contribute" not in str(unsupported.get("hard_invariant", "")).casefold():
        errors.append("policy must state that unsupported behavior never silently contributes to a metric")
    if policy.get("references", {}).get("card_semantics") != "workshop/projects/the-myr-singularity/simulation/card_semantics.json":
        errors.append("policy must reference the card_semantics artifact by path")
    policy_text = json.dumps(policy, ensure_ascii=False)
    for card_name in REQUIRED_OVERRIDE_CARDS:
        if card_name in policy_text:
            errors.append(
                f"policy must not encode fixture-specific card behavior directly; found {card_name!r}"
            )
    check("policy references card semantics and does not own fixture-specific card behavior", errors)

    # ---- policy: evidence + lifecycle boundary -------------------------------
    errors = []
    evidence = policy.get("evidence_language_boundary", {})
    for phrase in ("win rate", "gameplay performance", "generic deck quality"):
        if phrase not in [p.casefold() for p in evidence.get("forbidden_claims", [])]:
            errors.append(f"evidence boundary must forbid {phrase!r}")
    lifecycle = policy.get("lifecycle_boundary", {})
    if lifecycle.get("simulation_creates_deck_version") is not False:
        errors.append("lifecycle boundary must state simulation does not create a DeckVersion")
    if policy.get("explicit_boundary", {}).get("contains_production_result") is not False:
        errors.append("policy explicit_boundary.contains_production_result must be false")
    check("policy evidence-language and lifecycle boundaries are explicit", errors)

    # ---- card semantics: structure and required entries ----------------------
    errors = []
    if semantics.get("artifact_type") != "project_scoped_simulation_card_semantics":
        errors.append("card_semantics artifact_type is wrong")
    if semantics.get("explicit_boundary", {}).get("edits_card_facts") is not False:
        errors.append("card_semantics must declare it does not edit card facts")
    entries = {e.get("card_identity", {}).get("name"): e for e in semantics.get("entries", [])}
    canonical = {c.get("name"): c for c in load_json(CARDS_PATH).get("cards", [])}
    for card_name, expected in REQUIRED_OVERRIDE_CARDS.items():
        entry = entries.get(card_name)
        if not entry:
            errors.append(f"card_semantics is missing required entry for {card_name!r}")
            continue
        modeled = entry.get("modeled_behavior", {})
        for field, value in expected.items():
            if modeled.get(field) != value:
                errors.append(
                    f"{card_name} modeled_behavior.{field} must be {value!r}, found {modeled.get(field)!r}"
                )
        for field in ("scope", "source", "confidence", "validation_status", "limitations",
                      "compensates_for_missing_canonical_produced_mana"):
            if field not in entry:
                errors.append(f"{card_name} entry is missing required field {field!r}")
        if entry.get("validation_status") == "measured":
            errors.append(f"{card_name} entry must not claim a measured validation status")
        # override must compensate for a genuinely missing canonical produced_mana
        canonical_card = canonical.get(card_name)
        if canonical_card is None:
            errors.append(f"{card_name} does not resolve to a canonical Card Fact")
        elif canonical_card.get("produced_mana"):
            errors.append(
                f"{card_name} override is unnecessary: canonical produced_mana is populated"
            )
        elif entry.get("compensates_for_missing_canonical_produced_mana") is not True:
            errors.append(
                f"{card_name} entry must set compensates_for_missing_canonical_produced_mana true"
            )
    check("card semantics supply the required source-aware overrides for missing canonical mana", errors)

    # ---- card semantics: Urza's Saga bounded lifecycle -----------------------
    errors = []
    horizon_turn = policy.get("turn_semantics", {}).get("observation_horizon_turn", 6)
    saga = entries.get("Urza's Saga")
    if not saga:
        errors.append("Urza's Saga entry is required")
    else:
        window = saga.get("time_dependent_availability", {})
        if not window:
            errors.append("Urza's Saga must declare time_dependent_availability")
        if window.get("persists_as_permanent_land") is not False:
            errors.append("Urza's Saga must not persist as a permanent land")
        availability = window.get("availability_window", {})
        end_offset = availability.get("end_offset")
        if not isinstance(end_offset, int) or end_offset >= horizon_turn:
            errors.append("Urza's Saga availability window must end before the observation horizon")
        removal = window.get("removal_event", {})
        if removal.get("effect") != "removed_from_battlefield":
            errors.append("Urza's Saga must be removed from the battlefield after Chapter III")
        if removal.get("trigger") != "chapter_iii_resolves":
            errors.append("Urza's Saga removal must trigger on Chapter III resolution")
        unsupported = set(saga.get("unsupported_behaviors", []))
        for required in ("chapter_iii_artifact_tutor", "construct_token_creation"):
            if required not in unsupported:
                errors.append(f"Urza's Saga must mark {required!r} unsupported")
        if saga.get("modeled_behavior", {}).get("counts_as_five_color_source") is not False:
            errors.append("Urza's Saga must not count as a five-color source")
    check("Urza's Saga is a bounded, time-limited land that cannot persist through the horizon", errors)

    # ---- contracts: structure -------------------------------------------------
    errors = []
    for key in ("question_contract", "run_contract", "result_contract", "comparison_contract"):
        contract = documents[key]
        for field in ("artifact_type", "required_fields", "boundary_rules", "validation_expectations"):
            if field not in contract:
                errors.append(f"{key} is missing {field!r}")
    run_required = documents["run_contract"].get("required_fields", {})
    for field in ("project_id", "deck_version_id", "deck_content_fingerprint", "question_id",
                  "policy_id", "seed", "iteration_count", "limitations"):
        if field not in run_required:
            errors.append(f"run contract must require {field!r} so a run cannot float")
    if documents["run_contract"].get("task_30_state", {}).get("instances_created") != 0:
        errors.append("run contract must record zero instances created in Task 30")
    check("run contract prevents a floating run and creates no instance", errors)

    errors = []
    for key in ("result_contract", "comparison_contract"):
        boundary_rules = " ".join(documents[key].get("boundary_rules", [])).casefold()
        if "reasoning_interpretation" not in boundary_rules:
            errors.append(f"{key} must forbid carrying reasoning interpretation")
        if "product_owner_decision" not in boundary_rules:
            errors.append(f"{key} must forbid carrying a Product Owner decision")
        flags = documents[key].get("required_fields", {}).get("explicit_boundary", {}).get("required_fields", [])
        for flag in ("carries_interpretation", "carries_product_owner_decision", "is_gameplay_claim", "creates_deck_version"):
            if flag not in flags:
                errors.append(f"{key} explicit_boundary must include {flag!r}")
    comparison_rules = " ".join(documents["comparison_contract"].get("boundary_rules", [])).casefold()
    if "differing only in deckversion" not in comparison_rules and "only in deckversion" not in comparison_rules:
        errors.append("comparison contract must require config parity except DeckVersion")
    check("result and comparison contracts separate result from reasoning and decision", errors)

    # ---- taxonomy -------------------------------------------------------------
    errors = []
    category_ids = [c.get("category_id") for c in taxonomy.get("categories", [])]
    if len(category_ids) != len(set(category_ids)):
        errors.append("failure-pattern taxonomy has duplicate category_ids")
    families = {c.get("family") for c in taxonomy.get("categories", [])}
    for required_family in ("hand", "land", "mana", "ramp", "color", "boundary"):
        if required_family not in families:
            errors.append(f"taxonomy must cover the {required_family!r} failure family")
    if "unsupported_card_behavior_limited_run" not in category_ids:
        errors.append("taxonomy must include the unsupported-card-behavior boundary category")
    check("failure-pattern taxonomy covers hand, land, mana, ramp, color, and boundary families", errors)

    # ---- question: documented, not executed ----------------------------------
    errors = require_fields(
        question,
        ["question_id", "policy_id", "policy_version", "hypothesis", "question_text",
         "compared_versions", "target_metrics", "success_interpretation",
         "execution_status", "limitations", "explicit_boundary"],
        "question",
    )
    if question.get("policy_version") != POLICY_VERSION:
        errors.append("question policy_version must match the policy")
    if question.get("execution_status") != "not_executed":
        errors.append("question execution_status must be 'not_executed' in Task 30")
    for forbidden_field in ("metrics", "result", "results", "comparison_result", "raw_count"):
        if forbidden_field in question:
            errors.append(f"question must not carry result field {forbidden_field!r}")
    for version in question.get("compared_versions", []):
        version_id = version.get("deck_version_id")
        if version_id in recomputed and version.get("deck_content_fingerprint") != recomputed[version_id]:
            errors.append(f"question fingerprint for {version_id} does not match recomputation")
    catalog_ids = set(catalog)
    horizon = turns.get("observation_horizon_turn", 6)
    for metric in question.get("target_metrics", []):
        if metric.get("metric_id") not in catalog_ids:
            errors.append(f"question target metric {metric.get('metric_id')!r} is not in the policy catalog")
        if isinstance(metric.get("target_turn"), int) and metric["target_turn"] > horizon:
            errors.append(f"question target metric {metric.get('metric_id')!r} exceeds the horizon")
    flags = question.get("explicit_boundary", {})
    if flags.get("carries_results") is not False or flags.get("authorizes_deck_change") is not False or flags.get("is_gameplay_claim") is not False:
        errors.append("question explicit_boundary flags must all be false")
    check("first evidence question is documented, bound, and not executed", errors)

    # ---- evidence honesty: no forbidden claim in question free text ----------
    errors = []
    for field in ("hypothesis", "question_text"):
        found = find_forbidden(question.get(field, ""))
        if found:
            errors.append(f"question {field} contains forbidden claim(s): {found}")
    interp = question.get("success_interpretation", {})
    for field in ("directional_expectation", "notes"):
        found = find_forbidden(interp.get(field, ""))
        if found:
            errors.append(f"question success_interpretation.{field} contains forbidden claim(s): {found}")
    check("documented question uses honest evidence language", errors)

    # ---- no production run / result / comparison instance exists -------------
    errors = []
    for path in sorted(SIM_DIR.rglob("*.json")):
        try:
            document = load_json(path)
        except json.JSONDecodeError:
            continue
        if document.get("artifact_type") in INSTANCE_ARTIFACT_TYPES:
            errors.append(f"production simulation instance present: {path.relative_to(REPO_ROOT)}")
    check("no production SimulationRun, SimulationResult, or comparison instance exists", errors)

    return report(checks)


if __name__ == "__main__":
    sys.exit(main())
