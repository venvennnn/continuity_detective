import hashlib
import json


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def position(clip_id: str, time_ms: float, clip_order: list[str]):
    return (clip_order.index(clip_id), time_ms)


def resolve_reference(references: list[dict], clip_id: str, time_ms: float, clip_order: list[str]):
    current = position(clip_id, time_ms, clip_order)
    eligible = [ref for ref in references
                if position(ref['start_clip_id'], ref['start_ms'], clip_order) <= current]
    if not eligible:
        raise ValueError('No confirmed reference covers this sequence position')
    return max(eligible, key=lambda ref: position(ref['start_clip_id'], ref['start_ms'], clip_order))
