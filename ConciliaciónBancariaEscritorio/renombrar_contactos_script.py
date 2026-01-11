#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para renombrar referencias de contactos a terceros en archivos Python
Automatiza el renombrado masivo de:
- contactos → terceros
- contactoid → terceroid  
- contacto → tercero
- ContactID → TerceroID
"""

import os
import re
from pathlib import Path

# Directorio base
BASE_DIR = r"f:\1. Cloud\4. AI\1. Antigravity\Gastos SLB Vo"

# Archivos a procesar (excluir los ya modificados)
ARCHIVOS_A_PROCESAR = [
    "gestionar_contactos_ui.py",
    "asignar_contactos_ui.py",
    "reglas_asignacion_contactos_ui.py",
    "reglas_asignacion_contactos.py",
    "listar_descripciones_sin_contacto_ui.py",
    "listar_descripciones_sin_contacto.py",
    "cargar_movimientos_ui.py",
    "unificar_cuota_manejo_ui.py",
    "verificar_contactos.py",
    "verificar_asignaciones.py",
    "analizar_datos_para_ia.py",
    r"Verificar Estruturas\verificar_estructura_contactos.py",
    r"Verificar Estruturas\investigar_tablas.py",
]

# Patrones de reemplazo (orden importa - más específicos primero)
REPLACEMENTS = [
    # Nombres de clase e identificadores
    (r'\bGestionarContactosGUI\b', 'GestionarTercerosGUI'),
    
    # Nombres de tabla
    (r'\bcontactos\b', 'terceros'),
    (r'\bContactos\b', 'Terceros'),
    
    # Nombres de campos
    (r'\bcontactoid\b', 'terceroid'),
    (r'\bContactoID\b', 'TerceroID'),
    (r'\bContactID\b', 'TerceroID'),
    
    # Nombres de columnas
    (r'\bcontacto\b(?!\s*=)', 'tercero'),  # No reemplazar en asignaciones de variables
    
    # Strings específicos
    (r'"[Cc]ontacto"', lambda m: m.group(0).replace('ontacto', 'ercero')),
    (r"'[Cc]ontacto'", lambda m: m.group(0).replace('ontacto', 'ercero')),
    
    # Títulos y mensajes (preservar mayúsculas)
    (r'Contactos', 'Terceros'),
    (r'contactos', 'terceros'),
    (r'Contacto', 'Tercero'),
    
    # Variables y parámetros
    (r'\bcontacto_', 'tercero_'),
    (r'\bcontactoid_', 'terceroid_'),
    
    # Archivos y referencias
    (r'contactos\.', 'terceros.'),
    (r'insert_contactos', 'insert_terceros'),
]

# Patrones específicos por archivo
ARCHIVO_ESPECIFICO = {
    "gestionar_contactos_ui.py": [
        (r'title\("Gestión de Contactos"\)', 'title("Gestión de Terceros")'),
        (r'"Gestión de Contactos - CRUD"', '"Gestión de Terceros - CRUD"'),
    ],
    "asignar_contactos_ui.py": [
        (r'asignar_contactos_ui', 'asignar_terceros_ui'),
    ],
}

def procesar_archivo(ruta_archivo):
    """Procesa un archivo aplicando todos los reemplazos."""
    ruta = Path(BASE_DIR) / ruta_archivo
    
    if not ruta.exists():
        print(f"⚠️  Archivo no encontrado: {ruta_archivo}")
        return 0
    
    print(f"\n📄 Procesando: {ruta_archivo}")
    
    try:
        # Leer contenido
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        original = contenido
        cambios = 0
        
        # Aplicar reemplazos generales
        for patron, reemplazo in REPLACEMENTS:
            if callable(reemplazo):
                nuevo_contenido = re.sub(patron, reemplazo, contenido)
            else:
                nuevo_contenido = re.sub(patron, reemplazo, contenido)
            
            if nuevo_contenido != contenido:
                cambios += contenido.count(re.findall(patron, contenido)[0]) if re.findall(patron, contenido) else 1
                contenido = nuevo_contenido
        
        # Aplicar reemplazos específicos del archivo
        if ruta_archivo in ARCHIVO_ESPECIFICO:
            for patron, reemplazo in ARCHIVO_ESPECIFICO[ruta_archivo]:
                contenido = re.sub(patron, reemplazo, contenido)
        
        # Guardar cambios si hubo modificaciones
        if contenido != original:
            backup_path = ruta.with_suffix('.py.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original)
            
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            print(f"  ✓ {cambios} reemplazos realizados (backup: {backup_path.name})")
            return cambios
        else:
            print(f"  ℹ️  Sin cambios necesarios")
            return 0
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return 0

def main():
    """Función principal."""
    print("="*70)
    print(" "*15 + "RENOMBRADO MASIVO: CONTACTOS → TERCEROS")
    print("="*70)
    
    total_archivos = 0
    total_cambios = 0
    
    for archivo in ARCHIVOS_A_PROCESAR:
        cambios = procesar_archivo(archivo)
        if cambios > 0:
            total_archivos += 1
            total_cambios += cambios
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Archivos modificados: {total_archivos}")
    print(f"Total de reemplazos: {total_cambios}")
    print("="*70)
    print("\n✓ Proceso completado")

if __name__ == "__main__":
    main()
