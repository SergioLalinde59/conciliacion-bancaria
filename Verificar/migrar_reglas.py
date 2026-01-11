
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'Mvtos',
    'user': 'postgres',
    'password': 'SLB'
}

REGLAS_HARDCODED = [
    {
        'patron': 'Abono Intereses Ahorros', 
        'tid': 19, 'gid': 4, 'cid': 23,
        'tipo_match': 'contiene'
    },
    {
        'patron': 'Impto Gobierno', 
        'tid': 45, 'gid': 22, 'cid': 117,
        'tipo_match': 'contiene'
    },
    {
        'patron': 'Traslado De Fondo', 
        'tid': 76, 'gid': 47, 'cid': 399,
        'tipo_match': 'contiene'
    }
]

def migrar_reglas():
    print("Iniciando migración de reglas...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Crear tabla
        print("Creando tabla 'reglas_clasificacion'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reglas_clasificacion (
                id SERIAL PRIMARY KEY,
                patron VARCHAR(255) NOT NULL,
                tercero_id INT REFERENCES terceros(terceroid),
                grupo_id INT REFERENCES grupos(grupoid),
                concepto_id INT REFERENCES conceptos(conceptoid),
                tipo_match VARCHAR(20) DEFAULT 'contiene',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Insertar datos
        print("Insertando reglas hardcoded...")
        for regla in REGLAS_HARDCODED:
            # Verificar si ya existe para no duplicar
            cursor.execute("SELECT id FROM reglas_clasificacion WHERE patron = %s", (regla['patron'],))
            if cursor.fetchone():
                print(f"Skipping: '{regla['patron']}' ya existe.")
                continue
                
            cursor.execute("""
                INSERT INTO reglas_clasificacion (patron, tercero_id, grupo_id, concepto_id, tipo_match)
                VALUES (%s, %s, %s, %s, %s)
            """, (regla['patron'], regla['tid'], regla['gid'], regla['cid'], regla['tipo_match']))
            print(f"Insertada: '{regla['patron']}'")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Migración completada con éxito.")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")

if __name__ == "__main__":
    migrar_reglas()
