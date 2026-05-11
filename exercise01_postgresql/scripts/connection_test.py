import psycopg2

# Verbindung zur Datenbank herstellen
conn = psycopg2.connect(
    host="localhost",
    dbname="dis_test_db",
    user="Bob",
    password="bobbycar"
)

print("Verbindung erfolgreich:", conn.status)
conn.close()