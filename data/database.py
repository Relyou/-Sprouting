"""SQLite 业务数据管理"""

import os
import sqlite3
import shutil
import threading
from datetime import datetime
from config import APP_DATA_DIR, MAX_BACKUPS

DB_PATH = os.path.join(APP_DATA_DIR, "data.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule_labels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    color       TEXT    NOT NULL DEFAULT '#3B82F6',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS schedule_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    refresh_type TEXT   NOT NULL CHECK(refresh_type IN ('daily','weekly','monthly')),
    refresh_interval INTEGER NOT NULL DEFAULT 1,
    target_count INTEGER NOT NULL DEFAULT 1 CHECK(target_count BETWEEN 1 AND 127),
    current_count INTEGER NOT NULL DEFAULT 0,
    mark_icon   TEXT    DEFAULT '★',
    mark_color  TEXT    DEFAULT '#3B82F6',
    label_id    INTEGER,
    description TEXT    DEFAULT '',
    timer_minutes INTEGER,
    max_completions INTEGER,
    is_archived  INTEGER NOT NULL DEFAULT 0,
    is_completed INTEGER NOT NULL DEFAULT 0,
    reset_date  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS schedule_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL,
    done_date   TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (item_id) REFERENCES schedule_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS todo_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    due_date    TEXT,
    remind_time TEXT,
    importance  INTEGER NOT NULL DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
    urgency     INTEGER NOT NULL DEFAULT 3 CHECK(urgency BETWEEN 1 AND 5),
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_schedule_updated ON schedule_items(updated_at);
CREATE INDEX IF NOT EXISTS idx_schedule_logs_date ON schedule_logs(done_date);
CREATE INDEX IF NOT EXISTS idx_schedule_labels_name ON schedule_labels(name);
CREATE INDEX IF NOT EXISTS idx_todo_due ON todo_items(due_date);
CREATE INDEX IF NOT EXISTS idx_todo_urgency ON todo_items(urgency);
"""


class DatabaseManager:
    def __init__(self, path: str = DB_PATH):
        self._path = path
        self._local = threading.local()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self._local.conn = sqlite3.connect(self._path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def init_db(self):
        self._conn.executescript(_SCHEMA)
        self._migrate()
        self._conn.commit()

    def _migrate(self):
        """向前兼容：为旧数据库添加新增列"""
        migrations = [
            "ALTER TABLE schedule_items ADD COLUMN reset_date TEXT NOT NULL DEFAULT (datetime('now','localtime'))",
            "ALTER TABLE schedule_items ADD COLUMN label_id INTEGER",
            "ALTER TABLE schedule_items ADD COLUMN description TEXT DEFAULT ''",
            "ALTER TABLE schedule_items ADD COLUMN timer_minutes INTEGER",
            "ALTER TABLE schedule_items ADD COLUMN max_completions INTEGER",
            "ALTER TABLE schedule_items ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0",
        ]
        for sql in migrations:
            try:
                self._conn.execute(sql)
            except sqlite3.OperationalError:
                pass  # 列已存在
        # 确保 labels 表存在（旧数据库可能没有，用 executescript 处理 datetime 默认值约束）
        try:
            self._conn.executescript(
                """CREATE TABLE IF NOT EXISTS schedule_labels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT NOT NULL DEFAULT '#3B82F6',
                    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                );"""
            )
        except sqlite3.OperationalError:
            pass

    # ── 通用操作 ──
    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def commit(self):
        self._conn.commit()

    def fetch_one(self, sql: str, params=()):
        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        if row is None:
            return None
        return dict(zip([d[0] for d in cur.description], row))

    def fetch_all(self, sql: str, params=()) -> list[dict]:
        cur = self._conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ── 数据变更 ──
    def insert(self, sql: str, params=()) -> int:
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.lastrowid

    def update(self, sql: str, params=()):
        self._conn.execute(sql, params)
        self._conn.commit()

    def delete(self, sql: str, params=()):
        self._conn.execute(sql, params)
        self._conn.commit()

    # ── 备份 ──
    def backup(self):
        backup_dir = os.path.join(APP_DATA_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
        shutil.copy2(self._path, backup_path)

        # 滚动清理旧备份
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".db")],
            reverse=True,
        )
        for old in backups[MAX_BACKUPS:]:
            os.remove(os.path.join(backup_dir, old))

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
