"""
Demand forecasting engine.

Approach: Holt's linear-trend exponential smoothing over each PHC's daily
consumption log for a given medicine. This is deliberately a transparent,
lightweight model (no GPU / heavy training loop needed) so it can run at
national scale, on-device at a district server if needed, and be explained
to a non-technical health administrator: "level" is today's typical daily
use, "trend" is whether that use is rising or falling.

The per-PHC local model here is exactly the local model federated_learning.py
aggregates across a district/nation via FedAvg — so the same function is
reused as the "local training" step of the federated round.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional
import numpy as np


@dataclass
class LocalModel:
    level: float          # smoothed current daily demand
    trend: float          # smoothed daily change in demand
    slope: float          # linear-regression slope over the window (for FedAvg)
    intercept: float      # linear-regression intercept over the window (for FedAvg)
    n_points: int


def holt_smoothing(series: List[float], alpha: float = 0.4, beta: float = 0.2) -> LocalModel:
    """Fit Holt's linear trend model + an OLS line over the same window.

    series: chronologically ordered daily consumption values (most recent last).
    """
    if len(series) == 0:
        return LocalModel(level=0.0, trend=0.0, slope=0.0, intercept=0.0, n_points=0)

    if len(series) == 1:
        return LocalModel(level=series[0], trend=0.0, slope=0.0, intercept=series[0], n_points=1)

    level = series[0]
    trend = series[1] - series[0]
    for t in range(1, len(series)):
        value = series[t]
        last_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

    # OLS slope/intercept over the same window — this is the "model" that
    # gets shared (as two floats, never raw data) in the federated round.
    x = np.arange(len(series), dtype=float)
    y = np.array(series, dtype=float)
    x_mean, y_mean = x.mean(), y.mean()
    denom = ((x - x_mean) ** 2).sum()
    slope = float(((x - x_mean) * (y - y_mean)).sum() / denom) if denom > 0 else 0.0
    intercept = float(y_mean - slope * x_mean)

    return LocalModel(level=float(level), trend=float(trend), slope=slope,
                       intercept=intercept, n_points=len(series))


def project_forecast(model: LocalModel, horizon_days: int = 14,
                      global_slope: Optional[float] = None,
                      global_weight: float = 0.3) -> List[float]:
    """Project daily demand forward. If a federated global_slope is supplied
    (aggregated across districts/nations), blend it in at global_weight —
    this is how a low-traffic rural PHC benefits from the pooled pattern of
    hundreds of other PHCs without ever sharing its own raw log."""
    level, trend = model.level, model.trend
    if global_slope is not None:
        trend = (1 - global_weight) * trend + global_weight * global_slope

    out = []
    for h in range(1, horizon_days + 1):
        out.append(max(0.0, level + h * trend))
    return out


def predicted_stockout_date(current_qty: float, daily_forecast: List[float],
                             start: date) -> Optional[date]:
    remaining = current_qty
    for i, demand in enumerate(daily_forecast):
        remaining -= demand
        if remaining <= 0:
            return start + timedelta(days=i + 1)
    return None
