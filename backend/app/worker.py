"""Run separately: python -m backend.app.worker."""
import contextlib
import os
import threading
import time

from . import queue, storage


@contextlib.contextmanager
def singleton():
    storage.DATA.mkdir(parents=True, exist_ok=True)
    lock_path = storage.DATA / 'worker.lock'
    handle = lock_path.open('a+b')
    try:
        if os.name == 'nt':
            import msvcrt
            try:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b'1')
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                handle.close()
                raise RuntimeError(
                    'Another Continuity Detective worker is already running. '
                    'Close that worker window, then delete data\\worker.lock if this error remains.'
                ) from error
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        handle.close()


def process(job):
    # Heavy imports and inference live in this process, never the API server.
    from .analysis.pipeline import prepare_clip, extract_selected, analyse
    from .sequence import build_sequence
    payload = job['payload']
    progress = lambda n, total, phase: queue.progress(job['id'], n, total, phase)
    if job['kind'] == 'prepare':
        return storage.public_clip(prepare_clip(storage.get_clip(payload['clip_id']), progress=progress))
    if job['kind'] == 'extract_frame':
        return extract_selected(storage.get_clip(payload['clip_id']), payload['time_ms'])
    if job['kind'] == 'sequence':
        clips = [storage.get_clip(identity, prepared=True) for identity in payload['clip_ids']]
        return build_sequence(clips, progress=progress)
    if job['kind'] == 'analyse':
        clips = [storage.get_clip(identity, prepared=True) for identity in payload['clip_ids']]
        if any(payload.get('source_hashes', {}).get(clip['id']) != clip['source_hash'] for clip in clips):
            raise ValueError('Source media changed after this analysis was requested. Re-run explicitly.')
        result = analyse(clips, payload['references'], payload.get('config'), progress=progress)
        return {**result, 'run_id': payload['run_id'], 'project_id': payload['project_id'],
                'revision': payload['revision'], 'input_fingerprint': payload['input_fingerprint']}
    raise ValueError('Unknown job kind')


def run_once():
    queue.heartbeat()
    job = queue.claim()
    if job is None:
        return False
    try:
        result = process(job)
        queue.finish(job['id'], result=result)
    except Exception as error:
        # Preserve saved media/evidence; retry is an explicit new job.
        print(f"Job {job['id']} failed: {type(error).__name__}: {error}", flush=True)
        message = str(error)
        if hasattr(error, 'stderr') and error.stderr:
            message = error.stderr.decode('utf-8', errors='replace')[:1000]
        queue.finish(job['id'], error=message)
    return True


def main():
    with singleton():
        queue.interrupt_abandoned()
        stop = threading.Event()
        def keep_alive():
            while not stop.is_set():
                queue.heartbeat()
                stop.wait(3)
        heartbeat = threading.Thread(target=keep_alive, daemon=True)
        heartbeat.start()
        print('Continuity Detective worker ready', flush=True)
        try:
            while True:
                if not run_once():
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            heartbeat.join(timeout=4)


if __name__ == '__main__':
    main()
