
import psycopg2
import re

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def normalize_and_dedupe():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Normalizar descripciones (quitar espacios extra)
    print("1. Normalizando descripciones (quitando espacios extra)...")
    cursor.execute("""
        UPDATE tercero_descripciones 
        SET descripcion = TRIM(REGEXP_REPLACE(descripcion, '\s+', ' ', 'g'))
        WHERE descripcion IS NOT NULL
    """)
    updated = cursor.rowcount
    print(f"   Registros actualizados: {updated}")
    
    # 2. Eliminar duplicados exactos (mantener el menor ID)
    print("2. Eliminando duplicados exactos...")
    cursor.execute("""
        DELETE FROM tercero_descripciones 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM tercero_descripciones 
            GROUP BY terceroid, descripcion, COALESCE(referencia, '')
        )
    """)
    deleted = cursor.rowcount
    print(f"   Registros eliminados: {deleted}")
    
    conn.commit()
    
    # 3. Verificar
    print("\n3. Verificación:")
    
    print("\nAUTOLAND:")
    cursor.execute("SELECT id, descripcion, referencia FROM tercero_descripciones WHERE terceroid = 17")
    for r in cursor.fetchall():
        print(f"   ID={r[0]}, Desc='{r[1]}', Ref='{r[2]}'")
    
    print("\nCOMCEL:")
    cursor.execute("SELECT id, descripcion, referencia FROM tercero_descripciones WHERE terceroid = 35")
    for r in cursor.fetchall():
        print(f"   ID={r[0]}, Desc='{r[1]}', Ref='{r[2]}'")
    
    cursor.execute("SELECT COUNT(*) FROM tercero_descripciones")
    print(f"\nTotal registros: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    normalize_and_dedupe()
