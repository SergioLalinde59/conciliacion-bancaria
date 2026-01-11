import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

print("Ejecutando script SQL para renombrar tabla mvtos...")
print("=" * 60)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Renombrar la tabla
    print("\n1. Renombrando tabla mvtos → movimientos...")
    cursor.execute("ALTER TABLE Mvtos RENAME TO movimientos")
    print("   ✓ Tabla renombrada")
    
    # 2. Verificar los cambios
    print("\n2. Verificando estructura de la nueva tabla 'movimientos':")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'movimientos'
        ORDER BY ordinal_position
    """)
    
    print("\n" + "-" * 80)
    print(f"{'Columna':<20} {'Tipo':<30} {'Nullable':<10}")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:<20} {row[1]:<30} {row[2]:<10}")
    print("-" * 80)
    
    # Verificar conteo de registros
    cursor.execute("SELECT COUNT(*) FROM movimientos")
    count = cursor.fetchone()[0]
    print(f"\n✓ Total de registros en la tabla: {count:,}")
    
    # Commit
    conn.commit()
    print("\n✓✓✓ CAMBIOS APLICADOS EXITOSAMENTE ✓✓✓")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
