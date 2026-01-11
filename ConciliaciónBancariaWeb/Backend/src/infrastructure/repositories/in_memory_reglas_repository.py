from typing import List
from src.domain.models.regla_clasificacion import ReglaClasificacion
from src.domain.ports.reglas_repository import ReglasRepository

class InMemoryReglasRepository(ReglasRepository):
    """
    Repositorio en memoria con las reglas 'hardcoded' que migrarmos de la UI antigua.
    En el futuro, esto podría leer de una tabla 'reglas_negocio' en PostgreSQL.
    """
    
    def obtener_todos(self) -> List[ReglaClasificacion]:
        # Migración de REGLAS de asignar_clasificacion_movimiento_ui.py
        return [
            ReglaClasificacion(
                patron='Abono Intereses Ahorros', 
                tercero_id=19, grupo_id=4, concepto_id=23
            ),
            ReglaClasificacion(
                patron='Impto Gobierno', # Cubre "Impto Gobierno 4x100" y 4x1000
                tercero_id=45, grupo_id=22, concepto_id=117
            ),
            ReglaClasificacion(
                patron='Traslado De Fondo', 
                tercero_id=76, grupo_id=47, concepto_id=399
            ),
            # Podemos añadir más reglas comunes aquí
            ReglaClasificacion(
                patron='Netflix', 
                tercero_id=None, grupo_id=None, concepto_id=None # Ejemplo parcial
            )
        ]
