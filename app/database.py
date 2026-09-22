from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sends (
                    date TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    event_count INTEGER NOT NULL,
                    image_path TEXT,
                    telegram_message_id TEXT,
                    data_hash TEXT NOT NULL
                )
                """
            )

    def get(self, day: str) -> sqlite3.Row | None:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM sends WHERE date = ?", (day,)).fetchone()

    def upsert(self, day: str, status: str, event_count: int, image_path: str, msg_id: str, data_hash: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sends(date, generated_at, status, event_count, image_path, telegram_message_id, data_hash)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(date) DO UPDATE SET
                    generated_at=excluded.generated_at,
                    status=excluded.status,
                    event_count=excluded.event_count,
                    image_path=excluded.image_path,
                    telegram_message_id=excluded.telegram_message_id,
                    data_hash=excluded.data_hash
                """,
                (day, datetime.utcnow().isoformat(), status, event_count, image_path, msg_id, data_hash),
            )


def events_hash(payload: list[dict]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
