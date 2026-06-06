from pathlib import Path
import csv
import json
from collections import defaultdict

import psycopg2
from pymongo import MongoClient


BASE_DIR = Path(__file__).resolve().parent.parent

SALES_CSV = BASE_DIR / "data" / "coffee_sales.csv"
RECIPES_JSON = BASE_DIR / "data" / "coffee_recipes.json"

RESULTS_DIR = BASE_DIR / "results"
RESULTS_TXT = RESULTS_DIR / "nosql_results.txt"
DAILY_CSV = RESULTS_DIR / "daily_preparation_time.csv"


POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "dis_test_db",
    "user": "bob",
    "password": "bobbycar",
}

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "dis_nosql_db"
MONGO_COLLECTION = "coffee_recipes"


def read_recipes_json(path: Path) -> dict:
    """
    Die hochgeladene JSON-Datei enthält wahrscheinlich Windows-Sonderzeichen.
    Deshalb versuchen wir zuerst UTF-8 und dann cp1252.
    """
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            with path.open("r", encoding=encoding) as file:
                return json.load(file)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "unknown",
        b"",
        0,
        1,
        "Could not decode recipes JSON with utf-8, utf-8-sig or cp1252",
    )


def setup_postgres_sales_table() -> None:
    """
    Erstellt eine relationale Tabelle in PostgreSQL und lädt coffee_sales.csv hinein.
    """
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS coffee_sales;")

            cur.execute("""
                CREATE TABLE coffee_sales (
                    hour_of_day INTEGER,
                    cash_type TEXT,
                    money NUMERIC(10, 2),
                    coffee_name TEXT,
                    time_of_day TEXT,
                    weekday TEXT,
                    month_name TEXT,
                    weekdaysort INTEGER,
                    monthsort INTEGER,
                    sale_date DATE,
                    sale_time TIME
                );
            """)

            with SALES_CSV.open("r", encoding="utf-8-sig", newline="") as file:
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


def setup_mongodb_recipes() -> None:
    """
    Lädt die Rezeptdaten in MongoDB.
    """
    data = read_recipes_json(RECIPES_JSON)
    recipe_documents = data["recipes"]

    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    collection.delete_many({})

    if recipe_documents:
        collection.insert_many(recipe_documents)


def get_sold_coffee_names() -> set[str]:
    """
    Holt alle Kaffeespezialitäten aus der relationalen Sales-Tabelle.
    """
    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT coffee_name
                FROM coffee_sales
                WHERE coffee_name IS NOT NULL
                ORDER BY coffee_name;
            """)
            return {row[0] for row in cur.fetchall()}


def get_recipe_names() -> set[str]:
    """
    Holt alle Rezeptnamen aus MongoDB.
    """
    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    return {
        document["name"]
        for document in collection.find({}, {"name": 1})
    }


def find_americano_with_milk() -> dict:
    """
    Findet das geforderte Rezept Americano with Milk per MongoDB-API.
    """
    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    return collection.find_one(
        {"name": "Americano with Milk"},
        {"_id": 0}
    )


def insert_missing_recipes(missing_names: set[str]) -> None:
    """
    Ergänzt fehlende Rezeptdaten.
    Realismus ist laut Aufgabenblatt nett, aber nicht erforderlich.
    """
    fallback_recipes = {
        "Espresso": {
            "id": "espresso",
            "name": "Espresso",
            "category": "Espresso",
            "time_minutes": 2,
            "servings": 1,
            "ingredients": [
                {"item": "Coffee beans", "amount": 18, "unit": "g"},
                {"item": "Water", "amount": 30, "unit": "ml"}
            ],
            "equipment": ["Espresso machine"],
            "steps": [
                "Grind coffee beans.",
                "Brew one espresso shot."
            ]
        },
        "Cappuccino": {
            "id": "cappuccino",
            "name": "Cappuccino",
            "category": "Cappuccino",
            "time_minutes": 7,
            "servings": 1,
            "ingredients": [
                {"item": "Espresso", "amount": 1, "unit": "shot"},
                {"item": "Milk", "amount": 150, "unit": "ml"}
            ],
            "equipment": ["Espresso machine", "Milk pitcher", "Steam wand"],
            "steps": [
                "Brew one espresso shot.",
                "Steam milk until foamy.",
                "Pour milk foam over the espresso."
            ]
        }
    }

    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    for name in sorted(missing_names):
        recipe = fallback_recipes.get(name)

        if recipe is None:
            recipe = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "category": name,
                "time_minutes": 5,
                "servings": 1,
                "ingredients": [
                    {"item": "Placeholder ingredient", "amount": 1, "unit": "portion"}
                ],
                "equipment": ["Coffee machine"],
                "steps": [
                    "Prepare the drink."
                ]
            }

        collection.update_one(
            {"name": name},
            {"$set": recipe},
            upsert=True
        )


def get_recipe_times() -> dict[str, int]:
    """
    Holt Rezeptname -> Zubereitungszeit aus MongoDB.
    """
    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    recipe_times = {}

    for document in collection.find({}, {"name": 1, "time_minutes": 1, "_id": 0}):
        recipe_times[document["name"]] = int(document["time_minutes"])

    return recipe_times


def compute_daily_preparation_times(recipe_times: dict[str, int]) -> dict[str, int]:
    """
    Berechnet aggregierte Zubereitungszeit pro Tag:
    Summe über alle Verkäufe des Tages, jeweils mit Rezeptzeit aus MongoDB.
    """
    daily_minutes = defaultdict(int)

    with psycopg2.connect(**POSTGRES_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sale_date::text, coffee_name
                FROM coffee_sales
                WHERE coffee_name IS NOT NULL
                ORDER BY sale_date;
            """)

            for sale_date, coffee_name in cur.fetchall():
                daily_minutes[sale_date] += recipe_times[coffee_name]

    return dict(sorted(daily_minutes.items()))


def write_daily_csv(daily_minutes: dict[str, int]) -> None:
    """
    Speichert die Tagesaggregation zusätzlich als CSV.
    """
    with DAILY_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "preparation_time_minutes"])

        for day, minutes in daily_minutes.items():
            writer.writerow([day, minutes])


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    setup_postgres_sales_table()
    setup_mongodb_recipes()

    americano_with_milk = find_americano_with_milk()

    sold_names_before = get_sold_coffee_names()
    recipe_names_before = get_recipe_names()
    missing_before = sold_names_before - recipe_names_before

    insert_missing_recipes(missing_before)

    recipe_names_after = get_recipe_names()
    missing_after = sold_names_before - recipe_names_after

    recipe_times = get_recipe_times()
    daily_minutes = compute_daily_preparation_times(recipe_times)

    write_daily_csv(daily_minutes)

    total_sales = sum(1 for _ in SALES_CSV.open("r", encoding="utf-8-sig")) - 1
    total_days = len(daily_minutes)
    total_minutes = sum(daily_minutes.values())

    first_ten_days = list(daily_minutes.items())[:10]

    with RESULTS_TXT.open("w", encoding="utf-8") as file:
        file.write("Exercise Sheet 2 — NoSQL Databases\n")
        file.write("===================================\n\n")

        file.write("1. Verwendete Datenbanken\n")
        file.write("- PostgreSQL: relationale Sales-Daten aus coffee_sales.csv\n")
        file.write("- MongoDB: dokumentorientierte Rezeptdaten aus coffee_recipes.json\n\n")

        file.write("2. Rezeptsuche: Americano with Milk\n")
        file.write(json.dumps(americano_with_milk, indent=2, ensure_ascii=False))
        file.write("\n\n")

        file.write("3. Kaffeespezialitäten aus der Sales-Tabelle\n")
        for name in sorted(sold_names_before):
            file.write(f"- {name}\n")
        file.write("\n")

        file.write("4. Rezeptnamen vor Ergänzung\n")
        for name in sorted(recipe_names_before):
            file.write(f"- {name}\n")
        file.write("\n")

        file.write("5. Fehlende Rezepte vor Ergänzung\n")
        for name in sorted(missing_before):
            file.write(f"- {name}\n")
        file.write("\n")

        file.write("6. Fehlende Rezepte nach Ergänzung\n")
        if missing_after:
            for name in sorted(missing_after):
                file.write(f"- {name}\n")
        else:
            file.write("- Keine. Für jede verkaufte Kaffeespezialität existiert nun ein Rezept.\n")
        file.write("\n")

        file.write("7. Verwendete Zubereitungszeiten\n")
        for name, minutes in sorted(recipe_times.items()):
            file.write(f"- {name}: {minutes} Minuten\n")
        file.write("\n")

        file.write("8. Aggregierte Zubereitungszeit pro Tag\n")
        file.write(f"Anzahl Verkäufe insgesamt: {total_sales}\n")
        file.write(f"Anzahl Tage: {total_days}\n")
        file.write(f"Gesamte Zubereitungszeit: {total_minutes} Minuten\n\n")

        file.write("Erste 10 Tage:\n")
        for day, minutes in first_ten_days:
            file.write(f"- {day}: {minutes} Minuten\n")

        file.write("\n")
        file.write(f"Die vollständige Tagesaggregation liegt in: {DAILY_CSV}\n")

    print(f"Fertig. Ergebnisprotokoll liegt in {RESULTS_TXT}")
    print(f"Tagesaggregation liegt in {DAILY_CSV}")


if __name__ == "__main__":
    main()
