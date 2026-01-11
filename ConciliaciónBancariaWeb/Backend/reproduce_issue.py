import sys
import os
import psycopg2
from datetime import date

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.infrastructure.database.postgres_movimiento_repository import PostgresMovimientoRepository

# DB Config (matching reproduce_error.py)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def main():
    try:
        print("Connecting to DB...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected.")
        
        repo = PostgresMovimientoRepository(conn)
        
        # Date range from user issue
        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)
        
        print(f"Fetching movements between {start_date} and {end_date}...")
        
        # Call buscar_avanzado with logic similar to frontend filters
        # Frontend: desde, hasta, cuentaId='', terceroId='', grupoId='', conceptoId='', 
        # excluirTraslados=true, excluirPrestamos=true, ...
        
        # Case 1: All filters like frontend default
        movimientos, total = repo.buscar_avanzado(
            fecha_inicio=start_date,
            fecha_fin=end_date,
            excluir_traslados=False, # Let's try False first to see everything
            excluir_prestamos=False
        )
        
        print(f"Total found (No exclusions): {total}")
        
        # Case 2: With exclusions as per screenshot (User has Checked 'Excluir Traslados', 'Excluir Tita', 'Excluir Préstamos')
        # Note: 'Excluir Tita' corresponds to a specific excluded group, likely handled in 'grupos_excluidos'
        # But let's check basic exclusions first.
        
        movimientos_filtered, total_filtered = repo.buscar_avanzado(
            fecha_inicio=start_date,
            fecha_fin=end_date,
            excluir_traslados=True,
            excluir_prestamos=True
        )
        print(f"Total found (With Exclusions): {total_filtered}")
        
        if total > 0:
            print("\nFirst 5 movements (No Exclusions):")
            for m in movimientos[:5]:
                print(f"ID: {m.id}, Date: {m.fecha}, Desc: {m.descripcion}, Val: {m.valor}, Group: {m.grupo_id}")

        if total_filtered == 0 and total > 0:
             print("\nAll movements were filtered out!")
             
        # Check specific month data existence via raw SQL to be sure
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE Fecha >= %s AND Fecha <= %s", (start_date, end_date))
        raw_count = cursor.fetchone()[0]
        print(f"\nRaw SQL Count for Jan 2026: {raw_count}")
        cursor.close()

    except Exception as e:
        print(f"\nCRASHED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
