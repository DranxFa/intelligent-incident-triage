# 📃 Intelligent Incident Triage & Operational Copilot 🚨🤖

<p align="center">
  <img width="800" alt="Arquitectura del Sistema" src="docs/arquitectura_sistema.png" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-Terminado-green?style=for-the-badge"> &nbsp;
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white" alt="Python"> &nbsp;
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" alt="FastAPI"> &nbsp;
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=LangChain&logoColor=white" alt="LangGraph"> &nbsp;
  <img src="https://img.shields.io/badge/Google_Gemini-8E75C2?style=for-the-badge&logo=Google%20Gemini&logoColor=white" alt="Google Gemini"> &nbsp;
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=PostgreSQL&logoColor=white" alt="PostgreSQL"> &nbsp;
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white" alt="Docker"> &nbsp;
  <img src="https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=Power%20BI&logoColor=black" alt="Power BI"> &nbsp;
</p>

## 📝 Descripción del Proyecto

Sistema de triaje inteligente y copiloto operacional para mesas de ayuda de soporte TI. Automatiza la recepción de solicitudes, clasificación estructurada, cálculo matemático de acuerdos de nivel de servicio SLA, recuperación semántica de manuales técnicos institucionales mediante RAG y despacho multicanal de alertas críticas.

La solución almacena los registros operativos en PostgreSQL con soporte vectorial mediante pgvector y se conecta con un modelo analítico en Power BI para supervisar tiempos medios de resolución, cumplimiento de metas de atención y tasa de autoatención.

---

## 🏛️ Arquitectura del Sistema

```
[ Usuario / API ] ──► [ FastAPI Gateway ] ──► [ Orquestador LangGraph ]
                                                      │
         ┌───────────────────┬────────────────────────┴────────────────────────┐
         ▼                   ▼                                                 ▼
   [ Ruta A: P1 ]     [ Ruta B: RAG ]                                  [ Ruta C: Regular ]
         │                   │                                                 │
  BackgroundTasks     pgvector Search (<= 0.38)                          Cola Regular
  Discord / Telegram  ├─ Match ──► Solución Guiada                             │
  Outlook SMTP        └─ No Match ─► Escala a Humano                           │
         │                   │                                                 │
         └───────────────────┴────────────────────────┬────────────────────────┘
                                                      ▼
                                       [ PostgreSQL + pgvector ]
                                                      │
                                                      ▼
                                            [ Power BI Dashboard ]
```

El flujo técnico integra componentes especializados:

* **FastAPI Gateway:** Expone endpoints asíncronos para formularios web y consumo vía JSON, respondiendo confirmaciones inmediatas con el identificador del ticket.
* **Orquestador LangGraph:** Ejecuta el estado compartido tipado y procesa en paralelo la clasificación estructurada con el modelo de lenguaje y el cálculo del vector embedding de 768 dimensiones.
* **PostgreSQL con pgvector:** Almacena tablas operativas para reportería, estados técnicos del grafo y manuales vectorizados con índice HNSW para acelerar búsquedas por distancia coseno.
* **Notificaciones en Segundo Plano:** Envía alertas de emergencias críticas a Discord Webhooks, Telegram Bot API y servidores SMTP empresariales sin demorar la respuesta al usuario.
* **Power BI Dashboard:** Modelo analítico conectado directamente a la base de datos para medir indicadores de gestión y detectar oportunidades de automatización.

---

## 🔄 Modelado de Procesos BPMN 2.0

### Proceso Actual AS-IS

Operación manual tradicional caracterizada por demoras de triaje en bandejas compartidas, criterios subjetivos de asignación de prioridad, llamadas telefónicas manuales ante caídas críticas y saturación de analistas con consultas repetitivas.

<p align="center">
  <img width="800" alt="BPMN AS-IS" src="docs/bpmn_as_is.png" />
</p>

### Proceso Propuesto TO-BE

Flujo optimizado mediante un agente de IA que clasifica en milisegundos, despacha alertas críticas automáticamente, ofrece autoatención guiada con manuales institucionales y transfiere de forma segura a técnicos humanos solo cuando la consulta carece de documentación previa.

<p align="center">
  <img width="800" alt="BPMN TO-BE" src="docs/bpmn_to_be.png" />
</p>

---

## ⚙️ Rutas de Decisión del Agente

El agente evalúa el incidente y asigna deterministamente una de cuatro acciones operativas:

| Acción IA | Criterio de Activación | Comportamiento del Sistema | Canal de Salida |
| :--- | :--- | :--- | :--- |
| **`ALERTA_P1`** | Impacto alto y urgencia alta | Prioridad P1 con SLA de 2 horas. Despacho asíncrono inmediato | Discord, Telegram y Correo |
| **`SUGERENCIA_RAG`** | Consulta operativa o duda técnica | Coincidencia en pgvector con distancia coseno menor o igual a 0.38. Genera solución paso a paso | Interfaz de usuario |
| **`ESCALADO_A_HUMANO`** | Consulta sin manual disponible | Distancia coseno mayor a 0.38. Evita alucinaciones y deriva a especialista | Cola de especialista |
| **`COLA_REGULAR`** | Fallas estándar P2, P3 o P4 | Clasificación automática y asignación directa a la mesa de ayuda | Cola de atención N1/N2 |

---

## 📊 Dashboard Ejecutivo en Power BI

Tablero analítico con relación directa a la tabla de incidentes en PostgreSQL estructurado en lienzo panorámico:

<p align="center">
  <img width="800" alt="Dashboard en Power BI" src="docs/dashboard_powerbi.png" />
</p>

### Métricas e Indicadores Clave:

* **Total de Incidentes:** Volumen global de tickets procesados en el período analizado.
* **Backlog Activo:** Cantidad de tickets abiertos y en proceso que requieren atención técnica.
* **MTTR:** Tiempo medio de resolución calculado en horas sobre incidentes cerrados.
* **Cumplimiento de SLA:** Porcentaje de tickets resueltos dentro del límite temporal establecido.
* **Asistencia por IA:** Proporción de incidentes resueltos mediante manuales sugeridos por RAG sin consumo de horas técnicas.
* **Distribución de Acciones de IA:** Gráfico circular que audita la repartición entre alertas críticas, consultas autoatendidas, casos derivados y soporte regular.

---

## 📁 Estructura del Proyecto

```
intelligent-incident-triage/
├── dashboard/               # Archivos y documentación del reporte Power BI
├── data/
│   └── manuales_ti.md       # 10 manuales institucionales base para pgvector
├── docs/                    # Diagramas BPMN, arquitectura y capturas del dashboard
├── graph/                   # Orquestación con LangGraph
│   ├── llm.py               # Configuración de clientes LLM
│   ├── state.py             # Definición del estado tipado IncidentGraphState
│   ├── workflow.py          # Definición y compilación del StateGraph
│   └── nodes/               # Nodos del flujo
│       ├── alert.py         # Nodo de alerta crítica y despacho multicanal
│       ├── classifier.py    # Nodo de clasificación estructurada y embedding
│       ├── persist.py       # Nodo de persistencia en base de datos
│       ├── queue.py         # Nodo de derivación a cola regular
│       └── rag.py           # Nodo de búsqueda semántica y fallback a humano
├── scripts/
│   ├── init.sql             # Esquema DDL de PostgreSQL con pgvector e índices
│   ├── seed_bi_tickets.py   # Generador de 300 tickets normalizados para Power BI
│   └── seed_manuals.py      # Script de vectorización de manuales técnicos
├── services/
│   ├── embeddings.py        # Generación de vectores con Google Gemini
│   ├── incident_service.py  # Servicios de persistencia de tickets y estados
│   └── knowledge_service.py # Servicios de búsqueda vectorial por distancia coseno
├── database.py              # Modelos ORM SQLAlchemy y motor de conexiones
├── docker-compose.yml       # Contenedor Docker de PostgreSQL 16 con pgvector
├── main.py                  # API REST construida con FastAPI
├── schemas.py               # Esquemas Pydantic y matriz matemática 3x3 de SLA
├── requirements.txt         # Librerías de Python requeridas
└── test_graph.py            # Suite de pruebas automatizadas con pytest
```

---

## 🚀 Instalación y Despliegue Local

### 1. Clonar el repositorio y preparar el entorno

```powershell
git clone https://github.com/DranxFa/intelligent-incident-triage.git
cd intelligent-incident-triage
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Iniciar la base de datos con Docker

```powershell
docker compose up -d
```

### 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz tomando como referencia `.env.example`:

```env
DATABASE_URL=postgresql://admin:password123@localhost:5432/triage_db
GEMINI_API_KEY=tu_api_key_aqui
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion
ALERT_EMAIL_TO=guardia@empresa.com
```

### 4. Inicializar base de conocimiento y datos analíticos

```powershell
# Vectorizar manuales institucionales en pgvector
python scripts/seed_manuals.py --force

# Poblar 300 tickets para análisis en Power BI
python scripts/seed_bi_tickets.py --count 300
```

### 5. Iniciar el servidor API

```powershell
uvicorn main:app --reload --port 8000
```

Acceso a documentación interactiva OpenAPI Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con 14 pruebas unitarias y de integración que validan la matriz de prioridad, el enrutador condicional, las alertas simuladas, el fallback de RAG y los endpoints de FastAPI:

```powershell
pytest -v
```

---

## 👤 Autor

| [<img src="https://github.com/user-attachments/assets/ed62fad0-2a7e-4029-8525-2eec5c620be3" width="155"><br><sub>Andrio Contreras</sub>](https://github.com/DranxFa) |
| :---: |

---

## 📌 Estado del Proyecto

✅ **Terminado** — Proyecto con fines educativos y profesionales abierto a mejoras.
