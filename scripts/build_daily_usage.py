"""Build daily ingredient usage CSVs from coffee_sales.csv + coffee_recipes.json."""
import json
import os
from collections import defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Ingredient mapping (handles "Milk or water" -> Milk)
INGREDIENT_MAP = {
    "Milk": "milk",
    "Hot water": "water",
    "Cocoa powder": "cocoa",
    "Sugar": "sugar",
    "Salt": "salt",
    "Espresso": "espresso",
    "Milk or water": "milk",
}

TARGET_INGREDIENTS = ["milk", "sugar", "cocoa", "espresso"]


def load_recipes():
    json_path = os.path.join(DATA_DIR, "coffee_recipes.json")
    with open(json_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    return {r["name"]: r["ingredients"] for r in data["recipes"]}


def load_sales():
    csv_path = os.path.join(DATA_DIR, "coffee_sales.csv")
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.rename(columns={"Date": "date"})
    return df


def build_daily_usage(sales_df, recipes):
    daily = defaultdict(lambda: defaultdict(float))
    for _, row in sales_df.iterrows():
        coffee = row["coffee_name"]
        date = row["date"].date()
        if coffee not in recipes:
            continue
        for ing in recipes[coffee]:
            mapped = INGREDIENT_MAP.get(ing["item"])
            if mapped:
                daily[date][mapped] += ing["amount"]
    return daily


def main():
    recipes = load_recipes()
    sales = load_sales()
    daily = build_daily_usage(sales, recipes)

    for ingredient in TARGET_INGREDIENTS:
        records = []
        for date in sorted(daily.keys()):
            records.append({
                "date": date,
                "ingredient": ingredient,
                "amount": daily[date].get(ingredient, 0.0),
            })
        df = pd.DataFrame(records)
        out_path = os.path.join(RESULTS_DIR, f"daily_{ingredient}_usage.csv")
        df.to_csv(out_path, index=False)
        print(f"  {out_path}: {len(df)} rows")

    print("Done.")


if __name__ == "__main__":
    main()
