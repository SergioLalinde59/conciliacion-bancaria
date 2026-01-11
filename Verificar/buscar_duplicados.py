
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def find_duplicates():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("BUSCANDO DUPLICADOS (terceroid + descripcion)")
    print("=" * 80)
    
    cursor.execute("""
        SELECT td.terceroid, t.tercero, td.descripcion, COUNT(*) as cantidad
        FROM tercero_descripciones td
        JOIN terceros t ON td.terceroid = t.terceroid
        GROUP BY td.terceroid, t.tercero, td.descripcion
        HAVING COUNT(*) > 1
        ORDER BY cantidad DESC, t.tercero
    """)
    rows = cursor.fetchall()
    
    if rows:
        print(f"\n⚠️ Encontrados {len(rows)} grupos con duplicados:\n")
        print(tabulate(rows, headers=["TerceroID", "Tercero", "Descripción", "Cantidad"]))
        
        # Mostrar detalle de cada duplicado
        print("\n\nDETALLE DE DUPLICADOS:")
        for row in rows:
            terceroid, tercero, descripcion, _ = row
            cursor.execute("""
                SELECT id, terceroid, descripcion, referencia
                FROM tercero_descripciones
                WHERE terceroid = %s AND descripcion = %s
                ORDER BY id
            """, (terceroid, descripcion))
            details = cursor.fetchall()
            print(f"\n{tercero} - '{descripcion}':")
            print(tabulate(details, headers=["ID", "TerceroID", "Descripción", "Referencia"]))
    else:
        print("\n✅ No se encontraron duplicados")
    
    conn.close()

if __name__ == "__main__":
    find_duplicates()
