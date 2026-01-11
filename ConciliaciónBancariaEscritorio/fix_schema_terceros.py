#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir el esquema de la tabla terceros.
Agrega la restricción UNIQUE faltante en la columna 'tercero'.
"""

import psycopg2
import sys

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def fix_terceros_schema():
    print("=" * 60)
    print("CORRECCIÓN DE ESQUEMA: TABLA TERCEROS")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Verificar si existe duplicados antes de aplicar la restricción
        print("\n1. Verificando duplicados en columna 'tercero'...")
        cursor.execute("""
            SELECT tercero, COUNT(*) 
            FROM terceros 
            GROUP BY tercero 
            HAVING COUNT(*) > 1
        """)
        duplicados = cursor.fetchall()
        
        if duplicados:
            print(f"⚠️ ¡ATENCIÓN! Se encontraron {len(duplicados)} nombres duplicados.")
            print("   No se puede aplicar UNIQUE hasta resolverlos.")
            for dup in duplicados:
                print(f"   - '{dup[0]}': {dup[1]} veces")
            
            # Opción de limpieza automática simple (mantener el ID más bajo)
            print("\n   Intentando limpiar duplicados manteniendo el primer registro...")
            
            cursor.execute("""
                DELETE FROM terceros a USING (
                    SELECT MIN(ctid) as ctid, tercero
                    FROM terceros 
                    GROUP BY tercero HAVING COUNT(*) > 1
                ) b
                WHERE a.tercero = b.tercero 
                AND a.ctid <> b.ctid
            """)
            deleted_count = cursor.rowcount
            print(f"   ✓ Se eliminaron {deleted_count} registros duplicados.")
        else:
            print("   ✓ No se encontraron duplicados.")

        # 2. Verificar constraints existentes
        print("\n2. Verificando constraints existentes...")
        cursor.execute("""
             SELECT conname, pg_get_constraintdef(c.oid)
             FROM pg_constraint c
             JOIN pg_namespace n ON n.oid = c.connamespace
             WHERE n.nspname = 'public' AND c.conrelid = 'terceros'::regclass
        """)
        constraints = cursor.fetchall()
        for con in constraints:
            print(f"   - {con[0]}: {con[1]}")
            if 'UNIQUE (tercero)' in con[1]:
                print("\n✓ La restricción UNIQUE (tercero) YA EXISTE.")
                return True

        # 3. Aplicar Constraint
        print("\n3. Aplicando restricción UNIQUE (tercero)...")
        cursor.execute("ALTER TABLE terceros ADD CONSTRAINT terceros_tercero_key UNIQUE (tercero);")
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✓✓✓ ESQUEMA CORREGIDO EXITOSAMENTE")
        print("    Ahora puede ejecutar cargarDatosMaestros.py")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    fix_terceros_schema()
