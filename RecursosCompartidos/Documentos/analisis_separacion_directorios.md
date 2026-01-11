# Análisis de Separación de Directorios: Escritorio vs Web

## 1. Situación Actual

El proyecto "Gastos SLB Vo" contiene actualmente tres componentes principales mezclados en la estructura de carpetas, aunque lógicamente separados:

*   **Versión Escritorio (`VersionEscritorio/`)**:
    *   Conjunto de scripts independientes en Python.
    *   Interfaz Gráfica: **Tkinter** (Nativa).
    *   Acceso a Datos: Conexión **directa** a PostgreSQL (`psycopg2`).
    *   Configuración: Credenciales de base de datos a menudo hardcodeadas en los scripts.
*   **Versión Web (`Backend/` + `frontend/`)**:
    *   **Backend**: API REST moderna usando **FastAPI**. Sigue arquitectura hexagonal (`domain`, `infrastructure`, `application`).
    *   **Frontend**: Aplicación SPA usando **React**.
    *   Acceso a Datos: A través del Backend (SQLAlchemy/ORM).

### Hallazgo Clave
No existe una dependencia de código fuerte entre la versión de Escritorio y la Web.
*   La versión de Escritorio **NO consume** el Backend API.
*   La versión de Escritorio **re implementa** la lógica de negocio y las consultas SQL.
*   El único punto de unión es la **Base de Datos compartida**.

## 2. Propuesta de Reestructuración

Se propone dividir el directorio raíz en dos carpetas principales:

### Estructura Propuesta

```text
/ (Raíz del Repositorio)
├── ConciliaciónBancariaEscritorio/
│   ├── (Contenido actual de VersionEscritorio/)
│   ├── utils/ (Scripts compartidos o utilitarios necesarios)
│   └── (Archivos de configuración/creds propios)
│
├── ConciliaciónBancariaWeb/
│   ├── Backend/
│   │   ├── src/
│   │   └── ...
│   ├── frontend/
│   │   ├── src/
│   │   └── ...
│   ├── docker-compose.yml (si aplica)
│   └── (Archivos de configuración de la versión web)
│
└── Shared/ (Opcional)
    ├── Sql/ (Scripts de creación de BD, backups)
    ├── Maestros/ (Archivos CSV/Excel de datos maestros)
    └── Documentos/
```

## 3. Implicaciones

### Ventajas (Pros)
1.  **Claridad Organizacional**: Es mucho más evidente para un desarrollador (o IA) qué archivos pertenecen a qué ecosistema. Reduce el ruido visual al trabajar en una versión específica.
2.  **Independencia de Despliegue**: Facilita la creación de pipelines de CI/CD separados. Puedes desplegar la Web sin tocar nada del Escritorio.
3.  **Gestión de Dependencias**: `requirements.txt` separados y claros. Evita conflictos si la versión Web necesita una librería moderna que rompe algo en la versión de Escritorio (o viceversa).
4.  **Preparación para el Futuro**: Si la versión Escritorio se considera "Legacy" (heredada) y la Web es el futuro, esta separación facilita eventualmente archivar o deprecar la carpeta `ConciliaciónBancariaEscritorio` sin afectar la Web.

### Desventajas / Riesgos (Cons)
1.  **Recursos Compartidos (Archivos)**: Carpetas como `Maestros` o `Sql` parecen ser usadas por ambos. Al separar, tendrás que decidir:
    *   *Duplicarlos* (Malo: riesgo de desincronización).
    *   *Crear una carpeta `Shared`* (Bueno, pero requiere ajustar rutas en los scripts de Escritorio que esperan `../Maestros`).
2.  **Rutas Absolutas/Relativas**: Muchos scripts en `VersionEscritorio` probablemente usan rutas relativas (ej. `../Maestros/archivo.csv`). Mover la carpeta requerirá auditar y corregir estas rutas en varios scripts `.py`.
3.  **Divergencia de Lógica**: Al separarlos físicamente, se refuerza la idea de que son dos aplicaciones distintas. Si cambias una regla de negocio en el Backend Web, es fácil olvidar actualizar el script correspondiente en Escritorio. (Nota: Este riesgo ya existe hoy, pero la separación física lo hace mentalmente más distante).

## 4. Recomendación

**RECOMENDACIÓN: PROCEDER CON LA SEPARACIÓN**

La arquitectura actual ya opera como dos aplicaciones separadas que casualmente comparten una base de datos. Mezclarlas en la raíz solo genera confusión.

### Plan de Acción Sugerido:

1.  **Crear Directorios**:
    *   Crear `ConciliaciónBancariaEscritorio` y mover allí todo el contenido de `VersionEscritorio`.
    *   Crear `ConciliaciónBancariaWeb` y mover allí `Backend` y `frontend`.
2.  **Manejo de Comunes**:
    *   Mover `Maestros`, `Sql`, `Descargas`, `Documentos` a una carpeta raíz llamada `RecursosCompartidos` o mantenerlas en la raíz.
    *   *Alternativa*: Si la versión Web ya no usa archivos locales (carga todo a BD), dejar `Maestros` dentro de `ConciliaciónBancariaEscritorio`.
3.  **Corrección de Rutas (Critico)**:
    *   Se deberá ejecutar una búsqueda y reemplazo en los scripts de Python de Escritorio para ajustar las rutas de importación o lectura de archivos (ej. de `../Maestros` a `../RecursosCompartidos/Maestros`).
4.  **Unificación de Configuración**:
    *   Es el momento ideal para crear un `.env` en `ConciliaciónBancariaEscritorio` y dejar de usar credenciales hardcodeadas, alineándolo con las buenas prácticas de la versión Web.

**Conclusión**: La separación es higiénica y profesional. El esfuerzo de corregir las rutas de archivos en los scripts de escritorio es un costo único bajo comparado con el beneficio de orden a largo plazo.
