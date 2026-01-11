#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Reiniciar Todas las Tablas del Proyecto
Elimina todas las tablas de la base de datos Mvtos en PostgreSQL.

Autor: Antigravity
Fecha: 2025-12-29
"""

import psycopg2
from datetime import datetime
import sys

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

# Lista de tablas en orden de eliminación (respetando dependencias)
TABLAS = [
    'movimientos',  # Primero: tiene FKs a todas las maestras
    'conceptos',    # Segundo: tiene FK a grupos
    'grupos',       # Maestras sin dependencias
    'tipomov',
    'monedas',
    'terceros',
    'cuentas'
]


def log(mensaje, tipo='INFO'):
    """Imprime un mensaje con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    iconos = {
        'INFO': 'ℹ️',
        'SUCCESS': '✓',
        'ERROR': '✗',
        'WARNING': '⚠️',
        'QUESTION': '❓'
    }
    icono = iconos.get(tipo, '')
    print(f"[{timestamp}] {icono} {mensaje}")


def conectar_db():
    """Conecta a la base de datos PostgreSQL."""
    try:
        log("Conectando a la base de datos...", 'INFO')
        conn = psycopg2.connect(**DB_CONFIG)
        log(f"Conexión exitosa a '{DB_CONFIG['database']}'", 'SUCCESS')
        return conn
    except Exception as e:
        log(f"Error al conectar: {e}", 'ERROR')
        return None


def verificar_tablas_existentes(cursor):
    """Verifica qué tablas existen en la base de datos."""
    tablas_existentes = []
    
    for tabla in TABLAS:
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (tabla,))
            
            existe = cursor.fetchone()[0]
            if existe:
                # Contar registros en la tabla
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                count = cursor.fetchone()[0]
                tablas_existentes.append((tabla, count))
        except Exception as e:
            log(f"Error al verificar tabla '{tabla}': {e}", 'WARNING')
    
    return tablas_existentes


def confirmar_eliminacion(tablas_existentes):
    """Solicita confirmación al usuario antes de eliminar las tablas."""
    print("\n" + "="*70)
    print("⚠️  ADVERTENCIA: ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️")
    print("="*70)
    
    if not tablas_existentes:
        log("No se encontraron tablas para eliminar.", 'INFO')
        return False
    
    print(f"\nSe eliminarán las siguientes {len(tablas_existentes)} tabla(s):\n")
    
    total_registros = 0
    for tabla, count in tablas_existentes:
        print(f"  • {tabla:<15} - {count:>6,} registros")
        total_registros += count
    
    print(f"\n{'TOTAL':<17} - {total_registros:>6,} registros\n")
    print("="*70)
    
    print("\n❗ Todas estas tablas serán ELIMINADAS PERMANENTEMENTE.")
    print("❗ Se perderán TODOS los datos almacenados en ellas.\n")
    
    respuesta = input("Escribe 'SI' (en mayúsculas) para confirmar la eliminación: ")
    
    return respuesta == 'SI'


def eliminar_tablas(conn, tablas_existentes):
    """Elimina todas las tablas de la base de datos."""
    cursor = conn.cursor()
    tablas_eliminadas = []
    errores = []
    
    print("\n" + "="*70)
    log("INICIANDO ELIMINACIÓN DE TABLAS", 'INFO')
    print("="*70 + "\n")
    
    for tabla, count in tablas_existentes:
        try:
            log(f"Eliminando tabla '{tabla}' ({count:,} registros)...", 'INFO')
            cursor.execute(f"DROP TABLE IF EXISTS {tabla} CASCADE")
            conn.commit()
            log(f"Tabla '{tabla}' eliminada exitosamente", 'SUCCESS')
            tablas_eliminadas.append(tabla)
        except Exception as e:
            log(f"Error al eliminar tabla '{tabla}': {e}", 'ERROR')
            errores.append((tabla, str(e)))
            conn.rollback()
    
    cursor.close()
    return tablas_eliminadas, errores


def mostrar_resumen(tablas_eliminadas, errores):
    """Muestra un resumen de la operación."""
    print("\n" + "="*70)
    print("RESUMEN DE LA OPERACIÓN")
    print("="*70 + "\n")
    
    if tablas_eliminadas:
        log(f"Tablas eliminadas exitosamente: {len(tablas_eliminadas)}", 'SUCCESS')
        for tabla in tablas_eliminadas:
            print(f"  ✓ {tabla}")
    
    if errores:
        print()
        log(f"Errores encontrados: {len(errores)}", 'ERROR')
        for tabla, error in errores:
            print(f"  ✗ {tabla}: {error}")
    
    print("\n" + "="*70)
    
    if not errores and tablas_eliminadas:
        log("PROCESO COMPLETADO EXITOSAMENTE", 'SUCCESS')
    elif errores:
        log("PROCESO COMPLETADO CON ERRORES", 'WARNING')
    else:
        log("NO SE REALIZARON CAMBIOS", 'INFO')
    
    print("="*70 + "\n")


def main():
    """Función principal."""
    print("\n" + "="*70)
    print(" "*15 + "REINICIO DE TABLAS - Base de Datos MVTOS")
    print("="*70 + "\n")
    
    # Conectar a la base de datos
    conn = conectar_db()
    if not conn:
        log("No se pudo conectar a la base de datos. Abortando.", 'ERROR')
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Verificar tablas existentes
        log("Verificando tablas existentes...", 'INFO')
        tablas_existentes = verificar_tablas_existentes(cursor)
        
        if not tablas_existentes:
            log("No se encontraron tablas para eliminar.", 'INFO')
            cursor.close()
            conn.close()
            return
        
        # Solicitar confirmación
        cursor.close()
        if not confirmar_eliminacion(tablas_existentes):
            log("Operación cancelada por el usuario.", 'WARNING')
            conn.close()
            return
        
        # Eliminar tablas
        tablas_eliminadas, errores = eliminar_tablas(conn, tablas_existentes)
        
        # Mostrar resumen
        mostrar_resumen(tablas_eliminadas, errores)
        
    except Exception as e:
        log(f"Error crítico: {e}", 'ERROR')
    finally:
        if conn:
            conn.close()
            log("Conexión cerrada", 'INFO')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        log("Operación cancelada por el usuario (Ctrl+C)", 'WARNING')
        sys.exit(0)
