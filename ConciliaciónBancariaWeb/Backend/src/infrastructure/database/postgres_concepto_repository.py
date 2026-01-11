from typing import List, Optional
import psycopg2
from src.domain.models.concepto import Concepto
from src.domain.ports.concepto_repository import ConceptoRepository

class PostgresConceptoRepository(ConceptoRepository):
    def __init__(self, connection):
        self.conn = connection

    def guardar(self, concepto: Concepto) -> Concepto:
        cursor = self.conn.cursor()
        try:
            if concepto.conceptoid:
                # Actualizar
                cursor.execute(
                    """
                    UPDATE conceptos 
                    SET concepto = %s, grupoid_fk = %s, activa = %s
                    WHERE conceptoid = %s
                    """,
                    (concepto.concepto, concepto.grupoid_fk, concepto.activa, concepto.conceptoid)
                )
            else:
                # Insertar
                cursor.execute(
                    """
                    INSERT INTO conceptos (concepto, grupoid_fk, activa) 
                    VALUES (%s, %s, %s) 
                    RETURNING conceptoid
                    """,
                    (concepto.concepto, concepto.grupoid_fk, concepto.activa)
                )
                concepto.conceptoid = cursor.fetchone()[0]
            self.conn.commit()
            return concepto
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def obtener_por_id(self, conceptoid: int) -> Optional[Concepto]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT conceptoid, concepto, grupoid_fk, activa FROM conceptos WHERE conceptoid = %s AND activa = TRUE",
            (conceptoid,)
        )
        row = cursor.fetchone()
        cursor.close()
        if row:
            return Concepto(
                conceptoid=row[0], 
                concepto=row[1], 
                grupoid_fk=row[2],
                activa=row[3]
            )
        return None

    def obtener_todos(self) -> List[Concepto]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT conceptoid, concepto, grupoid_fk, activa FROM conceptos WHERE activa = TRUE ORDER BY concepto")
        rows = cursor.fetchall()
        cursor.close()
        return [
            Concepto(
                conceptoid=r[0], 
                concepto=r[1], 
                grupoid_fk=r[2],
                activa=r[3]
            ) for r in rows
        ]
    
    def buscar_por_grupoid(self, grupoid: int) -> List[Concepto]:
        """Busca conceptos por grupoid_fk"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT conceptoid, concepto, grupoid_fk, activa 
            FROM conceptos 
            WHERE grupoid_fk = %s AND activa = TRUE
            ORDER BY concepto
            """, 
            (grupoid,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            Concepto(
                conceptoid=r[0], 
                concepto=r[1], 
                grupoid_fk=r[2],
                activa=r[3]
            ) for r in rows
        ]
        
    def eliminar(self, conceptoid: int):
        cursor = self.conn.cursor()
        try:
            # Soft delete
            cursor.execute("UPDATE conceptos SET activa = FALSE WHERE conceptoid = %s", (conceptoid,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

