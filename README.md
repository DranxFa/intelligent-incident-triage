# Intelligent Incident Triage

API desarrollada con FastAPI y orquestada con **LangGraph** para el triaje inteligente automatizado de incidencias de TI mediante LLMs (Google Gemini / Groq), enrutamiento condicional y persistencia en **PostgreSQL con pgvector** para reportería en **Power BI**.

---

## Estructura del Proyecto

```
intelligent-incident-triage/
├── data/
│   └── manuales_ti.md       # 10 manuales de soluciones de TI para la base de conocimiento
├── graph/                   # Orquestación con LangGraph
│   ├── __init__.py          # Exporta triage_graph
│   ├── state.py             # Estado tipado (IncidentGraphState)
│   ├── llm.py               # Fábrica de modelos LLM (Gemini / Groq)
│   ├── workflow.py          # StateGraph compilado con enrutador condicional y persistencia
│   └── nodes/               # Nodos del flujo
│       ├── __init__.py
│       ├── classifier.py    # Nodo 1: Clasificación estructurada y SLA
│       ├── alert.py         # Nodo 2A: Envío de alertas P1 (Discord/Telegram/Correo)
│       ├── rag.py           # Nodo 2B: Búsqueda en manuales (pgvector) y solución sugerida
│       ├── queue.py         # Nodo 2C: Preparación de cola de atención regular
│       └── persist.py       # Nodo 3: Persistencia en PostgreSQL (Power BI y estados)
├── scripts/
│   ├── init.sql             # Inicialización de extensiones, tablas e índices pgvector
│   └── seed_manuals.py      # Script para generar embeddings y poblar knowledge_manuals
├── services/
│   ├── embeddings.py        # Generador de embeddings (Gemini text-embedding-004 768d)
│   ├── knowledge_service.py # Parseo de manuales y búsqueda por distancia coseno (<=>)
│   └── incident_service.py  # Persistencia de incidentes (Power BI) y estados de LangGraph
├── database.py              # Modelos ORM SQLAlchemy y gestión de conexiones
├── schemas.py               # Enums, matriz 3x3 de prioridad y modelos Pydantic
├── main.py                  # API FastAPI y endpoints
├── test_graph.py            # Pruebas del grafo, enrutador y rutas A, B y C
├── test_main.py             # Pruebas de endpoints FastAPI
├── test_persistence.py     # Pruebas de base de conocimiento, embeddings y persistencia
├── docker-compose.yml       # Contenedor PostgreSQL 16 con pgvector
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Plantilla de variables de entorno
└── .gitignore               # Archivos ignorados por git
```

---

## Modelos de Base de Datos (PostgreSQL + pgvector)

### 1. `incidents` (Diseñada para Power BI y Reportería)
- `id` (SERIAL PRIMARY KEY)
- `created_at` (TIMESTAMPTZ)
- `usuario` (VARCHAR)
- `titulo` (VARCHAR)
- `descripcion` (TEXT)
- `prioridad` (VARCHAR: P1, P2, P3, P4)
- `sla_horas` (INT: 2, 8, 24, 48)
- `categoria` (VARCHAR: CategoryEnum)
- `estado` (VARCHAR: ABIERTO, ALERTA_ENVIADA, SUGERENCIA_GENERADA)
- `tiempo_resolucion` (INT)
- `solucion_sugerida` (TEXT)
- `vector_embedding` (vector(768))

### 2. `incident_states` (Historial Técnico del Grafo LangGraph)
- `id` (SERIAL PRIMARY KEY)
- `incident_id` (FOREIGN KEY REFERENCES incidents.id ON DELETE CASCADE)
- `created_at` (TIMESTAMPTZ)
- `texto_original` (JSONB)
- `triage_data` (JSONB)
- `alert_sent` (BOOLEAN)
- `rag_context` (JSONB)
- `final_response` (TEXT)
- `error` (TEXT)

### 3. `knowledge_manuals` (Base de Conocimiento TI)
- `id` (SERIAL PRIMARY KEY)
- `titulo` (VARCHAR)
- `categoria` (VARCHAR)
- `contenido` (TEXT)
- `vector_embedding` (vector(768) con índice HNSW)

---

## 10 Soluciones de TI Incluidas (`data/manuales_ti.md`)

1. Cómo reiniciar el servicio de base de datos PostgreSQL.
2. Cómo solicitar accesos y licencias a SAP.
3. Solución al error de impresora de red sin conexión (Offline).
4. Desbloqueo de cuenta y reseteo de contraseña en Active Directory.
5. Solución a fallas de conexión a la VPN corporativa.
6. Diagnóstico y recuperación ante pantallas azules (BSOD) en Windows.
7. Reparación de sincronización y perfiles dañados en Microsoft Outlook.
8. Solución a errores 500 y 502 Bad Gateway en aplicaciones web internas.
9. Configuración de micrófono y cámara en Microsoft Teams / Zoom.
10. Diagnóstico y reporte de lentitud o saturación en la red de oficina.

---

## Puesta en Marcha Rápida

1. **Iniciar PostgreSQL con pgvector en Docker**:
   ```powershell
   docker compose up -d
   ```

2. **Configurar tu `.env`**:
   Asegúrate de colocar tu `GEMINI_API_KEY` en el archivo `.env`.

3. **Poblar la base de conocimiento**:
   ```powershell
   .\.venv\Scripts\python scripts/seed_manuals.py --force
   ```

4. **Iniciar la API FastAPI**:
   ```powershell
   .\.venv\Scripts\uvicorn main:app --reload --port 8000
   ```
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

5. **Ejecutar Pruebas Automatizadas**:
   ```powershell
   .\.venv\Scripts\pytest -v
   ```
