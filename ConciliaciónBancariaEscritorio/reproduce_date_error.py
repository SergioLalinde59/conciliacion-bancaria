from datetime import datetime

class DateParserTest:
    def parsear_fecha(self, fecha_str):
        """Convierte una fecha en formato DD/MMM/YYYY, YYYY-MM-DD o YYYY/MMM/DD a objeto datetime."""
        if not fecha_str or fecha_str.strip() == '':
            return None
        
        # 1. Intentar formato YYYY-MM-DD (ISO estándar)
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            pass
        
        # Diccionarios de meses (Inglés y Español)
        meses = {
            # Inglés
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            # Español
            'ene': 1, 'abr': 4, 'ago': 8, 'dic': 12
        }
        # Completar mapeo español si faltan o si se solapan con inglés (mar, may, jun, jul, sep, oct, nov son iguales o prefijos)
        # Nos aseguramos de cubrir todos
        meses_es = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }
        meses.update(meses_es)
        
        try:
            partes = fecha_str.split('/')
            if len(partes) != 3:
                raise ValueError("Formato de fecha no reconocido")
            
            # Detectar si es YYYY/MMM/DD o DD/MMM/YYYY
            # Asumimos que si el primero es > 31, es año.
            p1 = partes[0].strip()
            p2 = partes[1].strip().lower() # Mes nombre
            p3 = partes[2].strip()
            
            if p1.isdigit() and int(p1) > 31:
                # Formato YYYY/MMM/DD
                año = int(p1)
                mes = meses.get(p2)
                dia = int(p3)
            else:
                # Formato DD/MMM/YYYY
                dia = int(p1)
                mes = meses.get(p2)
                año = int(p3)
            
            if mes is None:
                raise ValueError(f"Mes desconocido: {p2}")
                
            return datetime(año, mes, dia).date()
        except Exception as e:
            return f"Error: {e}"

parser = DateParserTest()

# Test cases
test_dates = [
    "2026/ene/04", # Target failing case (Spanish YYYY/MMM/DD)
    "14/Jan/2025", # English DD/MMM/YYYY
    "2025-01-14",  # ISO YYYY-MM-DD
    "04/ene/2026", # Spanish DD/MMM/YYYY
    "2026/feb/04", # Spanish YYYY/MMM/DD
    "invalid"
]

print("Testing Spanish Date Support:")
for date_str in test_dates:
    result = parser.parsear_fecha(date_str)
    print(f"Input: '{date_str}' -> Result: {result}")
