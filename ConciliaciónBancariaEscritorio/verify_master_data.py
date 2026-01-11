import psycopg2
import sys
import os

sys.path.append(os.getcwd())

from src.domain.models.cuenta import Cuenta
from src.infrastructure.database.postgres_cuenta_repository import PostgresCuentaRepository
from src.domain.models.moneda import Moneda
from src.infrastructure.database.postgres_moneda_repository import PostgresMonedaRepository
from src.domain.models.tipo_mov import TipoMov
from src.infrastructure.database.postgres_tipo_mov_repository import PostgresTipoMovRepository
from src.domain.models.grupo import Grupo
from src.infrastructure.database.postgres_grupo_repository import PostgresGrupoRepository
from src.domain.models.concepto import Concepto
from src.infrastructure.database.postgres_concepto_repository import PostgresConceptoRepository

def main():
    print("=== VERIFICACIÓN DE DATOS MAESTROS (HEXAGONAL) ===")
    
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
        # Cuentas
        print("\n--- Cuentas ---")
        repo_cuentas = PostgresCuentaRepository(conn)
        cuentas = repo_cuentas.obtener_todas()
        print(f"Total Cuentas: {len(cuentas)}")
        if cuentas: print(f"Ejemplo: {cuentas[0]}")
        
        # Monedas
        print("\n--- Monedas ---")
        repo_monedas = PostgresMonedaRepository(conn)
        monedas = repo_monedas.obtener_todas()
        print(f"Total Monedas: {len(monedas)}")
        if monedas: print(f"Ejemplo: {monedas[0]}")

        # TipoMov
        print("\n--- TipoMov ---")
        repo_tipomov = PostgresTipoMovRepository(conn)
        tipos = repo_tipomov.obtener_todos()
        print(f"Total Tipos: {len(tipos)}")
        if tipos: print(f"Ejemplo: {tipos[0]}")
        
        # Grupos
        print("\n--- Grupos ---")
        repo_grupos = PostgresGrupoRepository(conn)
        grupos = repo_grupos.obtener_todos()
        print(f"Total Grupos: {len(grupos)}")
        if grupos: print(f"Ejemplo: {grupos[0]}")

        # Conceptos
        print("\n--- Conceptos ---")
        repo_conceptos = PostgresConceptoRepository(conn)
        conceptos = repo_conceptos.obtener_todos()
        print(f"Total Conceptos: {len(conceptos)}")
        if conceptos: print(f"Ejemplo: {conceptos[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
