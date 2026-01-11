
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def check_and_fix():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Ver Autoland
    print("AUTOLAND (terceroid=17):")
    cursor.execute("""
        SELECT id, terceroid, descripcion, referencia 
        FROM tercero_descripciones 
        WHERE terceroid = 17
        ORDER BY id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "TerceroID", "Descripción", "Referencia"]))
    
    # Ver Comcel
    print("\nCOMCEL (terceroid=35):")
    cursor.execute("""
        SELECT id, terceroid, descripcion, referencia 
        FROM tercero_descripciones 
        WHERE terceroid = 35
        ORDER BY id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "TerceroID", "Descripción", "Referencia"]))
    
    # Eliminar duplicados manteniendo el menor ID
    print("\n--- Eliminando duplicados ---")
    
    # Autoland: mantener solo distintas descripciones
    cursor.execute("""
        DELETE FROM tercero_descripciones 
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY terceroid, descripcion, COALESCE(referencia, '')
                    ORDER BY id
                ) as rn
                FROM tercero_descripciones
            ) t WHERE rn > 1
        )
    """)
    deleted = cursor.rowcount
    conn.commit()
    print(f"Registros eliminados: {deleted}")
    
    # Verificar resultado
    print("\n--- Después de limpieza ---")
    
    print("\nAUTOLAND:")
    cursor.execute("SELECT id, descripcion, referencia FROM tercero_descripciones WHERE terceroid = 17")
    for r in cursor.fetchall():
        print(f"  ID={r[0]}, Desc='{r[1]}', Ref='{r[2]}'")
    
    print("\nCOMCEL:")
    cursor.execute("SELECT id, descripcion, referencia FROM tercero_descripciones WHERE terceroid = 35")
    for r in cursor.fetchall():
        print(f"  ID={r[0]}, Desc='{r[1]}', Ref='{r[2]}'")
    
    cursor.execute("SELECT COUNT(*) FROM tercero_descripciones")
    print(f"\nTotal registros: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    check_and_fix()
