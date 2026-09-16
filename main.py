from typing import Annotated
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from graph import triage_graph
from graph.nodes.alert import dispatch_alert_notifications
from schemas import IncidentInput

app = FastAPI(
    title="Intelligent Incident Triage API",
    description="API para la recepción, triaje con LangGraph y persistencia en PostgreSQL con pgvector.",
    version="0.5.0",
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Verificar estado del servicio")
async def health_check():
    """Ruta raíz para verificar que el servicio está activo."""
    return {"status": "ok", "message": "API de triage de incidentes lista con LangGraph y persistencia"}


@app.post(
    "/incidents",
    status_code=status.HTTP_201_CREATED,
    summary="Recibir formulario de incidente (Form Data), procesar y persistir",
)
async def submit_incident_form(
    titulo: Annotated[str, Form(..., description="Título del incidente")],
    descripcion: Annotated[str, Form(..., description="Descripción detallada")],
    usuario: Annotated[str, Form(..., description="Usuario que reporta")],
    background_tasks: BackgroundTasks = None,
):
    """
    Recibe los datos del formulario (application/x-www-form-urlencoded o multipart/form-data),
    ejecuta el flujo condicional de triaje en LangGraph y persiste el resultado en PostgreSQL.
    Las alertas P1 se despachan de forma asíncrona en segundo plano sin demorar la respuesta al cliente.
    """
    initial_state = {
        "texto_original": {
            "titulo": titulo,
            "descripcion": descripcion,
            "usuario": usuario,
        },
        "triage_data": None,
        "vector_embedding": None,
        "accion_ia": None,
        "alert_sent": False,
        "alert_payload": None,
        "rag_context": None,
        "final_response": None,
        "incident_id": None,
        "error": None,
    }

    try:
        result_state = await triage_graph.ainvoke(initial_state)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en configuración de LLM: {str(val_err)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falla durante la orquestación del triaje: {str(exc)}",
        )

    # Despachar notificaciones de alertas P1 en segundo plano sin demorar la respuesta HTTP
    if result_state.get("alert_sent") and result_state.get("alert_payload") and background_tasks:
        background_tasks.add_task(
            dispatch_alert_notifications,
            result_state["alert_payload"],
        )

    return {
        "message": "Incidente procesado y persistido exitosamente por el flujo de triaje",
        "ticket_id": result_state.get("incident_id"),
        "texto_original": result_state.get("texto_original"),
        "triage_data": result_state.get("triage_data"),
        "accion_ia": result_state.get("accion_ia"),
        "alert_sent": result_state.get("alert_sent", False),
        "rag_context": result_state.get("rag_context"),
        "final_response": result_state.get("final_response"),
        "status": "processed",
    }


@app.post(
    "/incidents/json",
    status_code=status.HTTP_201_CREATED,
    summary="Recibir incidente en formato JSON, procesar y persistir",
)
async def submit_incident_json(
    payload: IncidentInput,
    background_tasks: BackgroundTasks = None,
):
    """
    Alternativa para recibir payload JSON (application/json), ejecutar el flujo condicional
    y persistir en la base de datos PostgreSQL.
    Las alertas P1 se despachan de forma asíncrona en segundo plano sin demorar la respuesta al cliente.
    """
    initial_state = {
        "texto_original": payload.model_dump(),
        "triage_data": None,
        "vector_embedding": None,
        "accion_ia": None,
        "alert_sent": False,
        "alert_payload": None,
        "rag_context": None,
        "final_response": None,
        "incident_id": None,
        "error": None,
    }

    try:
        result_state = await triage_graph.ainvoke(initial_state)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en configuración de LLM: {str(val_err)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falla durante la orquestación del triaje: {str(exc)}",
        )

    # Despachar notificaciones de alertas P1 en segundo plano sin demorar la respuesta HTTP
    if result_state.get("alert_sent") and result_state.get("alert_payload") and background_tasks:
        background_tasks.add_task(
            dispatch_alert_notifications,
            result_state["alert_payload"],
        )

    return {
        "message": "Incidente en formato JSON procesado y persistido exitosamente",
        "ticket_id": result_state.get("incident_id"),
        "texto_original": result_state.get("texto_original"),
        "triage_data": result_state.get("triage_data"),
        "accion_ia": result_state.get("accion_ia"),
        "alert_sent": result_state.get("alert_sent", False),
        "rag_context": result_state.get("rag_context"),
        "final_response": result_state.get("final_response"),
        "status": "processed",
    }
