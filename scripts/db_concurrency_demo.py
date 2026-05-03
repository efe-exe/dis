import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'coffee_demo.db')
DB_PATH = os.path.abspath(DB_PATH)
RESULTS = os.path.join(os.path.dirname(__file__), '..', 'results', 'concurrency_results.txt')

os.makedirs(os.path.dirname(RESULTS), exist_ok=True)

def log(msg):
    line = f"[{datetime.now().isoformat()}] {msg}\n"
    print(line, end='')
    with open(RESULTS, 'a', encoding='utf8') as f:
        f.write(line)

def run():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # initialize variables so finally can close safely
    conn_a = conn_b = conn_c = None
    cur_a = cur_b = cur_c = None
    b_insert_failed = False
    a_commit_success = False
    b_commit_success = False
    a_update_commit_success = False
    b_update_commit_success = False

    # i) Connection A
    conn_a = sqlite3.connect(DB_PATH, timeout=10)
    cur_a = conn_a.cursor()
    log('Connected (A)')

    # ii) create table and insert a tuple
    cur_a.execute('''CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note TEXT
    )''')
    cur_a.execute("INSERT INTO sales (note) VALUES (?)", ("initial",))
    conn_a.commit()
    log('Created table and inserted initial tuple (committed)')

    # iii) Connection B
    conn_b = sqlite3.connect(DB_PATH, timeout=10)
    cur_b = conn_b.cursor()
    log('Connected (B)')

    try:
        # iv) Start transaction in both
        cur_a.execute('BEGIN')
        cur_b.execute('BEGIN')
        log('Started transactions on A and B')

        # v) A adds a new record
        cur_a.execute("INSERT INTO sales (note) VALUES (?)", ("from A",))
        log('A inserted record (uncommitted)')

        # vi) B adds another new record (may fail if DB locked)
        try:
            cur_b.execute("INSERT INTO sales (note) VALUES (?)", ("from B",))
            log('B inserted record (uncommitted)')
        except sqlite3.OperationalError as e:
            b_insert_failed = True
            log(f'B failed to insert: {e}')
            try:
                conn_b.rollback()
                log('B rolled back')
            except Exception:
                pass

        # vii) Check contents in both connections
        try:
            cur_a.execute('SELECT * FROM sales')
            rows_a = cur_a.fetchall()
            log(f'A sees {len(rows_a)} rows: {rows_a}')
        except Exception as e:
            log(f'Error reading in A: {e}')

        try:
            cur_b.execute('SELECT * FROM sales')
            rows_b = cur_b.fetchall()
            log(f'B sees {len(rows_b)} rows: {rows_b}')
        except Exception as e:
            log(f'Error reading in B: {e}')

        # viii) Commit both (only commit B if its insert succeeded)
        try:
            conn_a.commit()
            log('A committed')
            a_commit_success = True
        except Exception as e:
            log(f'A commit failed: {e}')
        
        if not b_insert_failed:
            try:
                conn_b.commit()
                log('B committed')
                b_commit_success = True
            except sqlite3.OperationalError as e:
                log(f'B commit failed: {e}')
                try:
                    conn_b.rollback()
                except Exception:
                    pass
        else:
            log('B cannot commit because insert failed')

        # ix) Only if BOTH committed successfully: Open C and check
        if a_commit_success and b_commit_success:
            log('Both A and B committed successfully')
            conn_c = sqlite3.connect(DB_PATH)
            cur_c = conn_c.cursor()
            cur_c.execute('SELECT * FROM sales')
            log(f'C sees: {cur_c.fetchall()}')
        else:
            log(f'SKIPPING step ix: Not both successful (A={a_commit_success}, B={b_commit_success})')

        # x) Start new transactions in A and B (only if both previous commits successful)
        if a_commit_success and b_commit_success:
            cur_a.execute('BEGIN')
            cur_b.execute('BEGIN')
            log('Started second transactions on A and B')

            # xi) Modify the record created in step ii (id=1)
            cur_a.execute("UPDATE sales SET note=? WHERE id=1", ("updated by A",))
            log('A updated id=1 (uncommitted)')
            try:
                cur_b.execute("UPDATE sales SET note=? WHERE id=1", ("updated by B",))
                log('B updated id=1 (uncommitted)')
            except Exception as e:
                log(f'B failed to update id=1: {e}')

            # xii) Commit both
            try:
                conn_a.commit()
                log('A committed update')
                a_update_commit_success = True
            except Exception as e:
                log(f'A update commit failed: {e}')
                try:
                    conn_a.rollback()
                except:
                    pass
            
            try:
                conn_b.commit()
                log('B committed update')
                b_update_commit_success = True
            except Exception as e:
                log(f'B update commit failed: {e}')
                try:
                    conn_b.rollback()
                except:
                    pass

            # xiii) Only if BOTH UPDATE commits successful: Open C and check
            if a_update_commit_success and b_update_commit_success:
                log('Both A and B UPDATE committed successfully')
                if conn_c is None:
                    conn_c = sqlite3.connect(DB_PATH)
                    cur_c = conn_c.cursor()
                cur_c.execute('SELECT * FROM sales')
                log(f'Final C sees: {cur_c.fetchall()}')
            else:
                log(f'SKIPPING step xiii: Not both UPDATE successful (A={a_update_commit_success}, B={b_update_commit_success})')
        else:
            log('SKIPPING steps x-xiii: First commit round not both successful')

    except Exception as e:
        log(f'Unexpected error during demo: {e}')
    finally:
        for c, name in ((conn_a, 'A'), (conn_b, 'B'), (conn_c, 'C')):
            try:
                if c:
                    c.close()
                    log(f'Connection {name} closed')
            except Exception:
                pass

if __name__ == '__main__':
    run()
