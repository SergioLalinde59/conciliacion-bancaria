
import sys
import os

# Add Backend path to sys.path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Backend'))

import psycopg2
from src.domain.models.tercero_descripcion import TerceroDescripcion
from src.domain.models.tercero import Tercero
from src.infrastructure.database.postgres_tercero_descripcion_repository import PostgresTerceroDescripcionRepository
from src.infrastructure.database.postgres_tercero_repository import PostgresTerceroRepository

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def main():
    print("=== INICIANDO TEST CRUD TERCERO_DESCRIPCIONES ===")
    
    conn = get_connection()
    try:
        repo_desc = PostgresTerceroDescripcionRepository(conn)
        repo_tercero = PostgresTerceroRepository(conn)

        # 1. Necesitamos un Tercero Maestro para la prueba
        # Intentamos obtener uno existente o creamos uno de prueba
        tercero_maestro = None
        terceros_existentes = repo_tercero.obtener_todos()
        
        if terceros_existentes:
            tercero_maestro = terceros_existentes[0]
            print(f"✓ Usando tercero existente: {tercero_maestro.tercero} (ID: {tercero_maestro.terceroid})")
        else:
            print("Creating dummy tercero for test...")
            nuevo_tercero = Tercero(tercero="TEST_USER_AUTOMATION", terceroid=None)
            tercero_maestro = repo_tercero.guardar(nuevo_tercero)
            print(f"✓ Tercero de prueba creado: {tercero_maestro.tercero} (ID: {tercero_maestro.terceroid})")

        # 2. CREATE
        print("\n--- TEST: CREATE ---")
        nueva_desc = TerceroDescripcion(
            terceroid=tercero_maestro.terceroid,
            tercero_des="TEST_ALIAS_001",
            descripcion="Descripción de prueba creada por script",
            referencia="REF_TEST_123"
        )
        
        desc_guardada = repo_desc.guardar(nueva_desc)
        print(f"✓ Descripción guardada. ID: {desc_guardada.id}, CreatedAt: {desc_guardada.created_at}")
        
        # 3. READ (Get by ID)
        print("\n--- TEST: READ (By ID) ---")
        leida = repo_desc.obtener_por_id(desc_guardada.id)
        if leida:
             print(f"✓ Leído correctamente: Alias='{leida.tercero_des}', Ref='{leida.referencia}'")
             assert leida.tercero_des == "TEST_ALIAS_001"
        else:
            print("❌ ERROR: No se pudo leer el registro recién creado.")

        # 4. READ (Search by Alias)
        print("\n--- TEST: READ (Search by Alias) ---")
        busqueda = repo_desc.buscar_por_alias("test_alias_001") # Testing case insensitivity
        if busqueda:
            print(f"✓ Búsqueda exitosa: Encontrado ID {busqueda.id}")
        else:
            print("❌ ERROR: Búsqueda por alias falló.")

        # 5. UPDATE
        print("\n--- TEST: UPDATE ---")
        leida.descripcion = "Descripción ACTUALIZADA"
        leida.tercero_des = "TEST_ALIAS_UPDATED"
        actualizada = repo_desc.guardar(leida)
        
        verificacion = repo_desc.obtener_por_id(actualizada.id)
        print(f"✓ Valor actualizado en DB: '{verificacion.descripcion}'")
        print(f"✓ Alias actualizado en DB: '{verificacion.tercero_des}'")
        
        # 6. DELETE (Soft Delete)
        print("\n--- TEST: DELETE ---")
        repo_desc.eliminar(actualizada.id)
        borrado = repo_desc.obtener_por_id(actualizada.id)
        if borrado is None:
            print("✓ Registro borrado correctamente (No se recupera con obtener_por_id)")
        else:
             print("❌ ERROR: El registro sigue apareciendo activo.")

        # Verificar directamente en SQL que existe pero con activa=False
        cursor = conn.cursor()
        cursor.execute("SELECT activa FROM tercero_descripciones WHERE id = %s", (actualizada.id,))
        estado = cursor.fetchone()[0]
        print(f"✓ Verificación SQL directa: activa = {estado} (Esperado: False)")
        
        # Clean up (Optional: delete the detailed record physically for test repeatability)
        cursor.execute("DELETE FROM tercero_descripciones WHERE id = %s", (actualizada.id,))
        conn.commit()
        print("\n✓ Limpieza de datos de prueba realizada.")

    except Exception as e:
        print(f"\n❌ EXCEPCIÓN: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n=== FIN DEL TEST ===")

if __name__ == "__main__":
    main()
