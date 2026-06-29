#!/usr/bin/python3

""" Make sure matplotlib is installed to (.venv) and execute 
    "source BASE_DIR/.venv/bin/activate"
"""
from pathlib import Path
import psycopg2
import csv
import argparse
from datetime import date
from matplotlib import pyplot as plt
import forecaster
#from pymongo import MongoClient
#import json

BASE_DIR = Path(__file__).resolve().parent.parent
SALES_CSV = BASE_DIR / "data" / "Coffe_sales.csv"
RECIPES_JSON = BASE_DIR / "data" / "coffee_recipes_completed.json"

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "toomuchcoffee",
    "user": "dis_user",
    "password": "overdosedondatabase",
}

#MONGO_URI = "mongodb://localhost:27017/"
#MONGO_DB = "dis_nosql_db"
#MONGO_COLLECTION = "coffee_recipes"

INGREDIENT_MAP = {
        "coffee beans": ["coffee_beans_grams", "g"],
        "water": ["water_milliliters", "ml"],
        "milk": ["milk_milliliters", "ml"],
        "cocoa powder": ["cocoa_powder_grams", "g"],
        "sugar": ["sugar_grams", "g"],
        "salt": ["salt_pinches", "pinches"]}


def setup_raw_coffee_sales_table() -> None:
    """
    Reads the raw Coffe_sales.csv data and puts it into a
    Postgres table, thereby leaving the data unchanged.
    """
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS coffee_sales CASCADE;")

            cur.execute("""
                CREATE TABLE coffee_sales (
                    hour_of_day INTEGER,
                    cash_type TEXT,
                    money NUMERIC(10, 2),
                    coffee_name TEXT NOT NULL,
                    time_of_day TEXT,
                    weekday TEXT,
                    month_name TEXT,
                    weekdaysort INTEGER,
                    monthsort INTEGER,
                    sale_date DATE NOT NULL,
                    sale_time TIME
                );
            """)

            with SALES_CSV.open("r", encoding="utf-8", newline="") as file:
                cur.copy_expert("""
                    COPY coffee_sales (
                        hour_of_day,
                        cash_type,
                        money,
                        coffee_name,
                        time_of_day,
                        weekday,
                        month_name,
                        weekdaysort,
                        monthsort,
                        sale_date,
                        sale_time
                    )
                    FROM STDIN
                    WITH CSV HEADER
                """, file)

MIX_INGREDIENTS = {"Latte": {"espresso_shots": 2,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 0,
                             "milk_milliliters": 200,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0},
                   "Hot Chocolate": {"espresso_shots": 0,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 0,
                             "milk_milliliters": 250,
                             "cocoa_powder_grams": 20,
                             "sugar_grams": 10,
                             "salt_pinches": 1},
                   "Americano": {"espresso_shots": 2,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 200,
                             "milk_milliliters": 0,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0},
                   # Here, the recipe allowed 'milk or water'. We assumed water:
                   "Cocoa": {"espresso_shots": 0,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 250,
                             "milk_milliliters": 0,
                             "cocoa_powder_grams": 18,
                             "sugar_grams": 8,
                             "salt_pinches": 1},
                   "Cortado": {"espresso_shots": 1,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 0,
                             "milk_milliliters": 60,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0},
                   "Americano with Milk": {"espresso_shots": 1,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 150,
                             "milk_milliliters": 60,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0},
                   "Espresso": {"espresso_shots": 0,
                             "coffee_beans_grams": 18,
                             "water_milliliters": 30,
                             "milk_milliliters": 0,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0},
                   "Cappuccino": {"espresso_shots": 1,
                             "coffee_beans_grams": 0,
                             "water_milliliters": 0,
                             "milk_milliliters": 150,
                             "cocoa_powder_grams": 0,
                             "sugar_grams": 0,
                             "salt_pinches": 0}}

def resolve_to_base_ingredients(mix_ingredients: dict[str, dict[str, int]]) \
    -> dict[str, dict[str, int]]:
    """
    Translates 'espresso shots' to its base ingredients: coffee beans and water.
    Eventually returns a new recipe->ingredients dictionary without espresso shots.
    TODO: This could perhaps be done more elegantly by connecting to a MongoDB and
    querying the RECIPES_JSON file instead of hard-coding it like this.
    """
    base_ingredients = {}
    for drink in mix_ingredients:
        base_ingredients[drink] = {}
        for ingredient in mix_ingredients[drink]:
            if ingredient != 'espresso_shots':
                base_ingredients[drink][ingredient] = \
                        mix_ingredients[drink][ingredient] + \
                        mix_ingredients[drink]['espresso_shots'] * \
                        mix_ingredients['Espresso'][ingredient]
            
    return base_ingredients

def setup_recipe_base_ingredients_table(base_ingredients: dict[str, dict[str, int]]) \
    -> None:
    """
    Creates a table containing information about how much of a certain ingredient
    is in a certain drink.
    """
    
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS recipe_base_ingredients;")

            cur.execute("""
                CREATE TABLE recipe_base_ingredients (
                    drink_name TEXT NOT NULL,   -- must match sales.coffee_name exactly
                    base_ingredient TEXT NOT NULL,
                    amount INTEGER NOT NULL CHECK (amount >= 0),
                    PRIMARY KEY (drink_name, base_ingredient)
                );
            """)

            for drink in base_ingredients:
                for ingredient in base_ingredients[drink]:
                    cur.execute("""
                        INSERT INTO recipe_base_ingredients (
                            drink_name,
                            base_ingredient,
                            amount
                        )
                        VALUES (%s, %s, %s);""", 
                        (drink, 
                        ingredient,
                        base_ingredients[drink][ingredient])
                )

def setup_daily_ingredient_usage_view():
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP VIEW IF EXISTS daily_ingredient_usage;")
            
            cur.execute("""
                CREATE VIEW daily_ingredient_usage AS
                SELECT
                    s.sale_date         AS date,
                    r.base_ingredient   AS ingredient,
                    SUM(r.amount)       AS total_amount
                FROM coffee_sales s
                JOIN recipe_base_ingredients r 
                ON s.coffee_name = r.drink_name
                GROUP BY date, ingredient
                ORDER BY date, ingredient;
            """)
            
def setup_recipe_base_ingredients_table_v2(base_ingredients: dict[str, dict[str, int]]) \
    -> None:
    """
    FOR AN ALTERNATIVE SOLUTION! CAN OTHERWISE BE IGNORED!
    Creates a table containing information about the six required
    base ingredient quantities for each drink recipe.
    """
    
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS recipe_base_ingredients_v2;")

            cur.execute("""
                CREATE TABLE recipe_base_ingredients_v2 (
                    drink_name TEXT PRIMARY KEY,
                    coffee_beans_grams INTEGER NOT NULL CHECK (coffee_beans_grams >= 0),
                    water_milliliters INTEGER NOT NULL CHECK (water_milliliters >= 0),
                    milk_milliliters INTEGER NOT NULL CHECK (milk_milliliters >= 0),
                    cocoa_powder_grams INTEGER NOT NULL CHECK (cocoa_powder_grams >= 0),
                    sugar_grams INTEGER NOT NULL CHECK (sugar_grams >= 0),
                    salt_pinches INTEGER NOT NULL CHECK (salt_pinches >= 0)
                );
            """)

            for drink in base_ingredients:
                cur.execute("""
                    INSERT INTO recipe_base_ingredients_v2 (
                        drink_name,
                        coffee_beans_grams,
                        water_milliliters,
                        milk_milliliters,
                        cocoa_powder_grams,
                        sugar_grams,
                        salt_pinches
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s);""", 
                    (drink, 
                    base_ingredients[drink]["coffee_beans_grams"],
                    base_ingredients[drink]["water_milliliters"],
                    base_ingredients[drink]["milk_milliliters"],
                    base_ingredients[drink]["cocoa_powder_grams"],
                    base_ingredients[drink]["sugar_grams"],
                    base_ingredients[drink]["salt_pinches"])
                )

def get_series(ingredient: str = "coffee beans") \
    -> list[tuple[date, int]]:
    """
    Returns the time series data for a given ingredient
    as a list of (date, amount)-tuples: 
    """
    if ingredient not in INGREDIENT_MAP:
        raise SystemExit(f"Unknown ingredient '{ingredient}'. ")
    ingredient = INGREDIENT_MAP[ingredient][0]
    rows = []
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date, total_amount
                FROM daily_ingredient_usage
                WHERE ingredient = %s
                ORDER BY date;""",
                (ingredient,),
            )
            rows = cur.fetchall()
    return rows

from datetime import timedelta

def fill_gaps(rows: list[tuple[date, int]]) -> list[tuple[date, int]]:
    """
    Takes [(datetime.date, int), ...] (possibly with missing days)
    and returns a gap-free daily series with missing days filled as 0.
    """
    if not rows:
        return []

    # rows are already ordered by date
    start, end = rows[0][0], rows[-1][0]

    series = []
    day = start
    date_amount_lookup = {d: a for d, a in rows} #dictionary is faster, O(1)
    while day <= end:
        series.append((day, date_amount_lookup.get(day, 0))) #.get(key, default)
        day += timedelta(days=1)
    return series
    

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Time series forecasting with coffee sales data")
    parser.add_argument("-i", 
                        "--ingredient", 
                        default="coffee beans",
                        help="""Show time series for coffee beans, water, 
                                milk, cocoa powder, sugar or salt""")
    parser.add_argument("-ff",
                        "--forecast_from",
                        default="0001-01-01",
                        help="""\"yyyy-mm-dd\"""")
    parser.add_argument("-fu",
                        "--forecast_until",
                        default="0001-01-01",
                        help="""\"yyyy-mm-dd\"""")
    args = parser.parse_args()
    
    setup_raw_coffee_sales_table()
    base_ingredients = resolve_to_base_ingredients(MIX_INGREDIENTS)
    setup_recipe_base_ingredients_table(base_ingredients)
    setup_daily_ingredient_usage_view()

    time_series = get_series(str(args.ingredient))
    #print(len(time_series)) #test
    time_series = fill_gaps(time_series)
    #print(len(time_series)) #test
    #print(time_series[0:10]) #test
    dates   = [d for d, _ in time_series]
    amounts = [a for _, a in time_series]

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.figure(figsize=(12, 5))
    plt.plot(dates, amounts, label="Observed", color="tab:blue")
    #plt.scatter(dates, amounts, label="Observed", color="tab:blue")
    plt.xlabel("Date")
    plt.ylabel(f"{args.ingredient} [{INGREDIENT_MAP[str(args.ingredient)][1]}]")
    plt.title(f"Daily usage of {args.ingredient}")
    plt.legend()
    plt.tight_layout()   # verhindert abgeschnittene Labels
    plt.show()


if __name__ == "__main__":
    """
    Only executes main() if this file is run directly as a script.
    Does not execute main() if it is imported as a module.
    """
    main()