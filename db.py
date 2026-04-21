import sqlite3
import json
from pathlib import Path

DB_PATH = Path("activity_tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def add_entry(entry_date, activity_name, activity_type, start_time, end_time, duration_minutes):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO entries (
            entry_date, activity_name, activity_type, start_time, end_time, duration_minutes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entry_date, activity_name, activity_type, start_time, end_time, duration_minutes),
    )

    conn.commit()
    conn.close()


def get_entries_by_date(entry_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM entries
        WHERE entry_date = ?
        ORDER BY start_time
        """,
        (entry_date,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_entries():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM entries
        ORDER BY entry_date DESC, start_time ASC
        """
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def delete_entry(entry_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

    conn.commit()
    conn.close()


def get_recent_activities(limit=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT activity_name, activity_type, MAX(entry_date || ' ' || start_time) AS last_used
        FROM entries
        GROUP BY activity_name, activity_type
        ORDER BY last_used DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------------------
# CURRENT NOTES BOARD
# ----------------------------

def init_notes_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS current_notes (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            notes_json TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        INSERT OR IGNORE INTO current_notes (id, notes_json)
        VALUES (1, '[]')
        """
    )

    conn.commit()
    conn.close()


def get_notes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT notes_json FROM current_notes WHERE id = 1"
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return []

    try:
        return json.loads(row["notes_json"])
    except Exception:
        return []


def save_notes(notes_list):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE current_notes
        SET notes_json = ?
        WHERE id = 1
        """,
        (json.dumps(notes_list),)
    )

    conn.commit()
    conn.close()