from typing import Any, Dict, List, Optional, TypedDict
from schemas import IncidentAnalysis


class IncidentGraphState(TypedDict):
    """
    Estado tipado compartido a través de todos los nodos en LangGraph.
    Conforme el ticket pasa de nodo en nodo, cada función lee este estado
    y le agrega sus resultados.
    """

    texto_original: Dict[str, Any]  # Datos originales del formulario/ticket: titulo, descripcion, usuario
    triage_data: Optional[IncidentAnalysis]  # Clasificación resultante del primer nodo
    alert_sent: bool  # Indica si se envió alerta (Ruta A)
    rag_context: Optional[List[str]]  # Fragmentos recuperados de manuales (Ruta B)
    final_response: Optional[str]  # Respuesta final, solución sugerida o estado de registro
    error: Optional[str]  # Mensaje de error en caso de anomalía
