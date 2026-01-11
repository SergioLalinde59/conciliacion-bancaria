import psycopg2
import sys
import os

sys.path.append(os.getcwd())

from src.infrastructure.database.postgres_movimiento_repository import PostgresMovimientoRepository
from src.infrastructure.repositories.in_memory_reglas_repository import InMemoryReglasRepository
from src.application.services.clasificacion_service import ClasificacionService

def main():
    print("=== TEST DE CLASIFICACIÓN AUTOMÁTICA ===")
    
    conn = psycopg2.connect(host='localhost', port='5433', database='Mvtos', user='postgres', password='SLB')
    
    try:
        # Inyección de dependencias
        mov_repo = PostgresMovimientoRepository(conn)
        reglas_repo = InMemoryReglasRepository()
        service = ClasificacionService(mov_repo, reglas_repo)
        
        print("\n1. Buscando pendientes...")
        pendientes = mov_repo.buscar_pendientes_clasificacion()
        print(f"   Total pendientes: {len(pendientes)}")
        
        if not pendientes:
            print("   (No hay nada que clasificar)")
            return

        print("\n2. Ejecutando auto-clasificación (Dry Run - No commit si fuera real en UI, aquí sí guardamos para demo)...")
        resumen = service.auto_clasificar_pendientes()
        
        print(f"\nRESULTADOS:")
        print(f"Total procesados: {resumen['total']}")
        print(f"Clasificados con éxito: {resumen['clasificados']}")
        print("\nDetalles:")
        for det in resumen['detalles']:
            print(f" - {det}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
