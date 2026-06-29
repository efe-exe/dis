#!/usr/bin/python3

"""
Forecasting algorithm for the daily ingredient usage time series.

This module implements additive Triple Exponential Smoothing
(Holt-Winters) with a damped trend. The call signature of `forecast`
is unchanged from the previous mockup, so timeseries.py keeps working
without modification.

Why additive (not multiplicative) Holt-Winters?
-----------------------------------------------
The gap-filled café series contains genuine zero days (closed days are
filled with 0). The multiplicative variant divides by the seasonal
factors and becomes unstable near zero, whereas the additive variant
does not. The additive seasonal effect ("Mondays are about +30 units")
also matches a café's weekly rhythm well.

Why a damped trend?
-------------------
A plain linear Holt-Winters trend is extrapolated linearly and would
explode (or collapse below zero) over long horizons such as the
allowed multi-year forecast window. The damping parameter phi in (0, 1]
multiplies the trend each step so that it levels off to a plateau
instead of diverging. phi = 1 recovers the classical (undamped)
Holt-Winters model.

Non-negativity
--------------
Ingredient usage cannot be negative, so every produced value is clipped
to be >= 0.

Model equations (additive seasonality, damped trend)
----------------------------------------------------
Let m be the season length (here 7). For each observed value x_t:

    level_t  = alpha * (x_t - season_{t-m})
               + (1 - alpha) * (level_{t-1} + phi * trend_{t-1})
    trend_t  = beta  * (level_t - level_{t-1})
               + (1 - beta) * phi * trend_{t-1}
    season_t = gamma * (x_t - level_t)
               + (1 - gamma) * season_{t-m}

h-step-ahead forecast from the end of the history (step h = 1, 2, ...):

    x_hat_{T+h} = level_T
                + (phi + phi^2 + ... + phi^h) * trend_T
                + season_{T - m + ((h - 1) mod m) + 1}
"""

from datetime import date, timedelta


SEASON_LENGTH = 7  # weekly seasonality (days)


def _initial_components(
    values: list[float],
    m: int,
) -> tuple[float, float, list[float]]:
    """
    Naive initialisation of level, trend and the m seasonal indices,
    as permitted by the exercise sheet ("estimation ... done naively").

    - level0  : mean of the first season
    - trend0  : average per-step slope between the first and second season
    - season0 : deviation of each first-season value from level0
    """
    first_season = values[:m]
    level0 = sum(first_season) / m

    if len(values) >= 2 * m:
        second_season = values[m:2 * m]
        trend0 = (sum(second_season) - sum(first_season)) / (m * m)
    else:
        trend0 = 0.0

    seasonals = [v - level0 for v in first_season]
    return level0, trend0, seasonals


def _fit(
    values: list[float],
    m: int,
    alpha: float,
    beta: float,
    gamma: float,
    phi: float,
) -> tuple[float, float, list[float]]:
    """
    Run the Holt-Winters recursion over the whole history and return the
    final (level, trend, seasonals) state used for forecasting.
    """
    level, trend, seasonals = _initial_components(values, m)

    for t, x in enumerate(values):
        season_tm = seasonals[t % m]
        last_level = level

        level = alpha * (x - season_tm) + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - last_level) + (1 - beta) * phi * trend
        seasonals[t % m] = gamma * (x - level) + (1 - gamma) * season_tm

    return level, trend, seasonals


def forecast(
    history: list[tuple[date, int]],
    forecast_from: date,
    forecast_until: date,
    alpha: float = 0.3,
    beta: float = 0.05,
    gamma: float = 0.3,
    phi: float = 0.98,
    season_length: int = SEASON_LENGTH,
) -> list[tuple[date, int]]:
    """
    Produce a Holt-Winters forecast for every day in the closed interval
    [forecast_from, forecast_until].

    Parameters
    ----------
    history:
        The observed (gap-free) daily series as (date, amount) tuples.
        By contract, the caller passes only observations measured
        *before* forecast_from, so this function never sees data from
        the forecast window itself.
    forecast_from, forecast_until:
        Inclusive bounds of the interval to forecast.
    alpha, beta, gamma:
        Smoothing factors for level, trend and season, each in [0, 1].
    phi:
        Trend damping factor in (0, 1]. phi = 1 is the classical
        undamped model; phi < 1 makes the trend level off.
    season_length:
        Number of days in one season (7 for a weekly rhythm).

    Returns
    -------
    A list of (date, amount) tuples, one per day in the interval.
    Amounts are non-negative integers.
    """
    if not history:
        raise ValueError("Cannot forecast from an empty history.")

    m = season_length
    values = [float(a) for _, a in history]

    # With fewer than one full season we cannot estimate seasonality;
    # fall back to repeating the last observed value (graceful degradation).
    if len(values) < m:
        last_value = max(0, round(values[-1]))
        predictions = []
        day = forecast_from
        while day <= forecast_until:
            predictions.append((day, last_value))
            day += timedelta(days=1)
        return predictions

    level, trend, seasonals = _fit(values, m, alpha, beta, gamma, phi)

    # Forecast horizon is counted from the last observed day, so that a
    # gap between the last observation and forecast_from is handled
    # correctly (e.g. forecast_from = last_observed + 1).
    last_observed_day = history[-1][0]

    predictions: list[tuple[date, int]] = []
    day = forecast_from
    while day <= forecast_until:
        h = (day - last_observed_day).days  # 1, 2, 3, ...
        # Sum of the damping geometric series: phi + phi^2 + ... + phi^h
        if phi == 1.0:
            damped_trend = h * trend
        else:
            damped_trend = trend * phi * (1 - phi ** h) / (1 - phi)
        season = seasonals[(h - 1) % m]

        value = level + damped_trend + season
        predictions.append((day, max(0, round(value))))
        day += timedelta(days=1)

    return predictions
