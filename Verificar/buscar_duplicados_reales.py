
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def check_real_duplicates():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("BUSCANDO DUPLICADOS REALES (terceroid + descripcion + referencia)")
    print("=" * 80)
    
    cursor.execute("""
        SELECT terceroid, descripcion, COALESCE(referencia, '') as ref, COUNT(*) as cnt
        FROM tercero_descripciones
        GROUP BY terceroid, descripcion, COALESCE(referencia, '')
        HAVING COUNT(*) > 1
    """)
    rows = cursor.fetchall()
    
    if rows:
        print(f"\n⚠️ Duplicados REALES encontrados: {len(rows)}\n")
        print(tabulate(rows, headers=["TerceroID", "Descripción", "Referencia", "Cantidad"]))
    else:
        print("\n✅ No hay duplicados reales")
    
    # Verificar Autoland específicamente
    print("\n" + "=" * 80)
    print("AUTOLAND:")
    print("=" * 80)
    cursor.execute("""
        SELECT id, terceroid, descripcion, COALESCE(referencia, '(vacío)') as ref
        FROM tercero_descripciones
        WHERE terceroid = 17
        ORDER BY id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "TerceroID", "Descripción", "Referencia"]))
    
    conn.close()

if __name__ == "__main__":
    check_real_duplicates()
