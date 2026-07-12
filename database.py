"""
database.py
───────────
SQLite database initialisation for VenturePilot AI.

Creates the `users` table on first run.  Safe to call multiple times —
uses CREATE TABLE IF NOT EXISTS so it never overwrites existing data.
"""

import sqlite3
import os

# Path to the SQLite database file (next to app.py)
DB_PATH = os.path.join(os.path.dirname(__file__), "venturepilot.db")


def get_connection() -> sqlite3.Connection:
    """Return a new connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create all required tables if they do not already exist.
    Called once at application startup from app.py.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            startup_name   TEXT    NOT NULL,
            industry       TEXT    NOT NULL,
            business_stage TEXT    NOT NULL,
            report_data    TEXT    NOT NULL,
            created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialised.")


if __name__ == "__main__":
    init_db()
    print(f"[DB] Database file: {DB_PATH}")
