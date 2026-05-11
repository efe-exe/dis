"""Exercise 1, task 2b: concurrent transactions in PostgreSQL.

This script follows the exercise sheet in the prescribed order:
(i)   create/connect to a persistent database via connection A
(ii)  create a table and insert one initial tuple
(iii) open a second connection to the same database (connection B)
(iv)  start a new transaction in each connection
(v)   insert a new row via connection A
(vi)  insert a different new row via connection B
(vii) inspect the table contents in both connections
(viii) commit both transactions and inspect the committed state
(ix)  open a third connection and inspect the table contents
(x)   start a new transaction in each connection
(xi)  update the initial row in both transactions with different values
(xii) commit both transactions and inspect the committed state
(xiii) open a third connection and inspect the table contents

The script writes the output to stdout and to results/concurrency_results.txt.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import threading
import time
from dataclasses import dataclass
from typing import Iterable, Sequence

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED


@dataclass(frozen=True)
class DsnConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str

    def as_kwargs(self) -> dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
        }


TABLE_NAME = "dis_concurrency_demo"
RESULTS_PATH = pathlib.Path(__file__).resolve().parents[1] / "results" / "concurrency_results.txt"


class Logger:
    def __init__(self, path: pathlib.Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("w", encoding="utf-8")
        self._lock = threading.Lock()

    def close(self) -> None:
        self._file.close()

    def log(self, message: str = "") -> None:
        with self._lock:
            print(message)
            self._file.write(message + "\n")
            self._file.flush()


logger = Logger(RESULTS_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PostgreSQL concurrency demo for exercise 1, task 2b")
    parser.add_argument("--host", default=os.environ.get("PGHOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PGPORT", "5432")))
    parser.add_argument("--dbname", default=os.environ.get("PGDATABASE", "dis_test_db"))
    parser.add_argument("--user", default=os.environ.get("PGUSER", "bob"))
    parser.add_argument("--password", default=os.environ.get("PGPASSWORD", "bobbycar"))
    return parser.parse_args()


def connect(cfg: DsnConfig):
    conn = psycopg2.connect(**cfg.as_kwargs())
    conn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
    return conn


def fq_table() -> sql.SQL:
    return sql.Identifier(TABLE_NAME)


def run_query(conn, query: sql.SQL | str, params: Sequence[object] | None = None) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description is None:
            return []
        return cur.fetchall()


def print_rows(conn, heading: str) -> list[tuple]:
    rows = run_query(
        conn,
        sql.SQL("SELECT id, demo_value, last_updated FROM {} ORDER BY id").format(fq_table()),
    )
    logger.log(heading)
    if not rows:
        logger.log("  <empty>")
        return rows
    for row in rows:
        logger.log(f"  {row}")
    return rows


def execute(conn, statement: sql.SQL | str, params: Sequence[object] | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(statement, params)


def ensure_transaction_started(conn) -> None:
    execute(conn, "BEGIN")


def main() -> int:
    args = parse_args()
    cfg = DsnConfig(args.host, args.port, args.dbname, args.user, args.password)

    conn_a = connect(cfg)
    conn_b = None
    conn_c = None

    try:
        logger.log("Teil 2b — experimentelle Demonstration paralleler Transaktionen in PostgreSQL")
        logger.log(f"Verbindung: host={cfg.host} port={cfg.port} dbname={cfg.dbname} user={cfg.user}")
        logger.log("")

        # (i) Neue persistente Datenbank verbinden: Verbindung A bleibt offen.
        logger.log("(i) Verbindung A geöffnet und offen gehalten.")

        # (ii) Neue Tabelle anlegen und ein Tupel einfügen.
        logger.log("(ii) Tabelle anlegen und Initialtupel einfügen.")
        execute(conn_a, sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(fq_table()))
        execute(
            conn_a,
            sql.SQL(
                """
                CREATE TABLE {} (
                    id BIGSERIAL PRIMARY KEY,
                    demo_value TEXT NOT NULL,
                    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            ).format(fq_table()),
        )
        execute(
            conn_a,
            sql.SQL("INSERT INTO {} (demo_value) VALUES (%s)").format(fq_table()),
            ("initial value",),
        )
        conn_a.commit()
        logger.log("    Initialtupel wurde committed.")
        print_rows(conn_a, "    Inhalt nach Schritt (ii):")
        logger.log("")

        # (iii) Zweite Verbindung zur gleichen Datenbank.
        logger.log("(iii) Zweite Verbindung B geöffnet.")
        conn_b = connect(cfg)
        logger.log("")

        # (iv) Neue Transaktion in jeder Verbindung starten.
        logger.log("(iv) Neue Transaktionen in A und B starten.")
        ensure_transaction_started(conn_a)
        ensure_transaction_started(conn_b)
        logger.log("    Beide Transaktionen sind aktiv.")
        logger.log("")

        # (v) Mit Verbindung A einen neuen Datensatz einfügen.
        logger.log("(v) Verbindung A fügt einen neuen Datensatz ein.")
        execute(
            conn_a,
            sql.SQL("INSERT INTO {} (demo_value) VALUES (%s)").format(fq_table()),
            ("value from connection A",),
        )
        logger.log("    Einfügen in A ausgeführt, noch nicht committed.")

        # (vi) Mit Verbindung B einen anderen Datensatz einfügen.
        logger.log("(vi) Verbindung B fügt einen anderen neuen Datensatz ein.")
        execute(
            conn_b,
            sql.SQL("INSERT INTO {} (demo_value) VALUES (%s)").format(fq_table()),
            ("value from connection B",),
        )
        logger.log("    Einfügen in B ausgeführt, noch nicht committed.")
        logger.log("")

        # (vii) Tabelleninhalt in beiden Verbindungen prüfen.
        logger.log("(vii) Sichtbarkeit der Daten in A und B prüfen.")
        print_rows(conn_a, "    Sicht in Verbindung A:")
        print_rows(conn_b, "    Sicht in Verbindung B:")
        logger.log("    Erwartung: Jede Verbindung sieht ihre eigenen uncommitted Änderungen, aber nicht die der anderen.")
        logger.log("")

        # (viii) Beide Transaktionen committen und den Zustand erneut prüfen.
        logger.log("(viii) Beide Transaktionen committen.")
        conn_a.commit()
        conn_b.commit()
        logger.log("    Beide Commits erfolgreich.")
        print_rows(conn_a, "    Nach dem Commit in Verbindung A:")
        print_rows(conn_b, "    Nach dem Commit in Verbindung B:")
        logger.log("")

        # (ix) Dritte Verbindung öffnen und den Inhalt prüfen.
        logger.log("(ix) Dritte Verbindung C öffnen und Tabelleninhalt prüfen.")
        conn_c = connect(cfg)
        print_rows(conn_c, "    Sicht in Verbindung C:")
        logger.log("")

        # (x) Neue Transaktion in jeder Verbindung starten.
        logger.log("(x) Neue Transaktionen in A und B starten.")
        ensure_transaction_started(conn_a)
        ensure_transaction_started(conn_b)
        logger.log("    Beide Transaktionen sind wieder aktiv.")
        logger.log("")

        # (xi) Das Initialtupel in beiden Transaktionen aktualisieren.
        #      Hier wird bewusst das gleiche Tupel in zwei parallelen Transaktionen geändert.
        #      Die zweite UPDATE-Anweisung wartet in PostgreSQL auf den Row-Lock der ersten.
        logger.log("(xi) Beide Verbindungen aktualisieren das Initialtupel mit unterschiedlichen Werten.")
        update_ready_a = threading.Event()
        update_started_b = threading.Event()
        allow_commit_a = threading.Event()
        worker_errors: list[BaseException] = []
        worker_lock = threading.Lock()

        def remember_error(exc: BaseException) -> None:
            with worker_lock:
                worker_errors.append(exc)

        def worker_a() -> None:
            try:
                execute(
                    conn_a,
                    sql.SQL("UPDATE {} SET demo_value = %s, last_updated = NOW() WHERE id = %s").format(fq_table()),
                    ("updated by A", 1),
                )
                logger.log("    A: UPDATE ausgeführt, Row-Lock wird gehalten.")
                update_ready_a.set()
                allow_commit_a.wait()
                conn_a.commit()
                logger.log("    A: Commit erfolgreich.")
            except BaseException as exc:  # pragma: no cover - defensive logging
                remember_error(exc)
                try:
                    conn_a.rollback()
                except Exception:
                    pass

        def worker_b() -> None:
            try:
                update_ready_a.wait()
                update_started_b.set()
                execute(
                    conn_b,
                    sql.SQL("UPDATE {} SET demo_value = %s, last_updated = NOW() WHERE id = %s").format(fq_table()),
                    ("updated by B", 1),
                )
                logger.log("    B: UPDATE ausgeführt, nachdem A seinen Lock freigegeben hat.")
                conn_b.commit()
                logger.log("    B: Commit erfolgreich.")
            except BaseException as exc:  # pragma: no cover - defensive logging
                remember_error(exc)
                try:
                    conn_b.rollback()
                except Exception:
                    pass

        thread_a = threading.Thread(target=worker_a, name="worker-a")
        thread_b = threading.Thread(target=worker_b, name="worker-b")
        thread_a.start()
        update_ready_a.wait(timeout=10)
        thread_b.start()
        update_started_b.wait(timeout=10)
        time.sleep(0.2)
        allow_commit_a.set()
        thread_a.join()
        thread_b.join()

        if worker_errors:
            raise RuntimeError(f"Fehler in den Parallel-Workern: {worker_errors[0]}")

        logger.log("    Beide Updates wurden erfolgreich verarbeitet.")
        logger.log("")

        # (xii) Beide Transaktionen committen und den Zustand erneut prüfen.
        logger.log("(xii) Nach den Updates den Tabelleninhalt erneut prüfen.")
        print_rows(conn_a, "    Nach dem zweiten Commit in Verbindung A:")
        print_rows(conn_b, "    Nach dem zweiten Commit in Verbindung B:")
        logger.log("    Der letzte erfolgreich abgeschlossene Update-Vorgang bestimmt den finalen Wert der Zeile.")
        logger.log("")

        # (xiii) Dritte Verbindung öffnen und den endgültigen Zustand prüfen.
        logger.log("(xiii) Dritte Verbindung C prüft den endgültigen Tabelleninhalt.")
        if conn_c is not None:
            conn_c.close()
        conn_c = connect(cfg)
        print_rows(conn_c, "    Endgültige Sicht in Verbindung C:")
        logger.log("")

        logger.log("Fertig. Das Ergebnisprotokoll liegt in results/concurrency_results.txt")
        return 0
    finally:
        for conn in (conn_c, conn_b, conn_a):
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
