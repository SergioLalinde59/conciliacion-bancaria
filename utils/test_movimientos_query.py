import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='Mvtos',
    user='postgres',
    password='SLB'
)

cur = conn.cursor()

# Probar la consulta exacta que usa el repositorio
query = """
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
    ORDER BY m.Fecha DESC, m.Id DESC
    LIMIT 5
"""

try:
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Registros encontrados: {len(rows)}")
    
    if len(rows) > 0:
        print("\nPrimeros 5 movimientos:")
        for row in rows:
            print(f"ID: {row[0]}, Fecha: {row[1]}, Descripción: {row[2][:30]}...")
            print(f"  Cuenta: {row[13]}, Moneda: {row[14]}")
            print()
    else:
        print("No se encontraron movimientos")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

conn.close()
