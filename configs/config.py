from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class DatabaseConfig:
    url: str = f"sqlite:///{BASE_DIR / 'data' / 'bug_analyzer.db'}"
    echo: bool = False


@dataclass
class MLConfig:
    tfidf_max_features: int = 250
    tfidf_ngram_range: tuple = (1, 2)
    duplicate_threshold: float = 0.92
    confidence_threshold: float = 0.60
    retrain_override_count: int = 50
    model_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "models")
    classification_labels: list = field(
        default_factory=lambda: ["valid", "invalid", "duplicate", "enhancement", "wont_fix"]
    )


@dataclass
class IngestConfig:
    jira_column_map: dict = field(default_factory=lambda: {
        "Issue key": "external_id",
        "Summary": "summary",
        "Description": "description",
        "Status": "status",
        "Priority": "priority",
        "Severity": "severity",
        "Component/s": "component",
        "Reporter": "reporter",
        "Assignee": "assignee",
        "Created": "created_date",
        "Resolved": "resolved_date",
        "Resolution": "resolution",
        "Labels": "labels",
        "Issue Type": "original_type",
    })
    azure_devops_column_map: dict = field(default_factory=lambda: {
        "ID": "external_id",
        "Title": "summary",
        "Repro Steps": "description",
        "State": "status",
        "Priority": "priority",
        "Severity": "severity",
        "Area Path": "component",
        "Created By": "reporter",
        "Assigned To": "assignee",
        "Created Date": "created_date",
        "Resolved Date": "resolved_date",
        "Resolved Reason": "resolution",
        "Tags": "labels",
        "Work Item Type": "original_type",
    })
    generic_column_map: dict = field(default_factory=lambda: {
        "id": "external_id",
        "summary": "summary",
        "description": "description",
        "status": "status",
        "priority": "priority",
        "severity": "severity",
        "component": "component",
        "reporter": "reporter",
        "assignee": "assignee",
        "created_date": "created_date",
        "resolved_date": "resolved_date",
        "resolution": "resolution",
        "labels": "labels",
        "type": "original_type",
    })


@dataclass
class AppConfig:
    title: str = "Bug Report Accuracy Analyzer"
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = True
    templates_dir: Path = field(default_factory=lambda: BASE_DIR / "templates")
    static_dir: Path = field(default_factory=lambda: BASE_DIR / "static")


@dataclass
class Config:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    app: AppConfig = field(default_factory=AppConfig)


config = Config()
