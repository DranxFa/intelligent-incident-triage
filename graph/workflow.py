from langgraph.graph import END, START, StateGraph
from graph.nodes.alert import send_p1_alert
from graph.nodes.classifier import classify_incident
from graph.nodes.persist import persist_ticket
from graph.nodes.queue import regular_queue
from graph.nodes.rag import rag_manual_resolver
from graph.state import IncidentGraphState
from schemas import CategoryEnum, PriorityEnum


def route_incident(state: IncidentGraphState) -> str:
    """
    Enrutador condicional (Segundo nodo):
    - Ruta A ('send_p1_alert'): Se activa si la prioridad es P1.
    - Ruta B ('rag_manual_resolver'): Se activa si la categoría es CONSULTA_OPERATIVA o requiere_rag es True.
    - Ruta C ('regular_queue'): Se activa para incidentes normales (P2, P3, P4) sin manual/RAG.
    """
    triage = state.get("triage_data")
    if not triage:
        return "regular_queue"

    # Ruta A: Alerta crítica P1
    if triage.prioridad == PriorityEnum.P1:
        return "send_p1_alert"

    # Ruta B: Consultas operativas o incidentes que requieren consultar manuales
    if triage.categoria == CategoryEnum.CONSULTA_OPERATIVA or triage.requiere_rag:
        return "rag_manual_resolver"

    # Ruta C: Atención regular directa
    return "regular_queue"


def create_incident_workflow():
    """
    Construye y compila el flujo orquestado con LangGraph incluyendo:
    - Nodo 1: classify_incident (clasificación estructurada)
    - Enrutador condicional hacia:
        * Ruta A: send_p1_alert
        * Ruta B: rag_manual_resolver
        * Ruta C: regular_queue
    - Nodo Final: persist_ticket (guarda en tabla 'incidents' y 'incident_states' en PostgreSQL)
    """
    workflow = StateGraph(IncidentGraphState)

    # 1. Registro de nodos
    workflow.add_node("classify_incident", classify_incident)
    workflow.add_node("send_p1_alert", send_p1_alert)
    workflow.add_node("rag_manual_resolver", rag_manual_resolver)
    workflow.add_node("regular_queue", regular_queue)
    workflow.add_node("persist_ticket", persist_ticket)

    # 2. Transición inicial
    workflow.add_edge(START, "classify_incident")

    # 3. Transición condicional basada en el resultado de la clasificación
    workflow.add_conditional_edges(
        "classify_incident",
        route_incident,
        {
            "send_p1_alert": "send_p1_alert",
            "rag_manual_resolver": "rag_manual_resolver",
            "regular_queue": "regular_queue",
        },
    )

    # 4. Todas las ramas convergen en el nodo de persistencia antes de finalizar
    workflow.add_edge("send_p1_alert", "persist_ticket")
    workflow.add_edge("rag_manual_resolver", "persist_ticket")
    workflow.add_edge("regular_queue", "persist_ticket")

    # 5. Fin del flujo
    workflow.add_edge("persist_ticket", END)

    return workflow.compile()


# Instancia compilada del grafo reutilizable en la aplicación
triage_graph = create_incident_workflow()
