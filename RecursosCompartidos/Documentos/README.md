# Cargador de Datos Maestros a PostgreSQL 🗄️

**Interfaz gráfica (GUI)** para cargar datos maestros desde archivos CSV a la base de datos PostgreSQL "mvtos".

## Características

- ✅ **Interfaz gráfica intuitiva** con tkinter
- ✅ **Selección de tablas**: elige qué tablas cargar
- ✅ **Validación de dependencias**: verifica Foreign Keys automáticamente
- ✅ **Progreso en tiempo real**: barra de progreso y log detallado
- ✅ **Mensajes con colores**: errores en rojo, éxitos en verde, info en azul
- ✅ **Multi-threading**: no bloquea la interfaz durante la carga

## Requisitos

### Base de Datos
- PostgreSQL instalado y ejecutándose
- Base de datos `mvtos` creada
- Configuración:
  - Host: `localhost`
  - Puerto: `5433`
  - Usuario: `postgresql`
  - Contraseña: `SLB`

### Python
- Python 3.7 o superior
- Librerías requeridas (ver `requirements.txt`):
  - `psycopg2-binary`
  - `pandas`

## Instalación

1. **Instalar dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verificar que PostgreSQL esté ejecutándose:**
   ```bash
   # Verificar servicio PostgreSQL
   # En Windows: servicios de Windows o pgAdmin
   ```

3. **Crear la base de datos mvtos (si no existe):**
   ```sql
   -- Conectarse a PostgreSQL como superusuario
   psql -h localhost -p 5433 -U postgresql
   
   -- Crear base de datos
   CREATE DATABASE mvtos;
   ```

## Estructura de Archivos

```
Gastos SLB/
├── cargarDatosMaestros.py    # Script principal
├── requirements.txt           # Dependencias Python
├── README.md                  # Este archivo
└── Maestros/                  # Carpeta con archivos CSV
    ├── Cuentas.csv
    ├── Contacts.csv
    ├── Moneda.csv
    ├── TipoMov.csv
    ├── Grupos.csv
    └── Conceptos.csv
```

## Uso

### Ejecución
```bash
python cargarDatosMaestros.py
```

Se abrirá una ventana con la interfaz gráfica.

### Pasos:

1. **Seleccionar tablas**: Marca las casillas de las tablas que quieres cargar
   - Usa "Seleccionar Todas" o "Deseleccionar Todas" para agilizar
   - La tabla "Conceptos" requiere que "Grupos" esté seleccionada (Foreign Key)

2. **Iniciar carga**: Click en "Cargar Datos Seleccionados"

3. **Monitorear progreso**:
   - Barra de progreso muestra el avance
   - Log colorizado muestra cada paso:
     - 🔵 Azul: información general
     - 🟢 Verde: operaciones exitosas
     - 🔴 Rojo: errores
   - Estado en tiempo real en la parte inferior

4. **Resultado**: Al finalizar, un diálogo muestra el resumen

El script:
- Conecta a PostgreSQL
- Elimina y recrea cada tabla seleccionada
- Carga los datos en orden correcto (respetando dependencias)
- Muestra resumen de registros cargados

### Resultado Esperado

```
======================================================================
INICIANDO CARGA DE DATOS MAESTROS
======================================================================
[2025-12-28 20:00:00] [INFO] Conectando a PostgreSQL en localhost:5433...
[2025-12-28 20:00:00] [INFO] ✓ Conexión exitosa
[2025-12-28 20:00:00] [INFO] Creando tablas...
[2025-12-28 20:00:00] [INFO] ✓ Tablas creadas exitosamente

----------------------------------------------------------------------
CARGANDO DATOS DESDE CSV
----------------------------------------------------------------------
[2025-12-28 20:00:00] [INFO] Cargando Cuentas...
[2025-12-28 20:00:00] [INFO] ✓ 9 registros cargados en Cuentas
[2025-12-28 20:00:00] [INFO] Cargando Contacts...
[2025-12-28 20:00:00] [INFO] ✓ 758 registros cargados en Contacts
[2025-12-28 20:00:00] [INFO] Cargando Moneda...
[2025-12-28 20:00:00] [INFO] ✓ 2 registros cargados en Moneda
[2025-12-28 20:00:00] [INFO] Cargando TipoMov...
[2025-12-28 20:00:00] [INFO] ✓ 5 registros cargados en TipoMov
[2025-12-28 20:00:00] [INFO] Cargando Grupos...
[2025-12-28 20:00:00] [INFO] ✓ 52 registros cargados en Grupos
[2025-12-28 20:00:00] [INFO] Cargando Conceptos...
[2025-12-28 20:00:00] [INFO] ✓ 405 registros cargados en Conceptos

======================================================================
RESUMEN DE CARGA
======================================================================
  Cuentas         :     9 registros
  Contacts        :   758 registros
  Moneda          :     2 registros
  TipoMov         :     5 registros
  Grupos          :    52 registros
  Conceptos       :   405 registros
----------------------------------------------------------------------
  TOTAL           :  1231 registros
======================================================================

✓ PROCESO COMPLETADO EXITOSAMENTE
```

## Tablas Creadas

### 1. cuentas
- `cuentaid` (SERIAL PRIMARY KEY)
- `account` (TEXT)
- `accountid_original` (INTEGER)

### 2. contacts
- `contactid` (SERIAL PRIMARY KEY)
- `contact` (TEXT)
- `reference` (TEXT)
- `contactid_original` (INTEGER)

### 3. moneda
- `monedaid` (SERIAL PRIMARY KEY)
- `isocode` (TEXT)
- `moneda` (TEXT)

### 4. tipomov
- `tipomovid` (SERIAL PRIMARY KEY)
- `tipomov` (TEXT)
- `tmid_original` (INTEGER)

### 5. grupos
- `grupoid` (SERIAL PRIMARY KEY)
- `grupo` (TEXT)
- `grupoid_original` (INTEGER)

### 6. conceptos
- `conceptoid` (SERIAL PRIMARY KEY)
- `claveconcepto` (TEXT)
- `conceptoid_original` (INTEGER)
- `grupo` (TEXT)
- `concepto` (TEXT)
- `grupoid_fk` (INTEGER) → **FOREIGN KEY** a `grupos(grupoid_original)`

## Verificación

### Verificar tablas creadas
```sql
psql -h localhost -p 5433 -U postgresql -d mvtos

\dt
```

### Verificar datos cargados
```sql
SELECT 'Cuentas' as tabla, COUNT(*) as registros FROM cuentas
UNION ALL
SELECT 'Contacts', COUNT(*) FROM contacts
UNION ALL
SELECT 'Moneda', COUNT(*) FROM moneda
UNION ALL
SELECT 'TipoMov', COUNT(*) FROM tipomov
UNION ALL
SELECT 'Grupos', COUNT(*) FROM grupos
UNION ALL
SELECT 'Conceptos', COUNT(*) FROM conceptos;
```

### Verificar Foreign Key
```sql
SELECT c.concepto, c.grupo, g.grupo as grupo_tabla
FROM conceptos c
INNER JOIN grupos g ON c.grupoid_fk = g.grupoid_original
LIMIT 10;
```

## Solución de Problemas

### Error de conexión
- Verificar que PostgreSQL está ejecutándose en el puerto 5433
- Verificar usuario y contraseña
- Verificar que la base de datos `mvtos` existe

### Error de importación de módulos
```bash
pip install --upgrade psycopg2-binary pandas
```

### Error de permisos
- Verificar que el usuario `postgresql` tiene permisos para crear tablas en la base de datos `mvtos`

## Notas

- El script elimina y recrea las tablas cada vez que se ejecuta (DROP IF EXISTS)
- Los datos se cargan en el orden correcto para respetar la integridad referencial
- Las filas vacías en los CSV son automáticamente ignoradas
- El script incluye logging detallado para facilitar el seguimiento del proceso
