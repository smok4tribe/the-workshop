"""Frozen deterministic primitives shared by future simulation engines and validators."""

from __future__ import annotations

import hashlib
import re


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


def condition_is_satisfied(condition, state):
    """Resolve one registered mana-source condition against observation state."""
    if not isinstance(condition, dict) or not isinstance(state, dict):
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
        controlled = state.get("controlled_land_oracle_ids")
        candidate = state.get("candidate_land_oracle_id")
        if isinstance(controlled, list) and isinstance(candidate, str):
            return set(params.get("oracle_ids", [])) <= set(controlled) | {candidate}
        return state.get("complete_tron_set_controlled") is True
    if condition_id == "commander_color_identity":
        colors = state.get("commander_colors")
        return isinstance(colors, list) and set(colors) == set(params.get("colors", []))
    return False


def resolve_activation_profiles(group, condition_truth):
    """Resolve registered activation profiles using structured predicates only."""
    profiles = group.get("profiles") if isinstance(group, dict) else None
    if not isinstance(profiles, list):
        return [], ["activation group profiles must be an array"]
    legal = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("supported"):
            continue
        if all(condition_is_satisfied(condition, condition_truth) for condition in profile.get("conditions", [])):
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


def evaluate_end_step_state_transitions(record, *, post_development_state):
    """Resolve registered end-step removals after deterministic development."""
    if not isinstance(record, dict):
        return None, ["end-step transition evaluation requires a registered source"]
    transitions = record.get("state_transitions") or []
    removal_transitions = [
        transition for transition in transitions
        if isinstance(transition, dict) and transition.get("event_id") == "end_step_remove_unless_condition"
    ]
    remains = all(
        condition_is_satisfied(transition.get("condition"), post_development_state)
        for transition in removal_transitions
    )
    return {"remains_available": remains, "removed": not remains}, []


def _record_map(records):
    if isinstance(records, dict):
        return records
    if isinstance(records, list):
        return {
            record.get("oracle_id"): record
            for record in records
            if isinstance(record, dict) and isinstance(record.get("oracle_id"), str)
        }
    return {}


def _source_state(source, shared_state):
    state = dict(shared_state or {})
    state.update(source.get("condition_state") or {})
    return state


def _has_generic_payment_condition(profile):
    return any(
        isinstance(condition, dict)
        and condition.get("condition_id") == "generic_payment_available_from_other_sources"
        for condition in (profile.get("conditions") or [])
    )


def _resolved_profiles(record, state, *, exclude_generic_payment):
    profiles = []
    for group in record.get("activation_groups") or []:
        selected, errors = resolve_activation_profiles(group, state)
        if errors == ["highest-priority activation group has no matching supported profile"]:
            continue
        if errors:
            return [], errors
        profiles.extend(
            profile for profile in selected
            if not exclude_generic_payment or not _has_generic_payment_condition(profile)
        )
    return profiles, []


def _expired_bounded_source(record, state):
    supported = [
        profile
        for group in record.get("activation_groups") or []
        for profile in (group.get("profiles") or [])
        if isinstance(profile, dict) and profile.get("supported")
    ]
    if not supported or not all(any(
        isinstance(condition, dict) and condition.get("condition_id") == "bounded_controller_turn_window"
        for condition in (profile.get("conditions") or [])
    ) for profile in supported):
        return False
    # A bounded profile with a registered removal event remains usable during
    # the final development window, then is absent from the EOT observation.
    offset = state.get("controller_turn_offset")
    if _is_integer(offset) and all(any(
        isinstance(condition, dict)
        and condition.get("condition_id") == "bounded_controller_turn_window"
        and condition.get("params", {}).get("removal_event")
        and offset >= condition.get("params", {}).get("end_offset")
        for condition in (profile.get("conditions") or [])
    ) for profile in supported):
        return True
    return not any(
        all(condition_is_satisfied(condition, state) for condition in profile.get("conditions", []))
        for profile in supported
    )


def observe_source_capability(*, source_records, source_states, candidate_source_id, condition_state=None):
    """Evaluate source-capability-observation-v1 without reconstructing Policy prose.

    ``source_states`` contains the actual post-development sources. Each entry
    needs a unique ``source_id``, registered ``oracle_id``, ``online`` and
    ``tapped`` booleans, and may provide per-source ``condition_state``.
    Earlier tapping is intentionally ignored for gross source capability, but
    retained for residual spendable-mana checks.
    """
    records = _record_map(source_records)
    if not isinstance(source_states, list) or not isinstance(candidate_source_id, str):
        raise ValueError("source capability observation requires source states and candidate_source_id")
    shared_state = dict(condition_state or {})
    if "generic_payment_available_from_other_sources" in shared_state:
        raise ValueError("source capability observation derives external generic payment internally")
    seen_ids, surviving, candidate_state = set(), [], None
    for source in source_states:
        if not isinstance(source, dict):
            raise ValueError("source capability observation source states must be objects")
        source_id, oracle_id = source.get("source_id"), source.get("oracle_id")
        if not isinstance(source_id, str) or not source_id or source_id in seen_ids:
            raise ValueError("source capability observation source_id values must be unique non-empty strings")
        seen_ids.add(source_id)
        if not isinstance(oracle_id, str) or oracle_id not in records:
            raise ValueError("source capability observation requires registered source oracle_ids")
        if not isinstance(source.get("online"), bool) or not isinstance(source.get("tapped"), bool):
            raise ValueError("source capability observation requires explicit online and tapped state")
        local_state = _source_state(source, shared_state)
        if "generic_payment_available_from_other_sources" in local_state:
            raise ValueError("source capability observation derives external generic payment internally")
        if source_id == candidate_source_id:
            candidate_state = (source, records[oracle_id], local_state)
        if source.get("online") is not True or source.get("removed") is True:
            continue
        transition, errors = evaluate_end_step_state_transitions(records[oracle_id], post_development_state=local_state)
        if errors:
            raise ValueError(errors[0])
        if transition["removed"]:
            continue
        if _expired_bounded_source(records[oracle_id], local_state):
            continue
        surviving.append((source, records[oracle_id], local_state))
    if candidate_state is None:
        raise ValueError("source capability observation candidate_source_id must identify one supplied source")

    def base_capacity(item):
        _, record, local_state = item
        profiles, errors = _resolved_profiles(record, local_state, exclude_generic_payment=True)
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

    candidate_state = dict(candidate[2])
    candidate_state["generic_payment_available_from_other_sources"] = external_base_capacity
    capability_profiles, errors = _resolved_profiles(candidate[1], candidate_state, exclude_generic_payment=False)
    if errors:
        raise ValueError(errors[0])
    capability_colors = sorted({
        color for profile in capability_profiles for color in profile.get("output_capabilities", [])
        if color in {"W", "U", "B", "R", "G"}
    })

    spendable_state = dict(candidate[2])
    spendable_state["generic_payment_available_from_other_sources"] = residual_external_capacity
    spendable_profiles, errors = _resolved_profiles(candidate[1], spendable_state, exclude_generic_payment=False)
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
