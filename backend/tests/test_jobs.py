from backend.app import queue, storage, worker


def test_jobs_are_claimed_once_and_results_persist(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    identity = queue.enqueue('prepare', {'clip_id': 'sample'})
    assert queue.get(identity)['state'] == 'queued'
    assert queue.claim()['id'] == identity
    assert queue.claim() is None
    queue.progress(identity, 2, 5, 'Preparing')
    assert queue.get(identity)['completed'] == 2
    queue.finish(identity, result={'evidence': 'saved'})
    assert queue.get(identity)['result'] == {'evidence': 'saved'}
    assert queue.get(identity)['state'] == 'succeeded'


def test_interrupted_jobs_do_not_automatically_replay(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    identity = queue.enqueue('analyse', {'revision': 1})
    queue.claim()
    queue.interrupt_abandoned()
    assert queue.get(identity)['state'] == 'interrupted'
    assert queue.claim() is None


def test_worker_failure_is_visible_and_does_not_discard_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DATA', tmp_path)
    identity = queue.enqueue('prepare', {'clip_id': 'source'})
    def broken(job):
        raise ValueError('No usable local video')
    monkeypatch.setattr(worker, 'process', broken)
    assert worker.run_once()
    result = queue.get(identity)
    assert result['state'] == 'failed'
    assert result['error'] == 'No usable local video'
    assert result['payload'] == {'clip_id': 'source'}
    assert queue.worker_status()['online']

