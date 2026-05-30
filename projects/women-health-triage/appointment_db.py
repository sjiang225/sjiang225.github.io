from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Set, Tuple


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("APPOINTMENTS_DB", PROJECT_DIR / "appointments.sqlite3"))
BookedSlot = Tuple[str, str, str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                patient_name TEXT,
                patient_contact TEXT,
                symptom TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (doctor_name, appointment_date, appointment_time)
            )
            """
        )


def get_booked_slots() -> Set[BookedSlot]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT doctor_name, appointment_date, appointment_time
            FROM appointments
            """
        ).fetchall()
    return {(row["doctor_name"], row["appointment_date"], row["appointment_time"]) for row in rows}


def slot_key(doctor_name: str, appointment_date: str, appointment_time: str) -> BookedSlot:
    return (doctor_name, appointment_date, appointment_time)


def book_appointment(
    *,
    doctor_name: str,
    specialty: str,
    appointment_date: str,
    appointment_time: str,
    patient_name: str = "",
    patient_contact: str = "",
    symptom: str = "",
) -> bool:
    """
    Reserve a doctor/date/time slot.

    Returns False if another session has already booked the same slot.
    """
    init_db()
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO appointments (
                    doctor_name,
                    specialty,
                    appointment_date,
                    appointment_time,
                    patient_name,
                    patient_contact,
                    symptom,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doctor_name,
                    specialty,
                    appointment_date,
                    appointment_time,
                    patient_name,
                    patient_contact,
                    symptom,
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def list_appointments() -> Iterable[Dict[str, str]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT doctor_name, specialty, appointment_date, appointment_time,
                   patient_name, patient_contact, symptom, created_at
            FROM appointments
            ORDER BY appointment_date, appointment_time, doctor_name
            """
        ).fetchall()
    return [dict(row) for row in rows]
