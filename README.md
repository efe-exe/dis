Coffee Sales — DB Exercise

Anleitung und Skripte zur Bearbeitung der DB-Übung (Teil b und c).

Voraussetzungen:
- Python 3.9+
- Abhängigkeiten installieren: `pip install -r requirements.txt`

Skripte:
- `scripts/db_concurrency_demo.py` — führt Teil b (Concurrency-Demo) aus und schreibt Log in `results/concurrency_results.txt`.
- `scripts/import_coffee.py` — lädt `Coffe_sales.csv` in eine SQLite-Datenbank `coffee_sales.db`, fügt Constraints hinzu und normalisiert Tabellen.

Ausführung (PowerShell):
```
pip install -r requirements.txt
python .\scripts\db_concurrency_demo.py
python .\scripts\import_coffee.py
```
