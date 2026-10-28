"""File loading.

Loaders return a Dataset rather than raising, so a missing or malformed file
degrades one panel instead of the app. Caching is keyed on path + mtime + size,
so rerunning a research script refreshes the dashboard without a restart.

Read-only. This module opens files; it never writes to data/ or results/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from core import schema


@dataclass
class Dataset:
    ok: bool
    df: pd.DataFrame | None
    spec: schema.FileSpec
    reason: str = ""
    detail: str = ""
    metrics: dict[str, str] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.ok


def _stamp(path: Path) -> tuple[float, int]:
    try:
        s = path.stat()
        return (s.st_mtime, s.st_size)
    except OSError:
        return (0.0, -1)


@st.cache_data(show_spinner=False)
def _read_csv(path_str: str, stamp: tuple[float, int]) -> pd.DataFrame:
    # `stamp` is unused in the body by design: it invalidates the cache when
    # the underlying file changes on disk.
    return pd.read_csv(path_str)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(config.ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def resolve_metrics(df: pd.DataFrame) -> dict[str, str]:
    """Map canonical metric names to the column spellings actually present.

    Metric headers vary between exports (sMAPE_percent vs sMAPE, R2 vs R^2),
    so the dashboard resolves them rather than assuming one spelling.
    """
    found: dict[str, str] = {}
    lower = {str(c).lower(): c for c in df.columns}
    for canon, aliases in config.METRIC_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                found[canon] = alias
                break
            if alias.lower() in lower:
                found[canon] = lower[alias.lower()]
                break
    return found


def _parse_times(df: pd.DataFrame, spec: schema.FileSpec) -> pd.DataFrame:
    """Parse timestamps UTC-first.

    Local files carry offsets that change across DST. Parsing them directly
    makes pandas fall back to an object dtype, which breaks every downstream
    .dt accessor. Parsing as UTC first and converting afterwards avoids that.
    """
    for col in spec.time_cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], utc=True, errors="coerce")
        if not spec.utc:
            parsed = parsed.dt.tz_convert(config.TZ_LOCAL)
        df[col] = parsed
    return df


def load(key: str) -> Dataset:
    spec = schema.spec(key)
    path = spec.path

    if not path.exists():
        return Dataset(False, None, spec, "missing",
                       f"Expected at {rel(path)}")

    try:
        df = _read_csv(str(path), _stamp(path)).copy()
    except Exception as exc:  # noqa: BLE001
        return Dataset(False, None, spec, "error",
                       f"Could not read {rel(path)}: {exc}")

    missing = schema.missing_columns(df.columns, spec.required)
    if missing:
        return Dataset(
            False, None, spec, "columns",
            f"{rel(path)} is missing "
            f"{'column' if len(missing) == 1 else 'columns'}: "
            f"{', '.join(missing)}. Found: {', '.join(map(str, df.columns))}",
        )

    if df.empty:
        return Dataset(False, None, spec, "empty",
                       f"{rel(path)} has headers but no rows.")

    df = _parse_times(df, spec)
    return Dataset(True, df, spec, metrics=resolve_metrics(df))


# --------------------------------------------------------------------------
# Directory helpers
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _listdir(path_str: str, stamp: tuple[float, int],
             patterns: tuple[str, ...]) -> list[str]:
    base = Path(path_str)
    out: list[str] = []
    for pattern in patterns:
        out.extend(sorted(str(p) for p in base.glob(pattern)))
    return out


def list_files(key: str, patterns: tuple[str, ...]) -> list[Path]:
    """List files in a declared directory. Empty list when absent."""
    base, _ = schema.DIRECTORIES[key]
    if not base.exists():
        return []
    return [Path(p) for p in _listdir(str(base), _stamp(base), patterns)]


def directory_label(key: str) -> str:
    return schema.DIRECTORIES[key][1]


def directory_path(key: str) -> Path:
    return schema.DIRECTORIES[key][0]


# --------------------------------------------------------------------------
# Model naming
# --------------------------------------------------------------------------
def model_key(name: object) -> str:
    """Normalise for colour lookup only. Display always uses the stored name."""
    return (str(name).strip().lower()
            .replace("+", " ").replace("-", "_")
            .replace("  ", " ").strip().replace(" ", "_"))


def model_color(name: object, index: int = 0) -> str:
    key = model_key(name)
    if key in config.MODEL_COLORS:
        return config.MODEL_COLORS[key]
    for known, colour in config.MODEL_COLORS.items():
        if known in key or key in known:
            return colour
    return config.FALLBACK_CYCLE[index % len(config.FALLBACK_CYCLE)]


def model_column(df: pd.DataFrame) -> str | None:
    """Metric files use 'Model'; prediction files use 'model'."""
    for candidate in ("Model", "model"):
        if candidate in df.columns:
            return candidate
    for col in df.columns:
        if str(col).strip().lower() == "model":
            return col
    return None


def sorted_models(df: pd.DataFrame) -> list[str]:
    """Alphabetical. Never ordered by performance."""
    col = model_column(df)
    if col is None:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())


def feature_value_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Detect the feature-name and value columns of an importance table.

    Explainability exports have no confirmed headers, so the first non-numeric
    column is treated as the feature name and the first numeric column as the
    value.
    """
    feature_col = None
    value_col = None
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if value_col is None:
                value_col = col
        elif feature_col is None:
            feature_col = col
    if feature_col is None and len(df.columns):
        feature_col = df.columns[0]
    return feature_col, value_col


# --------------------------------------------------------------------------
# Status
# --------------------------------------------------------------------------
def availability() -> pd.DataFrame:
    rows = []
    for key, spec in schema.SPECS.items():
        ds = load(key)
        rows.append({
            "Artefact": spec.label,
            "Path": rel(spec.path),
            "Status": "Available" if ds.ok else ds.reason.title(),
            # Kept as text so the column has one dtype: mixing ints and
            # strings here makes Arrow serialisation fall back noisily.
            "Rows": f"{len(ds.df):,}" if ds.ok and ds.df is not None else "\u2014",
            "Produced by": spec.produced_by,
        })
    for key, (path, label) in schema.DIRECTORIES.items():
        files = list_files(key, ("*.csv", "*.png"))
        rows.append({
            "Artefact": label,
            "Path": rel(path) + "/",
            "Status": "Available" if files else "Missing",
            "Rows": f"{len(files)} files" if files else "\u2014",
            "Produced by": "the research pipeline",
        })
    return pd.DataFrame(rows)
