"""Normalize parsed bug report fields."""
from datetime import datetime


VALID_PRIORITIES = {"blocker", "critical", "major", "minor", "trivial", "high", "medium", "low"}
VALID_SEVERITIES = {"critical", "major", "minor", "trivial", "high", "medium", "low", "s1", "s2", "s3", "s4"}

BUG_REPORT_FIELDS = {
    "external_id", "summary", "description", "status", "priority", "severity",
    "component", "reporter", "assignee", "created_date", "resolved_date",
    "resolution", "labels", "original_type",
}


def normalize_string(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_priority(value) -> str:
    s = normalize_string(value).lower()
    if s in VALID_PRIORITIES:
        return s.capitalize()
    return normalize_string(value) or "Medium"


def normalize_severity(value) -> str:
    s = normalize_string(value).lower()
    if s in VALID_SEVERITIES:
        return s.capitalize()
    return normalize_string(value) or "Medium"


def parse_date(value) -> datetime | None:
    if not value or str(value).strip() == "":
        return None
    s = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def normalize_record(record: dict) -> dict:
    normalized = {}
    for field in BUG_REPORT_FIELDS:
        value = record.get(field, "")
        if field == "priority":
            normalized[field] = normalize_priority(value)
        elif field == "severity":
            normalized[field] = normalize_severity(value)
        elif field in ("created_date", "resolved_date"):
            normalized[field] = parse_date(value)
        elif field == "labels":
            normalized[field] = normalize_string(value)
        else:
            normalized[field] = normalize_string(value)
    return normalized


def normalize_records(records: list[dict]) -> list[dict]:
    return [normalize_record(r) for r in records]
