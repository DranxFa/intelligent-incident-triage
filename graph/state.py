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
    vector_embedding: Optional[List[float]]  # Vector de 768d precalculado concurrentemente
    accion_ia: Optional[str]  # ALERTA_P1, SUGERENCIA_RAG, ESCALADO_A_HUMANO, COLA_REGULAR
    alert_sent: bool  # Indica si se disparó alerta (Ruta A)
    alert_payload: Optional[Dict[str, Any]]  # Datos estructurados para BackgroundTasks de notificación
    rag_context: Optional[List[str]]  # Fragmentos recuperados de manuales (Ruta B)
    final_response: Optional[str]  # Respuesta final, solución sugerida o estado de registro
    incident_id: Optional[int]  # ID numérico persistido en PostgreSQL (tabla incidents)
    error: Optional[str]  # Mensaje de error en caso de anomalía
