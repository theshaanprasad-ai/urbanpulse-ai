"""
Temporal anomaly detection for complaint counts per (zone, category).

Method (per cell, evaluated at a reference time `as_of`):
  * Counts are aggregated into consecutive 24-hour windows ending at `as_of` (window 0 = most recent).
  * Baseline = windows 3..30 (28 days), leaving windows 1-2 as a guard band so a developing
    increase does not contaminate its own baseline (as in CDC EARS C2).
  * Optional day-of-week multipliers (estimated city-wide per category) adjust expectations.
  * Test statistic: observed count in the last 24h and last 72h.
      - Equidispersed baseline: exact conditional test for comparing two Poisson rates
        (observed | observed + baseline total ~ Binomial). This accounts for uncertainty in
        the baseline estimate and is valid for sparse/zero baselines.
      - Overdispersed baseline (variance > 1.2 x mean): negative-binomial upper tail with
        method-of-moments dispersion (plug-in, approximate).
  * Raw p-values from all cells and both windows form one family corrected with
    Benjamini-Hochberg (false discovery rate).
  * Median / MAD robust z-scores are reported as descriptive context only, never as p-values.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

WINDOW_HOURS = 24
GUARD_WINDOWS = 2
BASELINE_WINDOWS = 28
HISTORY_LOOKBACK = 6
N_WINDOWS = 1 + GUARD_WINDOWS + BASELINE_WINDOWS + HISTORY_LOOKBACK  # 37
MIN_BASELINE_WINDOWS = 14
MIN_WEEKDAY_WINDOWS = 28
OVERDISPERSION_RATIO = 1.2
FDR_ALPHA = 0.05
WATCH_P = 0.01
MIN_OBSERVED = 3
RARE_BASELINE_RATE = 0.2
HISTORY_ELEVATED_P = 0.05

METHOD_POISSON = "Exact conditional Poisson rate test (binomial), 28-day baseline, 2-day guard band"
METHOD_NB = "Negative-binomial upper-tail test (method-of-moments dispersion), 28-day baseline, 2-day guard band"


def window_bounds(as_of: datetime, index: int, hours: int = WINDOW_HOURS) -> Tuple[datetime, datetime]:
    end = as_of - timedelta(hours=hours * index)
    return end - timedelta(hours=hours), end


def window_index(ts: datetime, as_of: datetime, hours: int = WINDOW_HOURS) -> int:
    """Index of the window containing ts; -1 if ts is after as_of. Windows are (start, end]."""
    delta_h = (as_of - ts).total_seconds() / 3600.0
    if delta_h < 0:
        return -1
    if delta_h == 0:
        return 0
    return int(np.ceil(delta_h / hours)) - 1


def window_weekdays(as_of: datetime, n: int = N_WINDOWS) -> np.ndarray:
    return np.array([(as_of - timedelta(hours=WINDOW_HOURS * (i + 0.5))).weekday() for i in range(n)])


def covered_windows(as_of: datetime, earliest: Optional[datetime]) -> int:
    """Number of most-recent windows fully inside the observed data period."""
    if earliest is None:
        return 0
    span_h = (as_of - earliest).total_seconds() / 3600.0
    return max(0, int(np.floor(span_h / WINDOW_HOURS + 1e-9)))


def weekday_factors(counts: np.ndarray, weekdays: np.ndarray, covered: int, shrink: float = 3.0) -> Optional[np.ndarray]:
    """
    Day-of-week multipliers from pooled counts (excluding the recent guard/test windows).
    Shrunk toward 1.0 and normalised to mean 1. Returns None when history is too short.
    """
    idx = np.arange(1 + GUARD_WINDOWS, min(covered, len(counts)))
    if len(idx) < MIN_WEEKDAY_WINDOWS:
        return None
    c = counts[idx].astype(float)
    m = c.mean()
    if m <= 0:
        return None
    f = np.ones(7)
    for w in range(7):
        sel = c[weekdays[idx] == w]
        f[w] = ((sel.sum() + shrink * m) / (len(sel) + shrink)) / m
    return f / f.mean()


def benjamini_hochberg(p_values: Sequence[float]) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.minimum(q_sorted, 1.0)
    return q


@dataclass
class WindowTest:
    observed: int
    expected: float
    p_value: float
    method: str
    expected_ci95: Tuple[float, float]
    upper_prediction95: int
    windows: int


@dataclass
class CellResult:
    status: str  # TESTED, INSUFFICIENT_HISTORY
    baseline_windows: int
    baseline_total: int = 0
    baseline_rate_per_day: float = 0.0
    baseline_median: Optional[float] = None
    baseline_mad: Optional[float] = None
    robust_z: Optional[float] = None
    dispersion_ratio: Optional[float] = None
    overdispersed: bool = False
    test_1d: Optional[WindowTest] = None
    test_3d: Optional[WindowTest] = None
    history_elevated: List[bool] = field(default_factory=list)


def _test_window(
    counts: np.ndarray,
    factors: np.ndarray,
    obs_idx: Sequence[int],
    base_idx: Sequence[int],
    nb_size: Optional[float],
) -> WindowTest:
    x = int(counts[list(obs_idx)].sum())
    b = int(counts[list(base_idx)].sum())
    f_obs = float(factors[list(obs_idx)].sum())
    f_base = float(factors[list(base_idx)].sum())
    scale = f_obs / f_base
    expected = (b + 0.5) * scale  # Jeffreys-style pseudo-count keeps zero baselines finite
    lo = 0.0 if b == 0 else stats.chi2.ppf(0.025, 2 * b) / 2.0
    hi = stats.chi2.ppf(0.975, 2 * b + 2) / 2.0
    ci = (round(lo * scale, 3), round(hi * scale, 3))

    if nb_size is not None:
        size = nb_size * len(obs_idx)
        prob = size / (size + expected)
        p = float(stats.nbinom.sf(x - 1, size, prob)) if x > 0 else 1.0
        upper = int(stats.nbinom.ppf(0.95, size, prob))
        method = METHOD_NB
    else:
        n_total = x + b
        pi = f_obs / (f_obs + f_base)
        p = float(stats.binom.sf(x - 1, n_total, pi)) if x > 0 else 1.0
        upper = int(stats.poisson.ppf(0.95, expected))
        method = METHOD_POISSON
    return WindowTest(x, round(expected, 3), p, method, ci, upper, len(obs_idx))


def evaluate_cell(
    counts: np.ndarray,
    covered: int,
    factors: Optional[np.ndarray] = None,
    with_history: bool = True,
) -> CellResult:
    """
    counts[i] = complaints in window i (0 = most recent). `covered` = windows with data coverage.
    """
    n = len(counts)
    f = factors if factors is not None else np.ones(n)
    base_idx = [i for i in range(1 + GUARD_WINDOWS, 1 + GUARD_WINDOWS + BASELINE_WINDOWS) if i < min(n, covered)]
    if len(base_idx) < MIN_BASELINE_WINDOWS:
        return CellResult(status="INSUFFICIENT_HISTORY", baseline_windows=len(base_idx))

    base = counts[base_idx].astype(float)
    deseason = base / f[base_idx]
    m = float(deseason.mean())
    v = float(deseason.var(ddof=1)) if len(deseason) > 1 else 0.0
    dispersion = (v / m) if m > 0 else None
    nb_size = None
    if m > 0 and v > OVERDISPERSION_RATIO * m:
        nb_size = m * m / (v - m)

    median = float(np.median(deseason))
    mad = float(np.median(np.abs(deseason - median)))
    robust_z = None
    if mad > 0:
        robust_z = round((float(counts[0]) / f[0] - median) / (1.4826 * mad), 2)

    t1 = _test_window(counts, f, [0], base_idx, nb_size)
    t3 = _test_window(counts, f, [0, 1, 2], base_idx, nb_size)

    history: List[bool] = []
    if with_history:
        for j in range(1, HISTORY_LOOKBACK + 1):
            hb = [i for i in range(j + 1 + GUARD_WINDOWS, j + 1 + GUARD_WINDOWS + BASELINE_WINDOWS) if i < min(n, covered)]
            if len(hb) < MIN_BASELINE_WINDOWS or j >= covered:
                history.append(False)
                continue
            ht = _test_window(counts, f, [j], hb, nb_size)
            history.append(ht.p_value < HISTORY_ELEVATED_P and ht.observed >= 2)

    return CellResult(
        status="TESTED",
        baseline_windows=len(base_idx),
        baseline_total=int(base.sum()),
        baseline_rate_per_day=round(m, 3),
        baseline_median=round(median, 3),
        baseline_mad=round(mad, 3),
        robust_z=robust_z,
        dispersion_ratio=round(dispersion, 3) if dispersion is not None else None,
        overdispersed=nb_size is not None,
        test_1d=t1,
        test_3d=t3,
        history_elevated=history,
    )


def classify_level(q_value: float, p_value: float, observed: int) -> str:
    if observed >= MIN_OBSERVED and q_value <= FDR_ALPHA:
        return "ANOMALY"
    if observed >= MIN_OBSERVED and p_value < WATCH_P:
        return "WATCH"
    return "NORMAL"


def lifecycle(cell: CellResult) -> str:
    if cell.baseline_rate_per_day < RARE_BASELINE_RATE:
        return "NEW_OR_RARE"
    if sum(cell.history_elevated) >= 3:
        return "PERSISTENT"
    return "EMERGING"


def temporal_pattern(counts: np.ndarray, cell: CellResult) -> str:
    """SUSTAINED_INCREASE if at least 2 of the last 3 days exceed 1.5x expectation, else SPIKE."""
    per_day = cell.test_3d.expected / 3.0 if cell.test_3d else 0.0
    days_above = int(sum(1 for i in range(3) if counts[i] > max(1.5 * per_day, per_day + 1)))
    return "SUSTAINED_INCREASE" if days_above >= 2 else "SPIKE"


def pooled_test(
    observed: int,
    baseline_total: int,
    f_obs: float,
    f_base: float,
) -> Tuple[float, float]:
    """Exact conditional Poisson-rate test for pooled counts. Returns (expected, p_value)."""
    expected = (baseline_total + 0.5) * f_obs / f_base
    if observed <= 0:
        return expected, 1.0
    pi = f_obs / (f_obs + f_base)
    return expected, float(stats.binom.sf(observed - 1, observed + baseline_total, pi))


def share_test(cat_obs: int, zone_obs: int, cat_base: int, zone_base: int) -> Optional[float]:
    """
    Is the category's share of all zone complaints higher than its baseline share?
    Separates a category-specific rise from a general rise in reporting volume.
    """
    if zone_obs <= 0 or cat_obs <= 0:
        return None
    p0 = (cat_base + 0.5) / (zone_base + 1.0)
    return float(stats.binom.sf(cat_obs - 1, zone_obs, min(p0, 0.999)))
