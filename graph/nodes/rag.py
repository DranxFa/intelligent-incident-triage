import logging
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import get_llm
from graph.state import IncidentGraphState
from services.knowledge_service import search_manuals_with_threshold

logger = logging.getLogger("incident_triage.rag")


async def rag_manual_resolver(state: IncidentGraphState) -> dict:
    """
    Ruta B: Se activa cuando la categoría es CONSULTA_OPERATIVA o requiere_rag es True.
    1. Recupera fragmentos relevantes desde pgvector con umbral estricto de distancia coseno (<= 0.55).
    2. Si hay coincidencia: Redacta solución técnica automática con el LLM (accion_ia = 'SUGERENCIA_RAG').
    3. Si NO hay coincidencia: Escala a cola de soporte humano (accion_ia = 'ESCALADO_A_HUMANO') con mensaje empático.
    """
    texto_orig = state.get("texto_original") or {}
    titulo = texto_orig.get("titulo", "")
    descripcion = texto_orig.get("descripcion", "")
    query_vector = state.get("vector_embedding")

    query = f"{titulo}. {descripcion}".strip()

    # 1. Recuperar los fragmentos con umbral de similitud semántica (reutilizando query_vector si existe)
    fragments = search_manuals_with_threshold(
        query_text=query,
        query_vector=query_vector,
        max_distance=0.38,
        limit=2,
    )

    # 2. Si no se encontraron manuales pertinentes por encima del umbral -> Fallback a soporte humano
    if not fragments:
        logger.info(
            f"No se hallaron manuales con similitud suficiente para: '{query}'. Escalando a soporte humano."
        )
        escalation_message = (
            "No encontramos un manual con la solución exacta para tu consulta en nuestra base de conocimientos. "
            "Hemos derivado tu caso a la cola de soporte técnico humano. "
            "Un especialista se pondrá en contacto contigo a la brevedad."
        )
        return {
            "alert_sent": False,
            "accion_ia": "ESCALADO_A_HUMANO",
            "rag_context": None,
            "final_response": escalation_message,
            "error": None,
        }

    # 3. Si hay manuales pertinentes -> Redactar solución sugerida automática con LLM
    context_str = "\n\n".join([f"Fragmento {i+1}:\n{f}" for i, f in enumerate(fragments)])

    prompt_system = """Eres un asistente técnico de soporte de TI de nivel 1.
Tu objetivo es redactar una solución sugerida clara, paso a paso, educada y profesional
basándote en los fragmentos de manuales proporcionados.
Proporciona las instrucciones paso a paso para resolver la duda del usuario de forma inmediata."""

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
        response = await llm.ainvoke(messages)
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
        "accion_ia": "SUGERENCIA_RAG",
        "rag_context": fragments,
        "final_response": solucion_sugerida,
        "error": None,
    }
