import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

print("Ejecutando script SQL para renombrar columna en tabla cuentas...")
print("=" * 60)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Renombrar la columna
    print("\n1. Renombrando columna account → cuenta en tabla cuentas...")
    cursor.execute("ALTER TABLE cuentas RENAME COLUMN account TO cuenta")
    print("   ✓ Columna renombrada")
    
    # 2. Verificar los cambios
    print("\n2. Verificando estructura de la tabla 'cuentas':")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'cuentas'
        ORDER BY ordinal_position
    """)
    
    print("\n" + "-" * 60)
    print(f"{'Columna':<20} {'Tipo':<20} {'Nullable':<10}")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10}")
    print("-" * 60)
    
    # Commit
    conn.commit()
    print("\n✓✓✓ CAMBIOS APLICADOS EXITOSAMENTE ✓✓✓")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
