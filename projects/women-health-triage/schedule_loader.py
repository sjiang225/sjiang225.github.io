from __future__ import annotations

from io import BytesIO
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLINIC_DAY_START = os.getenv("CLINIC_DAY_START", "09:00")
CLINIC_DAY_END = os.getenv("CLINIC_DAY_END", "17:00")

FALSE_TOKENS = {"", "0", "n", "no", "false", "na", "n/a", "none", "nan", "unavailable", "off"}
TRUE_TOKENS = {"1", "y", "yes", "true", "available", "avail", "ok", "x"}

SPECIALTY_ALIASES = {
    "maternal_fetal": ["maternal", "fetal", "high-risk", "high risk", "mfm"],
    "urogynecology": ["urogynecology", "urogyne", "pelvic floor", "pelvic reconstructive", "reconstructive pelvic"],
    "gynecologic_oncology": ["oncology", "oncologic", "cancer"],
    "reproductive_endo": ["reproductive", "endocrinology", "infertility", "rei"],
    "minimally_invasive": ["minimally invasive", "complex surgery", "migs", "endometriosis", "fibroid"],
    "general_obgyn": ["general", "ob/gyn", "obgyn", "gynecology", "obstetrics"],
    "emergency": ["emergency", "er"],
}

INSURANCE_ALIASES = {
    "aetna": ["aetna"],
    "uhc": ["uhc", "united", "unitedhealthcare", "united healthcare"],
    "bcbs": ["bcbs", "blue cross", "blue shield", "bluecross", "blueshield"],
    "cigna": ["cigna"],
    "medicare": ["medicare"],
    "medicaid": ["medicaid"],
}


def _hourly_slots(start: str = CLINIC_DAY_START, end: str = CLINIC_DAY_END) -> List[str]:
    """Return one-hour appointment start times from start up to, but not including, end."""
    try:
        current = datetime.strptime(start, "%H:%M")
        closing = datetime.strptime(end, "%H:%M")
    except ValueError:
        current = datetime.strptime("09:00", "%H:%M")
        closing = datetime.strptime("17:00", "%H:%M")

    slots = []
    while current < closing:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(hours=1)
    return slots


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _split_values(value: Any) -> List[str]:
    text = _clean_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;/|]+", text) if part.strip()]


def _find_column(columns: Iterable[str], aliases: Iterable[str]) -> Optional[str]:
    normalized = {str(col).strip().lower(): col for col in columns}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    for col in columns:
        col_l = str(col).strip().lower()
        if any(alias.lower() in col_l for alias in aliases):
            return col
    return None


def _normalize_day(value: Any) -> Optional[str]:
    text = _clean_text(value).lower()
    if not text:
        return None
    day_lookup = {
        "mon": "Mon",
        "monday": "Mon",
        "tue": "Tue",
        "tues": "Tue",
        "tuesday": "Tue",
        "wed": "Wed",
        "wednesday": "Wed",
        "thu": "Thu",
        "thur": "Thu",
        "thurs": "Thu",
        "thursday": "Thu",
        "fri": "Fri",
        "friday": "Fri",
        "sat": "Sat",
        "saturday": "Sat",
        "sun": "Sun",
        "sunday": "Sun",
    }
    return day_lookup.get(text[:3], day_lookup.get(text))


def _is_available_token(value: Any) -> bool:
    text = _clean_text(value).lower()
    if text in FALSE_TOKENS:
        return False
    if text in TRUE_TOKENS:
        return True
    return bool(text)


def _normalize_time(hour: str, minute: Optional[str], meridiem: Optional[str]) -> str:
    hh = int(hour)
    mm = int(minute or 0)
    marker = (meridiem or "").lower()
    if marker == "pm" and hh < 12:
        hh += 12
    if marker == "am" and hh == 12:
        hh = 0
    if 7 <= hh <= 20 and 0 <= mm <= 59:
        return f"{hh:02d}:{mm:02d}"
    return ""


def _parse_times(value: Any) -> List[str]:
    text = _clean_text(value)
    if not text or text.lower() in FALSE_TOKENS:
        return []
    if text.lower() in TRUE_TOKENS:
        return _hourly_slots()

    times: List[str] = []
    for match in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text, re.I):
        normalized = _normalize_time(match.group(1), match.group(2), match.group(3))
        if normalized:
            times.append(normalized)

    seen = set()
    ordered = []
    for time_value in times:
        if time_value not in seen:
            seen.add(time_value)
            ordered.append(time_value)
    return ordered or (_hourly_slots() if _is_available_token(value) else [])


def _normalize_specialties(value: Any) -> List[str]:
    parts = _split_values(value)
    text = " ".join(parts).lower() if parts else _clean_text(value).lower()
    if not text:
        return ["general_obgyn"]

    codes = []
    for code, aliases in SPECIALTY_ALIASES.items():
        if any(alias in text for alias in aliases):
            codes.append(code)

    if "maternal_fetal" in codes and "general_obgyn" in codes:
        codes.remove("general_obgyn")
    return codes or ["general_obgyn"]


def _normalize_insurances(value: Any) -> List[str]:
    raw_parts = _split_values(value)
    if not raw_parts:
        return []

    normalized = []
    for part in raw_parts:
        part_l = part.lower()
        matched = None
        for code, aliases in INSURANCE_ALIASES.items():
            if any(alias in part_l for alias in aliases):
                matched = code
                break
        normalized.append(matched or part_l)
    return sorted(set(normalized))


def _build_doctor(
    name: Any,
    specialty: Any,
    insurance: Any,
    schedule: Dict[str, List[str]],
) -> Optional[Dict[str, Any]]:
    doctor_name = _clean_text(name)
    if not doctor_name:
        return None

    clean_schedule = {
        day: sorted(set(times))
        for day, times in schedule.items()
        if day in WEEKDAYS and times
    }

    return {
        "name": doctor_name,
        "subspecialties": _normalize_specialties(specialty),
        "insurances": _normalize_insurances(insurance),
        "schedule": clean_schedule,
    }


def _parse_wide_schedule(df: pd.DataFrame) -> List[Dict[str, Any]]:
    doctor_col = _find_column(df.columns, ["Doctor", "Provider", "Physician", "MD", "Name"])
    specialty_col = _find_column(df.columns, ["Specialty", "Subspecialty", "Department"])
    insurance_col = _find_column(df.columns, ["Insurance", "Insurances", "Payer", "Accepted Insurance"])
    day_cols = [(col, _normalize_day(col)) for col in df.columns]
    day_cols = [(col, day) for col, day in day_cols if day in WEEKDAYS]

    if not doctor_col or not day_cols:
        return []

    doctors = []
    for _, row in df.iterrows():
        schedule: Dict[str, List[str]] = {}
        for col, day in day_cols:
            times = _parse_times(row.get(col))
            if times:
                schedule.setdefault(day, []).extend(times)

        doctor = _build_doctor(
            row.get(doctor_col),
            row.get(specialty_col) if specialty_col else "General OB/GYN",
            row.get(insurance_col) if insurance_col else "",
            schedule,
        )
        if doctor:
            doctors.append(doctor)
    return doctors


def _parse_long_schedule(df: pd.DataFrame) -> List[Dict[str, Any]]:
    doctor_col = _find_column(df.columns, ["Doctor", "Provider", "Physician", "MD", "Name"])
    specialty_col = _find_column(df.columns, ["Specialty", "Subspecialty", "Department"])
    insurance_col = _find_column(df.columns, ["Insurance", "Insurances", "Payer", "Accepted Insurance"])
    day_col = _find_column(df.columns, ["Day", "Weekday"])
    time_col = _find_column(df.columns, ["Time", "Times", "Slot", "Slots", "Available Time"])
    available_col = _find_column(df.columns, ["Available", "Availability"])

    if not doctor_col or not day_col:
        return []

    grouped: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        name = _clean_text(row.get(doctor_col))
        day = _normalize_day(row.get(day_col))
        if not name or day not in WEEKDAYS:
            continue

        if time_col:
            times = _parse_times(row.get(time_col))
        elif available_col:
            times = _parse_times(row.get(available_col))
        else:
            times = _hourly_slots()

        if not times:
            continue

        item = grouped.setdefault(
            name,
            {
                "name": name,
                "subspecialties": _normalize_specialties(row.get(specialty_col) if specialty_col else "General OB/GYN"),
                "insurances": _normalize_insurances(row.get(insurance_col) if insurance_col else ""),
                "schedule": {},
            },
        )
        item["schedule"].setdefault(day, []).extend(times)

    doctors = []
    for item in grouped.values():
        item["schedule"] = {day: sorted(set(times)) for day, times in item["schedule"].items()}
        doctors.append(item)
    return doctors


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward-compatible helper that converts a supported schedule sheet into
    long rows with Doctor, Specialty, Day, Time, and Available columns.
    """
    df = df.rename(columns={col: str(col).strip() for col in df.columns})
    doctors = _parse_long_schedule(df) or _parse_wide_schedule(df)
    rows = []
    for doctor in doctors:
        specialty = ",".join(doctor.get("subspecialties", []))
        for day, times in doctor.get("schedule", {}).items():
            for time_value in times:
                rows.append(
                    {
                        "Doctor": doctor["name"],
                        "Specialty": specialty,
                        "Day": day,
                        "Time": time_value,
                        "Available": True,
                    }
                )
    if not rows:
        raise ValueError("Unrecognized schedule format.")
    return pd.DataFrame(rows)


def _excel_source(source: Any) -> Any:
    if isinstance(source, (bytes, bytearray)):
        return BytesIO(source)
    return source


def load_schedule(xlsx_source: Any) -> Dict[str, Any]:
    """
    Load an uploaded schedule into the structure expected by triage_agent.

    Supported formats:
    - Wide: Doctor, Specialty, optional Insurance, Mon, Tue, Wed...
      Day cells may contain Y/Yes/Available or concrete times. Y/Yes/Available
      means the whole clinic day is available and expands into one-hour slots
      from CLINIC_DAY_START to CLINIC_DAY_END.
    - Long: Doctor, Specialty, optional Insurance, Day, optional Time/Available.

    If no insurance column is present, the doctor is treated as accepting any
    insurance for matching purposes because the schedule does not provide payer
    restrictions.
    """
    excel = pd.ExcelFile(_excel_source(xlsx_source))
    doctors: List[Dict[str, Any]] = []

    for sheet_name in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet_name)
        df = df.dropna(how="all")
        if df.empty:
            continue
        df = df.rename(columns={col: str(col).strip() for col in df.columns})
        doctors.extend(_parse_long_schedule(df) or _parse_wide_schedule(df))

    if not doctors:
        raise ValueError(
            "Unrecognized schedule format. Expected columns like Doctor, Specialty, Mon/Tue... "
            "or Doctor, Specialty, Day, Time."
        )

    return {"doctors": doctors}
