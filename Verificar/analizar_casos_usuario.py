
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def analyze_cases():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cases = [
        ("Adobe", "%adobe%"),
        ("Autoland", "%autoland%"),
        ("Bancolombia", "%bancolombia%"),
        ("Capiro Vivero", "%capiro%vivero%")
    ]
    
    for name, pattern in cases:
        print("=" * 80)
        print(f"CASO: {name}")
        print("=" * 80)
        
        # 1. Ver registros en tabla TERCEROS
        print(f"\n📋 Registros en TERCEROS:")
        cursor.execute("""
            SELECT terceroid, tercero, descripcion, referencia
            FROM terceros
            WHERE tercero ILIKE %s AND activa = TRUE
            ORDER BY terceroid
        """, (pattern,))
        rows = cursor.fetchall()
        if rows:
            print(tabulate(rows, headers=["TerceroID", "Nombre", "Descripción", "Referencia"]))
            min_id = rows[0][0]
            print(f"   → ID mínimo (maestro): {min_id}")
        else:
            print("   (No hay registros)")
            min_id = None
        
        # 2. Ver registros en TERCERO_DESCRIPCIONES
        print(f"\n📋 Registros en TERCERO_DESCRIPCIONES:")
        cursor.execute("""
            SELECT td.id, td.terceroid, t.tercero, td.descripcion, td.referencia
            FROM tercero_descripciones td
            JOIN terceros t ON td.terceroid = t.terceroid
            WHERE t.tercero ILIKE %s
            ORDER BY td.terceroid, td.id
        """, (pattern,))
        rows = cursor.fetchall()
        if rows:
            print(tabulate(rows, headers=["ID", "TerceroID", "Tercero", "Descripción", "Referencia"]))
            unique_terceroids = set(r[1] for r in rows)
            print(f"   → TerceroIDs únicos: {sorted(unique_terceroids)}")
            if min_id and len(unique_terceroids) > 1:
                print(f"   ⚠️  PROBLEMA: Hay múltiples terceroIDs, deberían ser todos {min_id}")
            elif min_id and min_id not in unique_terceroids:
                print(f"   ⚠️  PROBLEMA: No usa el ID mínimo {min_id}")
        else:
            print("   (No hay registros)")
        
        print("\n")
    
    conn.close()

if __name__ == "__main__":
    analyze_cases()
