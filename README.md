# Intelligent Incident Triage

API desarrollada con FastAPI para la recepción y gestión de formularios de incidentes.

## Estructura del Proyecto

```
intelligent-incident-triage/
├── .venv/               # Entorno virtual de Python
├── main.py              # Aplicación FastAPI y endpoints
├── test_main.py         # Pruebas automatizadas (pytest)
├── requirements.txt     # Dependencias del proyecto
└── .gitignore           # Archivos y carpetas ignorados por git
```

## Requisitos y Configuración

1. **Activar el entorno virtual**:
   - En Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - En Windows (CMD):
     ```cmd
     .\.venv\Scripts\activate.bat
     ```

2. **Instalación de dependencias (si se requiere actualizar)**:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución del Servidor de Desarrollo

Inicia el servidor con Uvicorn:

```powershell
.\.venv\Scripts\uvicorn main:app --reload --port 8000
```

- Documentación interactiva (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Documentación alternativa (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Endpoints

### 1. `POST /incidents` (Formulario)
Recibe datos en formato `application/x-www-form-urlencoded` o `multipart/form-data`:
- `titulo` (string, requerido)
- `descripcion` (string, requerido)
- `usuario` (string, requerido)

Ejemplo con PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/incidents" -Method Post -Body @{
    titulo = "Error en base de datos"
    descripcion = "Falla de conexión en el pool"
    usuario = "juan_perez"
}
```

### 2. `POST /incidents/json` (JSON)
Recibe payload en formato `application/json`:
```json
{
  "titulo": "Error en base de datos",
  "descripcion": "Falla de conexión en el pool",
  "usuario": "juan_perez"
}
```

## Pruebas Automatizadas

Para ejecutar la suite de pruebas:

```powershell
.\.venv\Scripts\pytest
```
