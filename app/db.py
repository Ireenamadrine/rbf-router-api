"""
SQLite database layer.
Handles storing routes and feedback. Swap DATABASE_URL to Postgres later
without changing the rest of the code.
"""
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional


class Database:
    """Thread-safe SQLite wrapper. One connection per thread."""

    def __init__(self, db_path: str = "rbf_router.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL;")
        return self._local.conn

    @contextmanager
    def cursor(self):
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def _init_schema(self) -> None:
        with self.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    request_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    user_id TEXT,
                    recommended_tier TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    fallback_tier TEXT NOT NULL,
                    routed_at TEXT NOT NULL,
                    embedding BLOB
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    tier_used TEXT NOT NULL,
                    succeeded INTEGER NOT NULL,
                    quality_score REAL,
                    created_at TEXT NOT NULL,
                    vrs REAL DEFAULT 0.0,
                    FOREIGN KEY (request_id) REFERENCES routes(request_id)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_request
                ON feedback(request_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_routes_user
                ON routes(user_id)
            """)

    def insert_route(self, request_id: str, query: str, user_id: Optional[str],
                     recommended_tier: str, confidence: float,
                     fallback_tier: str, embedding_bytes: Optional[bytes] = None) -> None:
        with self.cursor() as cur:
            cur.execute("""
                INSERT INTO routes
                (request_id, query, user_id, recommended_tier, confidence,
                 fallback_tier, routed_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (request_id, query, user_id, recommended_tier, confidence,
                  fallback_tier, datetime.utcnow().isoformat(), embedding_bytes))

    def insert_feedback(self, request_id: str, tier_used: str,
                        succeeded: bool, quality_score: Optional[float],
                        vrs: float = 0.0) -> None:
        with self.cursor() as cur:
            cur.execute("""
                INSERT INTO feedback
                (request_id, tier_used, succeeded, quality_score, created_at, vrs)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (request_id, tier_used, int(succeeded), quality_score,
                  datetime.utcnow().isoformat(), vrs))

    def count_routes(self) -> int:
        with self.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM routes")
            return cur.fetchone()["c"]

    def count_feedback(self) -> int:
        with self.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM feedback")
            return cur.fetchone()["c"]

    def get_all_routes_with_feedback(self) -> list[dict[str, Any]]:
        """Returns routes joined with their feedback for training."""
        with self.cursor() as cur:
            cur.execute("""
                SELECT r.request_id, r.query, r.embedding,
                       r.recommended_tier, r.confidence,
                       f.tier_used, f.succeeded, f.quality_score, f.vrs
                FROM routes r
                JOIN feedback f ON f.request_id = r.request_id
                ORDER BY f.created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]

    def get_stats(self) -> dict[str, Any]:
        with self.cursor() as cur:
            cur.execute("SELECT recommended_tier, COUNT(*) AS c FROM routes GROUP BY recommended_tier")
            tier_dist = {row["recommended_tier"]: row["c"] for row in cur.fetchall()}

            cur.execute("""
                SELECT r.recommended_tier AS tier_used,
                       AVG(CASE WHEN r.recommended_tier = f.tier_used THEN 1.0 ELSE 0.0 END) AS acc,
                       COUNT(*) AS c
                FROM routes r JOIN feedback f ON f.request_id = r.request_id
                GROUP BY r.recommended_tier
            """)
            accuracy = {row["tier_used"]: float(row["acc"] or 0.0) for row in cur.fetchall()}

            cur.execute("SELECT AVG(confidence) AS avg_conf FROM routes")
            avg_conf = cur.fetchone()["avg_conf"] or 0.0

            return {
                "tier_distribution": tier_dist,
                "accuracy_by_tier": accuracy,
                "avg_confidence": float(avg_conf),
            }


_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(os.getenv("DATABASE_PATH", "rbf_router.db"))
    return _db