
import psycopg2
from src.infrastructure.database.connection import DB_CONFIG

def crear_cuenta_tc_smart():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT cuentaid FROM cuentas WHERE cuenta = 'Tarjeta Crédito (Smart)'")
        exists = cursor.fetchone()
        
        if exists:
            print(f"La cuenta 'Tarjeta Crédito (Smart)' ya existe con ID: {exists[0]}")
            # Ensure it is active
            cursor.execute("UPDATE cuentas SET activa = TRUE WHERE cuentaid = %s", (exists[0],))
            conn.commit()
            print("Se aseguró que la cuenta esté activa.")
        else:
            print("Creando cuenta 'Tarjeta Crédito (Smart)'...")
            cursor.execute(
                "INSERT INTO cuentas (cuenta, activa) VALUES (%s, %s) RETURNING cuentaid",
                ('Tarjeta Crédito (Smart)', True)
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            print(f"Cuenta creada exitosamente con ID: {new_id}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    crear_cuenta_tc_smart()
