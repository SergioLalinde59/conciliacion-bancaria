import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    user='postgres', 
    password='SLB', 
    database='Mvtos'
)

cursor = conn.cursor()

# Investigar estructura de cada tabla
tablas = ['monedas', 'cuentas', 'contactos', 'grupos', 'conceptos']

for tabla in tablas:
    print(f"\n{'='*60}")
    print(f"Tabla: {tabla.upper()}")
    print('='*60)
    
    # Obtener columnas
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = '{tabla}'
        ORDER BY ordinal_position
    """)
    
    print("\nColumnas:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
    
    # Obtener claves primarias
    cursor.execute(f"""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = '{tabla}'::regclass AND i.indisprimary
    """)
    
    pks = cursor.fetchall()
    if pks:
        print(f"\nClave Primaria: {', '.join([pk[0] for pk in pks])}")
    else:
        print("\n⚠ NO TIENE CLAVE PRIMARIA")

cursor.close()
conn.close()
