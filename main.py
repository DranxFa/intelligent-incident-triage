from typing import Annotated
from fastapi import FastAPI, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Intelligent Incident Triage API",
    description="API inicial para la recepción de incidencias mediante formulario.",
    version="0.1.0",
)

# Configuración de CORS para permitir peticiones desde clientes web locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IncidentSchema(BaseModel):
    titulo: str = Field(..., min_length=1, description="Título del incidente")
    descripcion: str = Field(..., min_length=1, description="Descripción detallada del incidente")
    usuario: str = Field(..., min_length=1, description="Usuario que reporta el incidente")


@app.get("/", summary="Verificar estado del servicio")
async def health_check():
    """Ruta raíz para verificar que el servicio está activo."""
    return {"status": "ok", "message": "API de triage de incidentes lista"}


@app.post(
    "/incidents",
    status_code=status.HTTP_201_CREATED,
    summary="Recibir formulario de incidente (Form Data)",
)
async def submit_incident_form(
    titulo: Annotated[str, Form(..., description="Título del incidente")],
    descripcion: Annotated[str, Form(..., description="Descripción detallada")],
    usuario: Annotated[str, Form(..., description="Usuario que reporta")],
):
    """
    Recibe los datos del formulario enviados mediante `application/x-www-form-urlencoded`
    o `multipart/form-data`.
    """
    return {
        "message": "Formulario recibido correctamente",
        "data": {
            "titulo": titulo,
            "descripcion": descripcion,
            "usuario": usuario,
        },
        "status": "received",
    }


@app.post(
    "/incidents/json",
    status_code=status.HTTP_201_CREATED,
    summary="Recibir incidente en formato JSON",
)
async def submit_incident_json(payload: IncidentSchema):
    """
    Alternativa para clientes API que envíen el formulario en formato JSON (`application/json`).
    """
    return {
        "message": "Datos en formato JSON recibidos correctamente",
        "data": payload.model_dump(),
        "status": "received",
    }
