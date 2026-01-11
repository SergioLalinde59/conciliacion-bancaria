# Plan de Trabajo: Normalización de Terceros

Este documento detalla el plan para normalizar la tabla `terceros` a la Tercera Forma Normal (3NF), creando una nueva tabla `tercero_descripciones` para manejar múltiples descripciones (alias) asociadas a un único tercero.

## 1. Objetivo
Centralizar la entidad "Tercero" para que exista un único registro por nombre (ej: "Amazon"), eliminando la duplicidad causada por tener diferentes descripciones (ej: "Amazon AWS", "Amazon Prime") en registros separados.

## 2. Estado Actual
La tabla `terceros` combina la entidad y la regla de mapeo:
- `Terceros (id, tercero, descripcion, referencia, activa)`
- **Problema**: Si "Amazon" aparece con descripciones diferentes, se crean múltiples `tercero_id`. Los movimientos quedan dispersos entre estos IDs.

## 3. Estado Deseado (Target)
Separación de la entidad y sus variantes de descripción:
1. **Tabla `terceros`**:
   - `terceroid` (PK)
   - `tercero` (Nombre único)
   - `referencia` (Opcional, si aplica al tercero globalmente)
   - `activa`

2. **Tabla `tercero_descripciones`** (Nueva):
   - `id` (PK)
   - `terceroid` (FK -> terceros.terceroid)
   - `descripcion` (Texto de coincidencia)

## 4. Plan de Ejecución

### Fase 1: Base de Datos (Migración)
Se ejecutará un script SQL para reestructurar los datos:
1. **Crear tabla** `tercero_descripciones`.
2. **Consolidar Datos**:
   - Identificar terceros únicos por nombre.
   - Elegir un "ID Maestro" para cada tercero único (ej. el menor ID).
   - Migrar las descripciones de los registros duplicados a la nueva tabla `tercero_descripciones`, vinculándolas al "ID Maestro".
3. **Actualizar Relaciones**:
   - Actualizar la tabla `movimientos`: Cambiar todos los `tercero_id` de los registros duplicados al "ID Maestro".
4. **Limpieza**:
   - Eliminar los registros duplicados en `terceros` (aquellos que no son "ID Maestro").
   - Eliminar la columna `descripcion` de la tabla `terceros`.

### Fase 2: Backend (Python)
Actualizar el código para reflejar el cambio de esquema:
1. **Modelos y DTOs**:
   - Actualizar `Tercero` (dataclass) para remover `descripcion` y añadir `descripciones: List[str]`.
   - Actualizar `TerceroDTO` (Pydantic).
2. **Repositorio (`PostgresTerceroRepository`)**:
   - Actualizar `guardar`: Ahora debe guardar el tercero y gestionar (insertar/borrar) sus descripciones en la tabla secundaria.
   - Actualizar busquedas:
     - `obtener_todos`: Usar `GROUP_CONCAT` (o string_agg en Postgres) o joins para traer las descripciones.
     - `buscar_por_descripcion`: Join con `tercero_descripciones`.
3. **Servicios/Scripts**:
   - Verificar `reglas_asignacion_terceros.py` y otros scripts de mantenimiento para asegurar que consulten la nueva estructura si es necesario.

### Fase 3: Frontend (React)
Adaptar la interfaz de usuario:
1. **Tipos**: Actualizar interface `Tercero` en `types.ts` (`descripcion` -> `descripciones[]`).
2. **Lista (`TercerosTable`)**:
   - Mostrar las descripciones agrupadas (ej. "3 alias" o lista separada por comas).
3. **Edición (`TerceroModal`)**:
   - Cambiar el campo simple de "Descripción" por un gestor de lista (Tags input o lista editable) donde el usuario pueda agregar/eliminar múltiples descripciones para el mismo tercero.

## 5. Estimación
- **Riesgo**: Medio (Implicaciones en integridad de datos de movimientos históricos).
- **Estrategia**: Backup previo de tablas `terceros` y `movimientos`.

---
**¿Procedemos con la Fase 1 (Script SQL de Migración)?**
