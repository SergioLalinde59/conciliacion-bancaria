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
    
    print("Searching for existing classification for Traslado De Fondo...")
    cursor.execute("""
        SELECT TerceroID, GrupoID, ConceptoID, Descripcion 
        FROM movimientos 
        WHERE Descripcion ILIKE '%Traslado De Fondo%' 
          AND TerceroID IS NOT NULL 
        LIMIT 5
    """)
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"Found: {row}")
    else:
        print("No classified examples found.")
        # Check specific Tercero
        cursor.execute("SELECT * FROM terceros WHERE descripcion ILIKE '%Fondo%' or tercero ILIKE '%Fondo%'")
        print("Possible Terceros:", cursor.fetchall())

    conn.close()
except Exception as e:
    print(e)
