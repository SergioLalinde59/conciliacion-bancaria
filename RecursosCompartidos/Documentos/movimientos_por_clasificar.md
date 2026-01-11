# Documentación: Movimientos por Clasificar (Versión Escritorio)

Este documento describe la funcionalidad, lógica de negocio y estructura del script `movimientos_por_clasificar.py` (anteriormente `asignar_clasificacion_movimiento_ui.py`) con el objetivo de facilitar su migración a la Arquitectura Hexagonal de la aplicación web.

## 1. Objetivo del Módulo
Herramienta visual para que un analista procese la cola de "Movimientos Pendientes" (aquellos sin Tercero, Grupo o Concepto asignado). Su meta es lograr una clasificación rápida asistida por sugerencias inteligentes y contexto histórico.

## 2. Flujo de Trabajo (UX)
1. **Carga de Pendientes**: El sistema carga los primeros 100 movimientos que tienen `NULL` en Tercero, Grupo o Concepto.
2. **Selección**: El usuario selecciona un movimiento de la lista.
3. **Asistencia (Contexto)**:
   - Se muestra una ventana modal (Editor).
   - En la parte inferior/trasera se cargan los **"Últimos 5 movimientos similares"** (Contexto Histórico) para ayudar a decidir.
   - El sistema **pre-llena** campos si detecta patrones confiables.
4. **Edición**:
   - El usuario puede aceptar la sugerencia o buscar manualmente (con autocompletado y fuzzy search).
   - Puede crear un **Nuevo Tercero** al vuelo si no existe.
5. **Guardado**:
   - Guardar individualmente (`UPDATE`).
   - Guardar en Lote ("Aplicar a Todos") si el sistema detecta múltiples movimientos con la misma descripción.

## 3. Lógica de Negocio y Reglas

### 3.1. Estrategia de Sugerencia Automática
El sistema intenta adivinar el Tercero/Clasificación en este orden de prioridad:

1.  **Reglas Estáticas (Hardcoded):**
    - Se verifica una lista `REGLAS` definida en código (ej. "Abono Intereses", "Impto Gobierno").
    - Si hay coincidencia ("Patrón"), se asigna Tercero/Grupo/Concepto automáticamente.
    
2.  **Histórico por Referencia (Match Exacto):**
    - Si el movimiento tiene `Referencia`:
        - Busca en la tabla `terceros` si esa referencia ya existe.
        - Busca en `movimientos` históricos si esa referencia fue usada antes.
    
3.  **Histórico por Descripción (Contexto Reciente):**
    - Si no hay match por referencia, busca los últimos 5 movimientos con descripción similar (mismas 2 primeras palabras).
    - Si encuentra un movimiento previo clasificado, sugiere ese Tercero.

4.  **Búsqueda Difusa (Fuzzy Search):**
    - Si los anteriores fallan, al buscar terceros manualmente, el sistema usa `thefuzz` (Levenshtein) para encontrar terceros con nombres similares a la descripción del movimiento.

### 3.2. Reglas de Negocio Específicas
- **Detección de Patrones de Referencia**: Analiza si la referencia parece un "Celular" (empieza por 3, 10 dígitos) o una "Cuenta Bancaria".
- **Conceptos Dependientes**: La lista de `Conceptos` se filtra obligatoriamente según el `Grupo` seleccionado.
- **Creación de Terceros**:
    - Permite crear terceros con el mismo nombre si la descripción o referencia difieren (Unique Constraint compuesta).

### 3.3. Funcionalidad "Aplicar a Todos" (Batch)
- Detecta si existen otros movimientos pendientes con la misma descripción (usando `ILIKE %pattern%`).
- Habilita un botón "⚡ Aplicar a Todos" para clasificar masivamente.

## 4. Estructura de Datos Requerida (Read Models)

Para migrar a web, necesitamos endpoints que provean:

1.  **Cola de Pendientes**: `GET /movimientos/pendientes` (con filtro por Cuenta).
2.  **Contexto Histórico**: `GET /movimientos/{id}/contexto`
    - Input: ID del movimiento.
    - Output: Lista de 5 movimientos previos (Fecha, Desc, Ref, Valor, Clasificación).
    - Output Adicional: Sugerencia calculada ("Meatball heuristics").
3.  **Búsqueda de Terceros**: `GET /terceros/buscar?q={query}`
    - Debe incluir lógica fuzzy si no hay match exacto.
4.  **Batch Update**: `POST /movimientos/clasificar-lote`
    - Input: Criterio de filtrado (descripción) y valores a asignar.

## 5. Brechas para Migración (Gap Analysis)

Lo que falta en el Backend actual (Hexagonal) para soportar esto completamente:

1.  **Migración de Reglas**: Las reglas están hardcoded en el script Python (`REGLAS = [...]`). Deben moverse a la tabla `reglas_clasificacion` y ser servidas por el `ReglasRepository`.
2.  **Endpoint de Sugerencias**: El backend tiene `clasificar_movimiento` (servicio), pero está diseñado para "Auto-run". Se necesita un servicio "Interactivo" que devuelva *sugerencias* sin guardar, para mostrar en el UI antes de que el usuario confirme.
3.  **Fuzzy Search en Base de Datos**: El script usa `thefuzz` en memoria cargando todos los terceros. En web (con miles de registros) esto es ineficiente. Se requiere:
    - O bien Full Text Search de Postgres (`tsvector`).
    - O búsqueda `ILIKE` optimizada (Trigram indices).
4.  **Lógica "Aplicar a Todos"**: El endpoint debe aceptar un patrón y ejecutar el update masivo de manera segura.

---
*Generado automáticamente por Antigravity a petición del usuario.*
