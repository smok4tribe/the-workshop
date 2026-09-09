"""Frozen deterministic primitives shared by future simulation engines and validators."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement
from types import MappingProxyType

from workshop.shared.identity import artifact_content_fingerprint, load_strict_json_bytes


MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1
PCG_MULTIPLIER = 6364136223846793005
PCG_STREAM_SELECTOR = 11400714819323198485


def _seed_from_payload(payload: str) -> int:
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big", signed=False)


def derive_run_seed(question_content_fingerprint, policy_content_fingerprint, deck_content_fingerprint, run_role):
    return _seed_from_payload("\x1f".join((question_content_fingerprint, policy_content_fingerprint, deck_content_fingerprint, run_role)))


def derive_iteration_seed(run_seed: int, iteration_index: int) -> int:
    if not isinstance(run_seed, int) or isinstance(run_seed, bool) or not 0 <= run_seed < 2 ** 64:
        raise ValueError("run_seed must be an unsigned 64-bit integer")
    if not isinstance(iteration_index, int) or isinstance(iteration_index, bool) or iteration_index < 1:
        raise ValueError("iteration_index must be one-based positive integer")
    return _seed_from_payload(f"sim-iteration-seed-sha256-v1\x1f{run_seed}\x1f{iteration_index}")


class PCG32:
    """The frozen pcg32-v1 implementation."""
    def __init__(self, initstate: int, initseq: int = PCG_STREAM_SELECTOR):
        self.state = 0
        self.inc = ((initseq << 1) | 1) & MASK64
        self._step()
        self.state = (self.state + (initstate & MASK64)) & MASK64
        self._step()

    def _step(self):
        self.state = (self.state * PCG_MULTIPLIER + self.inc) & MASK64

    def next_u32(self):
        old = self.state
        self._step()
        xorshifted = (((old >> 18) ^ old) >> 27) & MASK32
        rotation = (old >> 59) & 31
        return ((xorshifted >> rotation) | (xorshifted << ((-rotation) & 31))) & MASK32

    def bounded(self, bound: int):
        if not isinstance(bound, int) or not 1 <= bound <= 2 ** 32:
            raise ValueError("bound must be in 1..2^32")
        threshold = (2 ** 32 - bound) % bound
        while True:
            value = self.next_u32()
            if value >= threshold:
                return value % bound

    def shuffle(self, values):
        result = list(values)
        for index in range(len(result) - 1, 0, -1):
            swap_index = self.bounded(index + 1)
            result[index], result[swap_index] = result[swap_index], result[index]
        return result


def select_bottom_tokens(hand, *, mana_value, is_land):
    """Return deterministic-bottoming-v2 selection order for immutable card tokens."""
    required = hand.get("bottom_count", 0)
    cards = list(hand.get("cards", []))
    selected = []
    def token_key(token):
        match = re.fullmatch(r"(.+)#([1-9][0-9]*)", token)
        if match is None:
            raise ValueError(f"invalid deterministic token {token!r}")
        return match.group(1).lower(), int(match.group(2))
    nonlands = sorted(
        (token for token in cards if not is_land(token)),
        key=lambda token: (-mana_value(token), token_key(token)),
    )
    for token in nonlands:
        if len(selected) == required:
            return selected
        selected.append(token)
    remaining_lands = sorted((token for token in cards if is_land(token)), key=token_key)
    while len(selected) < required and len(remaining_lands) > 3:
        selected.append(remaining_lands.pop(0))
    while len(selected) < required and remaining_lands:
        selected.append(remaining_lands.pop(0))
    if len(selected) != required:
        raise ValueError("bottoming cannot select the required number of cards")
    return selected


def select_land(candidates, current_colors, horizon_turn, current_turn):
    """Select one land with the frozen Level 2 policy priority."""
    def key(item):
        colors = set(item.get("colors", []))
        new_colors = len(colors - set(current_colors))
        remaining = item.get("remaining_availability", horizon_turn - current_turn + 1)
        return (
            -new_colors,
            -int(bool(item.get("five_color_source"))),
            -int(bool(item.get("permanent", True))),
            -remaining,
            -item.get("mana_units", 1),
            item["oracle_id"].lower(),
            item.get("ordinal", 1),
        )
    return min(candidates, key=key) if candidates else None


def select_payable_ramp(candidates):
    """Select the highest-priority currently payable registered ramp source."""
    payable = [item for item in candidates if item.get("payable")]
    def key(item):
        return (
            -int(bool(item.get("same_turn_online_noncreature"))),
            -item.get("output_units", 1),
            -item.get("color_flexibility", 0),
            item.get("mana_value", 0),
            item["oracle_id"].lower(),
            item.get("ordinal", 1),
        )
    return min(payable, key=key) if payable else None


_PAYMENT_MANA_SYMBOL_ORDER = ("W", "U", "B", "R", "G", "C")
_PAYMENT_ALLOCATION_EFFECT_FIELD_ORDER = (
    "floating_mana_after",
    "tapped_source_instance_ids",
    "activated_sources",
    "consumed_mana",
    "external_payment_requirements",
    "life_payment",
)
_PAYMENT_ACTIVATED_SOURCE_FIELD_ORDER = (
    "instance_id",
    "oracle_id",
    "ordinal",
    "profile_id",
    "produced_symbols",
)


def _unicode_codepoint_key(value):
    return tuple(ord(character) for character in value)


def _canonical_payment_json(value):
    """Return exact JSON-compatible data with canonical object/list ordering."""
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueError("payment allocation projection keys must be strings")
        return {
            key: _canonical_payment_json(value[key])
            for key in sorted(value, key=_unicode_codepoint_key)
        }
    if type(value) in {list, tuple}:
        values = [_canonical_payment_json(item) for item in value]
        return sorted(values, key=_canonical_payment_json_text)
    if value is None or type(value) in {str, int, float, bool}:
        return value
    raise ValueError("payment allocation projection must contain exact JSON values")


def _canonical_payment_json_text(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _canonical_mana_symbol_map(value):
    if value is None:
        value = {}
    if not isinstance(value, Mapping) or set(value) - set(_PAYMENT_MANA_SYMBOL_ORDER):
        raise ValueError("payment allocation mana quantities must use the registered symbol domain")
    if any(type(quantity) is not int or quantity < 0 for quantity in value.values()):
        raise ValueError("payment allocation mana quantities must be non-negative integers")
    return {symbol: value.get(symbol, 0) for symbol in _PAYMENT_MANA_SYMBOL_ORDER}


def _canonical_produced_symbol_sequence(value):
    """Canonicalize Task 32H's selected-output symbol sequence without changing quantity."""
    if type(value) not in {list, tuple} or any(symbol not in _PAYMENT_MANA_SYMBOL_ORDER for symbol in value):
        raise ValueError("payment allocation produced_symbols must be a registered symbol sequence")
    rank = {symbol: index for index, symbol in enumerate(_PAYMENT_MANA_SYMBOL_ORDER)}
    return sorted(value, key=rank.__getitem__)


def _payment_allocation_effect_projection(item):
    """Project only registered, result-relevant allocation effects for a complete tie."""
    if not isinstance(item, Mapping):
        raise ValueError("payment allocation must be a Mapping")
    activated = item.get("activated_sources", [])
    if type(activated) not in {list, tuple}:
        raise ValueError("payment allocation activated_sources must be an array")
    canonical_activated = []
    for source in activated:
        if not isinstance(source, Mapping):
            raise ValueError("payment allocation activated_sources must contain objects")
        if type(source.get("instance_id")) is not str:
            raise ValueError("payment allocation activated_sources require physical identities")
        source_values = {
            "instance_id": source.get("instance_id"),
            "oracle_id": source.get("oracle_id"),
            "ordinal": source.get("ordinal"),
            "profile_id": source.get("profile_id"),
            "produced_symbols": _canonical_produced_symbol_sequence(source.get("produced_symbols")),
        }
        canonical_activated.append({
            field: source_values[field] for field in _PAYMENT_ACTIVATED_SOURCE_FIELD_ORDER
        })
    canonical_activated.sort(key=lambda source: _unicode_codepoint_key(source["instance_id"]))
    tapped = item.get("tapped_source_instance_ids", [])
    if type(tapped) not in {list, tuple} or any(type(instance_id) is not str for instance_id in tapped):
        raise ValueError("payment allocation tapped_source_instance_ids must be an array of physical identities")
    projection_values = {
        "floating_mana_after": _canonical_mana_symbol_map(item.get("floating_mana_after")),
        "tapped_source_instance_ids": sorted(tapped, key=_unicode_codepoint_key),
        "activated_sources": canonical_activated,
        "consumed_mana": _canonical_mana_symbol_map(item.get("consumed_mana")),
        "external_payment_requirements": _canonical_payment_json(item.get("external_payment_requirements", [])),
        "life_payment": _canonical_payment_json(item.get("life_payment", [])),
    }
    return {field: projection_values[field] for field in _PAYMENT_ALLOCATION_EFFECT_FIELD_ORDER}


def _payment_allocation_priority_key(item):
    """Return the one frozen ordering used for selection and equivalence."""
    ordered = tuple(sorted(
        ((oracle.lower(), ordinal, symbol) for oracle, ordinal, symbol in item["source_outputs"]),
    ))
    complete_tie = _canonical_payment_json_text(_payment_allocation_effect_projection(item))
    return item["flexible_generic_spend"], item["tapped_source_count"], ordered, complete_tie


def choose_payment(allocations):
    """Choose a legal allocation using the frozen payment tie-break.

    Each allocation contains flexible_generic_spend, tapped_source_count, and
    source_outputs as (oracle_id, ordinal, output-symbol) tuples.
    """
    if not allocations:
        return None
    return min(allocations, key=_payment_allocation_priority_key)


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


APPROVED_RUNTIME_MANA_SOURCE_SEMANTICS_FINGERPRINT = "artifact-content-sha256-v1:27b32917646e812031a1632a8f4cc476981240493944d2d89bc54e9ed3400c42"
APPROVED_RUNTIME_CARD_FACTS_FINGERPRINT = "artifact-content-sha256-v1:96f5c19764c889f4be8a36d3eaaa12dacc1f145c53260048511bec23df00e6c5"
APPROVED_RUNTIME_ARTIFACT_IDENTITY_PROJECTION_FINGERPRINT = "artifact-content-sha256-v1:651cf8d3ee36fd45672bae4bd93f0e049b4f66687902e9f40347a99689459290"
_RUNTIME_CONTEXT_CONSTRUCTION_TOKEN = object()


def _freeze_json(value):
    """Deep-freeze canonical JSON into fresh execution-only containers."""
    if type(value) is dict:
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    if value is None or type(value) in {str, int, float, bool}:
        return value
    raise ValueError("runtime semantic registry must contain only JSON values")


def _canonical_json_bytes(value):
    """Serialize one JSON value using artifact-content-sha256-v1 semantics."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("runtime semantic registry must be canonical JSON") from error


@dataclass(frozen=True, slots=True, init=False)
class SimulationRuntimeContext:
    """Sealed canonical executable semantics for runtime helpers."""

    _registry_canonical_bytes: bytes
    _card_facts_canonical_bytes: bytes
    registry_identity: tuple[str, str, str, str, str]
    registry_content_fingerprint: str
    card_facts_content_fingerprint: str
    canonical_land_oracle_ids: frozenset[str]
    canonical_artifact_oracle_ids: frozenset[str]
    canonical_commander_colors: frozenset[str]
    _construction_token: object

    def __init__(self, *args, **kwargs):
        raise TypeError("SimulationRuntimeContext instances are created only by validated canonical construction")

    @classmethod
    def _from_validated_registry(cls, registry, card_facts):
        if type(registry) is not dict:
            raise ValueError("validated runtime semantic registry must be an exact object")
        if type(card_facts) is not list:
            raise ValueError("validated canonical Card Facts must be an exact array")
        canonical_bytes = _canonical_json_bytes(registry)
        canonical_registry = load_strict_json_bytes(canonical_bytes)
        if type(canonical_registry) is not dict or type(canonical_registry.get("records")) is not list:
            raise ValueError("validated runtime semantic registry has no canonical records")
        records = canonical_registry["records"]
        if any(type(record) is not dict or type(record.get("oracle_id")) is not str or not record["oracle_id"] for record in records):
            raise ValueError("validated runtime semantic registry has invalid record identities")
        if len({record["oracle_id"] for record in records}) != len(records):
            raise ValueError("validated runtime semantic registry has duplicate record identities")
        card_facts_bytes = _canonical_json_bytes(card_facts)
        canonical_cards = load_strict_json_bytes(card_facts_bytes)
        if type(canonical_cards) is not list or any(
            type(card) is not dict or type(card.get("oracle_id")) is not str or not card["oracle_id"]
            or type(card.get("type_line")) is not str
            for card in canonical_cards
        ):
            raise ValueError("validated canonical Card Facts have invalid identities or types")
        if len({card["oracle_id"] for card in canonical_cards}) != len(canonical_cards):
            raise ValueError("validated canonical Card Facts have duplicate identities")
        card_by_oracle_id = {card["oracle_id"]: card for card in canonical_cards}
        if not {record["oracle_id"] for record in records} <= set(card_by_oracle_id):
            raise ValueError("validated canonical Card Facts do not cover executable source identities")
        if artifact_content_fingerprint(canonical_cards) != APPROVED_RUNTIME_CARD_FACTS_FINGERPRINT:
            raise ValueError("validated canonical Card Facts do not match the Policy-approved authority")
        instance = object.__new__(cls)
        object.__setattr__(instance, "registry_identity", tuple(
            canonical_registry[field] for field in ("schema_version", "artifact_type", "artifact_id", "project_id", "policy_version")
        ))
        object.__setattr__(instance, "_registry_canonical_bytes", canonical_bytes)
        object.__setattr__(instance, "_card_facts_canonical_bytes", card_facts_bytes)
        object.__setattr__(instance, "registry_content_fingerprint", artifact_content_fingerprint(canonical_registry))
        object.__setattr__(instance, "card_facts_content_fingerprint", artifact_content_fingerprint(canonical_cards))
        object.__setattr__(instance, "canonical_land_oracle_ids", frozenset(
            record["oracle_id"] for record in records if record.get("source_kind") == "land"
        ))
        object.__setattr__(instance, "canonical_artifact_oracle_ids", frozenset(
            card["oracle_id"] for card in canonical_cards if "Artifact" in card["type_line"].split(" — ", 1)[0].split()
        ))
        if artifact_content_fingerprint({"artifact_oracle_ids": sorted(instance.canonical_artifact_oracle_ids)}) != APPROVED_RUNTIME_ARTIFACT_IDENTITY_PROJECTION_FINGERPRINT:
            raise ValueError("validated Card Facts artifact identity projection does not match the approved authority")
        commander_colors = {
            color
            for record in records
            for group in (record.get("activation_groups") or ())
            for profile in (group.get("profiles") or ())
            for condition in (profile.get("conditions") or ())
            if condition.get("condition_id") == "commander_color_identity"
            for color in (condition.get("params") or {}).get("colors", ())
        }
        object.__setattr__(instance, "canonical_commander_colors", frozenset(commander_colors))
        object.__setattr__(instance, "_construction_token", _RUNTIME_CONTEXT_CONSTRUCTION_TOKEN)
        return instance


_RUNTIME_SNAPSHOT_CONSTRUCTION_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class AuthenticatedRuntimeSnapshot:
    """Fresh, operation-local executable semantics derived from canonical bytes."""

    _frozen_registry: Mapping
    _records_by_oracle_id: Mapping
    canonical_land_oracle_ids: frozenset[str]
    canonical_artifact_oracle_ids: frozenset[str]
    canonical_commander_colors: frozenset[str]
    registry_content_fingerprint: str
    _construction_token: object

    def __init__(self, *args, **kwargs):
        raise TypeError("AuthenticatedRuntimeSnapshot instances are created only during authentication")


def _require_authenticated_runtime_snapshot(snapshot):
    if type(snapshot) is not AuthenticatedRuntimeSnapshot:
        raise ValueError("runtime execution requires an authenticated runtime snapshot")
    if snapshot._construction_token is not _RUNTIME_SNAPSHOT_CONSTRUCTION_TOKEN:
        raise ValueError("runtime snapshot construction is not authenticated")
    return snapshot


def _authenticate_runtime_context(runtime_context):
    """Reconstruct one fresh authenticated snapshot for a runtime operation."""
    if type(runtime_context) is not SimulationRuntimeContext:
        raise ValueError("runtime execution requires a trusted SimulationRuntimeContext")
    if runtime_context._construction_token is not _RUNTIME_CONTEXT_CONSTRUCTION_TOKEN:
        raise ValueError("runtime semantic context construction is not authenticated")
    canonical_bytes = runtime_context._registry_canonical_bytes
    if type(canonical_bytes) is not bytes:
        raise ValueError("runtime semantic context canonical registry must be exact bytes")
    identity_metadata = runtime_context.registry_identity
    fingerprint_metadata = runtime_context.registry_content_fingerprint
    land_metadata = runtime_context.canonical_land_oracle_ids
    card_facts_bytes = runtime_context._card_facts_canonical_bytes
    card_facts_fingerprint_metadata = runtime_context.card_facts_content_fingerprint
    artifact_metadata = runtime_context.canonical_artifact_oracle_ids
    color_metadata = runtime_context.canonical_commander_colors
    if (
        type(identity_metadata) is not tuple
        or len(identity_metadata) != 5
        or any(type(value) is not str for value in identity_metadata)
        or type(fingerprint_metadata) is not str
        or type(land_metadata) is not frozenset
        or any(type(value) is not str for value in land_metadata)
        or type(color_metadata) is not frozenset
        or any(type(value) is not str for value in color_metadata)
        or type(card_facts_bytes) is not bytes
        or type(card_facts_fingerprint_metadata) is not str
        or type(artifact_metadata) is not frozenset
        or any(type(value) is not str for value in artifact_metadata)
    ):
        raise ValueError("runtime semantic context metadata has invalid types")
    try:
        registry = load_strict_json_bytes(canonical_bytes)
    except ValueError as error:
        raise ValueError("runtime semantic context canonical registry bytes are invalid") from error
    if type(registry) is not dict or _canonical_json_bytes(registry) != canonical_bytes:
        raise ValueError("runtime semantic context registry bytes are not canonical")
    fingerprint = artifact_content_fingerprint(registry)
    identity = tuple(registry.get(field) for field in ("schema_version", "artifact_type", "artifact_id", "project_id", "policy_version"))
    records = registry.get("records")
    if type(records) is not list or any(
        type(record) is not dict or type(record.get("oracle_id")) is not str or not record["oracle_id"]
        for record in records
    ) or len({record["oracle_id"] for record in records}) != len(records):
        raise ValueError("runtime semantic context registry records are invalid")
    if (
        fingerprint != APPROVED_RUNTIME_MANA_SOURCE_SEMANTICS_FINGERPRINT
        or fingerprint_metadata != fingerprint
        or identity_metadata != identity
    ):
        raise ValueError("runtime semantic context does not authenticate the approved executable registry")
    expected_lands = frozenset(record["oracle_id"] for record in records if record.get("source_kind") == "land")
    expected_commander_colors = frozenset(
        color
        for record in records
        for group in (record.get("activation_groups") or ())
        for profile in (group.get("profiles") or ())
        for condition in (profile.get("conditions") or ())
        if condition.get("condition_id") == "commander_color_identity"
        for color in (condition.get("params") or {}).get("colors", ())
    )
    if land_metadata != expected_lands or color_metadata != expected_commander_colors:
        raise ValueError("runtime semantic context identity domains do not derive from the approved registry")
    if (
        card_facts_fingerprint_metadata != APPROVED_RUNTIME_CARD_FACTS_FINGERPRINT
        or artifact_content_fingerprint({"artifact_oracle_ids": sorted(artifact_metadata)}) != APPROVED_RUNTIME_ARTIFACT_IDENTITY_PROJECTION_FINGERPRINT
    ):
        raise ValueError("runtime semantic context Card Facts identity domains are not authenticated")
    frozen_registry = _freeze_json(registry)
    frozen_records = frozen_registry.get("records")
    if type(frozen_records) is not tuple:
        raise ValueError("runtime semantic context authenticated records are not frozen")
    snapshot = object.__new__(AuthenticatedRuntimeSnapshot)
    object.__setattr__(snapshot, "_frozen_registry", frozen_registry)
    object.__setattr__(snapshot, "_records_by_oracle_id", MappingProxyType({
        record["oracle_id"]: record for record in frozen_records
    }))
    object.__setattr__(snapshot, "canonical_land_oracle_ids", expected_lands)
    object.__setattr__(snapshot, "canonical_artifact_oracle_ids", artifact_metadata)
    object.__setattr__(snapshot, "canonical_commander_colors", expected_commander_colors)
    object.__setattr__(snapshot, "registry_content_fingerprint", fingerprint)
    object.__setattr__(snapshot, "_construction_token", _RUNTIME_SNAPSHOT_CONSTRUCTION_TOKEN)
    return snapshot


def _resolve_runtime_record(authenticated_snapshot, oracle_id, *, required_source_kind=None):
    snapshot = _require_authenticated_runtime_snapshot(authenticated_snapshot)
    if type(oracle_id) is not str or not oracle_id:
        raise ValueError("runtime executable resolution requires a non-empty oracle_id")
    try:
        record = snapshot._records_by_oracle_id[oracle_id]
    except KeyError as error:
        raise ValueError("runtime executable resolution requires a canonical registered source oracle_id")
    if required_source_kind is not None and record.get("source_kind") not in required_source_kind:
        raise ValueError("runtime executable resolution source_kind is not permitted at this boundary")
    return record


_CONDITION_STATE_KEYS = {
    "generic_payment_available_from_other_sources": frozenset({"generic_payment_available_from_other_sources"}),
    "bounded_controller_turn_window": frozenset({"controller_turn_offset"}),
    "artifact_controlled": frozenset({"artifact_controlled_count"}),
    "complete_tron_set_controlled": frozenset({"controlled_land_oracle_ids", "candidate_land_oracle_id"}),
    "commander_color_identity": frozenset({"commander_colors"}),
}
_IDENTITY_STATE_KEYS = frozenset({"controlled_land_oracle_ids", "candidate_land_oracle_id", "commander_colors"})


def _condition_state_keys(condition):
    if not isinstance(condition, Mapping):
        return frozenset()
    return _CONDITION_STATE_KEYS.get(condition.get("condition_id"), frozenset())


def _conditions_state_keys(conditions):
    return frozenset(
        key
        for condition in conditions
        for key in _condition_state_keys(condition)
    )


def _condition_state_for_conditions(state, conditions):
    """Project already-validated broad state to registered condition-owned keys."""
    allowed = _conditions_state_keys(conditions)
    return {key: state[key] for key in allowed if key in state}


def _validate_condition_state(state, *, allowed_keys, runtime_snapshot=None, label="condition state"):
    """Validate one exact, closed runtime-state mapping without coercion."""
    if type(state) is not dict:
        raise ValueError(f"{label} must be an exact object")
    if "complete_tron_set_controlled" in state:
        raise ValueError(f"{label} complete_tron_set_controlled is forbidden")
    extras = sorted(set(state) - set(allowed_keys))
    if extras:
        raise ValueError(f"{label} has unregistered keys: {', '.join(extras)}")
    if set(state) & _IDENTITY_STATE_KEYS and type(runtime_snapshot) is not AuthenticatedRuntimeSnapshot:
        raise ValueError(f"{label} requires trusted runtime state authority")
    if set(state) & _IDENTITY_STATE_KEYS:
        _require_authenticated_runtime_snapshot(runtime_snapshot)

    for key in ("generic_payment_available_from_other_sources", "controller_turn_offset", "artifact_controlled_count"):
        if key in state and (type(state[key]) is not int or state[key] < 0):
            raise ValueError(f"{label} {key} must be a non-negative integer")

    if "controlled_land_oracle_ids" in state:
        controlled = state["controlled_land_oracle_ids"]
        if type(controlled) is not list:
            raise ValueError(f"{label} controlled_land_oracle_ids must be an array")
        if any(type(oracle_id) is not str or not oracle_id for oracle_id in controlled):
            raise ValueError(f"{label} controlled_land_oracle_ids must contain non-empty strings")
        if any(oracle_id not in runtime_snapshot.canonical_land_oracle_ids for oracle_id in controlled):
            raise ValueError(f"{label} controlled_land_oracle_ids must contain only canonical registered-land identities")

    if "candidate_land_oracle_id" in state:
        candidate = state["candidate_land_oracle_id"]
        if type(candidate) is not str or not candidate:
            raise ValueError(f"{label} candidate_land_oracle_id must be a non-empty string")
        if candidate not in runtime_snapshot.canonical_land_oracle_ids:
            raise ValueError(f"{label} candidate_land_oracle_id must be a canonical registered-land identity")

    if "commander_colors" in state:
        colors = state["commander_colors"]
        if type(colors) is not list:
            raise ValueError(f"{label} commander_colors must be an array")
        if any(type(color) is not str or color not in {"W", "U", "B", "R", "G"} for color in colors):
            raise ValueError(f"{label} commander_colors must contain only registered colors")
        if len(colors) != len(set(colors)):
            raise ValueError(f"{label} commander_colors must not contain duplicates")
        if set(colors) != set(runtime_snapshot.canonical_commander_colors):
            raise ValueError(f"{label} commander_colors must equal the canonical Commander identity")
    return state


def _condition_is_satisfied(condition, state, *, runtime_snapshot=None):
    """Resolve one registered mana-source condition against observation state."""
    allowed_keys = _condition_state_keys(condition)
    _validate_condition_state(
        state,
        allowed_keys=allowed_keys,
        runtime_snapshot=runtime_snapshot,
        label="condition state",
    )
    if not isinstance(condition, Mapping):
        return False
    condition_id, params = condition.get("condition_id"), condition.get("params") or {}
    if condition_id == "generic_payment_available_from_other_sources":
        available = state.get("generic_payment_available_from_other_sources", 0)
        return _is_integer(available) and available >= params.get("required_units")
    if condition_id == "bounded_controller_turn_window":
        offset = state.get("controller_turn_offset")
        return _is_integer(offset) and params.get("start_offset") <= offset <= params.get("end_offset")
    if condition_id == "artifact_controlled":
        count = state.get("artifact_controlled_count", 0)
        return _is_integer(count) and count >= params.get("minimum_count")
    if condition_id == "complete_tron_set_controlled":
        controlled = set(state.get("controlled_land_oracle_ids", []))
        candidate = {state["candidate_land_oracle_id"]} if "candidate_land_oracle_id" in state else set()
        return set(params.get("oracle_ids", [])) <= controlled | candidate
    if condition_id == "commander_color_identity":
        colors = state.get("commander_colors")
        return isinstance(colors, list) and set(colors) == set(params.get("colors", []))
    return False


def _resolve_activation_profiles(group, condition_truth, *, runtime_snapshot=None):
    """Resolve registered activation profiles using structured predicates only."""
    profiles = group.get("profiles") if isinstance(group, Mapping) else None
    if not isinstance(profiles, (list, tuple)):
        return [], ["activation group profiles must be an array"]
    conditions = [
        condition
        for profile in profiles if isinstance(profile, Mapping)
        for condition in (profile.get("conditions") or [])
    ]
    try:
        _validate_condition_state(
            condition_truth,
            allowed_keys=_conditions_state_keys(conditions),
            runtime_snapshot=runtime_snapshot,
            label="activation condition state",
        )
    except ValueError as error:
        return [], [str(error)]
    legal = []
    for profile in profiles:
        if not isinstance(profile, Mapping) or not profile.get("supported"):
            continue
        if all(
            _condition_is_satisfied(
                condition,
                _condition_state_for_conditions(condition_truth, [condition]),
                runtime_snapshot=runtime_snapshot,
            )
            for condition in profile.get("conditions", [])
        ):
            legal.append(profile)
    if group.get("selection") == "independent_modes":
        return legal, []
    if not legal:
        return [], ["highest-priority activation group has no matching supported profile"]
    highest = max(profile.get("priority") for profile in legal)
    selected = [profile for profile in legal if profile.get("priority") == highest]
    if len(selected) != 1:
        return [], ["highest-priority activation group has tied matching profiles"]
    return selected, []


def _evaluate_end_step_state_transitions(authenticated_snapshot, record, post_development_state):
    """Resolve registered end-step removals from one authenticated snapshot."""
    snapshot = _require_authenticated_runtime_snapshot(authenticated_snapshot)
    transitions = record.get("state_transitions") or []
    removal_transitions = [
        transition for transition in transitions
        if isinstance(transition, Mapping) and transition.get("event_id") == "end_step_remove_unless_condition"
    ]
    conditions = [transition.get("condition") for transition in removal_transitions]
    try:
        _validate_condition_state(
            post_development_state,
            allowed_keys=_conditions_state_keys(conditions),
            runtime_snapshot=snapshot,
            label="end-step condition state",
        )
    except ValueError as error:
        return None, [str(error)]
    remains = all(
        _condition_is_satisfied(
            transition.get("condition"),
            _condition_state_for_conditions(post_development_state, [transition.get("condition")]),
            runtime_snapshot=snapshot,
        )
        for transition in removal_transitions
    )
    return {"remains_available": remains, "removed": not remains}, []


def evaluate_end_step_state_transitions(*, runtime_context, oracle_id, post_development_state):
    """Resolve registered end-step removals after deterministic development."""
    try:
        snapshot = _authenticate_runtime_context(runtime_context)
        record = _resolve_runtime_record(snapshot, oracle_id)
    except ValueError as error:
        return None, [str(error)]
    return _evaluate_end_step_state_transitions(snapshot, record, post_development_state)


def _source_state(source, shared_state):
    state = shared_state.copy()
    state.update(source.get("condition_state", {}))
    return state


def _has_generic_payment_condition(profile):
    return any(
        isinstance(condition, Mapping)
        and condition.get("condition_id") == "generic_payment_available_from_other_sources"
        for condition in (profile.get("conditions") or [])
    )


def _resolved_profiles(record, state, *, exclude_generic_payment, runtime_snapshot=None):
    profiles = []
    for group in record.get("activation_groups") or []:
        conditions = [
            condition
            for profile in (group.get("profiles") or []) if isinstance(profile, Mapping)
            for condition in (profile.get("conditions") or [])
        ]
        selected, errors = _resolve_activation_profiles(
            group,
            _condition_state_for_conditions(state, conditions),
            runtime_snapshot=runtime_snapshot,
        )
        if errors == ["highest-priority activation group has no matching supported profile"]:
            continue
        if errors:
            return [], errors
        profiles.extend(
            profile for profile in selected
            if not exclude_generic_payment or not _has_generic_payment_condition(profile)
        )
    return profiles, []


def _expired_bounded_source(record, state, *, runtime_snapshot=None):
    supported = [
        profile
        for group in record.get("activation_groups") or []
        for profile in (group.get("profiles") or [])
        if isinstance(profile, Mapping) and profile.get("supported")
    ]
    if not supported or not all(any(
        isinstance(condition, Mapping) and condition.get("condition_id") == "bounded_controller_turn_window"
        for condition in (profile.get("conditions") or [])
    ) for profile in supported):
        return False
    # A bounded profile with a registered removal event remains usable during
    # the final development window, then is absent from the EOT observation.
    offset = state.get("controller_turn_offset")
    if _is_integer(offset) and all(any(
        isinstance(condition, Mapping)
        and condition.get("condition_id") == "bounded_controller_turn_window"
        and condition.get("params", {}).get("removal_event")
        and offset >= condition.get("params", {}).get("end_offset")
        for condition in (profile.get("conditions") or [])
    ) for profile in supported):
        return True
    return not any(
        all(
            _condition_is_satisfied(
                condition,
                _condition_state_for_conditions(state, [condition]),
                runtime_snapshot=runtime_snapshot,
            )
            for condition in profile.get("conditions", [])
        )
        for profile in supported
    )


def observe_source_capability(*, runtime_context, source_states, candidate_source_id, condition_state=None):
    """Evaluate source-capability-observation-v1 without reconstructing Policy prose.

    ``source_states`` contains the actual post-development sources. Each entry
    needs a unique ``source_id``, registered ``oracle_id``, ``online`` and
    ``tapped`` booleans, and may provide per-source ``condition_state``.
    Earlier tapping is intentionally ignored for gross source capability, but
    retained for residual spendable-mana checks.
    """
    snapshot = _authenticate_runtime_context(runtime_context)
    if type(source_states) is not list or type(candidate_source_id) is not str or not candidate_source_id:
        raise ValueError("source capability observation requires source states and candidate_source_id")
    shared_state = {} if condition_state is None else condition_state
    _validate_condition_state(
        shared_state,
        allowed_keys={"commander_colors", "artifact_controlled_count", "controlled_land_oracle_ids"},
        runtime_snapshot=snapshot,
        label="source capability shared condition state",
    )
    seen_ids, surviving, candidate_state = set(), [], None
    for source in source_states:
        if type(source) is not dict:
            raise ValueError("source capability observation source states must be objects")
        required_source_keys = {"source_id", "oracle_id", "online", "tapped"}
        allowed_source_keys = required_source_keys | {"removed", "condition_state"}
        if set(source) - allowed_source_keys:
            raise ValueError("source capability observation source states have unregistered fields")
        if not required_source_keys <= set(source):
            raise ValueError("source capability observation source states are missing required fields")
        source_id, oracle_id = source.get("source_id"), source.get("oracle_id")
        if type(source_id) is not str or not source_id or source_id in seen_ids:
            raise ValueError("source capability observation source_id values must be unique non-empty strings")
        seen_ids.add(source_id)
        try:
            record = _resolve_runtime_record(snapshot, oracle_id)
        except ValueError as error:
            raise ValueError(f"source capability observation {error}") from error
        if type(source.get("online")) is not bool or type(source.get("tapped")) is not bool:
            raise ValueError("source capability observation requires explicit online and tapped state")
        if "removed" in source and type(source["removed"]) is not bool:
            raise ValueError("source capability observation removed state must be a boolean")
        per_source_state = source.get("condition_state", {})
        _validate_condition_state(
            per_source_state,
            allowed_keys={"controller_turn_offset"},
            runtime_snapshot=snapshot,
            label="source capability per-source condition state",
        )
        local_state = _source_state({**source, "condition_state": per_source_state}, shared_state)
        if source_id == candidate_source_id:
            candidate_state = (source, record, local_state)
        if source.get("online") is not True or source.get("removed", False):
            continue
        transition_conditions = [
            transition.get("condition")
            for transition in (record.get("state_transitions") or [])
            if isinstance(transition, Mapping) and transition.get("event_id") == "end_step_remove_unless_condition"
        ]
        transition, errors = _evaluate_end_step_state_transitions(
            snapshot,
            record,
            post_development_state=_condition_state_for_conditions(local_state, transition_conditions),
        )
        if errors:
            raise ValueError(errors[0])
        if transition["removed"]:
            continue
        if _expired_bounded_source(record, local_state, runtime_snapshot=snapshot):
            continue
        surviving.append((source, record, local_state))
    if candidate_state is None:
        raise ValueError("source capability observation candidate_source_id must identify one supplied source")

    def base_capacity(item):
        _, record, local_state = item
        profiles, errors = _resolved_profiles(
            record,
            local_state,
            exclude_generic_payment=True,
            runtime_snapshot=snapshot,
        )
        if errors:
            raise ValueError(errors[0])
        return max((profile.get("mana_units", 0) for profile in profiles), default=0)

    external = [item for item in surviving if item[0]["source_id"] != candidate_source_id]
    external_base_capacity = sum(base_capacity(item) for item in external)
    residual_external_capacity = sum(base_capacity(item) for item in external if item[0]["tapped"] is False)
    candidates = [item for item in surviving if item[0]["source_id"] == candidate_source_id]
    if not candidates:
        return {
            "survives": False,
            "online": False,
            "source_capability": [],
            "five_color_available": False,
            "external_base_capacity": external_base_capacity,
            "residual_external_payment_capacity": residual_external_capacity,
            "candidate_spendable_output_capabilities": [],
        }
    candidate = candidates[0]

    candidate_state = candidate[2].copy()
    candidate_state["generic_payment_available_from_other_sources"] = external_base_capacity
    capability_profiles, errors = _resolved_profiles(
        candidate[1],
        candidate_state,
        exclude_generic_payment=False,
        runtime_snapshot=snapshot,
    )
    if errors:
        raise ValueError(errors[0])
    capability_colors = sorted({
        color for profile in capability_profiles for color in profile.get("output_capabilities", [])
        if color in {"W", "U", "B", "R", "G"}
    })

    spendable_state = candidate[2].copy()
    spendable_state["generic_payment_available_from_other_sources"] = residual_external_capacity
    spendable_profiles, errors = _resolved_profiles(
        candidate[1],
        spendable_state,
        exclude_generic_payment=False,
        runtime_snapshot=snapshot,
    )
    if errors:
        raise ValueError(errors[0])
    spendable_capabilities = sorted({
        color for profile in spendable_profiles for color in profile.get("output_capabilities", [])
        if color in {"W", "U", "B", "R", "G", "C"}
    }) if candidate[0]["tapped"] is False else []
    return {
        "survives": True,
        "online": True,
        "source_capability": capability_colors,
        "five_color_available": set("WUBRG") <= set(capability_colors),
        "external_base_capacity": external_base_capacity,
        "residual_external_payment_capacity": residual_external_capacity,
        "candidate_spendable_output_capabilities": spendable_capabilities,
    }
# Task 32H deliberately keeps physical observations and executable semantics
# separate.  A session owns a fresh Task-32F authenticated snapshot and frozen
# copies of physical observations for exactly one Level-2 development window.
# Callers apply the returned mutations, then create a fresh session; no result
# changing source projection is retained across physical state changes.
_RUNTIME_DEVELOPMENT_SESSION_TOKEN = object()
_MANA_SYMBOLS = frozenset({"W", "U", "B", "R", "G", "C"})
_MANA_SYMBOL_ORDER = {symbol: index for index, symbol in enumerate(("C", "W", "U", "B", "R", "G"))}


def _freeze_runtime_value(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_runtime_value(item) for key, item in value.items()})
    if type(value) in {list, tuple}:
        return tuple(_freeze_runtime_value(item) for item in value)
    if value is None or type(value) in {str, int, bool}:
        return value
    raise ValueError("runtime development result contains an unsupported value")


@dataclass(frozen=True, slots=True, init=False)
class RuntimeDevelopmentSession:
    """One sealed, operation-local authenticated development observation."""

    _runtime_context: SimulationRuntimeContext
    _snapshot: AuthenticatedRuntimeSnapshot | None
    _sources: tuple
    _turn_state: Mapping
    _floating_mana: Mapping
    _construction_token: object

    def __init__(self, *args, **kwargs):
        raise TypeError("RuntimeDevelopmentSession instances are created only by begin_runtime_development_session")


def _require_runtime_development_session(session):
    if type(session) is not RuntimeDevelopmentSession:
        raise ValueError("runtime development operation requires a sealed RuntimeDevelopmentSession")
    if session._construction_token is not _RUNTIME_DEVELOPMENT_SESSION_TOKEN:
        raise ValueError("runtime development session construction is not authenticated")
    if session._snapshot is not None:
        raise ValueError("runtime development session cannot retain an executable semantic snapshot")
    snapshot = _authenticate_runtime_context(session._runtime_context)
    if type(session._sources) is not tuple or any(type(source) is not MappingProxyType for source in session._sources):
        raise ValueError("runtime development session source observations are not sealed")
    if type(session._turn_state) is not MappingProxyType:
        raise ValueError("runtime development session turn observation is not sealed")
    if type(session._floating_mana) is not MappingProxyType:
        raise ValueError("runtime development session floating mana observation is not sealed")
    try:
        sources, turn_state, floating_mana = _validate_runtime_development_observations(
            snapshot, [dict(source) for source in session._sources], dict(session._turn_state),
            dict(session._floating_mana),
        )
    except (KeyError, TypeError) as error:
        raise ValueError("runtime development session physical observations are malformed") from error
    operation = object.__new__(RuntimeDevelopmentSession)
    object.__setattr__(operation, "_runtime_context", session._runtime_context)
    object.__setattr__(operation, "_snapshot", snapshot)
    object.__setattr__(operation, "_sources", sources)
    object.__setattr__(operation, "_turn_state", turn_state)
    object.__setattr__(operation, "_floating_mana", floating_mana)
    object.__setattr__(operation, "_construction_token", _RUNTIME_DEVELOPMENT_SESSION_TOKEN)
    return operation


def _validate_floating_mana_state(floating_mana_state):
    if type(floating_mana_state) is not dict:
        raise ValueError("floating_mana_state must be an exact object")
    if any(type(symbol) is not str for symbol in floating_mana_state):
        raise ValueError("floating_mana_state keys must be exact mana-symbol strings")
    extras = sorted(symbol for symbol in floating_mana_state if symbol not in _MANA_SYMBOLS)
    if extras:
        raise ValueError("floating_mana_state has unregistered mana symbols: " + ", ".join(extras))
    if any(type(quantity) is not int or quantity < 0 for quantity in floating_mana_state.values()):
        raise ValueError("floating_mana_state quantities must be non-negative integers")
    return {symbol: quantity for symbol, quantity in floating_mana_state.items() if quantity}


def _validate_runtime_development_sources(snapshot, source_states):
    if type(source_states) is not list:
        raise ValueError("source_states must be an exact array")
    required = {"instance_id", "oracle_id", "ordinal", "deployed_controller_turn_offset", "tapped", "removed"}
    seen = set()
    sources = []
    for source in source_states:
        if type(source) is not dict:
            raise ValueError("source_states entries must be exact objects")
        if set(source) != required:
            raise ValueError("source_states entries must contain exactly physical observation fields")
        instance_id = source["instance_id"]
        if type(instance_id) is not str or not instance_id or instance_id in seen:
            raise ValueError("source_states instance_id values must be unique non-empty strings")
        seen.add(instance_id)
        _resolve_runtime_record(snapshot, source["oracle_id"])
        if type(source["ordinal"]) is not int or source["ordinal"] < 1:
            raise ValueError("source_states ordinal must be a positive integer")
        if type(source["deployed_controller_turn_offset"]) is not int or source["deployed_controller_turn_offset"] < 0:
            raise ValueError("source_states deployed_controller_turn_offset must be a non-negative integer")
        if type(source["tapped"]) is not bool or type(source["removed"]) is not bool:
            raise ValueError("source_states tapped and removed must be booleans")
        sources.append(_freeze_runtime_value(source))
    return tuple(sources)


def _validate_runtime_development_observations(snapshot, source_states, turn_state, floating_mana_state):
    """Validate the complete physical-session boundary shared by all operations."""
    sources = _validate_runtime_development_sources(snapshot, source_states)
    if type(turn_state) is not dict or set(turn_state) != {"controller_turn_offset"}:
        raise ValueError("turn_state must contain exactly controller_turn_offset")
    offset = turn_state["controller_turn_offset"]
    if type(offset) is not int or offset < 0:
        raise ValueError("turn_state controller_turn_offset must be a non-negative integer")
    if any(source["deployed_controller_turn_offset"] > offset for source in sources):
        raise ValueError("source_states deployed_controller_turn_offset cannot exceed controller_turn_offset")
    return sources, _freeze_runtime_value(turn_state), _freeze_runtime_value(
        _validate_floating_mana_state(floating_mana_state)
    )


def begin_runtime_development_session(*, runtime_context, source_states, shared_state, turn_state, floating_mana_state):
    """Authenticate exact physical observations for one bounded development phase.

    ``shared_state`` exists only to make the engine/runtime boundary explicit;
    semantic conditions are never caller-provided and the only accepted value is
    an exact empty object.  Artifact count, Tron identities, Commander colors,
    and external payment capacity are derived below from the authenticated
    registry plus physical source observations.
    """
    snapshot = _authenticate_runtime_context(runtime_context)
    if type(shared_state) is not dict or shared_state:
        raise ValueError("shared_state must be an exact empty physical observation object")
    sources, sealed_turn_state, sealed_floating_mana = _validate_runtime_development_observations(
        snapshot, source_states, turn_state, floating_mana_state,
    )
    instance = object.__new__(RuntimeDevelopmentSession)
    object.__setattr__(instance, "_runtime_context", runtime_context)
    object.__setattr__(instance, "_snapshot", None)
    object.__setattr__(instance, "_sources", sources)
    object.__setattr__(instance, "_turn_state", sealed_turn_state)
    object.__setattr__(instance, "_floating_mana", sealed_floating_mana)
    object.__setattr__(instance, "_construction_token", _RUNTIME_DEVELOPMENT_SESSION_TOKEN)
    return instance


def _profile_output_alternatives(profile):
    units = profile.get("mana_units")
    capabilities = profile.get("output_capabilities")
    if type(units) is not int or units <= 0 or type(capabilities) is not tuple:
        raise ValueError("authenticated activation profile output is malformed")
    if any(symbol not in _MANA_SYMBOLS for symbol in capabilities):
        raise ValueError("authenticated activation profile has an unregistered mana symbol")
    selection = profile.get("output_selection")
    ordered = tuple(sorted(capabilities, key=_MANA_SYMBOL_ORDER.__getitem__))
    if selection == "fixed":
        if len(ordered) != 1:
            raise ValueError("authenticated fixed activation output must have exactly one symbol")
        return (ordered * units,)
    if selection == "one_choice":
        return tuple((symbol,) * units for symbol in ordered)
    if selection == "any_combination":
        return tuple(combination for combination in combinations_with_replacement(ordered, units))
    raise ValueError("authenticated activation profile has an unsupported output selection")


def _profile_is_currently_online(profile, source, controller_turn_offset):
    online_model = profile.get("online_model")
    if online_model == "immediate":
        return True
    if online_model == "next_controller_turn":
        return controller_turn_offset > source["deployed_controller_turn_offset"]
    if online_model == "bounded_window":
        return True
    raise ValueError("authenticated activation profile has an unregistered online model")


def _source_relative_controller_turn_offset(session, source):
    current = session._turn_state["controller_turn_offset"]
    deployed = source["deployed_controller_turn_offset"]
    if current < deployed:
        raise ValueError("source_states current controller turn cannot precede deployed_controller_turn_offset")
    return current - deployed


def _runtime_condition_state(session, *, source=None, external_generic_capacity=0):
    snapshot = session._snapshot
    controlled_lands = [
        source["oracle_id"]
        for source in session._sources
        if not source["removed"] and _resolve_runtime_record(snapshot, source["oracle_id"]).get("source_kind") == "land"
    ]
    artifact_count = sum(
        1
        for source in session._sources
        if not source["removed"] and source["oracle_id"] in snapshot.canonical_artifact_oracle_ids
    )
    return {
        "controlled_land_oracle_ids": controlled_lands,
        "artifact_controlled_count": artifact_count,
        "commander_colors": sorted(snapshot.canonical_commander_colors),
        "controller_turn_offset": (
            _source_relative_controller_turn_offset(session, source)
            if source is not None else session._turn_state["controller_turn_offset"]
        ),
        "generic_payment_available_from_other_sources": external_generic_capacity,
    }


def _base_profiles_for_source(session, source):
    record = _resolve_runtime_record(session._snapshot, source["oracle_id"])
    profiles, errors = _resolved_profiles(
        record,
        _runtime_condition_state(session, source=source),
        exclude_generic_payment=True,
        runtime_snapshot=session._snapshot,
    )
    if errors:
        raise ValueError(errors[0])
    return [
        profile for profile in profiles
        if _profile_is_currently_online(profile, source, session._turn_state["controller_turn_offset"])
    ]


def _derive_ledger_entries(session):
    base = {
        source["instance_id"]: _base_profiles_for_source(session, source)
        for source in session._sources if not source["removed"]
    }
    entries = []
    for source in session._sources:
        record = _resolve_runtime_record(session._snapshot, source["oracle_id"])
        if source["removed"]:
            entries.append(_freeze_runtime_value({
                **dict(source), "source_kind": record["source_kind"], "online": False,
                "usable": False, "activation_profiles": [], "gross_activation_profiles": [], "output_alternatives": [],
            }))
            continue
        gross_external_capacity = sum(
            max((profile.get("mana_units", 0) for profile in profiles), default=0)
            for other in session._sources
            if other["instance_id"] != source["instance_id"] and not other["removed"]
            for profiles in (base.get(other["instance_id"], []),)
        )
        residual_external_capacity = sum(
            max((profile.get("mana_units", 0) for profile in profiles), default=0)
            for other in session._sources
            if other["instance_id"] != source["instance_id"] and not other["removed"] and not other["tapped"]
            for profiles in (base.get(other["instance_id"], []),)
        ) + sum(session._floating_mana.values())
        profiles, errors = _resolved_profiles(
            record,
            _runtime_condition_state(session, source=source, external_generic_capacity=residual_external_capacity),
            exclude_generic_payment=False,
            runtime_snapshot=session._snapshot,
        )
        if errors:
            raise ValueError(errors[0])
        profiles = [
            profile for profile in profiles
            if _profile_is_currently_online(profile, source, session._turn_state["controller_turn_offset"])
        ]
        gross_profiles, errors = _resolved_profiles(
            record,
            _runtime_condition_state(session, source=source, external_generic_capacity=gross_external_capacity),
            exclude_generic_payment=False, runtime_snapshot=session._snapshot,
        )
        if errors:
            raise ValueError(errors[0])
        gross_profiles = [profile for profile in gross_profiles if _profile_is_currently_online(profile, source, session._turn_state["controller_turn_offset"])]
        def projection(profile):
            return {
                "profile_id": profile["profile_id"],
                "mana_units": profile["mana_units"],
                "output_capabilities": list(profile["output_capabilities"]),
                "output_selection": profile["output_selection"],
                "tap_model": profile["tap_model"],
                "payment_generic": profile["payment"]["generic"],
                "payment_colored": list(profile["payment"]["colored"]),
                "life_payment": dict(profile["payment"]["life"]),
                "natural_untap_model": profile["natural_untap_model"],
                "output_alternatives": [list(item) for item in _profile_output_alternatives(profile)],
            }
        activation_profiles = [projection(profile) for profile in profiles]
        gross_activation_profiles = [projection(profile) for profile in gross_profiles]
        entries.append(_freeze_runtime_value({
            **dict(source), "source_kind": record["source_kind"], "online": bool(activation_profiles),
            "usable": bool(activation_profiles) and not source["tapped"],
            "controller_turn_offset": _source_relative_controller_turn_offset(session, source),
            "activation_profiles": activation_profiles,
            "gross_activation_profiles": gross_activation_profiles,
            "output_alternatives": [item["output_alternatives"] for item in activation_profiles],
        }))
    return tuple(entries)


def _derive_runtime_resource_ledger(session):
    """Derive a ledger from one already-authenticated operation session."""
    state = _runtime_condition_state(session)
    return _freeze_runtime_value({
        "controller_turn_position": state["controller_turn_offset"],
        "controlled_land_oracle_ids": state["controlled_land_oracle_ids"],
        "artifact_controlled_count": state["artifact_controlled_count"],
        "commander_colors": state["commander_colors"],
        "floating_mana": dict(session._floating_mana),
        "sources": _derive_ledger_entries(session),
    })


def derive_runtime_resource_ledger(session):
    """Return fresh immutable current-source authority for a sealed session."""
    return _derive_runtime_resource_ledger(_require_runtime_development_session(session))


def derive_land_selection_state(session, *, candidate_land_oracle_id=None):
    """Derive the complete current selector condition state without caller rules."""
    session = _require_runtime_development_session(session)
    if candidate_land_oracle_id is not None:
        _resolve_runtime_record(session._snapshot, candidate_land_oracle_id, required_source_kind={"land"})
    state = _runtime_condition_state(session)
    entries = _derive_ledger_entries(session)
    external = sum(
        max((profile["mana_units"] for profile in entry["activation_profiles"]), default=0)
        for entry in entries if entry["usable"]
    ) + sum(session._floating_mana.values())
    result = {
        "commander_colors": state["commander_colors"],
        "canonical_commander_colors": state["commander_colors"],
        "current_colors": sorted({
            symbol
            for entry in entries if not entry["removed"]
            for profile in entry["gross_activation_profiles"]
            for symbol in profile["output_capabilities"]
            if symbol in {"W", "U", "B", "R", "G"}
        }),
        "controlled_land_oracle_ids": state["controlled_land_oracle_ids"],
        "artifact_controlled_count": state["artifact_controlled_count"],
        "generic_payment_available_from_other_sources": external,
        # The candidate is hypothetically played in this selector operation,
        # so its registered bounded age always starts at zero.
        "controller_turn_offset": 0,
    }
    if candidate_land_oracle_id is not None:
        result["candidate_land_oracle_id"] = candidate_land_oracle_id
    return _freeze_runtime_value(result)


def _validate_payment_cost(cost):
    if type(cost) is not dict or set(cost) != {"generic", "colored"}:
        raise ValueError("payment cost must contain exactly generic and colored")
    if type(cost["generic"]) is not int or cost["generic"] < 0:
        raise ValueError("payment cost generic must be a non-negative integer")
    if type(cost["colored"]) is not list or any(symbol not in _MANA_SYMBOLS for symbol in cost["colored"]):
        raise ValueError("payment cost colored must be an array of registered mana symbols")
    return cost


def _counts(symbols):
    result = {}
    for symbol in symbols:
        result[symbol] = result.get(symbol, 0) + 1
    return result


def _consume_cost_variants(resources, cost, *, forbidden_instance_id=None):
    """Enumerate every legal exact/generic payment before any ranking.

    Resource identity, including ephemeral activation provenance, is retained by
    the caller.  Therefore equal symbols cannot be collapsed before this
    function has explored their distinct downstream effects.
    """
    eligible = tuple(item for item in resources if forbidden_instance_id is None or item["instance_id"] != forbidden_instance_id)
    by_symbol = {symbol: tuple(item for item in eligible if item["symbol"] == symbol) for symbol in _MANA_SYMBOLS}
    states = [(frozenset(), frozenset())]
    for symbol in cost["colored"]:
        next_states = []
        for consumed, generic in states:
            for item in by_symbol[symbol]:
                if item["index"] not in consumed:
                    next_states.append((consumed | {item["index"]}, generic))
        states = next_states
        if not states:
            return ()
    variants = []
    for consumed, _generic in states:
        available = [item for item in eligible if item["index"] not in consumed]
        for selected in combinations(available, cost["generic"]):
            generic = frozenset(item["index"] for item in selected)
            variants.append((consumed | generic, generic))
    return tuple(sorted(set(variants), key=lambda item: (tuple(sorted(item[0])), tuple(sorted(item[1])))))


def _activation_choices_for_source(entry, resources):
    """Enumerate one source's payable choices with decision-time flexibility.

    Flexibility belongs to the physical source decision, so it is derived from
    every distinct exact output presently reachable through every payable
    registered profile, rather than from the selected output or profile.
    """
    choices = []
    for profile in sorted(entry["activation_profiles"], key=lambda item: item["profile_id"]):
        activation_cost = {"generic": profile["payment_generic"], "colored": list(profile["payment_colored"])}
        for payment_indexes, payment_generic in _consume_cost_variants(
            resources, activation_cost, forbidden_instance_id=entry["instance_id"],
        ):
            for output in profile["output_alternatives"]:
                choices.append((profile, payment_indexes, payment_generic, output))
    distinct_exact_outputs = frozenset(output for _profile, _indexes, _generic, output in choices)
    source_is_flexible = len(distinct_exact_outputs) > 1
    return tuple(
        (profile, payment_indexes, payment_generic, output, source_is_flexible)
        for profile, payment_indexes, payment_generic, output in choices
    )


def _flexible_generic_spend_for_consumption(consumed_resources, generic_indexes):
    """Count only allocation-ephemeral flexible units consumed as generic."""
    return sum(
        1 for item in consumed_resources
        if item["index"] in generic_indexes and item["ephemeral_flexible"]
    )


def _payment_allocation_from_transition(session, cost, activated_sources, activation_consumed, activation_generic, target_consumed, target_generic, remaining):
    """Freeze one causally-derived payment allocation for the public boundary."""
    consumed_resources = activation_consumed + target_consumed
    produced_symbols = [symbol for _entry, _profile, output in activated_sources for symbol in output]
    consumed_symbols = [item["symbol"] for item in consumed_resources]
    source_outputs = [
        (entry["oracle_id"], entry["ordinal"], symbol)
        for entry, _profile, output in activated_sources for symbol in output
    ]
    activation_colored_costs = sum(len(profile["payment_colored"]) for _entry, profile, _output in activated_sources)
    return _freeze_runtime_value({
        "source_outputs": source_outputs,
        "flexible_generic_spend": _flexible_generic_spend_for_consumption(
            consumed_resources, activation_generic | target_generic,
        ),
        "tapped_source_count": len(activated_sources),
        "tapped_source_instance_ids": [entry["instance_id"] for entry, _profile, _output in activated_sources],
        "activated_sources": [
            {"instance_id": entry["instance_id"], "oracle_id": entry["oracle_id"], "ordinal": entry["ordinal"],
             "profile_id": profile["profile_id"], "produced_symbols": list(output)}
            for entry, profile, output in activated_sources
        ],
        "produced_mana": _counts(produced_symbols),
        "consumed_mana": _counts(consumed_symbols),
        "floating_mana_before": dict(session._floating_mana),
        "floating_mana_after": _counts(item["symbol"] for item in remaining),
        "colored_satisfaction": _counts(cost["colored"]),
        "generic_satisfaction": cost["generic"],
        "external_payment_requirements": [
            {"instance_id": entry["instance_id"], "generic": profile["payment_generic"]}
            for entry, profile, _output in activated_sources if profile["payment_generic"]
        ],
        "life_payment": [
            {"instance_id": entry["instance_id"], **dict(profile["life_payment"])}
            for entry, profile, _output in activated_sources
            if profile["life_payment"]["amount"]
        ],
    })


_MAX_RUNTIME_PAYMENT_SEARCH_STATES = 65_536


def _payment_search_state_key(remaining, resources, activated, activation_consumed, activation_generic):
    """Canonical semantic state for deterministic causal-payment memoization."""
    resource_counts = {}
    for item in resources:
        key = (item["instance_id"], item["oracle_id"], item["ordinal"], item["symbol"], item["ephemeral_flexible"])
        resource_counts[key] = resource_counts.get(key, 0) + 1
    return (
        tuple(entry["instance_id"] for entry in remaining),
        tuple(sorted(
            ((key, quantity) for key, quantity in resource_counts.items()),
            key=lambda item: (
                item[0][0] is not None, item[0][0] or "", item[0][1] is not None,
                item[0][1] or "", item[0][2], _MANA_SYMBOL_ORDER[item[0][3]], item[0][4],
            ),
        )),
        tuple(sorted(
            (entry["instance_id"], profile["profile_id"], tuple(output))
            for entry, profile, output in activated
        )),
        tuple(sorted(_counts(item["symbol"] for item in activation_consumed).items())),
        _flexible_generic_spend_for_consumption(activation_consumed, activation_generic),
    )


def _derive_legal_payment_allocations_with_statistics(session, cost):
    """Explore only causally reachable activation states under a fixed bound.

    A source is activated at most once.  The search evaluates the target cost
    at every reachable state, then expands one immediately payable registered
    activation.  It never materializes a Cartesian source-option product and
    memoizes semantically identical resource states, so activation-order
    permutations cannot grow the frontier.  Exceeding the policy-owned bound
    is a fail-closed runtime error rather than a silently truncated result.
    """
    ledger = _derive_runtime_resource_ledger(session)
    remaining = tuple(sorted(
        (entry for entry in ledger["sources"] if entry["usable"]),
        key=lambda entry: entry["instance_id"],
    ))
    resources = []
    next_index = 0
    for symbol, quantity in session._floating_mana.items():
        for _ in range(quantity):
            resources.append({"index": next_index, "instance_id": None, "symbol": symbol, "oracle_id": None, "ordinal": 0, "ephemeral_flexible": False})
            next_index += 1

    statistics = {"explored_states": 0, "memoized_states": 0, "pruned_equivalent_states": 0, "expanded_activations": 0}
    seen = set()
    allocations = {}

    def add_allocation(activated, activation_consumed, activation_generic, current_resources):
        for target_indexes, target_generic in _consume_cost_variants(current_resources, cost):
            target_consumed = [item for item in current_resources if item["index"] in target_indexes]
            allocation = _payment_allocation_from_transition(
                session, cost, activated, activation_consumed, activation_generic, target_consumed, target_generic,
                [item for item in current_resources if item["index"] not in target_indexes],
            )
            allocation_key = _payment_allocation_priority_key(allocation)
            allocations[allocation_key] = allocation

    def explore(current_remaining, current_resources, activated, activation_consumed, activation_generic, next_resource_index):
        state_key = _payment_search_state_key(
            current_remaining, current_resources, activated, activation_consumed, activation_generic,
        )
        if state_key in seen:
            statistics["pruned_equivalent_states"] += 1
            return
        seen.add(state_key)
        statistics["explored_states"] += 1
        if statistics["explored_states"] > _MAX_RUNTIME_PAYMENT_SEARCH_STATES:
            raise ValueError("runtime payment allocation search exceeded its deterministic state bound")
        add_allocation(activated, activation_consumed, activation_generic, current_resources)
        for choice_index, entry in enumerate(current_remaining):
            for profile, payment_indexes, payment_generic, output, source_is_flexible in _activation_choices_for_source(entry, current_resources):
                paid = [item for item in current_resources if item["index"] in payment_indexes]
                after_payment = [item for item in current_resources if item["index"] not in payment_indexes]
                produced = [
                    {
                        "index": next_resource_index + output_index, "instance_id": entry["instance_id"],
                        "symbol": symbol, "oracle_id": entry["oracle_id"], "ordinal": entry["ordinal"],
                        "ephemeral_flexible": source_is_flexible,
                    }
                    for output_index, symbol in enumerate(output)
                ]
                statistics["expanded_activations"] += 1
                explore(
                    current_remaining[:choice_index] + current_remaining[choice_index + 1:],
                    after_payment + produced,
                    activated + [(entry, profile, output)], activation_consumed + paid, activation_generic | payment_generic,
                    next_resource_index + len(produced),
                )

    explore(remaining, resources, [], [], frozenset(), next_index)
    statistics["memoized_states"] = len(seen)
    statistics["legal_allocations"] = len(allocations)
    ordered = tuple(allocations[key] for key in sorted(allocations))
    return ordered, _freeze_runtime_value(statistics)


def derive_legal_payment_allocations(session, *, cost):
    """Derive legal full-output transitions with bounded causal state search."""
    session = _require_runtime_development_session(session)
    cost = _validate_payment_cost(cost)
    return _derive_legal_payment_allocations_with_statistics(session, cost)[0]


def derive_legal_payment_allocation_search_statistics(session, *, cost):
    """Return deterministic bounded-search evidence for KATs and audit output."""
    session = _require_runtime_development_session(session)
    cost = _validate_payment_cost(cost)
    return _derive_legal_payment_allocations_with_statistics(session, cost)[1]


def resolve_turn_start_state(session):
    """Derive exact natural-untap physical mutations; zeroing is defensive only."""
    session = _require_runtime_development_session(session)
    mutations = []
    for entry in _derive_ledger_entries(session):
        if entry["removed"] or not entry["tapped"]:
            continue
        models = {profile["natural_untap_model"] for profile in entry["activation_profiles"]}
        if models == {"normal"}:
            mutations.append({"instance_id": entry["instance_id"], "tapped": False})
    return _freeze_runtime_value({
        "controller_turn_offset": session._turn_state["controller_turn_offset"] + 1,
        "tapped_state_mutations": mutations,
        "floating_mana_defensive_invariant": {},
    })


def resolve_post_development_removals(session):
    """Derive exact Saga/conditional source removals after development ends."""
    session = _require_runtime_development_session(session)
    removals = []
    for source in session._sources:
        if source["removed"]:
            continue
        record = _resolve_runtime_record(session._snapshot, source["oracle_id"])
        state = _runtime_condition_state(session, source=source)
        transition, errors = _evaluate_end_step_state_transitions(
            session._snapshot, record,
            _condition_state_for_conditions(state, [
                item.get("condition") for item in (record.get("state_transitions") or []) if isinstance(item, Mapping)
            ]),
        )
        if errors:
            raise ValueError(errors[0])
        bounded_removal = _expired_bounded_source(record, state, runtime_snapshot=session._snapshot)
        if transition["removed"] or bounded_removal:
            removals.append({"instance_id": source["instance_id"], "removed": True})
    return _freeze_runtime_value({"removed_source_mutations": removals})


def end_level_2_development_phase(session):
    """The sole result-changing floating-mana lifetime boundary in sim-policy-v7."""
    _require_runtime_development_session(session)
    return _freeze_runtime_value({"floating_mana": {}})
