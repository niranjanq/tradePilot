from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TradeMemory:
    """Small durable memory layer for episodes, lessons, and aggregate stats."""

    def __init__(self, path: str = "data/tradepilot.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    trade_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    pnl REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source_trade_ids TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );
                """
            )

    def save_episode(self, trade: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO episodes(trade_id, created_at, asset, outcome, pnl, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    trade["trade_id"],
                    datetime.now(timezone.utc).isoformat(),
                    trade["asset"],
                    trade["outcome"],
                    trade["pnl"],
                    json.dumps(trade),
                ),
            )

    def add_lesson(self, lesson_id: str, lesson: str, confidence: float, source_trade_ids: list[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO lessons(lesson_id, created_at, lesson, confidence, source_trade_ids, active) VALUES (?, ?, ?, ?, ?, 1)",
                (
                    lesson_id,
                    datetime.now(timezone.utc).isoformat(),
                    lesson,
                    confidence,
                    json.dumps(source_trade_ids),
                ),
            )

    def retrieve(self, asset: str, limit: int = 10) -> dict[str, Any]:
        with self._connect() as conn:
            episodes = conn.execute(
                "SELECT payload FROM episodes WHERE asset = ? ORDER BY created_at DESC LIMIT ?",
                (asset, limit),
            ).fetchall()
            lessons = conn.execute(
                "SELECT lesson_id, lesson, confidence, source_trade_ids FROM lessons WHERE active = 1 ORDER BY confidence DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return {
            "episodes": [json.loads(row["payload"]) for row in episodes],
            "lessons": [
                {
                    "lesson_id": row["lesson_id"],
                    "lesson": row["lesson"],
                    "confidence": row["confidence"],
                    "source_trade_ids": json.loads(row["source_trade_ids"]),
                }
                for row in lessons
            ],
        }
