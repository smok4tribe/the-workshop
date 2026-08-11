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
