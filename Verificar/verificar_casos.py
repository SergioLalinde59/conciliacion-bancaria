
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def verify():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM tercero_descripciones")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}\n")
    
    # Verify Andrea Latorre case
    print("=" * 80)
    print("VERIFICAR: Andrea Latorre")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE t.tercero ILIKE '%andrea%latorre%'
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero", "Descripción", "Referencia"]))
    
    # Verify AgroBolibar
    print("\n" + "=" * 80)
    print("VERIFICAR: AgroBolibar")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE t.tercero ILIKE '%agrobol%'
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero", "Descripción", "Referencia"]))
    
    # Verify Adobe
    print("\n" + "=" * 80)
    print("VERIFICAR: Adobe")
    print("=" * 80)
    cursor.execute("""
        SELECT td.id, t.tercero, td.descripcion, td.referencia
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        WHERE t.tercero ILIKE '%adobe%'
        ORDER BY td.id
    """)
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Tercero", "Descripción", "Referencia"]))
    
    conn.close()

if __name__ == "__main__":
    verify()
