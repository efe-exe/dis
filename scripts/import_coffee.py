import sqlite3
import os
import pandas as pd
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_PATH = os.path.join(ROOT, 'Coffe_sales.csv')
DB_PATH = os.path.join(ROOT, 'coffee_sales.db')

def create_table(conn):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hour_of_day INTEGER NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
        cash_type TEXT NOT NULL CHECK (cash_type IN ('card','cash')),
        money REAL NOT NULL CHECK (money > 0),
        coffee_name TEXT,
        time_of_day TEXT,
        weekday TEXT,
        month_name TEXT,
        weekdaysort INTEGER,
        monthsort INTEGER,
        date TEXT,
        time TEXT
    )''')
    conn.commit()

def load_csv(conn):
    df = pd.read_csv(CSV_PATH)
    # basic type fixes
    df['hour_of_day'] = df['hour_of_day'].astype(int)
    df['weekdaysort'] = df['Weekdaysort'] if 'Weekdaysort' in df.columns else df['Weekdaysort']
    cur = conn.cursor()
    rows = df.to_dict(orient='records')
    for r in rows:
        cur.execute('''INSERT INTO sales (hour_of_day,cash_type,money,coffee_name,time_of_day,weekday,month_name,weekdaysort,monthsort,date,time)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                    (r.get('hour_of_day'), r.get('cash_type'), r.get('money'), r.get('coffee_name'), r.get('Time_of_Day'),
                     r.get('Weekday'), r.get('Month_name'), r.get('Weekdaysort'), r.get('Monthsort'), r.get('Date'), r.get('Time')))
    conn.commit()

def normalize(conn):
    cur = conn.cursor()
    # create lookup tables
    cur.execute('CREATE TABLE IF NOT EXISTS weekday (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, sort INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS month (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, sort INTEGER)')
    conn.commit()

    # populate lookups
    cur.execute('SELECT DISTINCT weekday, weekdaysort FROM sales')
    for name, sort in cur.fetchall():
        if name is None: continue
        cur.execute('INSERT OR IGNORE INTO weekday (name, sort) VALUES (?,?)', (name, sort))
    cur.execute('SELECT DISTINCT month_name, monthsort FROM sales')
    for name, sort in cur.fetchall():
        if name is None: continue
        cur.execute('INSERT OR IGNORE INTO month (name, sort) VALUES (?,?)', (name, sort))
    conn.commit()

    # create normalized sales table
    cur.execute('''CREATE TABLE IF NOT EXISTS sales_normalized (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hour_of_day INTEGER NOT NULL,
        cash_type TEXT NOT NULL,
        money REAL NOT NULL,
        coffee_name TEXT,
        time_of_day TEXT,
        weekday_id INTEGER,
        month_id INTEGER,
        date TEXT,
        time TEXT,
        FOREIGN KEY (weekday_id) REFERENCES weekday(id),
        FOREIGN KEY (month_id) REFERENCES month(id)
    )''')
    conn.commit()

    # populate normalized table by joining
    cur.execute('SELECT id, hour_of_day,cash_type,money,coffee_name,time_of_day,weekday,month_name,date,time FROM sales')
    rows = cur.fetchall()
    for r in rows:
        sid, hour, cash, money, coffee, tod, weekday, monthname, datev, timev = r
        cur.execute('SELECT id FROM weekday WHERE name=?', (weekday,))
        wid = cur.fetchone()
        wid = wid[0] if wid else None
        cur.execute('SELECT id FROM month WHERE name=?', (monthname,))
        mid = cur.fetchone()
        mid = mid[0] if mid else None
        cur.execute('INSERT INTO sales_normalized (hour_of_day,cash_type,money,coffee_name,time_of_day,weekday_id,month_id,date,time) VALUES (?,?,?,?,?,?,?,?,?)',
                    (hour, cash, money, coffee, tod, wid, mid, datev, timev))
    conn.commit()

def run():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        create_table(conn)
        load_csv(conn)
        # quick check
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM sales')
        print('Rows inserted:', cur.fetchone()[0])
        normalize(conn)
        cur.execute('SELECT COUNT(*) FROM sales_normalized')
        print('Rows in normalized table:', cur.fetchone()[0])
    finally:
        conn.close()

if __name__ == '__main__':
    run()
