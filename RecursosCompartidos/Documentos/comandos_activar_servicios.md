# Comandos para Servicios Backend y Frontend

## Arrancar Servicios

### Backend (Python/FastAPI)
```powershell
cd Backend
& '.\.venv\Scripts\Activate.ps1'
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
**Explicación**: Activa el entorno virtual e inicia el servidor FastAPI con auto-reload en el puerto 8000

### Frontend
```powershell
cd Frontend
npm run dev
```
**Explicación**: Inicia el servidor de desarrollo del frontend (Vite/React)

---

## Revisar Procesos Python Activos

```powershell
Get-Process python -ErrorAction SilentlyContinue
```
**Explicación**: Lista todos los procesos de Python activos con detalles (PID, uso de memoria, etc.)

**Versión detallada**:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, CPU
```
**Explicación**: Muestra información más específica de cada proceso Python

---

## Forzar Terminado de Procesos

### Por nombre de proceso:
```powershell
Stop-Process -Name python -Force
```
**Explicación**: Termina **todos** los procesos Python de forma forzada

### Por PID específico:
```powershell
Stop-Process -Id <PID> -Force
```
**Explicación**: Termina un proceso específico por su ID (reemplazar `<PID>` con el número)

### Ejemplo con PID:
```powershell
Stop-Process -Id 12345 -Force
```

---

## Comando Todo-en-Uno (Listar y Terminar)

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```
**Explicación**: Lista y termina todos los procesos Python en un solo comando
