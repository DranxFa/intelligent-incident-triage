from typing import Annotated
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from graph import triage_graph
from schemas import IncidentInput

app = FastAPI(
    title="Intelligent Incident Triage API",
    description="API para la recepción, triaje con LangGraph y persistencia en PostgreSQL con pgvector.",
    version="0.4.0",
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
):
    """
    Recibe los datos del formulario (application/x-www-form-urlencoded o multipart/form-data),
    ejecuta el flujo condicional de triaje en LangGraph y persiste el resultado en PostgreSQL.
    """
    initial_state = {
        "texto_original": {
            "titulo": titulo,
            "descripcion": descripcion,
            "usuario": usuario,
        },
        "triage_data": None,
        "alert_sent": False,
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

    return {
        "message": "Incidente procesado y persistido exitosamente por el flujo de triaje",
        "ticket_id": result_state.get("incident_id"),
        "texto_original": result_state.get("texto_original"),
        "triage_data": result_state.get("triage_data"),
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
async def submit_incident_json(payload: IncidentInput):
    """
    Alternativa para recibir payload JSON (application/json), ejecutar el flujo condicional
    y persistir en la base de datos PostgreSQL.
    """
    initial_state = {
        "texto_original": payload.model_dump(),
        "triage_data": None,
        "alert_sent": False,
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

    return {
        "message": "Incidente en formato JSON procesado y persistido exitosamente",
        "ticket_id": result_state.get("incident_id"),
        "texto_original": result_state.get("texto_original"),
        "triage_data": result_state.get("triage_data"),
        "alert_sent": result_state.get("alert_sent", False),
        "rag_context": result_state.get("rag_context"),
        "final_response": result_state.get("final_response"),
        "status": "processed",
    }
