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
    
    print("Checking schema for 'movimientos'...")
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'movimientos'")
    columns = cursor.fetchall()
    print([col[0] for col in columns])

    # Also check 'terceros' for that reference
    print("\nChecking Terceros for ref '01512988021':")
    cursor.execute("SELECT * FROM terceros WHERE referencia = '01512988021'")
    print(cursor.fetchall())
    
    # Check Movimientos history for that reference
    print("\nChecking Movimientos history for ref '01512988021':")
    cursor.execute("SELECT TerceroID, COUNT(*) FROM movimientos WHERE Referencia = '01512988021' AND TerceroID IS NOT NULL GROUP BY TerceroID")
    print(cursor.fetchall())

    conn.close()
except Exception as e:
    print(e)
