#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar la migración de la tabla terceros
Actualiza la tabla con constraints condicionales para permitir:
- Un tercero con múltiples descripciones (ej: Bancolombia -> cuota de manejo, intereses)
- Referencias únicas cuando existen (cuentas bancarias, celulares)
- Combinación (tercero, descripcion) única cuando no hay referencia

Ejecuta el archivo actualizar_tabla_terceros.sql
"""

import psycopg2
from pathlib import Path

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def ejecutar_migracion():
    """Ejecuta el script SQL de migración."""
    
    print("="*70)
    print("MIGRACIÓN: ACTUALIZAR TABLA TERCEROS CON CONSTRAINTS CONDICIONALES")
    print("="*70)
    
    # Leer el script SQL (está en la carpeta Sql)
    script_path = Path(__file__).parent / "Sql" / "actualizar_tabla_terceros.sql"
    
    if not script_path.exists():
        print(f"✗ Error: No se encuentra el archivo {script_path}")
        return False
    
    print(f"\n📄 Leyendo script: {script_path.name}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    print(f"✓ Script cargado ({len(sql_script)} caracteres)")
    
    # Conectar a la base de datos
    print(f"\n🔌 Conectando a la base de datos...")
    print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"   Database: {DB_CONFIG['database']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✓ Conexión establecida")
        
        # Ejecutar el script
        print("\n🚀 Ejecutando migración...")
        print("-"*70)
        
        cursor.execute(sql_script)
        conn.commit()
        
        print("-"*70)
        print("✓ Migración ejecutada exitosamente")
        
        # Verificar los cambios
        print("\n🔍 Verificando cambios...")
        
        # Verificar índices creados
        print("\n📊 Índices en tabla 'terceros':")
        cursor.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'terceros'
            ORDER BY indexname
        """)
        
        indices = cursor.fetchall()
        for idx_name, idx_def in indices:
            print(f"  ✓ {idx_name}")
            if 'WHERE' in idx_def.upper():
                # Mostrar condición del índice parcial
                where_clause = idx_def.split('WHERE', 1)[1].strip()
                print(f"    → Condición: WHERE {where_clause}")
        
        # Verificar estructura de la tabla
        print("\n📋 Estructura de la tabla 'terceros':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'terceros'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"  {'Columna':<20} {'Tipo':<20} {'Nullable':<10} {'Default'}")
        print("  " + "-" * 65)
        for col_name, data_type, nullable, default in columns:
            default_str = str(default)[:20] if default else ''
            print(f"  {col_name:<20} {data_type:<20} {nullable:<10} {default_str}")
        
        # Verificar si hay datos en la tabla
        cursor.execute("SELECT COUNT(*) FROM terceros")
        count = cursor.fetchone()[0]
        print(f"\n📈 Registros en tabla 'terceros': {count}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓✓✓ MIGRACIÓN COMPLETADA EXITOSAMENTE ✓✓✓")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    exito = ejecutar_migracion()
    
    if exito:
        print("\n💡 Próximos pasos:")
        print("  1. Probar inserción de terceros CON referencia (cuenta/celular)")
        print("  2. Probar inserción de terceros SIN referencia (mismo tercero, diferentes descripciones)")
        print("  3. Continuar con la implementación de la UI de asignación")
    else:
        print("\n⚠️ La migración falló. Revisa los errores arriba.")
