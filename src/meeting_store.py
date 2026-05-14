import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Dict


class MeetingStore:
    """Persist transcripts and minute summaries for reliable context retrieval."""

    def __init__(self, base_dir: Path, meeting_id: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "meeting_data.db"
        self.meeting_id = meeting_id
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    ts REAL NOT NULL,
                    source_lang TEXT,
                    source_text TEXT,
                    translated_text TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS minute_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    minute_index INTEGER NOT NULL,
                    start_ts REAL NOT NULL,
                    end_ts REAL NOT NULL,
                    summary_text TEXT NOT NULL,
                    UNIQUE(meeting_id, minute_index)
                )
                """
            )
            conn.commit()

    def append_transcript(
        self,
        source_lang: str,
        source_text: str,
        translated_text: str,
        ts: float | None = None,
    ):
        now = ts if ts is not None else time.time()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO transcripts (meeting_id, ts, source_lang, source_text, translated_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.meeting_id, now, source_lang, source_text, translated_text),
                )
                conn.commit()

    def upsert_minute_summary(
        self,
        minute_index: int,
        start_ts: float,
        end_ts: float,
        summary_text: str,
    ):
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO minute_summaries (meeting_id, minute_index, start_ts, end_ts, summary_text)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(meeting_id, minute_index)
                    DO UPDATE SET end_ts=excluded.end_ts, summary_text=excluded.summary_text
                    """,
                    (self.meeting_id, minute_index, start_ts, end_ts, summary_text),
                )
                conn.commit()

    def get_recent_transcripts(self, limit: int = 120) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ts, source_lang, source_text, translated_text
                FROM transcripts
                WHERE meeting_id = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (self.meeting_id, int(limit)),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_recent_summaries(self, limit: int = 5) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT minute_index, start_ts, end_ts, summary_text
                FROM minute_summaries
                WHERE meeting_id = ?
                ORDER BY minute_index DESC
                LIMIT ?
                """,
                (self.meeting_id, int(limit)),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def get_transcript_range(self, start_ts: float, end_ts: float, limit: int = 200) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ts, source_lang, source_text, translated_text
                FROM transcripts
                WHERE meeting_id = ? AND ts >= ? AND ts < ?
                ORDER BY ts ASC
                LIMIT ?
                """,
                (self.meeting_id, float(start_ts), float(end_ts), int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]

