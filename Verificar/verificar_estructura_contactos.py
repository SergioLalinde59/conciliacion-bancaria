import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Ver estructura de la tabla contactos
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'contactos'
    ORDER BY ordinal_position
""")

print("Estructura de la tabla 'contactos':")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]:<30} {row[1]}")

cursor.close()
conn.close()
