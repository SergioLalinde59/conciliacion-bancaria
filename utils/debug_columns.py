import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='Mvtos',
    user='postgres',
    password='SLB'
)

cur = conn.cursor()

# Get all columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'movimientos' 
    ORDER BY ordinal_position
""")

columns = [r[0] for r in cur.fetchall()]

print("Columnas de la tabla 'movimientos' (en orden):")
for i, col in enumerate(columns, 1):
    print(f"{i:2}. {col}")

# Ahora ejecutar el SELECT que usa el repo
print("\n" + "="*60)
print("Probando el SELECT del repositorio:")
print("="*60)

cur.execute("""
    SELECT m.Id, m.Fecha, m.Descripcion, m.Referencia, m.Valor, m.USD, m.TRM, 
           m.MonedaID, m.CuentaID, m.TerceroID, m.GrupoID, m.ConceptoID, m.created_at,
           c.cuenta AS cuenta_nombre,
           mon.moneda AS moneda_nombre,
           t.tercero AS tercero_nombre,
           g.grupo AS grupo_nombre,
           con.concepto AS concepto_nombre
    FROM movimientos m
    LEFT JOIN cuentas c ON m.CuentaID = c.cuentaid
    LEFT JOIN monedas mon ON m.MonedaID = mon.monedaid
    LEFT JOIN terceros t ON m.TerceroID = t.terceroid
    LEFT JOIN grupos g ON m.GrupoID = g.grupoid
    LEFT JOIN conceptos con ON m.ConceptoID = con.conceptoid
    LIMIT 1
""")

row = cur.fetchone()
if row:
    print("\nPrimera fila obtenida:")
    for i, value in enumerate(row):
        print(f"  Posición {i}: {value}")

conn.close()
