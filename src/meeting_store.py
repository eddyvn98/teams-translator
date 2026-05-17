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
                CREATE TABLE IF NOT EXISTS meeting_sessions (
                    meeting_id TEXT PRIMARY KEY,
                    created_ts REAL NOT NULL,
                    display_name TEXT
                )
                """
            )
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

    def set_meeting(self, meeting_id: str):
        self.meeting_id = (meeting_id or "").strip() or self.meeting_id

    def register_session(
        self,
        meeting_id: str | None = None,
        created_ts: float | None = None,
        display_name: str | None = None,
    ):
        session_id = (meeting_id or self.meeting_id or "").strip()
        if not session_id:
            return
        created = float(created_ts if created_ts is not None else time.time())
        name = (display_name or "").strip() or f"Session {session_id}"
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO meeting_sessions (meeting_id, created_ts, display_name)
                    VALUES (?, ?, ?)
                    ON CONFLICT(meeting_id)
                    DO UPDATE SET
                        created_ts = MIN(meeting_sessions.created_ts, excluded.created_ts),
                        display_name = COALESCE(NULLIF(excluded.display_name, ''), meeting_sessions.display_name)
                    """,
                    (session_id, created, name),
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

    def get_transcripts_by_meeting(self, meeting_id: str, limit: int = 2000) -> List[Dict[str, str]]:
        mid = (meeting_id or "").strip()
        if not mid:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ts, source_lang, source_text, translated_text
                FROM transcripts
                WHERE meeting_id = ?
                ORDER BY ts ASC
                LIMIT ?
                """,
                (mid, int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_latest_summary_by_meeting(self, meeting_id: str) -> str:
        mid = (meeting_id or "").strip()
        if not mid:
            return ""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT summary_text
                FROM minute_summaries
                WHERE meeting_id = ?
                ORDER BY minute_index DESC
                LIMIT 1
                """,
                (mid,),
            ).fetchone()
        return (dict(row).get("summary_text", "") if row else "").strip()

    def list_sessions(self, limit: int = 100) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                WITH transcript_stats AS (
                    SELECT meeting_id, MIN(ts) AS first_ts, MAX(ts) AS last_ts, COUNT(*) AS transcript_count
                    FROM transcripts
                    GROUP BY meeting_id
                ),
                summary_stats AS (
                    SELECT meeting_id, COUNT(*) AS summary_count
                    FROM minute_summaries
                    GROUP BY meeting_id
                )
                SELECT
                    m.meeting_id AS meeting_id,
                    m.created_ts AS created_ts,
                    m.display_name AS display_name,
                    COALESCE(t.transcript_count, 0) AS transcript_count,
                    COALESCE(s.summary_count, 0) AS summary_count
                FROM meeting_sessions m
                LEFT JOIN transcript_stats t ON t.meeting_id = m.meeting_id
                LEFT JOIN summary_stats s ON s.meeting_id = m.meeting_id
                UNION
                SELECT
                    t.meeting_id AS meeting_id,
                    COALESCE(t.first_ts, strftime('%s','now')) AS created_ts,
                    '' AS display_name,
                    COALESCE(t.transcript_count, 0) AS transcript_count,
                    COALESCE(s.summary_count, 0) AS summary_count
                FROM transcript_stats t
                LEFT JOIN summary_stats s ON s.meeting_id = t.meeting_id
                WHERE t.meeting_id NOT IN (SELECT meeting_id FROM meeting_sessions)
                ORDER BY created_ts DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]
