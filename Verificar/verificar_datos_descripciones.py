
import psycopg2
from tabulate import tabulate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def check_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM tercero_descripciones")
        count = cursor.fetchone()[0]
        print(f"Total records in tercero_descripciones: {count}")
        
        # Show sample with new structure
        cursor.execute("SELECT id, terceroid, descripcion, referencia FROM tercero_descripciones LIMIT 10")
        rows = cursor.fetchall()
        print(tabulate(rows, headers=["id", "terceroid", "descripcion", "referencia"]))
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
