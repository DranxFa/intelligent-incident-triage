from typing import Optional, TypedDict
from schemas import IncidentAnalysis


class IncidentGraphState(TypedDict):
    """Estado compartido en el flujo de orquestación de LangGraph."""

    titulo: str
    descripcion: str
    usuario: str
    analisis: Optional[IncidentAnalysis]
    error: Optional[str]
