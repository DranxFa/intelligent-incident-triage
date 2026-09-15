from typing import Annotated
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from graph import triage_graph
from schemas import IncidentInput

app = FastAPI(
    title="Intelligent Incident Triage API",
    description="API para la recepción y triaje automatizado de incidencias con LangGraph y LLM.",
    version="0.3.0",
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
    return {"status": "ok", "message": "API de triage de incidentes lista con LangGraph"}


@app.post(
    "/incidents",
    status_code=status.HTTP_201_CREATED,
    summary="Recibir formulario de incidente (Form Data) y procesar con LangGraph",
)
async def submit_incident_form(
    titulo: Annotated[str, Form(..., description="Título del incidente")],
    descripcion: Annotated[str, Form(..., description="Descripción detallada")],
    usuario: Annotated[str, Form(..., description="Usuario que reporta")],
):
    """
    Recibe los datos del formulario (application/x-www-form-urlencoded o multipart/form-data)
    y ejecuta el flujo condicional de triaje en LangGraph.
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
        "message": "Incidente procesado exitosamente por el flujo de triaje",
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
    summary="Recibir incidente en formato JSON y procesar con LangGraph",
)
async def submit_incident_json(payload: IncidentInput):
    """
    Alternativa para recibir payload JSON (application/json) y ejecutar el flujo condicional en LangGraph.
    """
    initial_state = {
        "texto_original": payload.model_dump(),
        "triage_data": None,
        "alert_sent": False,
        "rag_context": None,
        "final_response": None,
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
        "message": "Incidente en formato JSON procesado exitosamente por el flujo de triaje",
        "texto_original": result_state.get("texto_original"),
        "triage_data": result_state.get("triage_data"),
        "alert_sent": result_state.get("alert_sent", False),
        "rag_context": result_state.get("rag_context"),
        "final_response": result_state.get("final_response"),
        "status": "processed",
    }
