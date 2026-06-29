"""
Single Exponential Smoothing (SES) forecaster.

SES is the simplest exponential smoothing model from lecture 16
(slide 20). It tracks only the level (the "base" component of the
time series) and has a single smoothing parameter alpha.

    level_1 = x_1
    level_t = alpha * x_t + (1 - alpha) * level_{t-1}

The forecast for every future day is simply the last level, i.e. a
flat line. SES therefore works well for series without a trend, but
lags behind whenever the data trends up or down.
"""

from datetime import date, timedelta


def smooth_level(values: list[float], alpha: float) -> float:
    """
    Run the SES recursion over the whole history and return the final
    (most recent) smoothed level.
    """
    level = values[0]                      # level_1 = x_1
    for x in values[1:]:
        level = alpha * x + (1 - alpha) * level
    return level


def forecast(
    history: list[tuple[date, int]],
    forecast_from: date,
    forecast_until: date,
    alpha: float = 0.3
) -> list[tuple[date, int]]:
    """
    Produce an SES forecast for every day in the closed interval
    [forecast_from, forecast_until].

    Parameters
    ----------
    history:
        Observed (gap-free) daily series as (date, amount) tuples. By
        contract the caller passes only data measured *before*
        forecast_from.
    forecast_from, forecast_until:
        Inclusive bounds of the interval to forecast.
    alpha:
        Level smoothing factor in [0, 1]. Larger alpha reacts faster to
        recent values; smaller alpha smooths more strongly.

    Returns
    -------
    A list of (date, amount) tuples, one per day in the interval.
    Amounts are non-negative integers (usage cannot be negative).
    """
    if not history:
        raise ValueError("Cannot forecast from an empty history.")

    values = [float(a) for _, a in history]
    level = smooth_level(values, alpha)

    # SES predicts the same value (the last level) for every horizon.
    prediction = max(0, round(level))

    predictions: list[tuple[date, int]] = []
    day = forecast_from
    while day <= forecast_until:
        predictions.append((day, prediction))
        day += timedelta(days=1)
    return predictions
