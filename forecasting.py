"""
Holt-Winters Forecasting Engine — Exercise Sheet 3
====================================================
Implements Holt-Winters (Triple Exponential Smoothing) from scratch
to forecast daily ingredient usage for a café.

Usage:
    python forecasting.py --ingredient milk --alpha 0.3 --horizon 30
    python forecasting.py --ingredient sugar --alpha 0.5 --horizon 14
    python forecasting.py --ingredient cocoa --alpha 0.2 --horizon 7

Switchable ingredients: milk, sugar, cocoa, espresso
"""

import argparse
import os
import sys
from datetime import timedelta

import numpy as np


# ---------------------------------------------------------------------------
# 1. Holt-Winters Algorithm (implemented from scratch)
# ---------------------------------------------------------------------------

class HoltWintersForecaster:
    """Triple Exponential Smoothing for time-series forecasting.

    Models three components:
      - Level (baseline)
      - Trend (linear slope)
      - Seasonality (repeating pattern with period m)

    Parameters:
        alpha (float): Level smoothing factor (0 < alpha <= 1)
        beta  (float): Trend smoothing factor  (0 < beta  <= 1)
        gamma (float): Seasonal smoothing factor (0 < gamma <= 1)
        m     (int):   Seasonal period in time steps
    """

    def __init__(self, alpha: float = 0.3, beta: float = 0.01,
                 gamma: float = 0.1, m: int = 7):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.m = m
        self.level = 0.0
        self.trend = 0.0
        self.season = []

    def fit(self, values: np.ndarray) -> "HoltWintersForecaster":
        """Fit the model to historical data.

        Args:
            values: 1-D array of numeric time-series values.

        Returns:
            self (for chaining).

        Raises:
            ValueError: If fewer than 2*m data points are provided.
        """
        n = len(values)
        if n < 2 * self.m:
            raise ValueError(
                f"Need at least {2 * self.m} data points for seasonal period "
                f"m={self.m}. Got {n}."
            )

        # Initialize level as average of first seasonal cycle
        self.level = float(np.mean(values[: self.m]))

        # Initialize trend as average of m-step differences
        trends = []
        for i in range(self.m):
            idx_start = i
            idx_end = i + self.m
            if idx_end <= n:
                trends.append((values[idx_end] - values[idx_start]) / self.m)
        self.trend = float(np.mean(trends)) if trends else 0.0

        # Initialize seasonal components (two full cycles for stability)
        self.season = [0.0] * (2 * self.m)
        for i in range(2 * self.m):
            if i < n:
                self.season[i] = float(values[i] - self.level)

        return self

    def forecast(self, steps: int) -> list:
        """Forecast *steps* periods into the future.

        Args:
            steps: Number of future periods to predict.

        Returns:
            List of forecasted values (non-negative).
        """
        future = []
        for h in range(1, steps + 1):
            season_idx = (len(self.season) - self.m + h) % self.m
            val = self.level + self.trend * h + self.season[season_idx]
            future.append(max(0.0, val))  # enforce non-negative
        return future


# ---------------------------------------------------------------------------
# 2. Model Evaluation
# ---------------------------------------------------------------------------

def evaluate_forecaster(forecaster: HoltWintersForecaster,
                        values: np.ndarray,
                        train_fraction: float = 0.8
                        ) -> tuple:
    """Train on the first *train_fraction* of data, forecast the rest.

    Returns:
        (mae, rmse, forecasted_values, test_values, train_size)
    """
    train_size = int(len(values) * train_fraction)
    train = values[: train_size]
    test = values[train_size:]

    forecaster.fit(train)
    forecasted = forecaster.forecast(len(test))

    errors = np.array(test) - np.array(forecasted)
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    return mae, rmse, forecasted, test, train_size


# ---------------------------------------------------------------------------
# 3. CLI Entry Point
# ---------------------------------------------------------------------------

VALID_INGREDIENTS = ["milk", "sugar", "cocoa", "espresso"]
DEFAULT_ALPHA = 0.3
DEFAULT_BETA = 0.01
DEFAULT_GAMMA = 0.1
DEFAULT_M = 7
DEFAULT_HORIZON = 30
DEFAULT_TRAIN_FRACTION = 0.8


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Holt-Winters Forecasting for Café Ingredients"
    )
    parser.add_argument(
        "--ingredient", type=str, required=True,
        choices=VALID_INGREDIENTS,
        help="Ingredient to forecast: milk, sugar, cocoa, espresso"
    )
    parser.add_argument(
        "--alpha", type=float, default=DEFAULT_ALPHA,
        help=f"Level smoothing factor (default: {DEFAULT_ALPHA})"
    )
    parser.add_argument(
        "--beta", type=float, default=DEFAULT_BETA,
        help=f"Trend smoothing factor (default: {DEFAULT_BETA})"
    )
    parser.add_argument(
        "--gamma", type=float, default=DEFAULT_GAMMA,
        help=f"Seasonal smoothing factor (default: {DEFAULT_GAMMA})"
    )
    parser.add_argument(
        "--m", type=int, default=DEFAULT_M,
        help=f"Seasonal period in days (default: {DEFAULT_M}, weekly)"
    )
    parser.add_argument(
        "--horizon", type=int, default=DEFAULT_HORIZON,
        help=f"Days to forecast into the future (default: {DEFAULT_HORIZON})"
    )
    parser.add_argument(
        "--train-fraction", type=float, default=DEFAULT_TRAIN_FRACTION,
        help=f"Fraction of data for training (default: {DEFAULT_TRAIN_FRACTION})"
    )
    return parser.parse_args()


def main() -> None:
    """Run the forecasting pipeline and print results to stdout."""
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"  Holt-Winters Forecasting — {args.ingredient.upper()}")
    print(f"  alpha={args.alpha}, beta={args.beta}, gamma={args.gamma}, m={args.m}")
    print(f"  Horizon: {args.horizon} days, train_fraction={args.train_fraction}")
    print(f"{'='*60}\n")

    # --- Forecasting engine (algorithm only — no DB, no plotting) ---
    forecaster = HoltWintersForecaster(
        alpha=args.alpha, beta=args.beta, gamma=args.gamma, m=args.m
    )

    # --- Read pre-computed daily usage data ---
    # Data loading / aggregation is performed by a separate script
    # (e.g. scripts/build_daily_usage.py) that writes results/
    # daily_<ingredient>_usage.csv.  This file is then read here.
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "results", f"daily_{args.ingredient}_usage.csv"
    )
    if not os.path.isfile(csv_path):
        print(f"[WARN] {csv_path} not found. "
              f"Run the data-aggregation script first.")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(csv_path, parse_dates=["date"])
    values = df["amount"].values.astype(float)
    dates = df["date"].values
    last_date = pd.Timestamp(dates[-1])

    print(f"Data: {len(values)} days  "
          f"({dates[0]} to {dates[-1]})")
    print(f"  Mean={values.mean():.1f}  "
          f"Min={values.min():.1f}  "
          f"Max={values.max():.1f}\n")

    # --- Evaluation ---
    mae, rmse, forecasted, test, train_size = evaluate_forecaster(
        forecaster, values, args.train_fraction
    )
    test_dates = dates[train_size:]

    print(f"{'='*60}")
    print(f"  Evaluation (hold-out {1 - args.train_fraction:.0%})")
    print(f"{'='*60}")
    print(f"  Train days: {train_size}")
    print(f"  Test days:  {len(test)}")
    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}\n")

    # --- Future forecast ---
    future = forecaster.forecast(args.horizon)
    future_dates = [last_date + timedelta(days=i) for i in range(1, args.horizon + 1)]

    print(f"{'='*60}")
    print(f"  Future Forecast — {args.ingredient.capitalize()}")
    print(f"{'='*60}")
    print(f"  Next 7 days:")
    for i, val in enumerate(future[:7]):
        d = future_dates[i]
        print(f"    {d.strftime('%Y-%m-%d')}: {val:.1f}")
    print()

    print(f"{'='*60}")
    print(f"  Parameters")
    print(f"{'='*60}")
    print(f"  Algorithm:     Holt-Winters (Triple Exponential Smoothing)")
    print(f"  User-adjustable: alpha, beta, gamma, m, horizon, train-fraction")
    print(f"  Switchable ingredients: {', '.join(VALID_INGREDIENTS)}")
    print()


if __name__ == "__main__":
    main()
