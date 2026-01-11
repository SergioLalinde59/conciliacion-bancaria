
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de movimientos de Tarjeta de Crédito Bancolombia
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
        if len(partes) < 3: return None
        
        dia = int(partes[0])
        mes = meses.get(partes[1][:3]) # asegurar 3 chars
        if not mes: return None
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
        valor = valor_str.strip()
        es_negativo = False
        
        if valor.startswith('-'):
            es_negativo = True
            valor = valor[1:].strip()
            
        valor = valor.replace('$', '').strip()
        valor = valor.replace('.', '').replace(',', '.')
        
        resultado = Decimal(valor)
        if es_negativo:
            resultado = -resultado
            
        return resultado
    except Exception as e:
        print(f"⚠ Error al parsear valor '{valor_str}': {e}")
        return None

def extraer_movimientos_credito(pdf_path: str) -> List[Dict]:
    """
    Extrae movimientos de tarjeta de crédito Bancolombia.
    """
    movimientos = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Regex para encontrar fecha de inicio
                    # Formato esperado: FECHA DESC FECHA2 MONEDA [VALOR] CUOTAS
                    match_start = re.match(r'^(\d{1,2}\s+\w{3}\s+\d{4})\s+(.+)$', line)
                    
                    if match_start:
                        fecha_str = match_start.group(1)
                        resto = match_start.group(2)
                        
                        # Updated patterns to allow optional second date
                        # Pattern 1: Optional Date + Currency + Value + Quotas
                        # (?:...)? makes the date group non-capturing and optional
                        match_full = re.search(r'(?:(\d{1,2}\s+\w{3}\s+\d{4})\s+)?(COP|USD)\s+(\$?\s*[\d\.,]+)\s+(\d+)$', resto)
                        
                        # Pattern 2: Optional Date + Currency + Quotas (Value on next line)
                        match_wrap = re.search(r'(?:(\d{1,2}\s+\w{3}\s+\d{4})\s+)?(COP|USD)\s+(\d+)$', resto)
                        
                        fecha_txn = parsear_fecha(fecha_str) # Fecha transacción
                        
                        if match_full:
                            # Caso 1: Todo en una línea
                            fecha_post = match_full.group(1) # Fecha corte (opcional)
                            curr = match_full.group(2)
                            val_str = match_full.group(3)
                            cuotas = match_full.group(4)
                            desc = resto[:match_full.start()].strip()
                            
                            val = parsear_valor(val_str)
                            
                            if fecha_txn and val is not None:
                                movimientos.append({
                                    'fecha': fecha_txn,
                                    'descripcion': desc,
                                    'referencia': '', 
                                    'valor': val,
                                    'moneda': curr,
                                    'fecha_str': fecha_str,
                                    'valor_str': val_str
                                })
                                
                        elif match_wrap:
                            # Caso 2: Valor en siguiente línea
                            fecha_post = match_wrap.group(1)
                            curr = match_wrap.group(2)
                            cuotas = match_wrap.group(3)
                            desc = resto[:match_wrap.start()].strip()
                            
                            # Mirar siguiente linea para valor
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                # Buscar valor
                                match_val = re.match(r'^(-?\$?\s*[\d\.,]+)', next_line)
                                if match_val:
                                    val_str = match_val.group(1)
                                    val = parsear_valor(val_str)
                                    
                                    if fecha_txn and val is not None:
                                        movimientos.append({
                                            'fecha': fecha_txn,
                                            'descripcion': desc,
                                            'referencia': '',
                                            'valor': val,
                                            'moneda': curr,
                                            'fecha_str': fecha_str,
                                            'valor_str': val_str
                                        })
                                    # saltamos la linea usada
                                    i += 1
                    
                    i += 1
                    
    except Exception as e:
        print(f"Error extrayendo PDF crédito: {e}")
        raise e

    return movimientos

