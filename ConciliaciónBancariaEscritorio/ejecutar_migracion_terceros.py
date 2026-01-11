#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar la migración de contactos a terceros en la base de datos
Ejecuta el script SQL renombrar_contactos_a_terceros.sql
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
    print("MIGRACIÓN: CONTACTOS → TERCEROS")
    print("="*70)
    
    # Leer el script SQL
    script_path = Path(__file__).parent / "renombrar_contactos_a_terceros.sql"
    
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
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✓ Conexión establecida")
        
        # Ejecutar el script
        print("\n🚀 Ejecutando migración...")
        print("-"*70)
        
        cursor.execute(sql_script)
        
        print("-"*70)
        print("✓ Migración ejecutada exitosamente")
        
        # Verificar los cambios
        print("\n🔍 Verificando cambios...")
        
        # Verificar que la tabla terceros existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'terceros'
            );
        """)
        
        terceros_existe = cursor.fetchone()[0]
        
        if terceros_existe:
            print("  ✓ Tabla 'terceros' existe")
            
            # Verificar columnas
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'terceros'
                ORDER BY ordinal_position;
            """)
            
            columnas = [row[0] for row in cursor.fetchall()]
            print(f"  ✓ Columnas: {', '.join(columnas)}")
            
            if 'terceroid' in columnas and 'tercero' in columnas:
                print("  ✓ Columnas renombradas correctamente")
            else:
                print("  ⚠️ Advertencia: Columnas no tienen los nombres esperados")
        else:
            print("  ✗ Error: Tabla 'terceros' no existe")
            return False
        
        # Verificar columna TerceroID en movimientos
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'movimientos' 
                AND column_name = 'terceroid'
            );
        """)
        
        terceroid_existe = cursor.fetchone()[0]
        
        if terceroid_existe:
            print("  ✓ Columna 'TerceroID' existe en tabla 'movimientos'")
        else:
            print("  ⚠️ Advertencia: Columna 'TerceroID' no encontrada en 'movimientos'")
        
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
        return False

if __name__ == "__main__":
    exito = ejecutar_migracion()
    
    if exito:
        print("\n💡 Próximos pasos:")
        print("  1. Verificar que las aplicaciones funcionen correctamente")
        print("  2. Actualizar los archivos Python pendientes si no lo has hecho")
        print("  3. Probar los scripts de gestión CRUD y asignación")
    else:
        print("\n⚠️ La migración falló. Revisa los errores arriba.")
        print("   Puede que necesites revertir los cambios o investigar el problema.")
