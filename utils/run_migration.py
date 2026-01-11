import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'Mvtos',
    'user': 'postgres',
    'password': 'SLB'
}

def ejecutar_migracion():
    print("Conectando a la base de datos...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Leer el archivo SQL
        with open(r"f:\1. Cloud\4. AI\1. Antigravity\Gastos SLB Vo\Sql\agregar_soft_delete_maestras.sql", "r") as f:
            sql = f.read()

        print(f"Ejecutando SQL...")
        cursor.execute(sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Migración completada exitosamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ejecutar_migracion()
