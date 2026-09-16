import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import get_llm
from graph.state import IncidentGraphState
from schemas import IncidentAnalysis, calculate_priority_and_sla
from services.embeddings import get_embedding

SYSTEM_PROMPT = """Eres un sistema experto en triaje y clasificación automatizada de incidentes de TI y soporte operacional.
Tu labor es analizar minuciosamente el reporte de incidencia y devolver un JSON estructurado con la clasificación exacta.

CRITERIOS DE CLASIFICACIÓN:

1. Categoría (categoria):
- ACCESOS_Y_SEGURIDAD: Problemas de contraseñas, reseteo de credenciales, permisos en carpetas/archivos, accesos a red o VPN.
- SOFTWARE_APLICACIONES: Errores o bugs en aplicaciones de negocio (ERP, CRM, páginas web, sistemas internos).
- INFRAESTRUCTURA_RED: Caídas de internet, fallas en servidores, problemas de conectividad o lentitud general de red.
- HARDWARE_EQUIPOS: Fallas físicas en laptops, PCs de escritorio, impresoras, monitores, periféricos o suministros dañados.
- CONSULTA_OPERATIVA: Dudas sobre cómo utilizar una herramienta, consultas de manuales, solicitudes de capacitación o preguntas frecuentes.

2. Impacto (impacto):
- ALTO: Afecta a toda la empresa o interrumpe un proceso core de la organización.
- MEDIO: Afecta a un departamento, área o equipo de trabajo completo.
- BAJO: Afecta únicamente a un solo usuario individual.

3. Urgencia (urgencia):
- ALTA: Bloqueo total de la operación; no existe forma alternativa de continuar el trabajo.
- MEDIA: Operación degradada o con impacto relevante, pero existe alguna alternativa temporal o workaround.
- BAJA: Inconveniente menor no bloqueante; el usuario o equipo puede continuar trabajando.

4. Matriz de Prioridad (prioridad) y SLA (sla_horas):
- Impacto ALTO + Urgencia ALTA   -> Prioridad: P1 | SLA: 2 horas
- Impacto ALTO + Urgencia MEDIA  -> Prioridad: P2 | SLA: 8 horas
- Impacto ALTO + Urgencia BAJA   -> Prioridad: P3 | SLA: 24 horas
- Impacto MEDIO + Urgencia ALTA  -> Prioridad: P2 | SLA: 8 horas
- Impacto MEDIO + Urgencia MEDIA -> Prioridad: P3 | SLA: 24 horas
- Impacto MEDIO + Urgencia BAJA  -> Prioridad: P4 | SLA: 48 horas
- Impacto BAJO + Urgencia ALTA   -> Prioridad: P3 | SLA: 24 horas
- Impacto BAJO + Urgencia MEDIA  -> Prioridad: P4 | SLA: 48 horas
- Impacto BAJO + Urgencia BAJA   -> Prioridad: P4 | SLA: 48 horas

5. Resumen Ejecutivo (resumen_ejecutivo):
- Una sola línea limpia, concisa y objetiva resumiendo el problema central y su contexto inmediato.

6. Requiere RAG (requiere_rag):
- True: Si se trata de dudas de uso, consultas operativas, procedimientos paso a paso o errores comunes que típicamente se resuelven consultando manuales o bases de conocimiento.
- False: Si se trata de fallas de infraestructura crítica, hardware físico roto o situaciones que requieren intervención manual en el backend.
"""


async def classify_incident(state: IncidentGraphState) -> dict:
    """
    Primer nodo del grafo:
    Ejecuta concurrentemente con asyncio.gather:
    1. La clasificación estructurada del LLM (Gemini / Groq).
    2. La generación del vector embedding (768 dimensiones).
    Esto reduce drásticamente la latencia de respuesta en producción.
    """
    texto_orig = state.get("texto_original") or {}
    titulo = texto_orig.get("titulo") or state.get("titulo", "")
    descripcion = texto_orig.get("descripcion") or state.get("descripcion", "")
    usuario = texto_orig.get("usuario") or state.get("usuario", "")

    user_prompt = f"""Analiza el siguiente reporte de incidente:

- Reportado por: {usuario}
- Título: {titulo}
- Descripción: {descripcion}

Devuelve la clasificación estructurada según los criterios establecidos.
"""

    llm = get_llm()
    structured_llm = llm.with_structured_output(IncidentAnalysis)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    text_to_embed = f"{titulo}. {descripcion}".strip()

    # Ejecución paralela de clasificación y generación de vector
    analysis, vector = await asyncio.gather(
        structured_llm.ainvoke(messages),
        asyncio.to_thread(get_embedding, text_to_embed),
    )

    # Garantizar determinismo en Prioridad y SLA según la matriz 3x3
    prioridad_calculada, sla_calculado = calculate_priority_and_sla(
        analysis.impacto, analysis.urgencia
    )
    analysis.prioridad = prioridad_calculada
    analysis.sla_horas = sla_calculado

    return {
        "triage_data": analysis,
        "vector_embedding": vector,
        "error": None,
    }
