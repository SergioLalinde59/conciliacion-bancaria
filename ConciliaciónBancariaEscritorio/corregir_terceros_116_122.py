#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para CORREGIR los cambios y aplicar la lógica correcta:
- Eliminar tercero ID=122
- Mantener/restaurar tercero ID=116
- Actualizar movimientos para usar tercero ID=116
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def corregir_cambios():
    """Corrige los cambios aplicando la lógica correcta."""
    
    print("="*70)
    print("CORRECCIÓN: Eliminar 122, Mantener 116")
    print("="*70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n📋 Estado actual:")
        print("-" * 70)
        
        # Ver terceros 116 y 122
        cursor.execute("""
            SELECT terceroid, tercero, descripcion, referencia
            FROM terceros
            WHERE terceroid IN (116, 122)
            ORDER BY terceroid
        """)
        terceros = cursor.fetchall()
        
        if not terceros:
            print("⚠️  No se encontraron terceros 116 ni 122")
        else:
            for t in terceros:
                print(f"Tercero {t[0]}: {t[1]} | {t[2]} | Ref: {t[3]}")
        
        # Ver movimientos
        cursor.execute("""
            SELECT TerceroID, COUNT(*) as cantidad
            FROM movimientos
            WHERE TerceroID IN (116, 122)
            GROUP BY TerceroID
            ORDER BY TerceroID
        """)
        movs = cursor.fetchall()
        for m in movs:
            print(f"Movimientos con TerceroID={m[0]}: {m[1]}")
        
        print("\n🔄 Aplicando correcciones...")
        print("-" * 70)
        
        # Paso 1: Si no existe tercero 116, necesitamos crearlo/restaurarlo
        cursor.execute("SELECT COUNT(*) FROM terceros WHERE terceroid = 116")
        existe_116 = cursor.fetchone()[0]
        
        if existe_116 == 0:
            print("1. Recreando tercero 116...")
            # Obtener datos del tercero 122 para recrear 116
            cursor.execute("""
                SELECT tercero, descripcion, referencia
                FROM terceros
                WHERE terceroid = 122
            """)
            datos_122 = cursor.fetchone()
            
            if datos_122:
                cursor.execute("""
                    INSERT INTO terceros (terceroid, tercero, descripcion, referencia)
                    VALUES (116, %s, %s, %s)
                """, (datos_122[0], datos_122[1], datos_122[2]))
                print(f"   ✓ Tercero 116 recreado: {datos_122[0]}")
            else:
                # Si no existe 122, usar datos por defecto
                cursor.execute("""
                    INSERT INTO terceros (terceroid, tercero, descripcion, referencia)
                    VALUES (116, 'Juan David Quintero Navia', 'Juan David Quintero Navia', '41258577351')
                """)
                print("   ✓ Tercero 116 recreado con datos por defecto")
        else:
            print("1. Tercero 116 ya existe ✓")
        
        # Paso 2: Actualizar TODOS los movimientos con TerceroID=122 para usar 116
        print("\n2. Actualizando movimientos de 122 → 116...")
        cursor.execute("""
            UPDATE movimientos
            SET TerceroID = 116
            WHERE TerceroID = 122
        """)
        rows_updated = cursor.rowcount
        print(f"   ✓ {rows_updated} movimiento(s) actualizado(s)")
        
        # Paso 3: Eliminar tercero 122
        print("\n3. Eliminando tercero 122...")
        cursor.execute("DELETE FROM terceros WHERE terceroid = 122")
        if cursor.rowcount > 0:
            print("   ✓ Tercero 122 eliminado")
        else:
            print("   ℹ️  Tercero 122 no existía")
        
        # Commit
        conn.commit()
        
        print("\n📋 Estado FINAL:")
        print("-" * 70)
        
        # Verificar terceros
        cursor.execute("""
            SELECT terceroid, tercero, descripcion, referencia
            FROM terceros
            WHERE terceroid IN (116, 122)
            ORDER BY terceroid
        """)
        terceros_final = cursor.fetchall()
        for t in terceros_final:
            print(f"Tercero {t[0]}: {t[1]} | {t[2]} | Ref: {t[3]}")
        
        # Verificar movimientos
        cursor.execute("""
            SELECT TerceroID, COUNT(*) as cantidad
            FROM movimientos
            WHERE TerceroID IN (116, 122)
            GROUP BY TerceroID
        """)
        movs_final = cursor.fetchall()
        for m in movs_final:
            print(f"Movimientos con TerceroID={m[0]}: {m[1]}")
        
        # Verificar duplicados
        cursor.execute("""
            SELECT referencia, COUNT(*) as cantidad
            FROM terceros
            WHERE referencia = '41258577351'
            GROUP BY referencia
        """)
        dup = cursor.fetchone()
        if dup:
            print(f"\n⚠️  Referencia 41258577351: {dup[1]} registro(s)")
            if dup[1] > 1:
                print("   Todavía hay duplicados!")
        else:
            print("\n✓ Ya no hay duplicados con referencia 41258577351")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓✓✓ CORRECCIONES APLICADAS")
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
    corregir_cambios()
