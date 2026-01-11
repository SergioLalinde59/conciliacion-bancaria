
import psycopg2
from src.infrastructure.database.connection import DB_CONFIG
from decimal import Decimal

def check_apple_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"Buscando 'Apple.Com/Bill'...")
        # Use ILIKE for partial match
        cursor.execute("SELECT id, fecha, valor, usd, trm, descripcion, monedaid FROM movimientos WHERE descripcion ILIKE '%Apple%'")
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"ID: {row[0]}, Fecha: {row[1]}, Valor: {row[2]}, USD: {row[3]}, TRM: {row[4]}, Desc: '{row[5]}', MonedaID: {row[6]}")
            
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_apple_db()
