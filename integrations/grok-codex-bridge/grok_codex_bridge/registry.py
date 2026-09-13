"""Small local binding ledger, separate from Codex's database and histories."""
import json
from pathlib import Path
import re
import sqlite3
import time


class RegistryError(RuntimeError):
    pass


class Registry:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('''CREATE TABLE IF NOT EXISTS task_bindings (
            ordinal INTEGER PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
            spec_json TEXT NOT NULL, thread_id TEXT UNIQUE, state TEXT NOT NULL,
            created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
            error_class TEXT)''')
        columns = {row[1] for row in self.db.execute('PRAGMA table_info(task_bindings)')}
        if 'evidence_json' not in columns:
            self.db.execute('ALTER TABLE task_bindings ADD COLUMN evidence_json TEXT')
        self.db.commit()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    @staticmethod
    def decode(row):
        if row is None:
            return None
        record = dict(row)
        record['spec'] = json.loads(record.pop('spec_json'))
        record['evidence'] = json.loads(record.pop('evidence_json') or '{}')
        return record

    def get(self, request_key):
        return self.decode(self.db.execute(
            'SELECT * FROM task_bindings WHERE request_key=?', (request_key,)).fetchone())

    def for_thread(self, thread_id):
        return self.decode(self.db.execute(
            'SELECT * FROM task_bindings WHERE thread_id=?', (thread_id,)).fetchone())

    def reserve(self, request_key, spec):
        if not isinstance(request_key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', request_key):
            raise ValueError('Use a stable request key of 8–80 letters, digits, underscores or hyphens')
        encoded = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT * FROM task_bindings WHERE request_key=?',
                                  (request_key,)).fetchone()
            if row is not None:
                if row['spec_json'] != encoded:
                    raise RegistryError('Request key already belongs to a different task specification')
                return self.decode(row), False
            now = int(time.time())
            self.db.execute('''INSERT INTO task_bindings
                (request_key,spec_json,state,created_at,updated_at) VALUES (?,?,?,?,?)''',
                (request_key, encoded, 'reserved', now, now))
        return self.get(request_key), True

    def update(self, request_key, state, thread_id=None, error_class=None, evidence=None):
        if state not in {'reserved', 'identified', 'initializing', 'initialized', 'ready', 'uncertain', 'identity_mismatch'}:
            raise ValueError('Unknown binding lifecycle')
        with self.db:
            count = self.db.execute('''UPDATE task_bindings SET state=?,
                thread_id=COALESCE(?,thread_id), error_class=?, updated_at=?,
                evidence_json=COALESCE(?,evidence_json) WHERE request_key=?''',
                (state, thread_id, error_class, int(time.time()),
                 json.dumps(evidence, ensure_ascii=False) if evidence is not None else None, request_key)).rowcount
            if count != 1:
                raise RegistryError('Unknown creation request')
        return self.get(request_key)

    def list(self, limit=20, after=0, parent_id=None):
        if type(limit) is not int or not 1 <= limit <= 50 or type(after) is not int or after < 0:
            raise ValueError('Use limit 1–50 and a nonnegative ledger cursor')
        # Parent is one of a few small indexed specifications; filtering occurs before
        # LIMIT in SQLite, never by scanning arbitrary files or complete transcripts.
        sql = 'SELECT * FROM task_bindings WHERE ordinal>?'
        params = [after]
        if parent_id is not None:
            sql += " AND json_extract(spec_json, '$.parentThreadId')=?"
            params.append(parent_id)
        rows = self.db.execute(sql + ' ORDER BY ordinal LIMIT ?', params + [limit + 1]).fetchall()
        return {'data': [self.decode(row) for row in rows[:limit]],
                'nextCursor': rows[limit - 1]['ordinal'] if len(rows) > limit else None}
