import psycopg2
import os

# Configuración BD (tomada de connection.py)
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'Mvtos',
    'user': 'postgres',
    'password': 'SLB'
}

def ejecutar_migracion():
    sql_path = r'f:\1. Cloud\4. AI\1. Antigravity\Gastos SLB Vo\Sql\agregar_campo_es_traslado_grupos.sql'
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"Leyendo script: {sql_path}")
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("Ejecutando migración...")
        cursor.execute(sql)
        conn.commit()
        
        print("¡Migración completada con éxito!")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    ejecutar_migracion()
