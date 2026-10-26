"""One-process durable queue, atomically claimed by a separate worker."""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager

from . import storage


@contextmanager
def connection():
    storage.DATA.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(storage.DATA / 'jobs.sqlite', timeout=10)
    database.row_factory = sqlite3.Row
    database.execute('PRAGMA busy_timeout=10000')
    database.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
        state TEXT NOT NULL, phase TEXT, completed INTEGER DEFAULT 0,
        total INTEGER DEFAULT 0, result TEXT, error TEXT,
        created REAL NOT NULL, updated REAL NOT NULL)''')
    database.execute('CREATE TABLE IF NOT EXISTS worker_status (id INTEGER PRIMARY KEY, heartbeat REAL)')
    database.commit()
    try:
        yield database
        database.commit()
    except BaseException:
        database.rollback()
        raise
    finally:
        database.close()


def enqueue(kind: str, payload: dict, result=None):
    identity = uuid.uuid4().hex
    now = time.time()
    with connection() as db:
        db.execute('''INSERT INTO jobs(id,kind,payload,state,phase,result,created,updated)
            VALUES(?,?,?,?,?,?,?,?)''',
                   (identity, kind, json.dumps(payload), 'succeeded' if result is not None else 'queued',
                    'Complete' if result is not None else 'Queued',
                    json.dumps(result) if result is not None else None, now, now))
    return identity


def get(identity: str):
    storage.safe_id(identity)
    with connection() as db:
        row = db.execute('SELECT * FROM jobs WHERE id=?', (identity,)).fetchone()
    if row is None:
        return None
    value = dict(row)
    value['payload'] = json.loads(value['payload'])
    value['result'] = json.loads(value['result']) if value['result'] else None
    return value


def claim():
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
        if row is None:
            return None
        db.execute("UPDATE jobs SET state='running', phase='Starting', updated=? WHERE id=?",
                   (time.time(), row['id']))
        identity = row['id']
    return get(identity)


def progress(identity, completed, total, phase):
    with connection() as db:
        db.execute('UPDATE jobs SET completed=?,total=?,phase=?,updated=? WHERE id=?',
                   (completed, total, phase, time.time(), identity))


def finish(identity, result=None, error=None):
    with connection() as db:
        db.execute('UPDATE jobs SET state=?,phase=?,result=?,error=?,updated=? WHERE id=?',
                   ('failed' if error else 'succeeded', 'Failed' if error else 'Complete',
                    json.dumps(result) if result is not None else None, error, time.time(), identity))


def interrupt_abandoned():
    with connection() as db:
        db.execute("UPDATE jobs SET state='interrupted',phase='Interrupted',error=?,updated=? WHERE state='running'",
                   ('Worker restarted before this job completed. Explicitly retry the operation.', time.time()))


def heartbeat():
    with connection() as db:
        db.execute('INSERT OR REPLACE INTO worker_status(id,heartbeat) VALUES(1,?)', (time.time(),))


def worker_status():
    with connection() as db:
        row = db.execute('SELECT heartbeat FROM worker_status WHERE id=1').fetchone()
    stamp = row['heartbeat'] if row else None
    return {'heartbeat': stamp, 'online': stamp is not None and time.time() - stamp < 15}

