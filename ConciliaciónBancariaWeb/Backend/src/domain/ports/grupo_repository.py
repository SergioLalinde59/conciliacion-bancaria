from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.grupo import Grupo

class GrupoRepository(ABC):
    @abstractmethod
    def guardar(self, grupo: Grupo) -> Grupo:
        pass

    @abstractmethod
    def obtener_por_id(self, grupoid: int) -> Optional[Grupo]:
        pass

    @abstractmethod
    def obtener_todos(self) -> List[Grupo]:
        pass
    
    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> Optional[Grupo]:
        pass

    @abstractmethod
    def obtener_filtros_exclusion(self) -> List[dict]:
        """Obtiene la configuración de grupos a excluir matriculados"""
        pass
