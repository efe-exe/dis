"""
Aufgabe 2c iii)
- neue Datenbank
- Tabelle anlegen
- CSV automatisiert importieren
"""

import psycopg2
import csv

conn = psycopg2.connect(
    dbname="dis_test_db",
    user="Bob",
    password="bobbycar",
    host="localhost"
)

cur = conn.cursor()

# Tabelle OHNE Constraints (erstmal roh importieren)
cur.execute("""
DROP TABLE IF EXISTS coffee_sales_raw;

CREATE TABLE coffee_sales_raw (
    sale_date DATE,
    coffee_name TEXT,
    store TEXT,
    quantity INTEGER,
    unit_price NUMERIC,
    payment_type TEXT
);
""")

conn.commit()

# CSV-Import
with open("data/coffee_sales.csv", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # Header überspringen
    for row in reader:
        cur.execute("""
            INSERT INTO coffee_sales_raw
            VALUES (%s, %s, %s, %s, %s, %s)
        """, row)

conn.commit()

# Existenz prüfen
cur.execute("SELECT COUNT(*) FROM coffee_sales_raw;")
print("Importierte Zeilen:", cur.fetchone()[0])

cur.close()
conn.close()
