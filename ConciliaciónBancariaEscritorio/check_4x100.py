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
    
    print("Searching for existing classification for 4x100...")
    cursor.execute("""
        SELECT TerceroID, GrupoID, ConceptoID, Descripcion 
        FROM movimientos 
        WHERE Descripcion ILIKE '%Impto Gobierno 4x100%' 
          AND TerceroID IS NOT NULL 
        LIMIT 5
    """)
    results = cursor.fetchall()
    for row in results:
        print(f"Found: {row}")
        
    if not results:
        print("No classified examples found. checking concepts...")
        cursor.execute("SELECT * FROM conceptos WHERE concepto ILIKE '%4x100%' OR concepto ILIKE '%GMF%'")
        print(cursor.fetchall())
        
        cursor.execute("SELECT * FROM grupos WHERE grupo ILIKE '%Impuesto%' or grupo ILIKE '%Gasto%'")
        print(cursor.fetchall())

    conn.close()
except Exception as e:
    print(e)
