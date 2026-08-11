"""Canonical repository identities for Workshop evidence artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections import Counter


ARTIFACT_CONTENT_ALGORITHM_ID = "artifact-content-sha256-v1"
DECK_CONTENT_ALGORITHM_ID = "deck-content-sha256-canonical-v2"
IDENTITY_FIELDS = (
    "name",
    "normalized_name",
    "canonical_card_name",
    "display_name",
    "original_decklist_name",
)


def normalize_card_identity(value: str) -> str:
    """Normalize user-facing card names for Card Facts alias resolution."""
    return " ".join(unicodedata.normalize("NFKC", str(value)).split()).casefold()


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise ValueError(f"non-finite JSON constant {value!r} is not allowed")


def load_strict_json_bytes(data: bytes):
    """Parse canonical-fingerprint input with the frozen JSON restrictions."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"JSON is not strict UTF-8: {exc}") from exc
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )


def load_strict_json(path):
    return load_strict_json_bytes(path.read_bytes())


def artifact_content_fingerprint(value) -> str:
    """Return The Workshop canonical JSON content identity.

    The emitted bytes intentionally use the standard-library serialization frozen
    by the contract: sorted object keys, compact separators, UTF-8, no NaN.
    """
    def reject_nonfinite(node):
        if isinstance(node, float) and not math.isfinite(node):
            raise ValueError("non-finite JSON number is not allowed")
        if isinstance(node, dict):
            for key, item in node.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                reject_nonfinite(item)
        elif isinstance(node, list):
            for item in node:
                reject_nonfinite(item)

    reject_nonfinite(value)
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{ARTIFACT_CONTENT_ALGORITHM_ID}:{hashlib.sha256(payload).hexdigest()}"


def card_facts_identity_index(cards):
    """Return all Card Facts candidates for each normalized alias, without hiding ambiguity."""
    aliases = {}
    for record_index, record in enumerate(cards):
        if not isinstance(record, dict):
            continue
        for field in IDENTITY_FIELDS:
            value = record.get(field)
            if isinstance(value, str) and value.strip():
                aliases.setdefault(normalize_card_identity(value), []).append((record_index, record))
    return aliases


def resolve_card_fact(entry_name: str, cards):
    """Resolve one DeckVersion name/alias to exactly one canonical Card Facts record."""
    candidates = card_facts_identity_index(cards).get(normalize_card_identity(entry_name), [])
    unique = {index: candidate for index, candidate in candidates}
    if not unique:
        raise ValueError(f"DeckVersion entry {entry_name!r} has no canonical Card Facts resolution")
    if len(unique) != 1:
        raise ValueError(f"DeckVersion entry {entry_name!r} has ambiguous canonical Card Facts resolution")
    record = next(iter(unique.values()))
    oracle_id = record.get("oracle_id")
    if not isinstance(oracle_id, str) or not oracle_id.strip():
        raise ValueError(f"DeckVersion entry {entry_name!r} resolves to Card Facts without oracle_id")
    return record


def _zone_entries(version, source_field):
    if source_field == "commander":
        commander = version.get("commander")
        return [commander] if isinstance(commander, dict) else []
    entries = version.get(source_field)
    return entries if isinstance(entries, list) else []


def canonical_deck_tokens(version, cards):
    """Expand the modeled 99-card library into deterministic oracle-id tokens."""
    counts = Counter()
    for entry in _zone_entries(version, "main_deck"):
        if not isinstance(entry, dict) or not isinstance(entry.get("quantity"), int) or isinstance(entry["quantity"], bool) or entry["quantity"] < 1:
            raise ValueError(f"invalid library DeckVersion entry {entry!r}")
        record = resolve_card_fact(entry.get("name", ""), cards)
        counts[record["oracle_id"].lower()] += entry["quantity"]
    return [f"{oracle_id}#{ordinal}" for oracle_id in sorted(counts) for ordinal in range(1, counts[oracle_id] + 1)]


def deck_content_fingerprint(version, cards):
    """Implement deck-content-sha256-canonical-v2 exactly."""
    blocks = []
    for label, field in (("commander", "commander"), ("library", "main_deck")):
        counts = Counter()
        for entry in _zone_entries(version, field):
            if not isinstance(entry, dict) or not isinstance(entry.get("quantity"), int) or isinstance(entry["quantity"], bool) or entry["quantity"] < 1:
                raise ValueError(f"invalid {label} DeckVersion entry {entry!r}")
            record = resolve_card_fact(entry.get("name", ""), cards)
            counts[record["oracle_id"].lower()] += entry["quantity"]
        lines = [f"{counts[oracle_id]} {oracle_id}" for oracle_id in sorted(counts)]
        blocks.append(label + "\n" + "\n".join(lines))
    payload = "\n\x1e\n".join(blocks).encode("utf-8")
    return f"{DECK_CONTENT_ALGORITHM_ID}:{hashlib.sha256(payload).hexdigest()}"
