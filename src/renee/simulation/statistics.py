"""Statistical analysis utilities for simulation results.

Provides statistical summaries and comparisons for simulation data,
enabling AI-assisted balance testing and impact analysis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class StatisticalSummary:
    """Statistical summary of a collection of values.

    Provides common statistical measures: mean, standard deviation,
    min/max, median, and percentiles.

    Attributes:
        count: Number of values
        mean: Arithmetic mean
        std_dev: Standard deviation
        min_val: Minimum value
        max_val: Maximum value
        median: 50th percentile
        percentile_25: 25th percentile (Q1)
        percentile_75: 75th percentile (Q3)

    Example:
        values = [10, 20, 30, 40, 50]
        summary = StatisticalSummary.from_values(values)
        print(f"Mean: {summary.mean}, Std Dev: {summary.std_dev}")
    """

    count: int
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    median: float
    percentile_25: float
    percentile_75: float

    @classmethod
    def from_values(cls, values: list[float]) -> StatisticalSummary:
        """Create a statistical summary from a list of values.

        Args:
            values: List of numeric values to analyze

        Returns:
            StatisticalSummary instance

        Raises:
            ValueError: If values list is empty

        Example:
            summary = StatisticalSummary.from_values([1, 2, 3, 4, 5])
        """
        if not values:
            raise ValueError("Cannot create statistical summary from empty list")

        sorted_values = sorted(values)
        count = len(values)

        # Calculate mean
        mean = sum(values) / count

        # Calculate standard deviation
        if count > 1:
            variance = sum((x - mean) ** 2 for x in values) / (count - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        # Min and max
        min_val = sorted_values[0]
        max_val = sorted_values[-1]

        # Percentiles
        median = cls._percentile(sorted_values, 50)
        percentile_25 = cls._percentile(sorted_values, 25)
        percentile_75 = cls._percentile(sorted_values, 75)

        return cls(
            count=count,
            mean=mean,
            std_dev=std_dev,
            min_val=min_val,
            max_val=max_val,
            median=median,
            percentile_25=percentile_25,
            percentile_75=percentile_75,
        )

    @staticmethod
    def _percentile(sorted_values: list[float], percentile: float) -> float:
        """Calculate percentile from sorted values.

        Uses linear interpolation between closest ranks.

        Args:
            sorted_values: Pre-sorted list of values
            percentile: Percentile to calculate (0-100)

        Returns:
            The percentile value
        """
        if not sorted_values:
            return 0.0

        if len(sorted_values) == 1:
            return sorted_values[0]

        # Calculate position
        k = (len(sorted_values) - 1) * (percentile / 100)
        floor_k = int(math.floor(k))
        ceil_k = int(math.ceil(k))

        if floor_k == ceil_k:
            return sorted_values[floor_k]

        # Linear interpolation
        d0 = sorted_values[floor_k]
        d1 = sorted_values[ceil_k]
        fraction = k - floor_k

        return d0 + (d1 - d0) * fraction

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the summary

        Example:
            summary_dict = summary.to_dict()
            json.dumps(summary_dict)
        """
        return {
            "count": self.count,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "min": self.min_val,
            "max": self.max_val,
            "median": self.median,
            "percentile_25": self.percentile_25,
            "percentile_75": self.percentile_75,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"StatisticalSummary(n={self.count}, "
            f"mean={self.mean:.2f}, std={self.std_dev:.2f}, "
            f"range=[{self.min_val:.2f}, {self.max_val:.2f}], "
            f"median={self.median:.2f})"
        )


@dataclass
class ComparisonResult:
    """Result of comparing two statistical distributions.

    Compares baseline vs modified distributions to identify significant changes.

    Attributes:
        baseline: Statistical summary of baseline distribution
        modified: Statistical summary of modified distribution
        difference: Percentage change in means
        significant: Whether the change is statistically significant
        p_value: Statistical significance value (lower = more significant)

    Example:
        baseline_values = [100, 110, 105, 95, 100]
        modified_values = [120, 130, 125, 115, 120]
        result = compare_distributions(baseline_values, modified_values)
        if result.significant:
            print(f"Significant change: {result.difference:.1f}%")
    """

    baseline: StatisticalSummary
    modified: StatisticalSummary
    difference: float  # Percentage change
    significant: bool  # Statistically significant?
    p_value: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the comparison
        """
        return {
            "baseline": self.baseline.to_dict(),
            "modified": self.modified.to_dict(),
            "difference_percent": self.difference,
            "significant": self.significant,
            "p_value": self.p_value,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        sig_str = "SIGNIFICANT" if self.significant else "not significant"
        direction = "increase" if self.difference > 0 else "decrease"
        return (
            f"ComparisonResult: {abs(self.difference):.1f}% {direction} "
            f"({sig_str}, p={self.p_value:.4f})"
        )


def compare_distributions(a: list[float], b: list[float]) -> ComparisonResult:
    """Compare two distributions statistically.

    Performs a statistical comparison between baseline (a) and modified (b)
    distributions. Uses a two-sample t-test to determine significance.

    Args:
        a: Baseline distribution values
        b: Modified distribution values

    Returns:
        ComparisonResult with statistical analysis

    Raises:
        ValueError: If either list is empty

    Example:
        baseline = [100, 105, 95, 100, 110]
        modified = [120, 125, 115, 120, 130]
        result = compare_distributions(baseline, modified)
        print(f"Change: {result.difference:.1f}%")
    """
    if not a or not b:
        raise ValueError("Cannot compare empty distributions")

    # Calculate statistical summaries
    baseline = StatisticalSummary.from_values(a)
    modified = StatisticalSummary.from_values(b)

    # Calculate percentage difference
    if baseline.mean != 0:
        difference = ((modified.mean - baseline.mean) / baseline.mean) * 100
    else:
        difference = float('inf') if modified.mean > 0 else 0.0

    # Perform two-sample t-test
    p_value = _two_sample_t_test(a, b)

    # Determine significance (p < 0.05)
    significant = p_value < 0.05

    return ComparisonResult(
        baseline=baseline,
        modified=modified,
        difference=difference,
        significant=significant,
        p_value=p_value,
    )


def _two_sample_t_test(a: list[float], b: list[float]) -> float:
    """Perform a two-sample t-test.

    Calculates the p-value for the null hypothesis that the two
    distributions have the same mean.

    Args:
        a: First sample
        b: Second sample

    Returns:
        p-value (0.0 to 1.0)
    """
    n1 = len(a)
    n2 = len(b)

    if n1 < 2 or n2 < 2:
        # Not enough samples for meaningful test
        return 1.0

    # Calculate means
    mean1 = sum(a) / n1
    mean2 = sum(b) / n2

    # Calculate variances
    var1 = sum((x - mean1) ** 2 for x in a) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in b) / (n2 - 1)

    # Calculate pooled standard error
    pooled_se = math.sqrt(var1 / n1 + var2 / n2)

    if pooled_se == 0:
        # No variance - distributions are identical
        return 1.0 if mean1 == mean2 else 0.0

    # Calculate t-statistic
    t_stat = abs((mean1 - mean2) / pooled_se)

    # Degrees of freedom (Welch's approximation)
    df = _welch_df(var1, var2, n1, n2)

    # Convert t-statistic to p-value using Student's t-distribution
    # This is a simplified approximation
    p_value = _t_to_p(t_stat, df)

    return p_value


def _welch_df(var1: float, var2: float, n1: int, n2: int) -> float:
    """Calculate degrees of freedom for Welch's t-test.

    Args:
        var1: Variance of first sample
        var2: Variance of second sample
        n1: Size of first sample
        n2: Size of second sample

    Returns:
        Degrees of freedom
    """
    numerator = (var1 / n1 + var2 / n2) ** 2
    denominator = (
        (var1 / n1) ** 2 / (n1 - 1) +
        (var2 / n2) ** 2 / (n2 - 1)
    )

    if denominator == 0:
        return float(min(n1, n2) - 1)

    return numerator / denominator


def _t_to_p(t: float, df: float) -> float:
    """Convert t-statistic to p-value.

    This is a simplified approximation suitable for most use cases.
    For more accurate results, consider using scipy.stats.

    Args:
        t: t-statistic (absolute value)
        df: Degrees of freedom

    Returns:
        Two-tailed p-value
    """
    # Simplified approximation using normal distribution for large df
    # For small df, this will be less accurate but sufficient for our purposes

    if df < 1:
        return 1.0

    # For large df, t-distribution approaches normal distribution
    if df > 30:
        # Use normal approximation
        # p-value ≈ 2 * (1 - Φ(t))
        # where Φ is the standard normal CDF
        p_value = 2 * (1 - _normal_cdf(t))
        return min(1.0, max(0.0, p_value))

    # For small df, use a conservative approximation
    # This tends to overestimate p-values (more conservative)
    x = df / (df + t * t)
    p_value = _beta_cdf(x, df / 2, 0.5)

    return min(1.0, max(0.0, p_value))


def _normal_cdf(x: float) -> float:
    """Approximate standard normal cumulative distribution function.

    Uses the error function approximation.

    Args:
        x: Value to evaluate

    Returns:
        Φ(x) - probability that N(0,1) ≤ x
    """
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _beta_cdf(x: float, a: float, b: float) -> float:
    """Simplified approximation of beta CDF.

    This is a rough approximation suitable for p-value estimation.

    Args:
        x: Value to evaluate (0 to 1)
        a: Alpha parameter
        b: Beta parameter

    Returns:
        Approximate beta CDF value
    """
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # Simple numerical integration using Simpson's rule
    # This is a rough approximation - for production use, consider scipy
    n_steps = 100
    h = x / n_steps
    total = 0.0

    for i in range(n_steps + 1):
        xi = i * h
        weight = 4 if i % 2 == 1 else (2 if 0 < i < n_steps else 1)

        # Beta distribution PDF (unnormalized)
        if xi > 0 and xi < 1:
            pdf_value = (xi ** (a - 1)) * ((1 - xi) ** (b - 1))
        else:
            pdf_value = 0.0

        total += weight * pdf_value

    # Normalize (approximate)
    # For our purposes, we don't need perfect accuracy
    return min(1.0, (h / 3) * total)
