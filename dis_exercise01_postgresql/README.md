# Aufgabe 2b — Concurrent Transactions in PostgreSQL

Dieses Verzeichnis enthält eine lauffähige Demonstration für Aufgabe 2b.

## Dateien

- `scripts/db_concurrency_demo.py`
- `requirements.txt`
- `results/concurrency_results.txt` wird beim Lauf erzeugt

## Voraussetzung

Die PostgreSQL-Datenbank muss bereits existieren und erreichbar sein. Für die im Repo genannte Einrichtung können die Standardwerte aus der bisherigen README verwendet werden:

- Datenbank: `dis_test_db`
- Benutzer: `Bob`
- Passwort: `bobbycar`
- Host: `localhost`
- Port: `5432`

## Installation

```bash
pip install -r requirements.txt
```

## Ausführung

Im Verzeichnis `dis_exercise01_postgresql`:

```bash
python scripts/db_concurrency_demo.py
```

Optional mit expliziten Verbindungsdaten:

```bash
python scripts/db_concurrency_demo.py --host localhost --port 5432 --dbname dis_test_db --user Bob --password bobbycar
```

## Was das Skript tut

Das Skript folgt Aufgabe 2b strikt in der Reihenfolge i) bis xiii) und kommentiert die jeweiligen Abschnitte im Code. Es öffnet mehrere PostgreSQL-Verbindungen, zeigt die Sichtbarkeit uncommitteter Änderungen und demonstriert, wie PostgreSQL konkurrierende Updates auf dieselbe Zeile über Row-Locks behandelt.

## Erwartetes Ergebnis

- Vor dem Commit sieht jede Verbindung ihre eigenen uncommitteten Änderungen.
- Nach dem Commit sind die Daten in allen Verbindungen sichtbar.
- Beim zweiten Teil mit den `UPDATE`-Befehlen wartet die zweite Verbindung auf den Lock der ersten, danach setzen beide Transaktionen ihre Änderungen fort.
- Der Protokollauszug landet zusätzlich in `results/concurrency_results.txt`.
