"""Tests for ingestion (parser + normalizer)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
from io import BytesIO

import pytest
from src.ingest.parser import parse_upload, detect_source_system, read_file
from src.ingest.normalizer import normalize_record, normalize_records, parse_date


class TestParser:
    def test_parse_csv_file(self, sample_csv_path):
        records, source = parse_upload(sample_csv_path)
        assert len(records) == 3
        assert source == "jira"
        assert records[0]["summary"] == "Login fails"

    def test_parse_csv_bytes(self, sample_csv_path):
        content = sample_csv_path.read_bytes()
        records, source = parse_upload(BytesIO(content), "test.csv", "jira")
        assert len(records) == 3

    def test_detect_jira(self, sample_csv_path):
        import pandas as pd
        df = pd.read_csv(sample_csv_path)
        assert detect_source_system(df) == "jira"

    def test_detect_generic(self, tmp_path):
        csv_file = tmp_path / "generic.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "summary", "description"])
            writer.writerow(["1", "Bug one", "Desc one"])
        import pandas as pd
        df = pd.read_csv(csv_file)
        assert detect_source_system(df) == "generic"

    def test_missing_summary_raises(self, tmp_path):
        csv_file = tmp_path / "bad.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "title"])
            writer.writerow(["1", "Something"])
        with pytest.raises(ValueError, match="Missing required column"):
            parse_upload(csv_file, source_system="generic")

    def test_auto_detect_source(self, sample_csv_path):
        records, source = parse_upload(sample_csv_path, source_system="auto")
        assert source == "jira"


class TestNormalizer:
    def test_normalize_record(self):
        record = {
            "summary": "  Test bug  ",
            "priority": "major",
            "severity": "CRITICAL",
            "created_date": "2025-01-15",
        }
        result = normalize_record(record)
        assert result["summary"] == "Test bug"
        assert result["priority"] == "Major"
        assert result["severity"] == "Critical"
        assert result["created_date"] is not None

    def test_normalize_empty(self):
        result = normalize_record({})
        assert result["summary"] == ""
        assert result["priority"] == "Medium"

    def test_parse_date_formats(self):
        assert parse_date("2025-01-15") is not None
        assert parse_date("2025-01-15T10:30:00") is not None
        assert parse_date("01/15/2025") is not None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_normalize_records_batch(self):
        records = [
            {"summary": "Bug 1", "priority": "high"},
            {"summary": "Bug 2", "priority": "low"},
        ]
        results = normalize_records(records)
        assert len(results) == 2
        assert results[0]["priority"] == "High"
        assert results[1]["priority"] == "Low"
