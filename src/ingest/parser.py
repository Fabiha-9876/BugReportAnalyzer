"""Parse CSV and Excel files into normalized bug report dicts."""
from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd

from configs.config import config


COLUMN_MAPS = {
    "jira": config.ingest.jira_column_map,
    "azure_devops": config.ingest.azure_devops_column_map,
    "generic": config.ingest.generic_column_map,
}


def read_file(file_source: Union[str, Path, BytesIO], filename: str = "") -> pd.DataFrame:
    if isinstance(file_source, (str, Path)):
        path = Path(file_source)
        filename = filename or path.name
    else:
        path = None

    ext = Path(filename).suffix.lower() if filename else ""

    if ext in (".xlsx", ".xls"):
        if path:
            return pd.read_excel(path, engine="openpyxl")
        return pd.read_excel(file_source, engine="openpyxl")
    else:
        if path:
            return pd.read_csv(path)
        return pd.read_csv(file_source)


def detect_source_system(df: pd.DataFrame) -> str:
    columns = set(df.columns)
    jira_markers = {"Issue key", "Summary", "Issue Type"}
    azure_markers = {"ID", "Title", "Work Item Type"}

    if jira_markers.issubset(columns):
        return "jira"
    if azure_markers.issubset(columns):
        return "azure_devops"
    return "generic"


def map_columns(df: pd.DataFrame, source_system: str) -> pd.DataFrame:
    col_map = COLUMN_MAPS.get(source_system, COLUMN_MAPS["generic"])
    rename = {}
    for src_col, target_col in col_map.items():
        if src_col in df.columns:
            rename[src_col] = target_col
    df = df.rename(columns=rename)
    return df


def parse_upload(
    file_source: Union[str, Path, BytesIO],
    filename: str = "",
    source_system: str = "auto",
) -> list[dict]:
    df = read_file(file_source, filename)
    df = df.fillna("")

    if source_system == "auto":
        source_system = detect_source_system(df)

    df = map_columns(df, source_system)

    required = ["summary"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column after mapping: '{col}'")

    records = df.to_dict("records")
    return records, source_system
