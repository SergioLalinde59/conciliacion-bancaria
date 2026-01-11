import psycopg2
import sys

# Configuración de la base de datos
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
        
        print("Checking 'grupos' table:")
        cursor.execute("SELECT COUNT(*) FROM grupos")
        count_grupos = cursor.fetchone()[0]
        print(f"  Count: {count_grupos}")
        cursor.execute("SELECT * FROM grupos LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - {row}")

        print("\nChecking 'conceptos' table:")
        cursor.execute("SELECT COUNT(*) FROM conceptos")
        count_conceptos = cursor.fetchone()[0]
        print(f"  Count: {count_conceptos}")
        cursor.execute("SELECT * FROM conceptos LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - {row}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
