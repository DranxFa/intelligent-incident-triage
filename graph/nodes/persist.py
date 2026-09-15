from graph.state import IncidentGraphState
from services.incident_service import persist_incident_and_state


def persist_ticket(state: IncidentGraphState) -> dict:
    """
    Nodo de Persistencia Final:
    Registra el incidente en la tabla 'incidents' (diseñada para analítica en Power BI)
    y el estado técnico completo en 'incident_states' de PostgreSQL.
    """
    ticket_id = persist_incident_and_state(state)
    return {"incident_id": ticket_id}
