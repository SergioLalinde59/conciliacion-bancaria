
import psycopg2
from src.infrastructure.database.connection import DB_CONFIG

def check_cuentas():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cuentas")
        rows = cursor.fetchall()
        
        print(f"Total rows in 'cuentas': {len(rows)}")
        for row in rows:
            print(row)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cuentas()
