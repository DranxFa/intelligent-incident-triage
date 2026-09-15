from langgraph.graph import END, START, StateGraph
from graph.nodes.classifier import classify_incident
from graph.state import IncidentGraphState


def create_incident_workflow():
    """
    Construye y compila el flujo orquestado con LangGraph.
    Actualmente contiene el primer nodo: classify_incident.
    Estructurado para conectar los siguientes nodos fácilmente.
    """
    workflow = StateGraph(IncidentGraphState)

    # Registro del primer nodo
    workflow.add_node("classify_incident", classify_incident)

    # Definición de transiciones
    workflow.add_edge(START, "classify_incident")
    workflow.add_edge("classify_incident", END)

    return workflow.compile()


# Instancia compilada del grafo reutilizable en la aplicación
triage_graph = create_incident_workflow()
