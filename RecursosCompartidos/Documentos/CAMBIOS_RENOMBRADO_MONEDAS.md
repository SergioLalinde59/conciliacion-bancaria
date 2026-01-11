# Resumen de Cambios - Renombrado de Tabla moneda a monedas
**Fecha**: 2025-12-29  
**Autor**: Antigravity

## Cambios en la Base de Datos

### Tabla renombrada
- `moneda` → `monedas`

### Columnas
Las columnas mantienen sus nombres originales:
- `monedaid` (SERIAL PRIMARY KEY)
- `isocode` (TEXT NOT NULL)
- `moneda` (TEXT NOT NULL)

## Script SQL Ejecutado
**Archivo**: `ejecutar_renombrado_monedas.py`

```sql
ALTER TABLE moneda RENAME TO monedas;
```

✅ **Estado**: Ejecutado exitosamente

## Archivos Python Actualizados

### 1. cargarDatosMaestros.py
**Cambios realizados**:
- Línea 27: `'Moneda'` → `'Monedas'` en TABLES_INFO
- Líneas 294-302: Definición de tabla actualizada en table_sql
  - DROP TABLE: `moneda` → `monedas`
  - CREATE TABLE: `moneda` → `monedas`
- Línea 390: Método `load_moneda()` → `load_monedas()`
- Línea 398: INSERT INTO `moneda` → `monedas`

### 2. cargar_mvtos.py
**Cambios realizados**:
- Línea 318: FOREIGN KEY reference actualizada
  - `REFERENCES Moneda(MonedaID)` → `REFERENCES Monedas(MonedaID)`

### 3. investigar_tablas.py
**Cambios realizados**:
- Línea 14: Lista de tablas
  - `'moneda'` → `'monedas'`

## Archivos NO Modificados

Los siguientes archivos no requerían cambios:
- `cargar_movimientos_ui.py` - No referencia directamente la tabla moneda
- `listar_descripciones_sin_contacto_ui.py` - No usa la tabla moneda
- `listar_descripciones_sin_contacto.py` - No usa la tabla moneda
- Otros archivos sin referencias a moneda

## Resumen de Cambios por Tipo

| Tipo de Cambio | Cantidad |
|----------------|----------|
| Archivos SQL ejecutados | 1 |
| Archivos Python modificados | 3 |
| Tablas renombradas | 1 |
| Referencias a FK actualizadas | 1 |

## Estado Final

✅ Tabla renombrada de `moneda` a `monedas`  
✅ Todos los archivos Python actualizados  
✅ Foreign Key en tabla Mvtos actualizada  
✅ Nomenclatura consistente (plural)

## Estructura Final de Tablas Maestras

- ✅ **monedas** (plural)
- ✅ **cuentas** (plural)  
- ✅ **contatos** (plural, español)
- ✅ **grupos** (plural)
- ✅ **conceptos** (plural)
- ⚠️ **tipomov** (singular) - ¿renombrar a tipomovs o tiposmov?
