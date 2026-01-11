
import psycopg2
import sys

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def ejecutar_sql(archivo_sql):
    print(f"Ejecutando script: {archivo_sql}")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        with open(archivo_sql, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        cursor.execute(sql_content)
        conn.commit()
        
        print("✓ Script ejecutado exitosamente.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error ejecutando SQL: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
    else:
        archivo = "Sql/crear_tabla_tercero_descripciones.sql"
        
    ejecutar_sql(archivo)
