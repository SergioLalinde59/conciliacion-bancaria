
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'Mvtos',
    'user': 'postgres',
    'password': 'SLB'
}

def enable_trigram_extension():
    print("Habilitando extensión pg_trgm en PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Crear extensión
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        print("Extensión pg_trgm verificada/habilitada.")
        
        # 2. Crear índices GIN para búsqueda rápida
        print("Creando índices de trigramas para Terceros...")
        
        # Índice en descripción (para búsqueda fuzzy de descripción vs descripción)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS trgm_idx_terceros_descripcion 
            ON terceros USING gin (descripcion gin_trgm_ops);
        """)
        
        # Índice en nombre (para búsqueda fuzzy de descripción vs nombre)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS trgm_idx_terceros_nombre 
            ON terceros USING gin (tercero gin_trgm_ops);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Optimización de búsqueda completada.")
        
    except Exception as e:
        print(f"Error habilitando pg_trgm: {e}")
        print("NOTA: Puede requerir permisos de superusuario. Si falla, el script funcionará pero más lento.")

if __name__ == "__main__":
    enable_trigram_extension()
