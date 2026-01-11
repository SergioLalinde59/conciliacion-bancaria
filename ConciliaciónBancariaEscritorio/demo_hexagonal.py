import psycopg2
import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.append(os.getcwd())

from src.domain.models.tercero import Tercero
from src.infrastructure.database.postgres_tercero_repository import PostgresTerceroRepository

def main():
    print("--- DEMO DE ARQUITECTURA HEXAGONAL ---")
    
    # 1. Configuración (Infraestructura)
    # En una app real, esto vendría de variables de entorno
    db_config = {
        'host': 'localhost',
        'port': '5433',
        'database': 'Mvtos',
        'user': 'postgres',
        'password': 'SLB'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        print("1. Conexión a BD establecida.")
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        return

    # 2. Inyección de Dependencias
    # Le damos al repositorio la conexión que necesita
    repo = PostgresTerceroRepository(conn)
    print("2. Repositorio inicializado.")

    # 3. Lógica de Dominio (Pura)
    # Creamos un objeto en memoria. Aún no existe en la BD.
    nuevo_tercero = Tercero(
        terceroid=None,
        tercero="Demo Hexagonal",
        descripcion="Prueba de arquitectura",
        referencia="REF-HEX-001"
    )
    print(f"3. Objeto de dominio creado en memoria: {nuevo_tercero}")

    # 4. Persistencia
    # Usamos el puerto (interfaz) para guardar.
    try:
        # Primero verificamos si ya existe para no duplicar en cada corrida de demo
        existentes = repo.buscar_por_descripcion("Prueba de arquitectura")
        if existentes:
            print(f"   (El tercero ya existía, usando el primero encontrado: ID {existentes[0].terceroid})")
            guardado = existentes[0]
        else:
            guardado = repo.guardar(nuevo_tercero)
            print(f"4. Objeto guardado en BD. Nuevo ID: {guardado.terceroid}")
            
        # 5. Recuperación
        recuperado = repo.obtener_por_id(guardado.terceroid)
        print(f"5. Objeto recuperado de BD: {recuperado}")
        
    except Exception as e:
        print(f"Error en persistencia: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
