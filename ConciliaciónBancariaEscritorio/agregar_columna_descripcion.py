#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar la columna 'descripcion' a la tabla contactos
UNIQUE constraint sobre (contacto, descripcion) como par
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def agregar_columna_descripcion():
    """Agrega la columna descripcion y UNIQUE constraint sobre (contacto, descripcion)."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("AGREGANDO COLUMNA 'descripcion' A LA TABLA 'contactos'")
        print("=" * 70)
        
        # Paso 1: Verificar si la columna ya existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contactos' AND column_name = 'descripcion'
        """)
        
        if cursor.fetchone():
            print("\n⚠️  La columna 'descripcion' ya existe.")
        else:
            # Agregar la columna
            print("\n1. Agregando columna 'descripcion'...")
            cursor.execute("""
                ALTER TABLE contactos 
                ADD COLUMN descripcion VARCHAR(50);
            """)
            print("   ✓ Columna agregada")
            conn.commit()
        
        # Paso 2: Eliminar restricción anterior si existe
        print("\n2. Eliminando restricciones UNIQUE anteriores (si existen)...")
        try:
            cursor.execute("""
                ALTER TABLE contactos 
                DROP CONSTRAINT IF EXISTS contactos_descripcion_unique;
            """)
            print("   ✓ Restricción antigua eliminada")
            conn.commit()
        except:
            pass
        
        # Paso 3: Agregar restricción UNIQUE sobre (contacto, descripcion)
        print("\n3. Agregando restricción UNIQUE sobre (contacto, descripcion)...")
        try:
            cursor.execute("""
                ALTER TABLE contactos 
                ADD CONSTRAINT contactos_contacto_descripcion_unique 
                UNIQUE (contacto, descripcion);
            """)
            print("   ✓ UNIQUE (contacto, descripcion) aplicado")
            conn.commit()
        except psycopg2.errors.DuplicateObject:
            print("   ℹ️  La restricción ya existe")
            conn.rollback()
        
        print("\n" + "=" * 70)
        print("✓✓✓ MIGRACIÓN COMPLETADA EXITOSAMENTE ✓✓✓")
        print("=" * 70)
        print("\n📋 ESTRUCTURA FINAL:")
        print("   • contactoid      - ID autoincremental")
        print("   • contacto        - Nombre del contacto (manual)")
        print("   • descripcion     - Descripción del banco (automático, puede estar vacío)")
        print("   • referencia      - Referencia adicional")
        print("\n🔒 RESTRICCIÓN UNIQUE:")
        print("   • La combinación (contacto, descripcion) debe ser única")
        print("   • Permite mismo contacto con diferentes descripciones")
        print("   • Permite misma descripcion con diferentes contactos")
        print("   • No permite duplicar ambos campos juntos")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("\n📝 INFORMACIÓN:")
    print("   - Se agregará la columna 'descripcion' (VARCHAR(50))")
    print("   - UNIQUE constraint sobre la COMBINACIÓN (contacto, descripcion)")
    print("   - Permite valores NULL en descripcion")
    print("   - No habrá conflictos de duplicados\n")
    
    respuesta = input("¿Deseas continuar? (s/n): ")
    
    if respuesta.lower() == 's':
        agregar_columna_descripcion()
    else:
        print("\nOperación cancelada.")