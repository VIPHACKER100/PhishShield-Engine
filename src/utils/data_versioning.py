"""
Data Versioning — Track and manage dataset versions for reproducibility.
"""

import json
import os
import shutil
from datetime import datetime, timezone
from src.utils.logger import logger

VERSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "versions")
METADATA_PATH = os.path.join(VERSIONS_DIR, "metadata.json")


def _load_metadata() -> list[dict]:
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH) as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return list(data.values()) if data else []
        except Exception:
            pass
    return []


def _save_metadata(entries: list[dict]):
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    with open(METADATA_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def register_version(
    source_path: str,
    version_tag: str | None = None,
    source_description: str = "unknown",
    preprocessing_steps: list[str] | None = None,
) -> dict:
    """
    Copy a dataset file into the versioned store and record metadata.

    Parameters
    ----------
    source_path : str
        Path to the dataset CSV to version.
    version_tag : str, optional
        A tag like "v1". Auto-generated if not provided.
    source_description : str
        Where the data came from.
    preprocessing_steps : list[str]
        Human-readable list of steps applied.

    Returns
    -------
    dict with version info.
    """
    import pandas as pd

    entries = _load_metadata()
    if version_tag is None:
        version_tag = f"v{len(entries) + 1}"

    dest_name = f"{version_tag}_emails.csv"
    dest_path = os.path.join(VERSIONS_DIR, dest_name)
    shutil.copy2(source_path, dest_path)

    df = pd.read_csv(dest_path)
    entry = {
        "version": version_tag,
        "filename": dest_name,
        "source": source_description,
        "date_added": datetime.now(timezone.utc).isoformat(),
        "num_samples": len(df),
        "columns": list(df.columns),
        "preprocessing_steps": preprocessing_steps or [],
    }
    entries.append(entry)
    _save_metadata(entries)
    logger.info("Registered dataset version %s (%d samples) → %s", version_tag, len(df), dest_path)
    return entry


def list_versions() -> list[dict]:
    """Return all registered dataset versions."""
    return _load_metadata()


def get_version_path(version_tag: str) -> str:
    """Return the file path for a specific dataset version."""
    entries = _load_metadata()
    for e in entries:
        if e["version"] == version_tag:
            return os.path.join(VERSIONS_DIR, e["filename"])
    raise ValueError(f"Dataset version '{version_tag}' not found")
