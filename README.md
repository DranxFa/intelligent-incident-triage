# Intelligent Incident Triage

API desarrollada con FastAPI y orquestada con **LangGraph** para el triaje inteligente automatizado de incidencias de TI mediante Modelos de Lenguaje (LLM como Google Gemini o Groq).

## Estructura del Proyecto

```
intelligent-incident-triage/
├── .venv/                   # Entorno virtual de Python
├── graph/                   # Orquestación con LangGraph
│   ├── __init__.py          # Exporta triage_graph
│   ├── state.py             # Estado del grafo (IncidentGraphState)
│   ├── llm.py               # Fábrica de modelos LLM (Gemini / Groq)
│   ├── workflow.py          # Definición y compilación del StateGraph
│   └── nodes/               # Nodos del grafo
│       ├── __init__.py
│       └── classifier.py    # Primer nodo: clasificación estructurada y SLA
├── schemas.py               # Enums, matriz de prioridad y modelos Pydantic
├── main.py                  # API FastAPI y endpoints
├── test_graph.py            # Pruebas del grafo y cálculo de prioridades
├── test_main.py             # Pruebas de endpoints FastAPI
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Plantilla de variables de entorno
└── .gitignore               # Archivos y carpetas ignorados por git
```

## Configuración y Variables de Entorno

1. Copia `.env.example` a `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Configura tu proveedor y API Key en `.env`:
   ```ini
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=tu_clave_aqui
   # O si prefieres Groq:
   # LLM_PROVIDER=groq
   # GROQ_API_KEY=tu_clave_aqui
   ```

## Ejecución del Servidor

Inicia el servidor con Uvicorn:

```powershell
.\.venv\Scripts\uvicorn main:app --reload --port 8000
```

- Documentación interactiva (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Documentación alternativa (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Flujo del Primer Nodo (Clasificación con LLM)

El primer nodo (`classify_incident`) analiza el incidente y genera la siguiente estructura:

- **`categoria` (CategoryEnum)**:
  - `ACCESOS_Y_SEGURIDAD`: contraseñas, permisos de carpetas, VPN.
  - `SOFTWARE_APLICACIONES`: bugs en ERP, CRM, errores en páginas web.
  - `INFRAESTRUCTURA_RED`: caída de internet, servidores, lentitud general.
  - `HARDWARE_EQUIPOS`: laptops dañadas, impresoras, monitores.
  - `CONSULTA_OPERATIVA`: dudas de uso, manuales, preguntas frecuentes.
- **`impacto` (ImpactoEnum)**:
  - `ALTO`: toda la empresa.
  - `MEDIO`: un departamento.
  - `BAJO`: un solo usuario.
- **`urgencia` (UrgenciaEnum)**:
  - `ALTA`: bloqueo total.
  - `MEDIA`: degradado con alternativa temporal.
  - `BAJA`: inconveniente menor no bloqueante.
- **`prioridad` (PriorityEnum) y `sla_horas` (int)** calculados según la matriz 3x3:
  - `P1` (2h)
  - `P2` (8h)
  - `P3` (24h)
  - `P4` (48h)
- **`resumen_ejecutivo` (str)**: Descripción en 1 línea limpia.
- **`requiere_rag` (bool)**: `True` si es duda de procedimiento, consulta de manual o error conocido documentado.

### Matriz 3x3 de Prioridad y SLA

| Impacto \ Urgencia | ALTA (bloqueo total) | MEDIA (degradado) | BAJA (no bloqueante) |
| :--- | :---: | :---: | :---: |
| **ALTO** (empresa) | **P1** (2h) | **P2** (8h) | **P3** (24h) |
| **MEDIO** (departamento) | **P2** (8h) | **P3** (24h) | **P4** (48h) |
| **BAJO** (un usuario) | **P3** (24h) | **P4** (48h) | **P4** (48h) |

---

## Pruebas Automatizadas

Para ejecutar todas las pruebas unitarias y de integración:

```powershell
.\.venv\Scripts\pytest -v
```
