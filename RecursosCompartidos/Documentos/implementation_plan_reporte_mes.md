
# Plan de Implementación: Reporte Ingresos y Gastos por Mes

Este reporte permitirá visualizar la evolución mensual de ingresos y egresos, aplicando los mismos filtros que el reporte de clasificación.

## Backend

### 1. Repositorio de Movimientos (`postgres_movimiento_repository.py`)
- Agregar método `resumir_ingresos_gastos_por_mes`:
  - Agrupar movimientos por mes (`YYYY-MM`).
  - Calcular:
    - `ingresos`: Suma de valores positivos.
    - `egresos`: Suma de valores absolutos de valores negativos.
    - `saldo`: Diferencia.
  - Aplicar filtros (cuenta, tercero, grupo, concepto, fechas).
  - Lógica para excluir traslados (`Grupo.es_traslado = FALSE` o `GrupoID IS NULL`).

### 2. Router de Movimientos (`movimientos.py`)
- Crear endpoint `GET /api/movimientos/reporte/ingresos-gastos-mes`.
- Recibir parámetros de filtro habituales.
- Retornar lista de objetos con estructura: `{ "mes": "YYYY-MM", "ingresos": float, "egresos": float, "saldo": float }`.

## Frontend

### 1. Servicio API (`api.ts`)
- Agregar método `reporteIngresosGastosMes` a `apiService.movimientos`.

### 2. Nueva Página (`ReporteIngresosGastosMesPage.tsx`)
- Copiar estructura base de `ReporteClasificacionesPage`.
- **Filtros**: Mantener la misma barra de filtros.
- **Gráficas**:
  - Implementar dos gráficas de barras (BarChart de Recharts):
    1. **Evolución de Ingresos**: Eje X = Mes, Eje Y = Ingresos (Color Verde/Emerald).
    2. **Evolución de Egresos**: Eje X = Mes, Eje Y = Egresos (Color Rojo/Rose).
- **Resumen**:
  - Mostrar tarjetas de totales (Ingresos, Egresos, Saldo) acumulados en el rango seleccionado.
- **Tabla**:
  - Detalle por mes mostrando los valores exactos.

### 3. Navegación
- **Sidebar (`Sidebar.tsx`)**:
  - Agregar "Ingresos y Gastos" en la sección "Reportes", posición 2.
- **App (`App.tsx`)**:
  - Definir la ruta `/reportes/ingresos-gastos`.
