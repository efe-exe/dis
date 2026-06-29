"""
Forecasting algorithms for the daily ingredient usage time series.

For now this module only contains a trivial *mockup* forecaster that
simply repeats the previous day's observed value. The real Triple
Exponential Smoothing (Holt-Winters) implementation will replace
`forecast` later on, keeping the same call signature so that
timeseries.py does not have to change again.
"""

from datetime import date, timedelta


def forecast(
    history: list[tuple[date, int]],
    forecast_from: date,
    forecast_until: date,
) -> list[tuple[date, int]]:
    """
    Produce a forecast for every day in the closed interval
    [forecast_from, forecast_until].

    Parameters
    ----------
    history:
        The observed (gap-free) daily series as a list of
        (date, amount) tuples. By contract, the caller passes only
        observations measured *before* `forecast_from`, so this
        function never sees data from the forecast window itself.
    forecast_from, forecast_until:
        Inclusive bounds of the interval to forecast.

    Returns
    -------
    A list of (date, amount) tuples, one per day in the interval.

    Mockup behaviour
    ----------------
    The forecast for each day is simply the value of the *previous*
    day. The first forecast day repeats the last observed value; every
    subsequent forecast day repeats its own predecessor's forecast.
    """
    if not history:
        raise ValueError("Cannot forecast from an empty history.")

    # Start from the last observed value.
    previous_value = history[-1][1]

    predictions: list[tuple[date, int]] = []
    day = forecast_from
    while day <= forecast_until:
        predictions.append((day, previous_value))
        previous_value = predictions[-1][1]  # repeat the previous day's value
        day += timedelta(days=1)
    return predictions
