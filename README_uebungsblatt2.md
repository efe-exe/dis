# Exercise Sheet 2 — NoSQL Databases

Dieses Projekt dokumentiert die Umsetzung von **Übungsblatt 2: NoSQL Databases** im Kurs *Databases and Information Systems 2026*. Ziel der Aufgabe ist es, Rezeptdaten für Kaffeespezialitäten in einer NoSQL-Datenbank zu speichern, diese Daten abzufragen und sie anschließend mit relationalen Verkaufsdaten aus dem vorherigen Übungsblatt zu verbinden.

Die Umsetzung verwendet zwei Datenbanksysteme:

- **PostgreSQL** für die relationalen Verkaufsdaten aus `coffee_sales.csv`
- **MongoDB** für die dokumentorientierten Rezeptdaten aus `coffee_recipes.json`

PostgreSQL wird in dieser Aufgabe nicht mehr zur Untersuchung paralleler Transaktionen verwendet. Es dient hier nur als relationale Datenquelle für die Verkaufsdaten. Der NoSQL-Anteil der Aufgabe wird mit MongoDB umgesetzt.

---

## Ziel der Aufgabe

Die Aufgabe besteht aus zwei Teilen.

Im ersten Teil wird eine NoSQL-Datenbank eingerichtet und mit den Rezeptdaten befüllt. Anschließend wird über die Datenbank-API das Rezept für **Americano with Milk** gesucht und ausgegeben.

Im zweiten Teil werden die NoSQL-Rezeptdaten mit den relationalen Sales-Daten verbunden. Dafür werden die in der Sales-Tabelle vorkommenden Kaffeespezialitäten mit den vorhandenen Rezeptnamen verglichen. Fehlende Rezepte werden ergänzt. Sobald für jede verkaufte Kaffeespezialität ein Rezept existiert, wird pro Tag berechnet, wie viel Zeit insgesamt für die Kaffeezubereitung benötigt wurde.

---

## Verwendete Technologien

| Technologie | Rolle im Projekt |
|---|---|
| Python | Führt das Skript aus und verbindet die Datenquellen. |
| PostgreSQL | Speichert die Verkaufsdaten aus `coffee_sales.csv` relational. |
| MongoDB | Speichert die Rezeptdaten als dokumentorientierte NoSQL-Datenbank. |
| psycopg2 | Python-Bibliothek für die Verbindung zu PostgreSQL. |
| pymongo | Python-Bibliothek für die Verbindung zu MongoDB. |
| Homebrew | Installiert und startet PostgreSQL und MongoDB auf macOS. |

---

## Projektstruktur

Die relevante Projektstruktur sieht so aus:

```text
dis/
├── data/
│   ├── coffee_sales.csv
│   └── coffee_recipes.json
├── results/
│   ├── nosql_results.txt
│   └── daily_preparation_time.csv
├── scripts/
│   └── nosql_recipes_demo.py
├── requirements.txt
└── README.md
```

### Eingabedateien

| Datei | Bedeutung |
|---|---|
| `data/coffee_sales.csv` | Verkaufsdaten der Kaffeespezialitäten. Diese Daten werden in PostgreSQL geladen. |
| `data/coffee_recipes.json` | Rezeptdaten der Kaffeespezialitäten. Diese Daten werden in MongoDB geladen. |

### Ausgabedateien

| Datei | Bedeutung |
|---|---|
| `results/nosql_results.txt` | Textprotokoll der Durchführung und wichtigsten Ergebnisse. |
| `results/daily_preparation_time.csv` | Aggregierte Zubereitungszeit pro Tag. |

---

## Voraussetzungen

Auf dem Mac müssen PostgreSQL und MongoDB laufen.

Prüfen:

```bash
brew services list
```

Falls nötig starten:

```bash
brew services start postgresql@17
brew services start mongodb-community@8.0
```

Die Python-Umgebung wird im Projektordner aktiviert:

```bash
cd /Users/bastianqueckenstedt/dis
source .venv/bin/activate
```

Die benötigten Python-Pakete stehen in `requirements.txt`:

```text
psycopg2-binary>=2.9,<3
pymongo>=4.0,<5
```

Installation der Abhängigkeiten:

```bash
pip install -r requirements.txt
```

---

## Durchführung

Das Skript für diese Aufgabe liegt unter:

```text
scripts/nosql_recipes_demo.py
```

Es wird aus dem Projektordner heraus gestartet:

```bash
python scripts/nosql_recipes_demo.py
```

Das Skript führt folgende Schritte aus:

1. Die CSV-Datei `coffee_sales.csv` wird in PostgreSQL in eine relationale Tabelle geladen.
2. Die JSON-Datei `coffee_recipes.json` wird in MongoDB in eine Collection geladen.
3. Das Rezept **Americano with Milk** wird über die MongoDB-API abgefragt.
4. Die verkauften Kaffeespezialitäten aus PostgreSQL werden mit den Rezeptnamen aus MongoDB verglichen.
5. Fehlende Rezepte werden in MongoDB ergänzt.
6. Für jeden Verkauf wird anhand des Rezeptnamens die Zubereitungszeit bestimmt.
7. Die Zubereitungszeiten werden pro Tag aufsummiert.
8. Die Ergebnisse werden in `results/nosql_results.txt` und `results/daily_preparation_time.csv` gespeichert.

---

## Datenmodellierung

### Relationale Daten in PostgreSQL

Die Sales-Daten sind tabellarisch aufgebaut. Jede Zeile beschreibt einen Verkauf. Relevante Spalten sind unter anderem:

- `coffee_name`
- `Date`
- `Time`
- `money`
- `cash_type`
- `hour_of_day`

Diese Struktur passt gut zu einer relationalen Datenbank, weil alle Verkäufe die gleiche Tabellenstruktur besitzen.

### Dokumentdaten in MongoDB

Die Rezeptdaten sind dokumentorientiert aufgebaut. Ein Rezept enthält nicht nur einfache Werte wie Name und Zubereitungszeit, sondern auch verschachtelte Listen, zum Beispiel Zutaten, Equipment und Zubereitungsschritte.

Beispielhafte Struktur eines Rezeptdokuments:

```json
{
  "id": "americano_with_milk",
  "name": "Americano with Milk",
  "category": "Americano",
  "time_minutes": 4,
  "servings": 1,
  "ingredients": [
    { "item": "Espresso", "amount": 1, "unit": "shot" },
    { "item": "Hot water", "amount": 150, "unit": "ml" },
    { "item": "Milk", "amount": 60, "unit": "ml" }
  ],
  "equipment": ["Espresso machine", "Kettle"],
  "steps": [
    "Brew 1 espresso shot into a mug.",
    "Add hot water to form the Americano base.",
    "Add milk (steamed or hot) and stir gently."
  ]
}
```

Diese verschachtelte Struktur ist ein typischer Anwendungsfall für eine dokumentorientierte NoSQL-Datenbank wie MongoDB.

---

## Ergebnisse

### 1. Abfrage von Americano with Milk

Das Rezept **Americano with Milk** wurde erfolgreich in MongoDB gefunden. Es enthält folgende Hauptinformationen:

- Kategorie: `Americano`
- Zubereitungszeit: `4` Minuten
- Portionen: `1`
- Zutaten:
  - Espresso: 1 shot
  - Hot water: 150 ml
  - Milk: 60 ml

Damit ist der erste Teil der Aufgabe erfüllt: Die Zutaten eines bestimmten Rezepts wurden über die API der NoSQL-Datenbank abgefragt.

---

### 2. Vergleich von Sales-Daten und Rezeptdaten

In den Verkaufsdaten kommen acht unterschiedliche Kaffeespezialitäten vor:

- Americano
- Americano with Milk
- Cappuccino
- Cocoa
- Cortado
- Espresso
- Hot Chocolate
- Latte

In der ursprünglichen Rezeptdatei waren sechs Rezepte vorhanden:

- Americano
- Americano with Milk
- Cocoa
- Cortado
- Hot Chocolate
- Latte

Beim Vergleich wurde festgestellt, dass folgende Rezepte fehlten:

- Cappuccino
- Espresso

Diese beiden fehlenden Einträge wurden ergänzt, damit für jede verkaufte Kaffeespezialität auch ein Rezept mit Zubereitungszeit existiert.

---

### 3. Verwendete Zubereitungszeiten

Für die Berechnung der Tageszeiten wurden folgende Zubereitungszeiten verwendet:

| Kaffeespezialität | Zubereitungszeit |
|---|---:|
| Americano | 3 Minuten |
| Americano with Milk | 4 Minuten |
| Cappuccino | 7 Minuten |
| Cocoa | 10 Minuten |
| Cortado | 6 Minuten |
| Espresso | 2 Minuten |
| Hot Chocolate | 12 Minuten |
| Latte | 8 Minuten |

---

### 4. Aggregierte Zubereitungszeit pro Tag

Für jeden Verkauf wurde die Zubereitungszeit der jeweiligen Kaffeespezialität ermittelt. Danach wurden alle Zeiten pro Datum aufsummiert.

Die Berechnung folgt diesem Prinzip:

```text
Zubereitungszeit pro Tag = Summe der Zubereitungszeiten aller verkauften Getränke an diesem Tag
```

Ergebnisüberblick:

| Kennzahl | Wert |
|---|---:|
| Anzahl Verkäufe | 3.547 |
| Anzahl Tage | 381 |
| Zeitraum | 2024-03-01 bis 2025-03-23 |
| Gesamte Zubereitungszeit | 22.068 Minuten |
| Tag mit höchster Zubereitungszeit | 2024-10-11 mit 184 Minuten |
| Tage mit niedrigster Zubereitungszeit | 2024-08-29 und 2025-01-06 mit jeweils 3 Minuten |

Die vollständige Tagesaggregation liegt in:

```text
results/daily_preparation_time.csv
```

---

## Interpretation

Die Aufgabe zeigt, wie relationale und dokumentorientierte Datenbanken gemeinsam verwendet werden können.

Die Verkaufsdaten sind regelmäßig strukturiert und passen gut in eine relationale Tabelle. Die Rezeptdaten enthalten dagegen verschachtelte Informationen wie Zutatenlisten und Zubereitungsschritte. Für solche Daten ist MongoDB geeignet, weil ein komplettes Rezept als ein zusammenhängendes Dokument gespeichert werden kann.

Durch den Vergleich beider Datenquellen wurde sichtbar, dass die Rezeptdaten zunächst unvollständig waren. Erst nach Ergänzung der fehlenden Rezepte konnte für jeden Verkauf eine Zubereitungszeit bestimmt werden. Danach war es möglich, eine Tagesaggregation zu berechnen.

Die zentrale Aussage der Aufgabe ist daher:

> NoSQL-Datenbanken eignen sich gut für flexible, verschachtelte Dokumentdaten. Relationale Datenbanken eignen sich gut für strukturierte, tabellarische Daten. In praktischen Anwendungen können beide Ansätze kombiniert werden, um eine vollständige Auswertung zu ermöglichen.

---

## Nützliche Befehle

PostgreSQL starten:

```bash
brew services start postgresql@17
```

MongoDB starten:

```bash
brew services start mongodb-community@8.0
```

Dienste prüfen:

```bash
brew services list
```

Skript ausführen:

```bash
python scripts/nosql_recipes_demo.py
```

Ergebnisdatei anzeigen:

```bash
cat results/nosql_results.txt
```

Ergebnisordner im Finder öffnen:

```bash
open results
```

Datenbanken nach der Arbeit stoppen:

```bash
brew services stop postgresql@17
brew services stop mongodb-community@8.0
```

---

## Abgrenzung zu Übungsblatt 1

Diese README beschreibt nur **Übungsblatt 2**.

Übungsblatt 1 behandelte relationale Datenbanken, PostgreSQL, CSV-Import, Normalisierung und parallele Transaktionen. Übungsblatt 2 nutzt die relationalen Sales-Daten weiter, untersucht aber nicht mehr das Transaktionsverhalten. Der Fokus liegt stattdessen auf NoSQL-Daten, MongoDB, Rezeptdokumenten und der Verbindung zwischen relationalen Verkaufsdaten und dokumentorientierten Rezeptdaten.
