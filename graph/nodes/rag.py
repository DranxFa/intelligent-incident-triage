import logging
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import get_llm
from graph.state import IncidentGraphState
from services.knowledge_service import search_manuals_vector

logger = logging.getLogger("incident_triage.rag")


def rag_manual_resolver(state: IncidentGraphState) -> dict:
    """
    Ruta B: Se activa cuando la categoría es CONSULTA_OPERATIVA o requiere_rag es True.
    Recupera los 2 fragmentos más relevantes de manuales desde pgvector y redacta una solución sugerida.
    """
    texto_orig = state.get("texto_original") or {}
    titulo = texto_orig.get("titulo", "")
    descripcion = texto_orig.get("descripcion", "")

    query = f"{titulo}. {descripcion}".strip()

    # 1. Recuperar los 2 fragmentos más parecidos mediante distancia coseno en pgvector
    fragments = search_manuals_vector(query, limit=2)

    context_str = "\n\n".join([f"Fragmento {i+1}:\n{f}" for i, f in enumerate(fragments)])

    # 2. Redactar solución sugerida automática con LLM
    prompt_system = """Eres un asistente técnico de soporte de TI de nivel 1.
Tu objetivo es redactar una solución sugerida clara, paso a paso, educada y profesional
basándote en los fragmentos de manuales proporcionados.
Si los fragmentos ofrecen la respuesta, proporciona las instrucciones paso a paso para resolver la duda del usuario.
Si los manuales no contienen la solución exacta, indícale al usuario qué pasos iniciales seguir y que un técnico atenderá su consulta."""

    prompt_user = f"""Incidente reportado:
Título: {titulo}
Descripción: {descripcion}

Manuales encontrados en la base de conocimiento:
{context_str}

Por favor, redacta una respuesta y solución sugerida automática para el usuario."""

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=prompt_system),
            HumanMessage(content=prompt_user),
        ]
        response = llm.invoke(messages)
        solucion_sugerida = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.warning(f"No se pudo generar solución con LLM: {exc}. Usando plantilla con fragmentos.")
        solucion_sugerida = (
            f"Solución sugerida preliminar basada en manuales de la base de conocimiento:\n\n"
            f"{context_str}\n\n"
            f"Por favor verifique los pasos indicados en los manuales de referencia."
        )

    return {
        "alert_sent": False,
        "rag_context": fragments,
        "final_response": solucion_sugerida,
        "error": None,
    }
