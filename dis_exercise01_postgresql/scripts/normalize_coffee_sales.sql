-- Aufgabe 2c iv) & v)

BEGIN;

-- Produkt-Tabelle
CREATE TABLE coffee (
    coffee_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Store-Tabelle
CREATE TABLE store (
    store_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Ziel-Tabelle mit Constraints
CREATE TABLE coffee_sales (
    sale_id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    coffee_id INTEGER NOT NULL REFERENCES coffee(coffee_id),
    store_id INTEGER NOT NULL REFERENCES store(store_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL CHECK (unit_price > 0),
    payment_type TEXT NOT NULL
);

-- Redundanzen auflösen
INSERT INTO coffee(name)
SELECT DISTINCT coffee_name FROM coffee_sales_raw;

INSERT INTO store(name)
SELECT DISTINCT store FROM coffee_sales_raw;

-- Daten migrieren
INSERT INTO coffee_sales (
    sale_date, coffee_id, store_id, quantity, unit_price, payment_type
)
SELECT
    r.sale_date,
    c.coffee_id,
    s.store_id,
    r.quantity,
    r.unit_price,
    r.payment_type
FROM coffee_sales_raw r
JOIN coffee c ON r.coffee_name = c.name
JOIN store s ON r.store = s.name;

COMMIT;
