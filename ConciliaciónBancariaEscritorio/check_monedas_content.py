import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monedas")
    rows = cursor.fetchall()
    print("Monedas Table Content:")
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(e)
