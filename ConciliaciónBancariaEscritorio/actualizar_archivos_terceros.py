#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para completar el renombrado de contactos a terceros
Actualiza todos los archivos Python pendientes

EJECUTAR ESTE SCRIPT DESPUÉSS DE LA MIGRACIÓN SQL
"""

import os
import re
from pathlib import Path

# Directorio base
BASE_DIR = Path(__file__).parent

# Archivos a actualizar
ARCHIVOS_PENDIENTES = [
    "reglas_asignacion_contactos.py",
    "asignar_contactos_ui.py",
    "listar_descripciones_sin_contacto_ui.py",
    "listar_descripciones_sin_contacto.py",
    "cargar_movimientos_ui.py",
    "unificar_cuota_manejo_ui.py",
    "verificar_contactos.py",
    "verificar_asignaciones.py",
    "analizar_datos_para_ia.py",
]

# Patrones de reemplazo
REPLACEMENTS = [
    # SQL - Tabla
    (r'\bFROM contactos\b', 'FROM terceros'),
    (r'\bINTO contactos\b', 'INTO terceros'),
    (r'\bJOIN contactos\b', 'JOIN terceros'),
    (r'\btable_name = [\'"]contactos[\'"]\b', "table_name = 'terceros'"),
    
    # SQL - Columnas
    (r'\bcontactoid\b', 'terceroid'),
    (r'\bContactoID\b', 'TerceroID'),
    (r'\bContactID\b', 'TerceroID'),
    (r'\.contacto\b', '.tercero'),
    (r'c\.contacto\b', 'c.tercero'),
    
    # Python - Variables
    (r'\bcontacto_var\b', 'tercero_var'),
    (r'\bcontactoid_sugerido\b', 'terceroid_sugerido'),
    (r'\bnombre_contacto\b', 'nombre_tercero'),
    (r'\bdescripcion_contacto\b', 'descripcion_tercero'),
    
    # SQL INSERT columns
    (r'\(contacto,', '(tercero,'),
    (r', contacto,', ', tercero,'),
    
    # Strings y mensajes
    (r'"contacto"', '"tercero"'),
    (r"'contacto'", "'tercero'"),
    (r'"Contacto"', '"Tercero"'),
    (r"'Contacto'", "'Tercero'"),
    (r'contactos manualmente', 'terceros manualmente'),
    (r'asignaci[óo]n de ContactoID', 'asignación de TerceroID'),
    (r'Sin ContactoID', 'Sin TerceroID'),
    
    # Nombres de archivos
    (r'insert_contactos', 'insert_terceros'),
]

def actualizar_archivo(ruta_archivo):
    """Actualiza un archivo aplicando todos los reemplazos."""
    ruta = BASE_DIR / ruta_archivo
    
    if not ruta.exists():
        print(f"⚠️  Archivo no encontrado: {ruta_archivo}")
        return False, 0
    
    try:
        # Leer contenido
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        original = contenido
        cambios_totales = 0
        
        # Aplicar reemplazos
        for patron, reemplazo in REPLACEMENTS:
            matches = re.findall(patron, contenido)
            if matches:
                nuevo_contenido = re.sub(patron, reemplazo, contenido)
                if nuevo_contenido != contenido:
                    cambios_totales += len(matches)
                    contenido = nuevo_contenido
        
        # Guardar si hubo cambios
        if contenido != original:
            # Crear backup
            backup_path = ruta.with_suffix('.py.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original)
            
            # Guardar cambios
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            return True, cambios_totales
        else:
            return True, 0
    except Exception as e:
        print(f"✗ Error en {ruta_archivo}: {e}")
        return False, 0

def main():
    """Función principal."""
    print("=" * 70)
    print(" " * 15 + "ACTUALIZACIÓN DE ARCHIVOS PYTHON")
    print(" " * 15 + "CONTACTOS → TERCEROS")
    print("=" * 70)
    print()
    
    archivos_actualizados = 0
    archivos_sin_cambios = 0
    cambios_totales = 0
    errores = []
    
    for archivo in ARCHIVOS_PENDIENTES:
        print(f"📄 {archivo}...", end=" ")
        exito, cambios = actualizar_archivo(archivo)
        
        if exito:
            if cambios > 0:
                print(f"✓ ({cambios} cambios)")
                archivos_actualizados += 1
                cambios_totales += cambios
            else:
                print("ℹ️  (sin cambios)")
                archivos_sin_cambios += 1
        else:
            print("✗ ERROR")
            errores.append(archivo)
    
    # Archivos en subdirectorios
    print("\n📁 Subdirectorio: Verificar Estruturas")
    sub_archivos = [
        "Verificar Estruturas/verificar_estructura_contactos.py",
        "Verificar Estruturas/investigar_tablas.py"
    ]
    
    for archivo in sub_archivos:
        print(f"📄 {archivo}...", end=" ")
        exito, cambios = actualizar_archivo(archivo)
        
        if exito:
            if cambios > 0:
                print(f"✓ ({cambios} cambios)")
                archivos_actualizados += 1
                cambios_totales += cambios
            else:
                print("ℹ️  (sin cambios)")
                archivos_sin_cambios += 1
        else:
            print("✗ ERROR")
            errores.append(archivo)
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Archivos actualizados: {archivos_actualizados}")
    print(f"Archivos sin cambios: {archivos_sin_cambios}")
    print(f"Total de reemplazos: {cambios_totales}")
    
    if errores:
        print(f"\n⚠️  Errores en {len(errores)} archivo(s):")
        for error in errores:
            print(f"  - {error}")
    
    print("=" * 70)
    
    if archivos_actualizados > 0:
        print("\n✓ Actualización completada")
        print("\n💡 Próximos pasos:")
        print("  1. Probar las aplicaciones actualizadas")
        print("  2. Verificar que no haya errores en runtime")
        print("  3. Los archivos originales están respaldados como .py.bak")
    else:
        print("\nℹ️  No se encontraron cambios necesarios")

if __name__ == "__main__":
    main()
