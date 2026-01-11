import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='Mvtos',
    user='postgres',
    password='SLB'
)

cur = conn.cursor()

# Verificar las columnas de la tabla movimientos
query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'movimientos'
    ORDER BY ordinal_position
"""

cur.execute(query)
columns = cur.fetchall()

print("Columnas en la tabla 'movimientos':")
print("-" * 50)
for col in columns:
    print(f"{col[0]:25} {col[1]}")

conn.close()
