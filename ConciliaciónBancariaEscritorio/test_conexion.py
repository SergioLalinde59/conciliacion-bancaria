#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba de conexión a PostgreSQL
"""

import psycopg2

# Configuración de conexión
HOST = 'localhost'
PORT = 5433
USER = 'postgres'
PASSWORD = 'SLB'
DATABASE = 'Mvtos'

print("="*60)
print("PROBANDO CONEXIÓN A POSTGRESQL")
print("="*60)
print(f"Host:     {HOST}")
print(f"Puerto:   {PORT}")
print(f"Usuario:  {USER}")
print(f"Password: {'*' * len(PASSWORD)}")
print(f"Database: {DATABASE}")
print("-"*60)

try:
    print("\n[1/3] Intentando conectar...")
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    print("✓ Conexión exitosa!")
    
    print("\n[2/3] Probando cursor...")
    cursor = conn.cursor()
    print("✓ Cursor creado exitosamente!")
    
    print("\n[3/3] Ejecutando consulta de prueba...")
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ Versión de PostgreSQL:")
    print(f"  {version[0]}")
    
    # Verificar si la base de datos mvtos existe
    print("\n[Extra] Verificando tablas en la base de datos...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    if tables:
        print(f"✓ Se encontraron {len(tables)} tabla(s):")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("  (No hay tablas en la base de datos aún)")
    
    # Cerrar
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ TODAS LAS PRUEBAS EXITOSAS")
    print("="*60)
    print("\n¡La conexión está funcionando correctamente!")
    print("Puedes proceder a cargar los datos maestros.\n")
    
except psycopg2.OperationalError as e:
    print(f"\n✗ ERROR DE CONEXIÓN:")
    print(f"  {str(e)}")
    print("\nPosibles causas:")
    print("  1. PostgreSQL no está corriendo")
    print("  2. El puerto 5433 no es correcto")
    print("  3. El usuario o contraseña son incorrectos")
    print("  4. La base de datos 'mvtos' no existe")
    print("\nSoluciones:")
    print("  - Verifica que PostgreSQL esté ejecutándose")
    print("  - Confirma que la base de datos 'mvtos' exista")
    print("  - Verifica las credenciales de acceso\n")
    
except Exception as e:
    print(f"\n✗ ERROR INESPERADO:")
    print(f"  {str(e)}\n")
