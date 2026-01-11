import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

print("Ejecutando script SQL para renombrar tabla contacts...")
print("=" * 60)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Renombrar la tabla
    print("\n1. Renombrando tabla contacts → contatos...")
    cursor.execute("ALTER TABLE contacts RENAME TO contatos")
    print("   ✓ Tabla renombrada")
    
    # 2. Renombrar las columnas
    print("\n2. Renombrando columnas:")
    
    print("   - contactid → contactoid...")
    cursor.execute("ALTER TABLE contatos RENAME COLUMN contactid TO contactoid")
    print("     ✓ Listo")
    
    print("   - contact → contacto...")
    cursor.execute("ALTER TABLE contatos RENAME COLUMN contact TO contacto")
    print("     ✓ Listo")
    
    print("   - reference → referencia...")
    cursor.execute("ALTER TABLE contatos RENAME COLUMN reference TO referencia")
    print("     ✓ Listo")
    
    # 3. Verificar los cambios
    print("\n3. Verificando estructura de la nueva tabla 'contatos':")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'contatos'
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
