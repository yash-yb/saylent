"""
Federated Averaging (FedAvg) over district-local demand models.

This is the core "federated" piece of the platform. Each district trains a
small local model (see forecasting.holt_smoothing -> slope/intercept) purely
on its own PHCs' consumption logs. Only (slope, intercept, n_points) ever
leave the district boundary. The national/BRICS aggregator combines them
into one global trend model with a sample-size-weighted average — the
standard FedAvg rule, just applied to a 2-parameter linear model instead of
a neural net, which keeps it auditable and fast enough to run per medicine,
per night, over an entire country.

Why this matters for the brief: it lets every PHC's forecast benefit from
national (and eventually cross-BRICS) demand patterns for a medicine —
e.g. a monsoon-driven spike in anti-malarials seen in one state can lift
the trend estimate for a PHC in another state that has only 10 days of
its own history — without any raw patient-level or stock-level data ever
being centralised.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from .forecasting import LocalModel


@dataclass
class GlobalModel:
    slope: float
    intercept: float
    participating_units: int
    total_samples: int


def federated_average(local_models: List[LocalModel]) -> GlobalModel:
    """Weighted FedAvg: each district's contribution is weighted by how
    many data points (n_points) it trained on, so a district with 90 days
    of history isn't drowned out by ten districts with 3 days each, and a
    sparse district still gets to vote."""
    usable = [m for m in local_models if m.n_points > 0]
    if not usable:
        return GlobalModel(slope=0.0, intercept=0.0, participating_units=0, total_samples=0)

    total_n = sum(m.n_points for m in usable)
    slope = sum(m.slope * m.n_points for m in usable) / total_n
    intercept = sum(m.intercept * m.n_points for m in usable) / total_n

    return GlobalModel(
        slope=slope,
        intercept=intercept,
        participating_units=len(usable),
        total_samples=total_n,
    )
