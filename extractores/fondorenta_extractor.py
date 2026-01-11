#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de movimientos bancarios para Fondo Renta (Bancolombia)
Usamos la misma lógica base que Bancolombia ya que los extractos suelen compartir formato (Fecha - Descripción - Valor).
"""

import pdfplumber
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import os

# Reutilsamos funciones de parseo del extractor de Bancolombia si es posible,
# pero para independencia las copiaremos aquí.

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
        if len(partes) < 3:
            return None
            
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
    Adaptado para Fondo Renta que sigue un formato similar.
    """
    movimientos = []
    
    lines = texto.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Buscar líneas que empiecen con fecha (ej: "27 dic 2025")
        # A veces Fondo Renta puede tener descripción antes, pero asumimos standard primero.
        fecha_match = re.match(r'^(\d{1,2}\s+\w{3}\s+\d{4})\s+(.+)', line)
        
        if fecha_match:
            fecha_str = fecha_match.group(1)
            resto = fecha_match.group(2)
            
            # Buscar el valor al final (ej: -$ 28.000,00 o $ 150.000,00)
            valor_match = re.search(r'(-?\$\s*[\d,.]+)', resto)
            
            if valor_match:
                valor_str = valor_match.group(1)
                # Todo lo que está antes del valor es la descripción
                desc_ref = resto[:valor_match.start()].strip()
                
                # En Fondo Renta a veces no hay referencia numérica explícita, 
                # o es parte de la descripción.
                # Intentamos separar referencia si existen números al final
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


def extraer_movimientos_fondorenta(pdf_path: str) -> List[Dict]:
    """
    Extrae todos los movimientos de un PDF de Fondo Renta.
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
