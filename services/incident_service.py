import logging
from typing import Optional
from database import Incident, IncidentStateRecord, get_db_context
from graph.state import IncidentGraphState
from services.embeddings import get_embedding

logger = logging.getLogger("incident_triage.incidents")


def persist_incident_and_state(state: IncidentGraphState) -> Optional[int]:
    """
    Persiste el incidente en la tabla 'incidents' (diseñada para analítica en Power BI)
    y el diccionario tipado completo en la tabla 'incident_states' (historial técnico de LangGraph).
    """
    texto_orig = state.get("texto_original") or {}
    triage = state.get("triage_data")
    titulo = texto_orig.get("titulo", "Sin título")
    descripcion = texto_orig.get("descripcion", "Sin descripción")
    usuario = texto_orig.get("usuario", "desconocido")

    prioridad = triage.prioridad.value if triage else "P4"
    sla_horas = triage.sla_horas if triage else 48
    categoria = triage.categoria.value if triage else "CONSULTA_OPERATIVA"
    solucion_sugerida = state.get("final_response")
    alert_sent = state.get("alert_sent", False)
    rag_context = state.get("rag_context")

    # Determinar estado del ciclo de vida del ticket
    if alert_sent:
        estado = "ALERTA_ENVIADA"
    elif rag_context:
        estado = "SUGERENCIA_GENERADA"
    else:
        estado = "ABIERTO"

    try:
        # Calcular vector embedding del problema para búsqueda y analítica semántica
        text_for_embedding = f"{titulo}. {descripcion}"
        incident_vector = get_embedding(text_for_embedding)

        with get_db_context() as db:
            # 1. Registro en la tabla operativa para Power BI
            incident_record = Incident(
                usuario=usuario,
                titulo=titulo,
                descripcion=descripcion,
                prioridad=prioridad,
                sla_horas=sla_horas,
                categoria=categoria,
                estado=estado,
                tiempo_resolucion=None,
                solucion_sugerida=solucion_sugerida,
                vector_embedding=incident_vector,
            )
            db.add(incident_record)
            db.flush()  # Obtener el ID asignado por PostgreSQL

            # 2. Registro del estado completo de LangGraph
            state_record = IncidentStateRecord(
                incident_id=incident_record.id,
                texto_original=texto_orig,
                triage_data=triage.model_dump() if triage else {},
                alert_sent=alert_sent,
                rag_context=rag_context,
                final_response=solucion_sugerida,
                error=state.get("error"),
            )
            db.add(state_record)
            db.commit()

            logger.info(
                f"Incidente #{incident_record.id} y su estado técnico fueron persistidos exitosamente en PostgreSQL."
            )
            return incident_record.id

    except Exception as exc:
        logger.warning(
            f"No se pudo persistir el incidente en PostgreSQL ({exc}). Verifique que el contenedor Docker esté activo."
        )
        return None
