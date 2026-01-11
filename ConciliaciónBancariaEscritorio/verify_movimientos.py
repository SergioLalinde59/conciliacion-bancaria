import psycopg2
import sys
import os
from datetime import date
from decimal import Decimal

sys.path.append(os.getcwd())

from src.domain.models.movimiento import Movimiento
from src.infrastructure.database.postgres_movimiento_repository import PostgresMovimientoRepository

def main():
    print("=== VERIFICACIÓN DE MOVIMIENTOS (HEXAGONAL) ===")
    
    db_config = {
        'host': 'localhost',
        'port': '5433',
        'database': 'Mvtos',
        'user': 'postgres',
        'password': 'SLB'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
    except Exception as e:
        print(f"Error conexión: {e}")
        return

    try:
        repo = PostgresMovimientoRepository(conn)
        
        # 1. Crear un movimiento de prueba
        print("\n1. Creando Movimiento de Prueba...")
        nuevo_mov = Movimiento(
            moneda_id=1,        # Asumiendo 1 existe (Pesos)
            cuenta_id=1,        # Asumiendo 1 existe (Efectivo)
            fecha=date.today(),
            valor=Decimal("-15000.50"),
            descripcion="Prueba Hexagonal",
            referencia="REF-TEST-HEX-001"
        )
        
        # Guardar
        guardado = repo.guardar(nuevo_mov)
        print(f"   ✓ Movimiento guardado con ID: {guardado.id}")
        
        # 2. Leer por ID
        print("\n2. Leyendo por ID...")
        leido = repo.obtener_por_id(guardado.id)
        print(f"   ✓ Recuperado: {leido.descripcion} | Valor: {leido.valor}")
        
        # 3. Buscar pendientes (debería aparecer porque no tiene grupo/concepto)
        print("\n3. Buscando Pendientes de Clasificación...")
        pendientes = repo.buscar_pendientes_clasificacion()
        encontrado = any(m.id == guardado.id for m in pendientes)
        if encontrado:
            print("   ✓ El movimiento nuevo aparece en pendientes (Correcto)")
        else:
            print("   ✗ El movimiento NO aparece en pendientes (Error)")
            
        # 4. Actualizar (Clasificar)
        print("\n4. Clasificando Movimiento...")
        leido.grupo_id = 1    # Asumiendo ID 1 existe
        leido.concepto_id = 1 # Asumiendo ID 1 existe
        actualizado = repo.guardar(leido)
        print("   ✓ Movimiento actualizado")
        
        # 5. Verificar que ya no está pendiente
        pendientes_post = repo.buscar_pendientes_clasificacion()
        encontrado_post = any(m.id == guardado.id for m in pendientes_post)
        if not encontrado_post:
            print("   ✓ El movimiento YA NO aparece en pendientes (Correcto)")
        else:
            print("   ✗ El movimiento sigue apareciendo en pendientes (Error)")

    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
