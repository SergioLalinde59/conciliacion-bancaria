#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar el cambio de tipo de dato del campo 'cuenta'
De TEXT a VARCHAR(50)
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

print("Ejecutando script SQL para cambiar tipo de dato del campo 'cuenta'...")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\n1. Cambiando tipo de dato de 'cuenta' a VARCHAR(50)...")
    cursor.execute("ALTER TABLE cuentas ALTER COLUMN cuenta TYPE VARCHAR(50)")
    conn.commit()
    print("✓ Campo 'cuenta' modificado exitosamente")
    
    # Verificar el cambio
    print("\n2. Verificando estructura de la tabla 'cuentas':")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'cuentas'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("\n   Columna         | Tipo de Dato | Longitud Máxima")
    print("   " + "-" * 55)
    for col in columns:
        length = col[2] if col[2] is not None else "N/A"
        print(f"   {col[0]:15} | {col[1]:12} | {length}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Proceso completado exitosamente")
    print("\nRESUMEN:")
    print("  - Campo 'cuenta' cambiado de TEXT a VARCHAR(50)")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    if conn:
        conn.rollback()
        conn.close()
