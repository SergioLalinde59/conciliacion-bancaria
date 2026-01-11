#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar duplicados en la tabla terceros ANTES de la migración
Identifica y resuelve referencias duplicadas
"""

import psycopg2

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def limpiar_duplicados():
    """Identifica y muestra duplicados para resolución manual."""
    
    print("="*70)
    print("ANÁLISIS DE DUPLICADOS EN TABLA TERCEROS")
    print("="*70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n🔍 Buscando referencias duplicadas...")
        
        # Buscar referencias duplicadas (no vacías)
        cursor.execute("""
            SELECT referencia, COUNT(*) as cantidad, 
                   array_agg(terceroid) as ids,
                   array_agg(tercero) as nombres
            FROM terceros
            WHERE referencia IS NOT NULL AND referencia != ''
            GROUP BY referencia
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        """)
        
        duplicados_ref = cursor.fetchall()
        
        if duplicados_ref:
            print(f"\n⚠️  Se encontraron {len(duplicados_ref)} referencias duplicadas:\n")
            print(f"{'Referencia':<20} {'Cantidad':<10} {'IDs':<30} {'Terceros'}")
            print("-" * 90)
            
            for ref, cant, ids, nombres in duplicados_ref:
                ids_str = str(ids)[:28]
                nombres_str = str(nombres)[:40] if nombres else ''
                print(f"{ref:<20} {cant:<10} {ids_str:<30} {nombres_str}")
            
            print("\n📋 Detalles de cada duplicado:\n")
            for ref, cant, ids, nombres in duplicados_ref[:5]:  # Mostrar primeros 5
                print(f"\n🔸 Referencia: {ref}")
                cursor.execute("""
                    SELECT terceroid, tercero, descripcion, referencia
                    FROM terceros
                    WHERE referencia = %s
                    ORDER BY terceroid
                """, (ref,))
                
                registros = cursor.fetchall()
                for tid, tercero, desc, ref_val in registros:
                    print(f"   ID: {tid} | Tercero: {tercero} | Descripción: {desc}")
        
        else:
            print("✓ No se encontraron referencias duplicadas")
        
        # Buscar duplicados en (tercero, descripcion) donde referencia esté vacía
        print("\n\n🔍 Buscando duplicados en (tercero, descripcion) con referencia vacía...")
        
        cursor.execute("""
            SELECT tercero, descripcion, COUNT(*) as cantidad,
                   array_agg(terceroid) as ids
            FROM terceros
            WHERE referencia IS NULL OR referencia = ''
            GROUP BY tercero, descripcion
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        """)
        
        duplicados_tercero_desc = cursor.fetchall()
        
        if duplicados_tercero_desc:
            print(f"\n⚠️  Se encontraron {len(duplicados_tercero_desc)} combinaciones (tercero, descripcion) duplicadas:\n")
            print(f"{'Tercero':<30} {'Descripción':<30} {'Cantidad':<10} {'IDs'}")
            print("-" * 90)
            
            for tercero, desc, cant, ids in duplicados_tercero_desc:
                ids_str = str(ids)[:20]
                print(f"{tercero:<30} {desc:<30} {cant:<10} {ids_str}")
        else:
            print("✓ No se encontraron duplicados en (tercero, descripcion)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        
        if duplicados_ref or duplicados_tercero_desc:
            print("⚠️  ACCIÓN REQUERIDA:")
            print("   Hay duplicados que deben resolverse antes de la migración.")
            print("\n💡 Opciones:")
            print("   1. Eliminar duplicados manualmente (conservar el ID más bajo)")
            print("   2. Consolidar datos (mover referencias de movimientos)")
            print("   3. Modificar referencias para hacerlas únicas")
            return False
        else:
            print("✓✓✓ NO HAY DUPLICADOS - Puede proceder con la migración")
            return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    resultado = limpiar_duplicados()
    
    if resultado:
        print("\n✅ Puede ejecutar: python ejecutar_actualizacion_terceros.py")
    else:
        print("\n❌ Resuelva los duplicados primero")
