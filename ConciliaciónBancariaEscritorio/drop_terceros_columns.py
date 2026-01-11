#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar columnas descripcion y referencia de la tabla terceros.
Estas columnas ahora residen en tercero_descripciones (3NF).
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def drop_columns():
    """Elimina las columnas obsoletas de la tabla terceros."""
    print("=" * 60)
    print("ELIMINAR COLUMNAS descripcion/referencia DE terceros")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar columnas actuales
        print("\n📋 Columnas actuales en tabla terceros:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'terceros'
            ORDER BY ordinal_position
        """)
        for col in cursor.fetchall():
            print(f"   - {col[0]} ({col[1]})")
        
        # Verificar si existen las columnas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'terceros' 
              AND column_name IN ('descripcion', 'referencia')
        """)
        columns_to_drop = [row[0] for row in cursor.fetchall()]
        
        if not columns_to_drop:
            print("\n✓ Las columnas 'descripcion' y 'referencia' ya no existen.")
            return True
        
        print(f"\n🔄 Eliminando columnas: {columns_to_drop}")
        
        # Ejecutar DROP COLUMN
        for col in columns_to_drop:
            print(f"   Eliminando columna '{col}'...")
            cursor.execute(f"ALTER TABLE terceros DROP COLUMN IF EXISTS {col}")
        
        conn.commit()
        
        # Verificar resultado
        print("\n📋 Columnas después de la eliminación:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'terceros'
            ORDER BY ordinal_position
        """)
        for col in cursor.fetchall():
            print(f"   - {col[0]} ({col[1]})")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓✓✓ COLUMNAS ELIMINADAS EXITOSAMENTE")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    drop_columns()
