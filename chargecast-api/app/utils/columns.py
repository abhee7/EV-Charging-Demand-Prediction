"""Runtime column resolution.

Several audited artefacts have schemas this service has not inspected. Rather
than assume header names, resolvers match at load time against candidate
spellings. Two rules hold throughout:

* a column that cannot be resolved is reported absent, never invented
* the full stored table is always available, so nothing is hidden by a failed
  resolution
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

# Containment matching below this length produces false positives: a header
# named "N" would otherwise satisfy a candidate such as "criterion".
MIN_CONTAINMENT_LEN = 3


def normalise(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def find(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    if df is None or not len(df.columns):
        return None
    cols = list(df.columns)

    for candidate in candidates:
        if candidate in cols:
            return candidate

    normalised = {normalise(c): c for c in cols}
    for candidate in candidates:
        key = normalise(candidate)
        if key in normalised:
            return normalised[key]

    for candidate in candidates:
        key = normalise(candidate)
        if len(key) < MIN_CONTAINMENT_LEN:
            continue
        for norm_col, original in normalised.items():
            if len(norm_col) < MIN_CONTAINMENT_LEN:
                continue
            if key in norm_col or norm_col in key:
                return original
    return None


def find_numeric(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    col = find(df, candidates)
    if col is not None and pd.api.types.is_numeric_dtype(df[col]):
        return col
    for candidate in candidates:
        key = normalise(candidate)
        if len(key) < MIN_CONTAINMENT_LEN:
            continue
        for column in df.columns:
            if (key in normalise(column)
                    and pd.api.types.is_numeric_dtype(df[column])):
                return column
    return None


@dataclass
class Resolution:
    columns: dict[str, str] = field(default_factory=dict)
    absent: list[str] = field(default_factory=list)

    def get(self, name: str) -> str | None:
        return self.columns.get(name)

    def has(self, *names: str) -> bool:
        return all(n in self.columns for n in names)


def resolve(df: pd.DataFrame, wanted: dict[str, tuple[str, ...]],
            numeric: tuple[str, ...] = ()) -> Resolution:
    out = Resolution()
    for name, candidates in wanted.items():
        col = (find_numeric(df, candidates) if name in numeric
               else find(df, candidates))
        if col is None:
            out.absent.append(name)
        else:
            out.columns[name] = col
    return out


# --------------------------------------------------------------------------
# Candidate spellings
# --------------------------------------------------------------------------
MODEL_CANDIDATES = ("model", "Model", "model_name")

DM_FIELDS = {
    "model_a": ("model_a", "modela", "model_1", "model1", "baseline",
                "Model A"),
    "model_b": ("model_b", "modelb", "model_2", "model2", "comparison",
                "Model B"),
    "statistic": ("dm_statistic", "dm_stat", "statistic", "test_statistic",
                  "dm"),
    "p_value": ("p_value", "pvalue", "pval", "p_val", "p"),
    "observations": ("observations", "n_obs", "nobs", "n_observations",
                     "paired_observations", "sample_size", "n"),
    "hac_lag": ("hac_lag", "newey_west_lag", "nw_lag", "truncation_lag",
                "hac", "lag"),
    "loss": ("loss_function", "loss", "criterion"),
    "horizon": ("horizon",),
    "significant": ("significant_5pct", "significant", "reject"),
}
DM_NUMERIC = ("statistic", "p_value", "observations", "hac_lag")

PEAK_FIELDS = {
    "model": MODEL_CANDIDATES,
    "precision": ("precision", "prec"),
    "recall": ("recall", "sensitivity", "tpr"),
    "f1": ("f1_score", "f1", "fscore"),
    "true_positive": ("true_positive", "true_positives", "tp"),
    "false_positive": ("false_positive", "false_positives", "fp"),
    "false_negative": ("false_negative", "false_negatives", "fn"),
    "true_negative": ("true_negative", "true_negatives", "tn"),
    "threshold": ("threshold", "peak_threshold", "cutoff"),
    "percentile": ("percentile", "quantile"),
}
PEAK_NUMERIC = ("precision", "recall", "f1", "true_positive",
                "false_positive", "false_negative", "true_negative",
                "threshold", "percentile")

THRESHOLD_FIELDS = {
    "percentile": ("percentile", "quantile", "level"),
    "threshold": ("threshold_kwh", "threshold", "value", "demand_kwh"),
    "label": ("label", "name", "statistic"),
}
THRESHOLD_NUMERIC = ("percentile", "threshold")


def feature_value_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """First non-numeric column is the feature, first numeric is the value."""
    feature = value = None
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if value is None:
                value = col
        elif feature is None:
            feature = col
    if feature is None and len(df.columns):
        feature = df.columns[0]
    return feature, value


def model_column(df: pd.DataFrame) -> str | None:
    for candidate in ("Model", "model"):
        if candidate in df.columns:
            return candidate
    for col in df.columns:
        if normalise(col) == "model":
            return col
    return None


def resolve_metrics(df: pd.DataFrame, aliases: dict) -> dict[str, str]:
    """Map canonical metric keys to the column spellings actually present."""
    found: dict[str, str] = {}
    lower = {str(c).lower(): c for c in df.columns}
    for canon, spellings in aliases.items():
        for spelling in spellings:
            if spelling in df.columns:
                found[canon] = spelling
                break
            if spelling.lower() in lower:
                found[canon] = lower[spelling.lower()]
                break
    return found
