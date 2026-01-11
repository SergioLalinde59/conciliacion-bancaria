
import psycopg2
from src.infrastructure.database.connection import DB_CONFIG

def migrate_cuentas():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Add column if not exists
        cursor.execute("""
            ALTER TABLE cuentas 
            ADD COLUMN IF NOT EXISTS permite_carga BOOLEAN DEFAULT FALSE;
        """)
        
        # 2. Reset all to False first
        cursor.execute("UPDATE cuentas SET permite_carga = FALSE")
        
        # 3. Set True for specific accounts
        cuentas_habilitadas = [
            'Ahorros', 
            'Tarjeta Crédito (Smart)', 
            'FondoRenta', 
            'Protección'
        ]
        
        for nombre in cuentas_habilitadas:
            cursor.execute(
                "UPDATE cuentas SET permite_carga = TRUE WHERE cuenta = %s",
                (nombre,)
            )
            print(f"Habilitada carga para: {nombre}")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Migración completada exitosamente.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_cuentas()
