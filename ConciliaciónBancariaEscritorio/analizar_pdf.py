#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar la estructura del PDF de Bancolombia y extraer movimientos
"""

import pdfplumber
import re
from datetime import datetime

pdf_path = r"F:\1. Cloud\4. AI\1. Antigravity\Gastos SLB\MovimientosPendientes\MovimientosTusCuentasBancolombia28Dic2025.pdf"

print("="*80)
print("ANÁLISIS DE PDF - MOVIMIENTOS BANCOLOMBIA")
print("="*80)

def parse_movimientos_from_text(text):
    """Extrae movimientos del texto del PDF usando expresiones regulares."""
    movimientos = []
    
    # Patrón para capturar: Fecha, Descripción (multi-línea), Referencia (opcional), Valor
    # Formato: DD mes YYYY descripción [referencia] $valor
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Buscar líneas que empiecen con fecha (ej: "27 dic 2025")
        fecha_match = re.match(r'^(\d{1,2}\s+\w{3}\s+\d{4})\s+(.+)', line)
        
        if fecha_match:
            fecha_str = fecha_match.group(1)
            resto = fecha_match.group(2)
            
            # Buscar el valor al final (ej: -$ 28.000,00 o $ 150.000,00)
            valor_match = re.search(r'(-?\$\s*[\d,.]+)', resto)
            
            if valor_match:
                valor_str = valor_match.group(1)
                # Todo lo que está antes del valor es descripción + referencia
                desc_ref = resto[:valor_match.start()].strip()
                
                # Intentar separar referencia (números al final)
                ref_match = re.search(r'(\d{6,})$', desc_ref)
                if ref_match:
                    referencia = ref_match.group(1)
                    descripcion = desc_ref[:ref_match.start()].strip()
                else:
                    referencia = ""
                    descripcion = desc_ref
                
                movimiento = {
                    'fecha': fecha_str,
                    'descripcion': descripcion,
                    'referencia': referencia,
                    'valor': valor_str
                }
                movimientos.append(movimiento)
        
        i += 1
    
    return movimientos

try:
    all_movimientos = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\n📄 Archivo: {pdf_path}")
        print(f"📊 Total de páginas: {len(pdf.pages)}")
        
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            if text:
                movimientos = parse_movimientos_from_text(text)
                all_movimientos.extend(movimientos)
                print(f"\n📄 Página {i}: {len(movimientos)} movimientos encontrados")
    
    print(f"\n{'='*80}")
    print(f"RESUMEN: Total de {len(all_movimientos)} movimientos extraídos")
    print('='*80)
    
    # Mostrar primeros 10 movimientos
    print("\n📋 PRIMEROS 10 MOVIMIENTOS:")
    print("-"*80)
    for idx, mov in enumerate(all_movimientos[:10], 1):
        print(f"\n{idx}. Fecha: {mov['fecha']}")
        print(f"   Descripción: {mov['descripcion']}")
        print(f"   Referencia: {mov['referencia']}")
        print(f"   Valor: {mov['valor']}")
    
    # Estadísticas
    print(f"\n{'='*80}")
    print("ESTADÍSTICAS")
    print('='*80)
    print(f"Total movimientos: {len(all_movimientos)}")
    
    # Contar débitos y créditos
    debitos = sum(1 for m in all_movimientos if '-$' in m['valor'])
    creditos = sum(1 for m in all_movimientos if '-$' not in m['valor'])
    print(f"Débitos: {debitos}")
    print(f"Créditos: {creditos}")
    
except Exception as e:
    print(f"\n❌ Error al analizar el PDF: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("FIN DEL ANÁLISIS")
print("="*80)
