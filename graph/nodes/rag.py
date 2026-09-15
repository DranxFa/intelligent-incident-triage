import logging
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import get_llm
from graph.state import IncidentGraphState

logger = logging.getLogger("incident_triage.rag")

# Base de conocimiento inicial / fallback para pruebas (preparada para sustitución por pgvector en la siguiente fase)
FALLBACK_MANUALS = [
    {
        "tema": "VPN y Accesos Remotos",
        "fragmento": "Manual de VPN y Credenciales: Para reconectar a la VPN corporativa, asegúrese de reiniciar el cliente Cisco AnyConnect o FortiClient. Si sus credenciales han expirado, ingrese al portal de autoservicio de contraseñas https://selfservice.empresa.local para sincronizar su cuenta de Active Directory.",
    },
    {
        "tema": "ERP y Facturación",
        "fragmento": "Procedimiento ERP Facturación y Reportes: Para exportar reportes a formato Excel o PDF, diríjase al módulo 'Reportes Contables > Exportar > Formato XLSX'. Si el sistema arroja error de memoria, reduzca el rango de fechas a un máximo de 30 días.",
    },
    {
        "tema": "Impresoras y Escáneres",
        "fragmento": "Guía de Soporte de Impresoras de Red: Verifique que la cola de impresión en Windows esté vacía. Si la impresora aparece fuera de línea, reinicie el servicio 'Cola de impresión' (Spooler) desde services.msc y valide que el equipo esté en la misma subred.",
    },
    {
        "tema": "Sistemas Web Internos",
        "fragmento": "Guía de Limpieza de Caché y Sesiones Web: Si los formularios de las páginas internas quedan cargando indefinidamente, limpie la memoria caché del navegador (Ctrl + Shift + R) o intente abrir la aplicación en modo incógnito para descartar extensiones conflictivas.",
    },
]


def search_manuals_pgvector(query: str, limit: int = 2) -> List[str]:
    """
    Búsqueda de fragmentos más similares mediante distancia coseno en pgvector.
    En esta etapa incluye el fallback de fragmentos representativos;
    en la siguiente fase se conectará directamente a la tabla 'manuales' con pgvector.
    """
    query_lower = query.lower()

    # Ponderación simple por relevancia temática en caso de usar fallback
    scored = []
    for item in FALLBACK_MANUALS:
        score = sum(1 for word in query_lower.split() if word in item["fragmento"].lower() or word in item["tema"].lower())
        scored.append((score, item["fragmento"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected_fragments = [frag for _, frag in scored[:limit]]

    # Si no hubo coincidencia específica, devolver los dos primeros fragmentos estándar
    if not selected_fragments:
        selected_fragments = [item["fragmento"] for item in FALLBACK_MANUALS[:limit]]

    return selected_fragments


def rag_manual_resolver(state: IncidentGraphState) -> dict:
    """
    Ruta B: Se activa cuando la categoría es CONSULTA_OPERATIVA o requiere_rag es True.
    Recupera los 2 fragmentos más relevantes de manuales y redacta una solución sugerida automática.
    """
    texto_orig = state.get("texto_original") or {}
    titulo = texto_orig.get("titulo", "")
    descripcion = texto_orig.get("descripcion", "")

    query = f"{titulo}. {descripcion}".strip()

    # 1. Recuperar los 2 fragmentos más parecidos
    fragments = search_manuals_pgvector(query, limit=2)

    context_str = "\n\n".join([f"Fragmento {i+1}:\n{f}" for i, f in enumerate(fragments)])

    # 2. Redactar solución sugerida automática con LLM
    prompt_system = """Eres un asistente técnico de soporte de TI de nivel 1.
Tu objetivo es redactar una solución sugerida clara, paso a paso, educada y profesional
basándote ÚNICAMENTE en los fragmentos de manuales proporcionados.
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
