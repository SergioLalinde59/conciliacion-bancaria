
import psycopg2
from tabulate import tabulate

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def get_table_info(table_name):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND table_name = %s
        ORDER BY ordinal_position;
        """
        
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()
        
        # Get constraints (PK, FK, Unique)
        query_constraints = """
        SELECT 
            tc.constraint_name, 
            tc.constraint_type, 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.table_name = %s;
        """
        cursor.execute(query_constraints, (table_name,))
        constraints = cursor.fetchall()
        
        conn.close()
        return columns, constraints
    except Exception as e:
        print(f"Error: {e}")
        return [], []

def print_structure(table_name):
    print(f"\n{'='*50}")
    print(f"ESTRUCTURA DE TABLA: {table_name}")
    print(f"{'='*50}")
    
    columns, constraints = get_table_info(table_name)
    
    if not columns:
        print("❌ Tabla no encontrada o error de conexión.")
        return

    print("\n📋  COLUMNAS:")
    headers = ["Nombre", "Tipo", "Nullable", "Default"]
    print(tabulate(columns, headers=headers, tablefmt="grid"))
    
    if constraints:
        print("\n🔒  RESTRICCIONES (Constraints):")
        headers_const = ["Nombre Constraint", "Tipo", "Columna", "Tabla Ref", "Columna Ref"]
        print(tabulate(constraints, headers=headers_const, tablefmt="simple"))
    else:
        print("\n🔒  Sin restricciones explícitas encontradas.")

if __name__ == "__main__":
    print_structure("terceros")
    print_structure("tercero_descripciones")
