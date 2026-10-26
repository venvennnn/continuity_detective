import pytest

from backend.app.analysis.references import resolve_reference, canonical_hash


def test_forward_change_is_inclusive_and_leaves_earlier_segment_intact():
    old = {'id': 'old', 'start_clip_id': 'a', 'start_ms': 0}
    new = {'id': 'new', 'start_clip_id': 'b', 'start_ms': 1000}
    refs, order = [old, new], ['a', 'b', 'c']
    assert resolve_reference(refs, 'a', 9000, order) is old
    assert resolve_reference(refs, 'b', 999, order) is old
    assert resolve_reference(refs, 'b', 1000, order) is new
    assert resolve_reference(refs, 'c', 0, order) is new


def test_order_not_recording_time_defines_reference_scope():
    refs = [{'id': 'a', 'start_clip_id': 'late_recording', 'start_ms': 0},
            {'id': 'b', 'start_clip_id': 'early_recording', 'start_ms': 0}]
    assert resolve_reference(refs, 'early_recording', 0,
                             ['late_recording', 'early_recording'])['id'] == 'b'


def test_no_reference_is_not_silently_assumed():
    with pytest.raises(ValueError, match='No confirmed reference'):
        resolve_reference([], 'a', 0, ['a'])


def test_evidence_fingerprint_tracks_reference_and_crop():
    value = {'source': 'hash', 'reference': 'v1', 'crop': [0.1, 0.1, 0.5, 0.5]}
    assert canonical_hash(value) == canonical_hash(dict(reversed(list(value.items()))))
    assert canonical_hash(value) != canonical_hash({**value, 'reference': 'v2'})
    assert canonical_hash(value) != canonical_hash({**value, 'crop': [0, 0, 0.5, 0.5]})
