#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación Post-Migración
Verifica que la migración de contactos a terceros fue exitosa
"""

import psycopg2
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def verificar_base_datos():
    """Verifica la estructura de la base de datos."""
    print("=" * 70)
    print("VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Verificar que existe tabla terceros
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'terceros'
            );
        """)
        
        if cur.fetchone()[0]:
            print("✓ Tabla 'terceros' existe")
        else:
            print("✗ ERROR: Tabla 'terceros' NO existe")
            return False
        
        # 2. Verificar que NO existe tabla contactos
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'contactos'
            );
        """)
        
        if not cur.fetchone()[0]:
            print("✓ Tabla 'contactos' NO existe (correcto)")
        else:
            print("⚠️  ADVERTENCIA: Tabla 'contactos' aún existe")
        
        # 3. Verificar columnas de terceros
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'terceros'
            ORDER BY ordinal_position;
        """)
        
        columnas = [r[0] for r in cur.fetchall()]
        print(f"✓ Columnas de 'terceros': {', '.join(columnas)}")
        
        if 'terceroid' in columnas and 'tercero' in columnas:
            print("✓ Columnas renombradas correctamente")
        else:
            print("✗ ERROR: Columnas no están correctamente renombradas")
            return False
        
        # 4. Verificar columna TerceroID en movimientos
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'movimientos' AND column_name = 'terceroid'
            );
        """)
        
        if cur.fetchone()[0]:
            print("✓ Columna 'TerceroID' existe en 'movimientos'")
        else:
            print("✗ ERROR: Columna 'TerceroID' NO existe en 'movimientos'")
            return False
        
        # 5. Verificar foreign key
        cur.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'movimientos' 
            AND constraint_name = 'fk_tercero';
        """)
        
        if cur.fetchone():
            print("✓ Foreign key 'fk_tercero' existe")
        else:
            print("⚠️  ADVERTENCIA: Foreign key 'fk_tercero' no encontrada")
        
        # 6. Contar registros
        cur.execute("SELECT COUNT(*) FROM terceros;")
        count_terceros = cur.fetchone()[0]
        print(f"✓ Registros en 'terceros': {count_terceros}")
        
        cur.execute("SELECT COUNT(*) FROM movimientos WHERE terceroid IS NOT NULL;")
        count_mov = cur.fetchone()[0]
        print(f"✓ Movimientos con TerceroID: {count_mov}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def verificar_importaciones():
    """Verifica que los módulos Python pueden importarse."""
    print("\n" + "=" * 70)
    print("VERIFICACIÓN DE MÓDULOS PYTHON")
    print("=" * 70)
    
    modulos = [
        'gestionar_contactos_ui',
        'reglas_asignacion_contactos_ui',
        'reglas_asignacion_contactos',
        'asignar_contactos_ui',
        'cargar_movimientos_ui',
        'unificar_cuota_manejo_ui',
    ]
    
    errores = []
    
    for modulo in modulos:
        try:
            __import__(modulo)
            print(f"✓ {modulo}")
        except Exception as e:
            print(f"✗ {modulo}: {e}")
            errores.append(modulo)
    
    return len(errores) == 0

def main():
    """Función principal."""
    print("\n")
    print("=" * 70)
    print(" " * 20 + "VERIFICACIÓN POST-MIGRACIÓN")
    print(" " * 20 + "CONTACTOS → TERCEROS")
    print("=" * 70)
    print()
    
    # Verificar base de datos
    db_ok = verificar_base_datos()
    
    # Verificar módulos Python
    py_ok = verificar_importaciones()
    
    # Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    
    if db_ok and py_ok:
        print("✓✓✓ TODAS LAS VERIFICACIONES PASARON EXITOSAMENTE ✓✓✓")
        print("\n💡 La migración está completa y funcional")
        print("   Puedes comenzar a usar las aplicaciones normalmente")
        return 0
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        if not db_ok:
            print("   - Base de datos tiene problemas")
        if not py_ok:
            print("   - Algunos módulos Python tienen errores de importación")
        return 1

if __name__ == "__main__":
    sys.exit(main())
