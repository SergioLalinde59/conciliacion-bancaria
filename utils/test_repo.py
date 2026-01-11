import sys
sys.path.insert(0, 'Backend')

import psycopg2
from src.infrastructure.database.postgres_movimiento_repository import PostgresMovimientoRepository

# Conectar
conn = psycopg2.connect(
    host='localhost',
    port='5433',
    database='Mvtos',
    user='postgres',
    password='SLB'
)

# Crear repositorio
repo = PostgresMovimientoRepository(conn)

try:
    # Intentar obtener todos
    movimientos = repo.obtener_todos()
    print(f"✅ Repositorio funciona correctamente")
    print(f"Total movimientos obtenidos: {len(movimientos)}")
    
    if len(movimientos) > 0:
        mov = movimientos[0]
        print(f"\nPrimer movimiento:")
        print(f"  ID: {mov.id}")
        print(f"  Fecha: {mov.fecha}")
        print(f"  Descripción: {mov.descripcion[:30]}...")
        print(f"  Cuenta display: {mov.cuenta_display}")
        print(f"  Moneda display: {mov.moneda_display}")
        
except Exception as e:
    print(f"❌ Error en el repositorio:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

conn.close()
