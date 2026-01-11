#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de movimientos bancarios desde PDFs de Bancolombia Ahorros
"""

import pdfplumber
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional


def parsear_fecha(fecha_str: str) -> Optional[datetime]:
    """
    Convierte una fecha en formato "DD mes YYYY" a datetime.
    Ejemplo: "27 dic 2025" -> datetime(2025, 12, 27)
    """
    if not fecha_str or not fecha_str.strip():
        return None
    
    try:
        # Mapeo de meses en español
        meses = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }
        
        partes = fecha_str.lower().split()
        dia = int(partes[0])
        mes = meses[partes[1]]
        año = int(partes[2])
        
        return datetime(año, mes, dia)
    except Exception as e:
        print(f"⚠ Error al parsear fecha '{fecha_str}': {e}")
        return None


def parsear_valor(valor_str: str) -> Optional[Decimal]:
    """
    Convierte un valor en formato "$X.XXX,XX" o "-$ X.XXX,XX" a Decimal.
    Ejemplos:
    - "$ 150.000,00" -> Decimal("150000.00")
    - "-$ 28.000,00" -> Decimal("-28000.00")
    """
    if not valor_str or not valor_str.strip():
        return None
    
    try:
        # Limpiar el string
        valor = valor_str.strip()
        es_negativo = False
        
        # Detectar signo negativo
        if valor.startswith('-'):
            es_negativo = True
            valor = valor[1:].strip()
        
        # Remover símbolo de peso y espacios
        valor = valor.replace('$', '').strip()
        
        # Remover puntos (separadores de miles) y reemplazar coma por punto (decimal)
        valor = valor.replace('.', '').replace(',', '.')
        
        resultado = Decimal(valor)
        
        if es_negativo:
            resultado = -resultado
        
        return resultado
    except Exception as e:
        print(f"⚠ Error al parsear valor '{valor_str}': {e}")
        return None


def extraer_movimientos_desde_texto(texto: str) -> List[Dict]:
    """
    Extrae movimientos del texto del PDF usando expresiones regulares.
    
    Returns:
        Lista de diccionarios con keys: fecha, descripcion, referencia, valor
    """
    movimientos = []
    
    lines = texto.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
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
                
                # Intentar separar referencia (números al final, mínimo 6 dígitos)
                ref_match = re.search(r'(\d{6,})$', desc_ref)
                if ref_match:
                    referencia = ref_match.group(1)
                    descripcion = desc_ref[:ref_match.start()].strip()
                else:
                    referencia = ""
                    descripcion = desc_ref
                
                movimiento = {
                    'fecha_str': fecha_str,
                    'descripcion': descripcion,
                    'referencia': referencia,
                    'valor_str': valor_str
                }
                movimientos.append(movimiento)
    
    return movimientos


def extraer_movimientos_bancolombia(pdf_path: str) -> List[Dict]:
    """
    Extrae todos los movimientos de un PDF de Bancolombia Ahorros.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        Lista de diccionarios con los movimientos. Cada movimiento contiene:
        - fecha: datetime
        - descripcion: str
        - referencia: str
        - valor: Decimal
        - fecha_str: str (original)
        - valor_str: str (original)
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        Exception: Si hay error al leer el PDF
    """
    movimientos_raw = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    movs = extraer_movimientos_desde_texto(texto)
                    movimientos_raw.extend(movs)
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error al leer el PDF: {e}")
    
    # Normalizar y parsear los datos
    movimientos_procesados = []
    
    for mov in movimientos_raw:
        fecha = parsear_fecha(mov['fecha_str'])
        valor = parsear_valor(mov['valor_str'])
        
        # Solo agregar si se pudo parsear fecha y valor
        if fecha and valor is not None:
            movimientos_procesados.append({
                'fecha': fecha,
                'descripcion': mov['descripcion'].strip(),
                'referencia': mov['referencia'].strip(),
                'valor': valor,
                'fecha_str': mov['fecha_str'],
                'valor_str': mov['valor_str']
            })
    
    return movimientos_procesados


def obtener_estadisticas(movimientos: List[Dict]) -> Dict:
    """
    Calcula estadísticas sobre los movimientos extraídos.
    
    Returns:
        Diccionario con estadísticas: total, debitos, creditos, suma_total
    """
    total = len(movimientos)
    debitos = sum(1 for m in movimientos if m['valor'] < 0)
    creditos = total - debitos
    suma_total = sum(m['valor'] for m in movimientos)
    
    return {
        'total': total,
        'debitos': debitos,
        'creditos': creditos,
        'suma_total': suma_total
    }


if __name__ == "__main__":
    # Test del extractor
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = r"F:\1. Cloud\4. AI\1. Antigravity\Gastos SLB\MovimientosPendientes\MovimientosTusCuentasBancolombia28Dic2025.pdf"
    
    print("="*80)
    print("TEST - EXTRACTOR BANCOLOMBIA")
    print("="*80)
    
    try:
        movimientos = extraer_movimientos_bancolombia(pdf_path)
        stats = obtener_estadisticas(movimientos)
        
        print(f"\n✓ Archivo procesado: {pdf_path}")
        print(f"✓ Total movimientos extraídos: {stats['total']}")
        print(f"  - Débitos: {stats['debitos']}")
        print(f"  - Créditos: {stats['creditos']}")
        print(f"  - Suma total: ${stats['suma_total']:,.2f}")
        
        print("\n📋 PRIMEROS 5 MOVIMIENTOS:")
        print("-"*80)
        for i, mov in enumerate(movimientos[:5], 1):
            print(f"\n{i}. {mov['fecha'].strftime('%Y-%m-%d')}")
            print(f"   {mov['descripcion']}")
            print(f"   Ref: {mov['referencia'] if mov['referencia'] else ''}")
            print(f"   Valor: ${mov['valor']:,.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
