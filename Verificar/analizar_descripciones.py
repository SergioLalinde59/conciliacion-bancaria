
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def analyze_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("EJEMPLO 1: 553 Tratoria (terceroid=1)")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero as tercero_maestro, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE td.terceroid = 1
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero Maestro", "Descripción", "Referencia"]))
    
    print("\n" + "=" * 80)
    print("EJEMPLO 2: Adobe (terceroid=2)")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero as tercero_maestro, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE td.terceroid = 2
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero Maestro", "Descripción", "Referencia"]))
    
    print("\n" + "=" * 80)
    print("EJEMPLO 3: AgroBolibar (terceroid=4)")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero as tercero_maestro, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE td.terceroid = 4
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero Maestro", "Descripción", "Referencia"]))
    
    print("\n" + "=" * 80)
    print("REGISTROS CON DESCRIPCIÓN VACÍA O NULA")
    print("=" * 80)
    cursor.execute("""
        SELECT COUNT(*) FROM tercero_descripciones 
        WHERE descripcion IS NULL OR descripcion = '' OR descripcion = '-'
    """)
    count = cursor.fetchone()[0]
    print(f"Total registros con descripción vacía: {count}")
    
    print("\n" + "=" * 80)
    print("CUENTA 'EFECTIVO' - ID de cuenta")
    print("=" * 80)
    cursor.execute("""
        SELECT cuentaid, cuenta FROM cuentas WHERE cuenta ILIKE '%efectivo%'
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["CuentaID", "Cuenta"]))
    
    conn.close()

if __name__ == "__main__":
    analyze_data()
