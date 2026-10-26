import numpy as np

from backend.app.config import DEFAULT_CONFIG
from backend.app.analysis import pipeline


def test_changed_effective_mask_invalidates_finding_identity(monkeypatch):
    image = np.random.default_rng(42).integers(30, 210, (200, 200, 3), dtype=np.uint8)
    evidence = {'id': 'frame', 'image_hash': 'same-image', 'source_hash': 'same-source',
                'pts': 0, 'clip_id': 'clip', 'model_hash': 'model'}
    polygon = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    person = np.ones((200, 200), np.float32)
    pose = {'polygon': polygon, 'visibility': 1, 'presence': 1, 'person_mask': person}
    monkeypatch.setattr(pipeline, 'load_evidence', lambda _: evidence)
    monkeypatch.setattr(pipeline, 'evidence_pixels', lambda _: (image, pose))
    reference = {'id': 'reference', 'evidence_id': 'frame', 'crop': [0.2, 0.2, 0.6, 0.6]}
    first = pipeline.compare(reference, evidence, DEFAULT_CONFIG)
    person[50:60, 50:60] = 0
    second = pipeline.compare(reference, evidence, DEFAULT_CONFIG)
    assert first['status'] != 'not_assessable'
    assert second['status'] != 'not_assessable'
    assert first['reference_evidence']['effective_mask_hash'] != second['reference_evidence']['effective_mask_hash']
    assert first['fingerprint'] != second['fingerprint']
