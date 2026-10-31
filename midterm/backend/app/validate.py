import re
from datetime import date, datetime, timedelta, timezone


def today_utc():
    return datetime.now(timezone.utc).date().isoformat()


def add_days(iso_date, days):
    year, month, day = (int(part) for part in iso_date.split("-"))
    shifted = date(year, month, day) + timedelta(days=days)
    return shifted.isoformat()


def parse_id(value):
    if not re.fullmatch(r"[1-9]\d*", str(value)):
        return None
    return int(value)


def parse_iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    if parsed.isoformat() != value:
        return None
    return value


def clean_text(value, max_length):
    if value is None:
        return None, None
    if not isinstance(value, str):
        return "invalid", None
    trimmed = value.strip()
    if not trimmed:
        return None, None
    if len(trimmed) > max_length:
        return "invalid", None
    return None, trimmed


def resolve_as_of(value):
    if value is None or value == "":
        return today_utc()
    parsed = parse_iso_date(value)
    if parsed is None:
        return None
    latest = add_days(today_utc(), 1)
    if parsed < "2000-01-01" or parsed > latest:
        return None
    return parsed
