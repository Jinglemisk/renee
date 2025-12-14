"""Generic simulation runner.

This module is intentionally game-agnostic: games provide a scenario function
that returns metrics, and the engine aggregates statistics across trials.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Callable


@dataclass(frozen=True, slots=True)
class SimulationStats:
    trials: int
    mean: float
    stdev: float
    min: float
    max: float


def simulate(
    *,
    trials: int,
    seed: int = 0,
    scenario: Callable[[random.Random], float],
) -> SimulationStats:
    if trials <= 0:
        raise ValueError("trials must be > 0")
    rng = random.Random(seed)
    values: list[float] = [float(scenario(rng)) for _ in range(trials)]
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    stdev = math.sqrt(var)
    return SimulationStats(trials=trials, mean=mean, stdev=stdev, min=min(values), max=max(values))

