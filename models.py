"""
models.py
─────────
Data-access layer for the users table.
All database interaction goes through these functions — auth.py and app.py
never call sqlite3 directly.
"""

from database import get_connection


def create_user(full_name: str, email: str, password_hash: str) -> int:
    """
    Insert a new user row and return the new user's id.

    Raises sqlite3.IntegrityError if the email already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
        (full_name.strip(), email.strip().lower(), password_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str):
    """
    Return the user row for the given email, or None if not found.
    The row is a sqlite3.Row — access fields by name: row['id'], row['full_name'] …
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.strip().lower(),),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    """Return the user row for the given id, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_user_name(user_id: int, full_name: str) -> None:
    """Update the full_name of an existing user."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET full_name = ? WHERE id = ?",
        (full_name.strip(), user_id),
    )
    conn.commit()
    conn.close()


def update_user_password(user_id: int, password_hash: str) -> None:
    """Replace the password hash for the given user."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    conn.commit()
    conn.close()


def email_exists(email: str) -> bool:
    """Return True if the email is already registered."""
    return get_user_by_email(email) is not None


# ── Reports ───────────────────────────────────────────────────────────────────

def save_report(user_id: int, startup_name: str, industry: str,
                business_stage: str, report_data: str) -> int:
    """Insert a new report row and return its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO reports (user_id, startup_name, industry, business_stage, report_data)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, startup_name.strip(), industry.strip(), business_stage.strip(), report_data),
    )
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id


def get_reports_by_user(user_id: int):
    """Return all reports for the given user, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_report_by_id(report_id: int):
    """Return the report row for the given id, or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def delete_report(report_id: int, user_id: int) -> bool:
    """
    Delete the report only if it belongs to user_id.
    Returns True if a row was deleted, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM reports WHERE id = ? AND user_id = ?",
        (report_id, user_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
