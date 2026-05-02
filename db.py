import json
import psycopg2
import psycopg2.extras
import streamlit as st


def get_connection():
    return psycopg2.connect(st.secrets["SUPABASE_DB_URL"])


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id BIGSERIAL PRIMARY KEY,
            entry_date DATE NOT NULL,
            activity_name TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def add_entry(entry_date, activity_name, activity_type, start_time, end_time, duration_minutes):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO entries (
            entry_date, activity_name, activity_type, start_time, end_time, duration_minutes
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (entry_date, activity_name, activity_type, start_time, end_time, duration_minutes),
    )

    conn.commit()
    cur.close()
    conn.close()


def get_entries_by_date(entry_date):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        SELECT *
        FROM entries
        WHERE entry_date = %s
        ORDER BY start_time
        """,
        (entry_date,),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_all_entries():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        SELECT *
        FROM entries
        ORDER BY entry_date DESC, start_time ASC
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_entry(entry_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM entries WHERE id = %s", (entry_id,))

    conn.commit()
    cur.close()
    conn.close()


def get_recent_activities(limit=10):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        SELECT activity_name, activity_type, MAX(entry_date::text || ' ' || start_time) AS last_used
        FROM entries
        GROUP BY activity_name, activity_type
        ORDER BY last_used DESC
        LIMIT %s
        """,
        (limit,),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_latest_entry_by_date(entry_date):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        SELECT *
        FROM entries
        WHERE entry_date = %s
        ORDER BY end_time DESC
        LIMIT 1
        """,
        (entry_date,),
    )

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


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
        INSERT INTO current_notes (id, notes_json)
        VALUES (1, '[]')
        ON CONFLICT (id) DO NOTHING
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def get_notes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT notes_json FROM current_notes WHERE id = 1")
    row = cur.fetchone()

    cur.close()
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
        SET notes_json = %s
        WHERE id = 1
        """,
        (json.dumps(notes_list),),
    )

    conn.commit()
    cur.close()
    conn.close()
