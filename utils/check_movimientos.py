import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='Mvtos',
    user='postgres',
    password='SLB'
)

cur = conn.cursor()

# Verificar total de movimientos
cur.execute('SELECT COUNT(*) FROM movimientos')
total = cur.fetchone()[0]
print(f'Total movimientos: {total}')

# Verificar si la columna activa existe
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'movimientos' AND column_name = 'activa'
""")
result = cur.fetchone()
print(f'Columna activa existe: {result is not None}')

if result:
    # Si existe, verificar cuántos están activos
    cur.execute('SELECT COUNT(*) FROM movimientos WHERE activa = TRUE')
    activos = cur.fetchone()[0]
    print(f'Movimientos activos: {activos}')
    
    cur.execute('SELECT COUNT(*) FROM movimientos WHERE activa = FALSE')
    inactivos = cur.fetchone()[0]
    print(f'Movimientos inactivos: {inactivos}')
    
    cur.execute('SELECT COUNT(*) FROM movimientos WHERE activa IS NULL')
    nulls = cur.fetchone()[0]
    print(f'Movimientos con activa NULL: {nulls}')
else:
    print('La columna activa NO existe')

# Verificar si existe TipoMovID
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'movimientos' AND column_name = 'tipomovid'
""")
result_tipomov = cur.fetchone()
print(f'Columna TipoMovID existe: {result_tipomov is not None}')

conn.close()
