"""Statistical routines computed in memory from stored artefacts.

Nothing here fits a model or writes a file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DMResult:
    model_a: str
    model_b: str
    statistic: float
    p_value: float
    observations: int
    hac_lag: int
    loss: str = "squared error"

    @property
    def significant_at_5pct(self) -> bool:
        return self.p_value < 0.05


def _normal_two_sided_p(z: float) -> float:
    """Two-sided normal p-value without a scipy dependency."""
    return math.erfc(abs(z) / math.sqrt(2.0))


def _newey_west_variance(d: np.ndarray, lag: int) -> float:
    """Long-run variance with Bartlett (Newey-West) weights."""
    n = d.size
    d = d - d.mean()
    total = float(np.dot(d, d)) / n
    for k in range(1, min(lag, n - 1) + 1):
        gamma = float(np.dot(d[: n - k], d[k:])) / n
        total += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    return total


def diebold_mariano(actual, pred_a, pred_b, hac_lag: int) -> DMResult | None:
    """Paired DM test on squared-error loss with a HAC variance estimate.

    The statistic's sign indicates which model carried the larger average
    squared error over the sample. The test reports whether the difference is
    distinguishable from zero; it does not order the models.
    """
    y = np.asarray(actual, dtype=float)
    a = np.asarray(pred_a, dtype=float)
    b = np.asarray(pred_b, dtype=float)
    mask = np.isfinite(y) & np.isfinite(a) & np.isfinite(b)
    y, a, b = y[mask], a[mask], b[mask]
    if y.size < 8:
        return None

    d = (y - a) ** 2 - (y - b) ** 2
    lrv = _newey_west_variance(d, hac_lag)
    if lrv <= 0:
        return None

    stat = float(d.mean() / math.sqrt(lrv / y.size))
    return DMResult("", "", stat, _normal_two_sided_p(stat), int(y.size),
                    int(hac_lag))


def dm_from_predictions(frame: pd.DataFrame, model_col: str, model_a: str,
                        model_b: str, hac_lag: int) -> DMResult | None:
    """Align two models on shared timestamps, then run the test."""
    if "timestamp" not in frame.columns:
        return None
    a = (frame[frame[model_col].astype(str) == model_a]
         .drop_duplicates(subset=["timestamp"]).set_index("timestamp"))
    b = (frame[frame[model_col].astype(str) == model_b]
         .drop_duplicates(subset=["timestamp"]).set_index("timestamp"))
    shared = a.index.intersection(b.index)
    if len(shared) < 8:
        return None

    result = diebold_mariano(a.loc[shared, "actual"].to_numpy(),
                             a.loc[shared, "prediction"].to_numpy(),
                             b.loc[shared, "prediction"].to_numpy(), hac_lag)
    if result is None:
        return None
    result.model_a, result.model_b = model_a, model_b
    return result


@dataclass
class PeakScore:
    model: str
    precision: float
    recall: float
    f1: float
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int


def peak_scores(frame: pd.DataFrame, model_col: str,
                percentile: int) -> tuple[list[PeakScore], float]:
    """Classify hours at or above a percentile of observed test demand."""
    actual = frame["actual"].dropna().to_numpy(dtype=float)
    if actual.size == 0:
        return [], float("nan")
    threshold = float(np.percentile(actual, percentile))

    out: list[PeakScore] = []
    for model in sorted(frame[model_col].dropna().astype(str).unique()):
        sub = frame[frame[model_col].astype(str) == model]
        mask = sub["actual"].notna() & sub["prediction"].notna()
        if not mask.any():
            continue
        y = sub.loc[mask, "actual"].to_numpy(dtype=float) >= threshold
        p = sub.loc[mask, "prediction"].to_numpy(dtype=float) >= threshold
        tp = int(np.sum(y & p))
        fp = int(np.sum(~y & p))
        fn = int(np.sum(y & ~p))
        tn = int(np.sum(~y & ~p))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0.0)
        out.append(PeakScore(model, precision, recall, f1, tp, fp, fn, tn))
    return out, threshold


def acf(values: pd.Series, max_lag: int) -> list[float]:
    """Autocorrelation at lags 1..max_lag, biased estimator."""
    x = pd.Series(values).astype(float).dropna().to_numpy()
    n = x.size
    max_lag = int(min(max_lag, max(1, n - 1)))
    xc = x - x.mean()
    denom = float(np.dot(xc, xc))
    if denom == 0:
        return [0.0] * max_lag
    return [float(np.dot(xc[: n - k], xc[k:])) / denom
            for k in range(1, max_lag + 1)]


def acf_at(values: pd.Series, lag: int) -> float | None:
    x = pd.Series(values).astype(float).dropna().to_numpy()
    if lag < 1 or lag >= x.size:
        return None
    xc = x - x.mean()
    denom = float(np.dot(xc, xc))
    if denom == 0:
        return None
    return float(np.dot(xc[: x.size - lag], xc[lag:])) / denom


def window_stats(actual: pd.Series, prediction: pd.Series) -> dict:
    a = pd.Series(actual).astype(float)
    p = pd.Series(prediction).astype(float)
    mask = a.notna() & p.notna()
    a, p = a[mask], p[mask]
    if a.empty:
        return {}
    err = p - a
    ss_res = float((err ** 2).sum())
    ss_tot = float(((a - a.mean()) ** 2).sum())
    return {
        "mae": float(err.abs().mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "r2": (1 - ss_res / ss_tot) if ss_tot > 0 else None,
        "observedTotal": float(a.sum()),
        "predictedTotal": float(p.sum()),
        "observedPeak": float(a.max()),
        "predictedPeak": float(p.max()),
        "observations": int(a.size),
    }


def summarise(series: pd.Series) -> dict:
    s = pd.Series(series).astype(float).dropna()
    if s.empty:
        return {}
    q = s.quantile([0.75, 0.90, 0.95, 0.99])
    mean = float(s.mean())
    maximum = float(s.max())
    return {
        "observations": int(s.size),
        "totalKwh": float(s.sum()),
        "mean": mean,
        "median": float(s.median()),
        "maximum": maximum,
        "minimum": float(s.min()),
        "zeroHours": int((s <= 0).sum()),
        "p75": float(q.loc[0.75]),
        "p90": float(q.loc[0.90]),
        "p95": float(q.loc[0.95]),
        "p99": float(q.loc[0.99]),
        "peakOverAverage": (maximum / mean) if mean else None,
    }
