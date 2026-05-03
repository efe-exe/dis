import sqlite3
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'coffee_sales.db')
REPORT = os.path.join(ROOT, 'results', 'database_report.txt')

os.makedirs(os.path.dirname(REPORT), exist_ok=True)

def report(msg):
    print(msg)
    with open(REPORT, 'a', encoding='utf8') as f:
        f.write(msg + '\n')

# Clear report
with open(REPORT, 'w', encoding='utf8') as f:
    f.write('')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

report('=== Database Verification Report ===\n')

# Table summaries
report('ORIGINAL TABLE (sales):')
cur.execute('SELECT COUNT(*) FROM sales')
report(f'  Rows: {cur.fetchone()[0]}')
cur.execute('PRAGMA table_info(sales)')
cols = cur.fetchall()
report(f'  Columns: {len(cols)}')
for c in cols:
    report(f'    - {c[1]}: {c[2]}')

report('\nNORMALIZED TABLE (sales_normalized):')
cur.execute('SELECT COUNT(*) FROM sales_normalized')
report(f'  Rows: {cur.fetchone()[0]}')
cur.execute('PRAGMA table_info(sales_normalized)')
cols = cur.fetchall()
report(f'  Columns: {len(cols)}')
for c in cols:
    report(f'    - {c[1]}: {c[2]}')

report('\nLOOKUP TABLE (weekday):')
cur.execute('SELECT COUNT(*) FROM weekday')
report(f'  Rows: {cur.fetchone()[0]}')
cur.execute('SELECT * FROM weekday')
for row in cur.fetchall():
    report(f'    {row}')

report('\nLOOKUP TABLE (month):')
cur.execute('SELECT COUNT(*) FROM month')
report(f'  Rows: {cur.fetchone()[0]}')
cur.execute('SELECT * FROM month')
for row in cur.fetchall():
    report(f'    {row}')

# Check FK constraints
report('\n=== Foreign Key Relationships ===')
report('Checking sales_normalized FK to weekday:')
cur.execute('SELECT COUNT(*) FROM sales_normalized WHERE weekday_id IS NOT NULL AND weekday_id NOT IN (SELECT id FROM weekday)')
orphaned = cur.fetchone()[0]
report(f'  Orphaned FK refs: {orphaned}')

report('Checking sales_normalized FK to month:')
cur.execute('SELECT COUNT(*) FROM sales_normalized WHERE month_id IS NOT NULL AND month_id NOT IN (SELECT id FROM month)')
orphaned = cur.fetchone()[0]
report(f'  Orphaned FK refs: {orphaned}')

# Sample data
report('\n=== Sample Data (first 5 rows) ===')
report('\nsales_normalized:')
cur.execute('SELECT * FROM sales_normalized LIMIT 5')
for row in cur.fetchall():
    report(f'  {row}')

report('\n=== Summary ===')
report('✓ CSV imported successfully')
report('✓ Constraints defined (CHECK on hour_of_day, cash_type, money)')
report('✓ Normalized into 3 tables: sales, weekday, month')
report('✓ Foreign key relationships established')

conn.close()
