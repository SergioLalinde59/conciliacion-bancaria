
import psycopg2
from src.infrastructure.database.connection import DB_CONFIG
from decimal import Decimal

def check_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        fecha = '2025-12-06'
        print(f"Buscando movimientos para {fecha}...")
        
        cursor.execute("SELECT id, fecha, valor, descripcion, cuentaid FROM movimientos WHERE fecha = %s", (fecha,))
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"ID: {row[0]}, Fecha: {row[1]}, Valor: {row[2]}, Desc: '{row[3]}', Cuenta: {row[4]}")
            
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_db()
