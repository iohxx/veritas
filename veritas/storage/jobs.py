import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
from veritas.attestation.canonical import canonical, parse_json
from veritas.security.policy import safe_id
from veritas.errors import VeritasError


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as f:
            f.write(canonical(value))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_json(path, limit=8000000):
    with Path(path).open('rb') as f:
        return parse_json(f.read(limit+1), limit)


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in ('jobs','evidence','attestations','logs'):
            (self.root / folder).mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / 'state.sqlite3', timeout=5)
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, requester TEXT, nonce TEXT, hash TEXT, state TEXT, UNIQUE(requester,nonce))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (kind TEXT, at INTEGER)')
        self.db.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)')
        self.db.commit()

    def close(self):
        self.db.close()

    def job_path(self, job_id):
        path = self.root / 'jobs' / safe_id(job_id)
        if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(self.root / 'jobs'):
            raise VeritasError('unsafe_job_path')
        return path

    def reserve(self, job, hashed):
        try:
            self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', (job.job_id,job.requester,job.nonce,hashed,'processing'))
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            raise VeritasError('duplicate_job_or_nonce')
        path = self.job_path(job.job_id)
        path.mkdir(exist_ok=False)
        return path

    def finish(self, job_id, state):
        self.db.execute('UPDATE jobs SET state=? WHERE id=?', (state,job_id))
        self.db.commit()

    def get(self, key, default=None):
        row = self.db.execute('SELECT value FROM state WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO state VALUES (?,?)',(key,json.dumps(value)))
        self.db.commit()

    def quota(self, kind, limit):
        now = int(time.time())
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('DELETE FROM events WHERE at<=?',(now-3600,))
        count = self.db.execute('SELECT COUNT(*) FROM events WHERE kind=?',(kind,)).fetchone()[0]
        if count >= limit:
            self.db.rollback()
            raise VeritasError('rate_limit_' + kind)
        self.db.execute('INSERT INTO events VALUES (?,?)',(kind,now))
        self.db.commit()

    def log(self, event, job_id=None, status=None, duration_ms=None):
        entry = {'event':event,'timestamp':int(time.time())}
        if job_id:
            entry['job_id'] = safe_id(job_id)
        if status:
            entry['status'] = status
        if duration_ms is not None:
            entry['duration_ms'] = duration_ms
        with (self.root/'logs'/'events.jsonl').open('ab') as f:
            f.write(canonical(entry) + b'\n')
