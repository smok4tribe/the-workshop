"""Frozen deterministic primitives shared by future simulation engines and validators."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
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


def choose_payment(allocations):
    """Choose a legal allocation using the frozen payment tie-break.

    Each allocation contains flexible_generic_spend, tapped_source_count, and
    source_outputs as (oracle_id, ordinal, output-symbol) tuples.
    """
    if not allocations:
        return None
    color_rank = {"C": 0, "W": 1, "U": 2, "B": 3, "R": 4, "G": 5}
    def key(item):
        ordered = tuple(sorted(
            ((oracle.lower(), ordinal, color_rank[color]) for oracle, ordinal, color in item["source_outputs"]),
        ))
        return item["flexible_generic_spend"], item["tapped_source_count"], ordered
    return min(allocations, key=key)


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


APPROVED_RUNTIME_MANA_SOURCE_SEMANTICS_FINGERPRINT = "artifact-content-sha256-v1:bd867436cc899bf18a4a3d89550f820c8096db1e1ca5290fdda36c1a04d2c7fa"
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
    registry_identity: tuple[str, str, str, str, str]
    registry_content_fingerprint: str
    canonical_land_oracle_ids: frozenset[str]
    canonical_commander_colors: frozenset[str]
    _construction_token: object

    def __init__(self, *args, **kwargs):
        raise TypeError("SimulationRuntimeContext instances are created only by validated canonical construction")

    @classmethod
    def _from_validated_registry(cls, registry):
        if type(registry) is not dict:
            raise ValueError("validated runtime semantic registry must be an exact object")
        canonical_bytes = _canonical_json_bytes(registry)
        canonical_registry = load_strict_json_bytes(canonical_bytes)
        if type(canonical_registry) is not dict or type(canonical_registry.get("records")) is not list:
            raise ValueError("validated runtime semantic registry has no canonical records")
        records = canonical_registry["records"]
        if any(type(record) is not dict or type(record.get("oracle_id")) is not str or not record["oracle_id"] for record in records):
            raise ValueError("validated runtime semantic registry has invalid record identities")
        if len({record["oracle_id"] for record in records}) != len(records):
            raise ValueError("validated runtime semantic registry has duplicate record identities")
        instance = object.__new__(cls)
        object.__setattr__(instance, "registry_identity", tuple(
            canonical_registry[field] for field in ("schema_version", "artifact_type", "artifact_id", "project_id", "policy_version")
        ))
        object.__setattr__(instance, "_registry_canonical_bytes", canonical_bytes)
        object.__setattr__(instance, "registry_content_fingerprint", artifact_content_fingerprint(canonical_registry))
        object.__setattr__(instance, "canonical_land_oracle_ids", frozenset(
            record["oracle_id"] for record in records if record.get("source_kind") == "land"
        ))
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
