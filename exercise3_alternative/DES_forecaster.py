"""
Double Exponential Smoothing (DES) forecaster, also known as "Holt's
linear method".

In addition to the level, DES also smooths the trend, i.e. the
difference between consecutive levels. DES therefore follows a rising 
or falling series instead of lagging behind it like SES does.

Two components, two smoothing parameters (alpha for the level, beta for
the trend):

    level_1 = x_1
    trend_1 = x_2 - x_1                              (initial slope)

    level_t = alpha * x_t + (1 - alpha) * (level_{t-1} + trend_{t-1})
    trend_t = beta  * (level_t - level_{t-1})
              + (1 - beta) * trend_{t-1}

The level update already adds the previous trend, so the level moves
along with the slope. The trend update is the smoothed difference of
two successive levels.

h-step-ahead forecast (a straight line from the last level):

    x_hat_{T+h} = level_T + h * trend_T

"""

from datetime import date, timedelta


def smooth_level_and_trend(
    values: list[float],
    alpha: float,
    beta: float,
) -> tuple[float, float]:
    """
    Run the DES recursion over the whole history and return the final
    (level, trend) state used for forecasting.
    """
    level = values[0]                 # level_1 = x_1
    trend = values[1] - values[0]     # initial slope from the first step

    for x in values[1:]:
        last_level = level
        level = alpha * x + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

    return level, trend


def forecast(
    history: list[tuple[date, int]],
    forecast_from: date,
    forecast_until: date,
    alpha: float = 0.3,
    beta: float = 0.1
) -> list[tuple[date, int]]:
    """
    Produce a DES forecast for every day in the closed interval
    [forecast_from, forecast_until].

    Parameters
    ----------
    history:
        Observed (gap-free) daily series as (date, amount) tuples. By
        contract the caller passes only data measured before forecast_from.
    forecast_from, forecast_until:
        Inclusive bounds of the interval to forecast.
    alpha:
        Level smoothing factor in [0, 1].
    beta:
        Trend smoothing factor in [0, 1].

    Returns
    -------
    A list of (date, amount) tuples, one per day in the interval.
    Amounts are non-negative integers (usage cannot be negative).
    """
    if not history:
        raise ValueError("Cannot forecast from an empty history.")

    values = [float(a) for _, a in history]

    # With only a single observation there is no slope to estimate;
    # fall back to repeating that value.
    if len(values) < 2:
        prediction = max(0, values[-1])
        predictions = []
        day = forecast_from
        while day <= forecast_until:
            predictions.append((day, prediction))
            day += timedelta(days=1)
        return predictions

    level, trend = smooth_level_and_trend(values, alpha, beta)

    # The horizon h is counted from the last observed day, so a gap
    # between the last observation and forecast_from is handled
    # correctly (e.g. forecast_from = last_observed + 1 -> h = 1).
    last_observed_day = history[-1][0]

    predictions: list[tuple[date, int]] = []
    day = forecast_from
    while day <= forecast_until:
        h = (day - last_observed_day).days        # 1, 2, 3, ...
        value = level + h * trend
        predictions.append((day, max(0, round(value))))
        day += timedelta(days=1)
    return predictions
