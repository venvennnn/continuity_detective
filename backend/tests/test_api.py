import hashlib

import pytest
from fastapi.testclient import TestClient

from backend.app import storage
from backend.app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    from backend.app.analysis import pipeline
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    monkeypatch.setattr(pipeline, 'DATA', tmp_path)
    return TestClient(app)


def make_clip(identity='one'):
    source = storage.DATA / f'{identity}.mp4'
    source.write_bytes(bytes(range(256)) * 4)
    clip = {'id': identity, 'source_hash': hashlib.sha256(source.read_bytes()).hexdigest(),
            'filename': f'{identity}.mp4', 'media_path': str(source), 'size': source.stat().st_size,
            'metadata': {'duration_ms': 1000}, 'samples': [], 'proposal_id': None}
    storage.write_json(storage.clip_path(identity), clip)
    storage.write_json(storage.DATA / 'prepared' / f'{identity}.json', clip)
    return clip


def test_public_clip_does_not_leak_paths_and_media_supports_range(client):
    make_clip()
    response = client.get('/api/clips/one')
    assert response.status_code == 200
    assert response.json()['available']
    assert 'media_path' not in response.json()
    ranged = client.get('/api/media/one', headers={'Range': 'bytes=10-19'})
    assert ranged.status_code == 206
    assert ranged.content == bytes(range(10, 20))
    assert ranged.headers['content-range'] == 'bytes 10-19/1024'


def test_missing_media_stays_visible_as_unavailable(client):
    clip = make_clip()
    from pathlib import Path
    Path(clip['media_path']).unlink()
    assert client.get('/api/clips/one').json()['available'] is False
    assert client.get('/api/media/one').status_code == 404


def test_analysis_requires_confirmed_valid_reference_before_queuing(client):
    make_clip()
    evidence = 'a' * 64
    storage.write_json(storage.evidence_path(evidence, 'evidence.json'), {'clip_id': 'one'})
    reference = {'id': 'reference', 'evidence_id': evidence, 'crop': [0.2, 0.2, 0.4, 0.4],
                 'start_clip_id': 'one', 'start_ms': 0, 'confirmed': True}
    payload = {'project_id': 'project', 'revision': 1, 'clip_ids': ['one'], 'references': [reference]}
    response = client.post('/api/analysis-runs', json=payload)
    assert response.status_code == 200
    job = client.get('/api/jobs/' + response.json()['job_id']).json()
    assert job['state'] == 'queued'
    assert job['result'] is None
    assert 'payload' not in job
    payload['references'][0]['confirmed'] = False
    assert client.post('/api/analysis-runs', json=payload).status_code == 422


def test_bad_ids_origins_and_empty_upload_are_rejected(client):
    assert client.get('/api/assets/not-an-evidence-hash').status_code == 422
    assert client.get('/api/health', headers={'Origin': 'https://outside.example'}).status_code == 403
    assert client.post('/api/clips', files={'file': ('empty.mp4', b'', 'video/mp4')}).status_code == 422
    assert client.post('/api/sequences', json={'clip_ids': ['../secret']}).status_code == 422


def test_relink_checks_actual_source_hash(client):
    clip = make_clip()
    wrong = client.post('/api/clips/one/relink', files={'file': ('one.mp4', b'wrong', 'video/mp4')})
    assert wrong.status_code == 409
    from pathlib import Path
    content = Path(clip['media_path']).read_bytes()
    Path(clip['media_path']).unlink()
    correct = client.post('/api/clips/one/relink', files={'file': ('one.mp4', content, 'video/mp4')})
    assert correct.status_code == 200
    assert Path(clip['media_path']).read_bytes() == content

