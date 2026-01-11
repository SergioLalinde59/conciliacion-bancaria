#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resolver el duplicado del tercero ID=116
Ejecuta resolver_duplicado_tercero_116.sql
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

def resolver_duplicado():
    """Resuelve el duplicado eliminando tercero 116 y actualizando movimiento 95."""
    
    print("="*70)
    print("RESOLVER DUPLICADO: Tercero ID=116")
    print("="*70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n📋 Estado ANTES del cambio:")
        print("-" * 70)
        
        # Ver movimiento 95
        cursor.execute("""
            SELECT Id, Fecha, Descripcion, TerceroID
            FROM movimientos
            WHERE Id = 95
        """)
        mov = cursor.fetchone()
        if mov:
            print(f"Movimiento 95: TerceroID actual = {mov[3]}")
        
        # Ver terceros 116 y 122 (sin descripcion/referencia - 3NF)
        cursor.execute("""
            SELECT terceroid, tercero
            FROM terceros
            WHERE terceroid IN (116, 122)
            ORDER BY terceroid
        """)
        terceros = cursor.fetchall()
        for t in terceros:
            print(f"Tercero {t[0]}: {t[1]}")
        
        # Contar movimientos con tercero 116
        cursor.execute("""
            SELECT COUNT(*) FROM movimientos WHERE TerceroID = 116
        """)
        count_116 = cursor.fetchone()[0]
        print(f"\nMovimientos usando tercero 116: {count_116}")
        
        print("\n🔄 Ejecutando cambios...")
        print("-" * 70)
        
        # Paso 1: Actualizar movimiento 95
        print("1. Actualizando movimiento 95...")
        cursor.execute("""
            UPDATE movimientos
            SET TerceroID = 122
            WHERE Id = 95 AND TerceroID = 116
        """)
        print(f"   ✓ Movimiento 95 actualizado: TerceroID 116 → 122")
        
        # Paso 2: Verificar otros movimientos
        cursor.execute("""
            SELECT COUNT(*) FROM movimientos WHERE TerceroID = 116
        """)
        remaining = cursor.fetchone()[0]
        
        if remaining > 0:
            print(f"\n⚠️  Aún hay {remaining} movimiento(s) usando tercero 116")
            print("   No se eliminará el tercero 116 automáticamente")
        else:
            print("\n2. Eliminando tercero 116...")
            cursor.execute("""
                DELETE FROM terceros WHERE terceroid = 116
            """)
            print("   ✓ Tercero 116 eliminado")
        
        # Commit
        conn.commit()
        
        print("\n📋 Estado DESPUÉS del cambio:")
        print("-" * 70)
        
        # Ver movimiento 95
        cursor.execute("""
            SELECT m.Id, m.Fecha, m.Descripcion, 
                   t.terceroid, t.tercero
            FROM movimientos m
            LEFT JOIN terceros t ON m.TerceroID = t.terceroid
            WHERE m.Id = 95
        """)
        mov = cursor.fetchone()
        if mov:
            print(f"Movimiento 95: TerceroID = {mov[3]} ({mov[4]})")
        
        # Verificar duplicados (referencia ahora está en tercero_descripciones)
        cursor.execute("""
            SELECT td.referencia, COUNT(*) as cantidad
            FROM tercero_descripciones td
            WHERE td.referencia = '41258577351'
            GROUP BY td.referencia
        """)
        dup = cursor.fetchone()
        if dup:
            print(f"\nReferencia 41258577351: {dup[1]} registro(s)")
        else:
            print("\n✓ Ya no hay duplicados con referencia 41258577351")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓✓✓ CAMBIOS APLICADOS EXITOSAMENTE")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    exito = resolver_duplicado()
    
    if exito:
        print("\n✅ Puede ejecutar: python ejecutar_actualizacion_terceros.py")
    else:
        print("\n❌ Revise los errores arriba")
