"""
SQLite database wrapper and schema migrations
"""
import sqlite3
import os
from typing import Optional
from contextlib import contextmanager


DB_PATH = "queuectl.db"


def get_db_path() -> str:
    """Get the database file path"""
    return os.environ.get("QUEUECTL_DB_PATH", DB_PATH)


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection"""
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            locked_by TEXT,
            locked_at TEXT,
            last_error TEXT,
            run_after INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_state_run_after 
        ON jobs(state, run_after, created_at)
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    defaults = {
        "backoff_base": "2",
        "max_retries": "3",
        "worker_pids": ""
    }
    
    for key, value in defaults.items():
        cursor.execute("""
            INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()


def reset_db():
    """Reset database for testing purposes"""
    db_path = get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(db_path + "-wal"):
        os.remove(db_path + "-wal")
    if os.path.exists(db_path + "-shm"):
        os.remove(db_path + "-shm")
    init_db()
