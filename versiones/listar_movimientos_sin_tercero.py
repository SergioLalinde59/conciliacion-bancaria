#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listado de Movimientos sin Tercero
Genera un listado de todas las descripciones únicas de movimientos
que no se encuentran en la tabla terceros.

Autor: Antigravity
Fecha: 2025-12-29
"""

import psycopg2
from psycopg2 import sql
import pandas as pd
from datetime import datetime
import os

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def conectar_bd():
    """Establece conexión con la base de datos."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Conexión exitosa a la base de datos")
        return conn
    except Exception as e:
        print(f"✗ Error al conectar a la base de datos: {e}")
        return None

def obtener_movimientos_sin_tercero(conn):
    """
    Obtiene todas las descripciones únicas de movimientos
    que no están en la tabla terceros.
    
    Returns:
        list: Lista de diccionarios con contact y reference
    """
    cursor = conn.cursor()
    
    # Query para obtener descripciones que no están en terceros
    # Agrupamos por descripción y tomamos una referencia de ejemplo
    query = """
        SELECT DISTINCT
            m.Descripcion as contact,
            MIN(m.Referencia) as reference,
            COUNT(*) as cantidad_movimientos,
            MIN(m.Fecha) as primera_fecha,
            MAX(m.Fecha) as ultima_fecha
        FROM movimientos m
        LEFT JOIN terceros c ON LOWER(TRIM(m.Descripcion)) = LOWER(TRIM(c.tercero))
        WHERE c.terceroid IS NULL
        GROUP BY m.Descripcion
        ORDER BY cantidad_movimientos DESC, m.Descripcion
    """
    
    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    
    # Convertir a lista de diccionarios
    descripciones = []
    for row in resultados:
        descripciones.append({
            'contact': row[0],
            'reference': row[1] if row[1] else '',
            'cantidad_movimientos': row[2],
            'primera_fecha': row[3],
            'ultima_fecha': row[4]
        })
    
    return descripciones

def generar_reporte_csv(descripciones, filename='movimientos_sin_tercero.csv'):
    """
    Genera un archivo CSV con el reporte.
    
    Args:
        descripciones: Lista de diccionarios con los datos
        filename: Nombre del archivo CSV
    """
    if not descripciones:
        print("⚠ No hay movimientos sin tercero")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(descripciones)
    
    # Guardar CSV
    filepath = os.path.join(os.path.dirname(__file__), filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"✓ Reporte guardado en: {filepath}")
    print(f"  Total de descripciones únicas sin tercero: {len(descripciones)}")
    
    return filepath

def generar_reporte_consola(descripciones):
    """
    Muestra un reporte formateado en consola.
    
    Args:
        descripciones: Lista de diccionarios con los datos
    """
    print("\n" + "="*100)
    print("MOVIMIENTOS SIN TERCERO ASIGNADO")
    print("="*100)
    print(f"\nTotal de descripciones únicas sin tercero: {len(descripciones)}\n")
    
    # Encabezado
    print(f"{'#':<5} {'TERCERO (Descripción)':<50} {'REFERENCIA':<30} {'Cant.':<8}")
    print("-"*100)
    
    # Mostrar primeras 50 descripciones
    for i, desc in enumerate(descripciones[:50], 1):
        contact = desc['contact'][:48] if len(desc['contact']) > 48 else desc['contact']
        reference = desc['reference'][:28] if len(desc['reference']) > 28 else desc['reference']
        cantidad = desc['cantidad_movimientos']
        
        print(f"{i:<5} {contact:<50} {reference:<30} {cantidad:<8}")
    
    if len(descripciones) > 50:
        print(f"\n... y {len(descripciones) - 50} descripciones más (ver archivo CSV completo)")
    
    print("\n" + "="*100)
    
    # Estadísticas adicionales
    total_movimientos = sum(d['cantidad_movimientos'] for d in descripciones)
    print(f"\nEstadísticas:")
    print(f"  • Total de movimientos sin tercero: {total_movimientos:,}")
    print(f"  • Descripciones únicas: {len(descripciones):,}")
    print(f"  • Promedio movimientos por descripción: {total_movimientos/len(descripciones):.1f}")

def generar_script_insert(descripciones, filename='insert_terceros.sql', limite=None):
    """
    Genera un script SQL con INSERT para crear los terceros faltantes.
    
    Args:
        descripciones: Lista de diccionarios con los datos
        filename: Nombre del archivo SQL
        limite: Número máximo de registros a generar (None = todos)
    """
    if not descripciones:
        return
    
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    # Limitar si se especifica
    datos = descripciones[:limite] if limite else descripciones
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("-- Script para insertar terceros faltantes\n")
        f.write(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total de terceros a insertar: {len(datos)}\n\n")
        f.write("BEGIN;\n\n")
        
        for i, desc in enumerate(datos, 1):
            contact_name = desc['contact'].replace("'", "''")  # Escapar comillas
            reference = desc['reference'].replace("'", "''") if desc['reference'] else ''
            
            f.write(f"-- Descripción #{i}: {desc['cantidad_movimientos']} movimientos\n")
            f.write(f"INSERT INTO terceros (tercero, contacttypeid) \n")
            f.write(f"VALUES ('{contact_name}', NULL);\n")
            f.write(f"-- Referencia de ejemplo: {reference}\n\n")
        
        f.write("COMMIT;\n")
        f.write(f"\n-- Total de inserts: {len(datos)}\n")
    
    print(f"✓ Script SQL generado en: {filepath}")
    print(f"  Total de INSERT statements: {len(datos)}")

def main():
    """Función principal."""
    print("\n" + "="*100)
    print("GENERADOR DE LISTADO DE MOVIMIENTOS SIN TERCERO")
    print("="*100 + "\n")
    
    # Conectar a la base de datos
    conn = conectar_bd()
    if not conn:
        return
    
    try:
        # Obtener descripciones sin tercero
        print("\n🔍 Buscando movimientos sin tercero...")
        descripciones = obtener_movimientos_sin_tercero(conn)
        
        if not descripciones:
            print("✓ Todos los movimientos tienen un tercero asignado")
            return
        
        # Generar reportes
        print(f"\n✓ Se encontraron {len(descripciones)} descripciones únicas sin tercero\n")
        
        # 1. Reporte en consola
        generar_reporte_consola(descripciones)
        
        # 2. Reporte CSV completo
        print("\n📄 Generando archivos de reporte...")
        csv_path = generar_reporte_csv(descripciones)
        
        # 3. Script SQL para insertar terceros (opcional)
        respuesta = input("\n¿Deseas generar un script SQL para insertar estos terceros? (s/n): ")
        if respuesta.lower() == 's':
            generar_script_insert(descripciones)
        
        print("\n✓ Proceso completado exitosamente")
        
    except Exception as e:
        print(f"\n✗ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n✓ Conexión cerrada")

if __name__ == "__main__":
    main()
