from graph.state import IncidentGraphState


def regular_queue(state: IncidentGraphState) -> dict:
    """
    Ruta C: Se activa para incidentes normales (P2, P3, P4) que no son críticos y no requieren RAG.
    Se salta las alertas y el RAG, registrándose para entrar a la cola de atención regular.
    (En la siguiente fase insertará el registro en la base de datos PostgreSQL).
    """
    triage = state.get("triage_data")
    prioridad = triage.prioridad.value if triage else "P3"
    sla = triage.sla_horas if triage else 24

    return {
        "alert_sent": False,
        "rag_context": None,
        "final_response": (
            f"Ticket registrado directamente en la cola de atención regular. "
            f"Prioridad asignada: {prioridad} (SLA: {sla} horas). Pendiente de asignación técnica."
        ),
        "error": None,
    }
