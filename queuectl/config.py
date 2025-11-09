"""
Configuration management helpers
"""
from typing import Optional
from queuectl.db import get_db


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get configuration value by key"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def set_config(key: str, value: str):
    """Set configuration value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)
        """, (key, value))


def get_config_int(key: str, default: int) -> int:
    """Get configuration value as integer"""
    value = get_config(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_config_float(key: str, default: float) -> float:
    """Get configuration value as float"""
    value = get_config(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default
