#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el constraint de la tabla conceptos
y recargar los datos desde el CSV
"""

import psycopg2

# Configuración de conexión
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def main():
    print("="*70)
    print("ACTUALIZACIÓN DE CONSTRAINT DE TABLA CONCEPTOS")
    print("="*70)
    
    try:
        # Conectar a la base de datos
        print("\n1. Conectando a la base de datos...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   ✓ Conexión exitosa")
        
        # Paso 1: Eliminar el constraint actual
        print("\n2. Eliminando constraint UNIQUE actual en 'concepto'...")
        cursor.execute("ALTER TABLE conceptos DROP CONSTRAINT IF EXISTS conceptos_concepto_key;")
        conn.commit()
        print("   ✓ Constraint eliminado")
        
        # Paso 2: Agregar nuevo constraint en 'claveconcepto'
        print("\n3. Agregando constraint UNIQUE en 'claveconcepto'...")
        cursor.execute("ALTER TABLE conceptos ADD CONSTRAINT conceptos_claveconcepto_key UNIQUE (claveconcepto);")
        conn.commit()
        print("   ✓ Constraint agregado")
        
        # Paso 3: Limpiar la tabla
        print("\n4. Limpiando tabla conceptos...")
        cursor.execute("TRUNCATE TABLE conceptos RESTART IDENTITY CASCADE;")
        conn.commit()
        print("   ✓ Tabla limpiada")
        
        # Verificar el constraint
        print("\n5. Verificando constraints de la tabla conceptos...")
        cursor.execute("""
            SELECT constraint_name, column_name
            FROM information_schema.constraint_column_usage
            WHERE table_name = 'conceptos' 
            AND constraint_schema = 'public'
            ORDER BY constraint_name;
        """)
        constraints = cursor.fetchall()
        for constraint_name, column_name in constraints:
            print(f"   - {constraint_name}: {column_name}")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print("\nAhora puede ejecutar 'cargarDatosMaestros.py' para cargar los datos.")
        print("Esta vez cargará los 405 registros correctamente.")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
