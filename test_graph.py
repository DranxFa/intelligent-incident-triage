from unittest.mock import MagicMock, patch
import pytest
from graph.workflow import route_incident, triage_graph
from schemas import (
    CategoryEnum,
    ImpactoEnum,
    IncidentAnalysis,
    PriorityEnum,
    UrgenciaEnum,
    calculate_priority_and_sla,
)


def test_priority_matrix_and_sla_combinations():
    """Valida la matriz 3x3 de Impacto y Urgencia para prioridad y SLA."""
    # ALTO
    assert calculate_priority_and_sla(ImpactoEnum.ALTO, UrgenciaEnum.ALTA) == (
        PriorityEnum.P1,
        2,
    )
    assert calculate_priority_and_sla(ImpactoEnum.ALTO, UrgenciaEnum.MEDIA) == (
        PriorityEnum.P2,
        8,
    )
    assert calculate_priority_and_sla(ImpactoEnum.ALTO, UrgenciaEnum.BAJA) == (
        PriorityEnum.P3,
        24,
    )

    # MEDIO
    assert calculate_priority_and_sla(ImpactoEnum.MEDIO, UrgenciaEnum.ALTA) == (
        PriorityEnum.P2,
        8,
    )
    assert calculate_priority_and_sla(ImpactoEnum.MEDIO, UrgenciaEnum.MEDIA) == (
        PriorityEnum.P3,
        24,
    )
    assert calculate_priority_and_sla(ImpactoEnum.MEDIO, UrgenciaEnum.BAJA) == (
        PriorityEnum.P4,
        48,
    )

    # BAJO
    assert calculate_priority_and_sla(ImpactoEnum.BAJO, UrgenciaEnum.ALTA) == (
        PriorityEnum.P3,
        24,
    )
    assert calculate_priority_and_sla(ImpactoEnum.BAJO, UrgenciaEnum.MEDIA) == (
        PriorityEnum.P4,
        48,
    )
    assert calculate_priority_and_sla(ImpactoEnum.BAJO, UrgenciaEnum.BAJA) == (
        PriorityEnum.P4,
        48,
    )


def test_conditional_router_decisions():
    """Valida que la función route_incident derive correctamente a las rutas A, B y C."""
    # Caso Ruta A: P1
    state_p1 = {
        "triage_data": IncidentAnalysis(
            categoria=CategoryEnum.INFRAESTRUCTURA_RED,
            impacto=ImpactoEnum.ALTO,
            urgencia=UrgenciaEnum.ALTA,
            prioridad=PriorityEnum.P1,
            sla_horas=2,
            resumen_ejecutivo="Caída total del core de red",
            requiere_rag=False,
        )
    }
    assert route_incident(state_p1) == "send_p1_alert"

    # Caso Ruta B: CONSULTA_OPERATIVA
    state_consulta = {
        "triage_data": IncidentAnalysis(
            categoria=CategoryEnum.CONSULTA_OPERATIVA,
            impacto=ImpactoEnum.BAJO,
            urgencia=UrgenciaEnum.BAJA,
            prioridad=PriorityEnum.P4,
            sla_horas=48,
            resumen_ejecutivo="Duda de uso del ERP",
            requiere_rag=True,
        )
    }
    assert route_incident(state_consulta) == "rag_manual_resolver"

    # Caso Ruta B: requiere_rag=True (aunque sea otra categoría)
    state_rag = {
        "triage_data": IncidentAnalysis(
            categoria=CategoryEnum.ACCESOS_Y_SEGURIDAD,
            impacto=ImpactoEnum.BAJO,
            urgencia=UrgenciaEnum.MEDIA,
            prioridad=PriorityEnum.P4,
            sla_horas=48,
            resumen_ejecutivo="Reinicio de contraseña VPN",
            requiere_rag=True,
        )
    }
    assert route_incident(state_rag) == "rag_manual_resolver"

    # Caso Ruta C: P2/P3 normal sin RAG
    state_regular = {
        "triage_data": IncidentAnalysis(
            categoria=CategoryEnum.SOFTWARE_APLICACIONES,
            impacto=ImpactoEnum.MEDIO,
            urgencia=UrgenciaEnum.MEDIA,
            prioridad=PriorityEnum.P3,
            sla_horas=24,
            resumen_ejecutivo="Error menor en reporte mensual",
            requiere_rag=False,
        )
    }
    assert route_incident(state_regular) == "regular_queue"


@pytest.mark.anyio
async def test_workflow_ruta_a_p1_alert():
    """Valida la ejecución completa de la Ruta A (alerta Webhook P1 y concurrencia)."""
    from unittest.mock import AsyncMock
    from graph.nodes.alert import dispatch_alert_notifications

    mock_analysis = IncidentAnalysis(
        categoria=CategoryEnum.INFRAESTRUCTURA_RED,
        impacto=ImpactoEnum.ALTO,
        urgencia=UrgenciaEnum.ALTA,
        prioridad=PriorityEnum.P1,
        sla_horas=2,
        resumen_ejecutivo="Pasarela de pagos caída",
        requiere_rag=False,
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=mock_analysis)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    dummy_vector = [0.05] * 768

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm), patch(
        "graph.nodes.classifier.get_embedding", return_value=dummy_vector
    ), patch(
        "graph.nodes.persist.persist_incident_and_state", return_value=101
    ):
        state_input = {
            "texto_original": {
                "titulo": "Pasarela de pagos caída",
                "descripcion": "El checkout no responde y los clientes no pueden pagar.",
                "usuario": "admin_checkout",
            },
            "triage_data": None,
            "vector_embedding": None,
            "accion_ia": None,
            "alert_sent": False,
            "alert_payload": None,
            "rag_context": None,
            "final_response": None,
            "incident_id": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"] is not None
        assert result["triage_data"].prioridad == PriorityEnum.P1
        assert result["alert_sent"] is True
        assert result["accion_ia"] == "ALERTA_P1"
        assert result["alert_payload"] is not None
        assert result["alert_payload"]["resumen"] == "Pasarela de pagos caída"
        assert result["rag_context"] is None
        assert "🚨 ALERTA P1" in result["final_response"]
        assert "SLA: 2 horas" in result["final_response"]
        assert result["incident_id"] == 101


@pytest.mark.anyio
async def test_dispatch_alert_notifications():
    """Valida la función independiente dispatch_alert_notifications (ejecutada en BackgroundTasks)."""
    from graph.nodes.alert import dispatch_alert_notifications

    alert_payload = {
        "alert_message": "🚨 ALERTA P1: Core switch sin respuesta. SLA: 2 horas.",
        "resumen": "Core switch sin respuesta",
        "sla_horas": 2,
        "categoria": "INFRAESTRUCTURA_RED",
        "usuario": "noc_operator",
        "titulo": "Core switch sin respuesta",
        "descripcion": "Tráfico detenido en datacenter",
    }

    env_vars = {
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/mocked/test",
        "TELEGRAM_BOT_TOKEN": "mock_token",
        "TELEGRAM_CHAT_ID": "123456",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "admin@example.com",
        "SMTP_PASSWORD": "password",
        "ALERT_EMAIL_TO": "guardia@example.com",
    }

    with patch.dict("os.environ", env_vars), patch(
        "graph.nodes.alert.httpx.post"
    ) as mock_http, patch("graph.nodes.alert.smtplib.SMTP") as mock_smtp:
        mock_http_response = MagicMock()
        mock_http_response.raise_for_status.return_value = None
        mock_http.return_value = mock_http_response

        mock_smtp_inst = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_inst

        channels = dispatch_alert_notifications(alert_payload)

        assert "Discord" in channels
        assert "Telegram" in channels
        assert "Outlook/Correo" in channels
        assert mock_http.call_count == 2
        assert mock_smtp_inst.send_message.call_count == 1


@pytest.mark.anyio
async def test_workflow_ruta_b_rag_match():
    """Valida la Ruta B cuando SÍ existen manuales pertinentes (accion_ia = SUGERENCIA_RAG)."""
    from unittest.mock import AsyncMock

    mock_analysis = IncidentAnalysis(
        categoria=CategoryEnum.CONSULTA_OPERATIVA,
        impacto=ImpactoEnum.BAJO,
        urgencia=UrgenciaEnum.BAJA,
        prioridad=PriorityEnum.P4,
        sla_horas=48,
        resumen_ejecutivo="Consulta sobre exportación a Excel en el ERP",
        requiere_rag=True,
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=mock_analysis)

    mock_rag_response = MagicMock()
    mock_rag_response.content = "Para exportar a Excel, diríjase a Reportes Contables > Exportar > XLSX."

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm.ainvoke = AsyncMock(return_value=mock_rag_response)

    mock_fragments = [
        "Manual: Procedimiento ERP Facturación y Reportes [SOFTWARE_APLICACIONES]\nExportar reportes.",
        "Manual: Guía de exportación [CONSULTA_OPERATIVA]\nPaso a paso.",
    ]
    dummy_vector = [0.05] * 768

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm), patch(
        "graph.nodes.classifier.get_embedding", return_value=dummy_vector
    ), patch(
        "graph.nodes.rag.get_llm", return_value=mock_llm
    ), patch(
        "graph.nodes.rag.search_manuals_with_threshold", return_value=mock_fragments
    ), patch(
        "graph.nodes.persist.persist_incident_and_state", return_value=102
    ):
        state_input = {
            "texto_original": {
                "titulo": "Exportar facturas a Excel",
                "descripcion": "¿Cómo puedo exportar los reportes contables a Excel?",
                "usuario": "usuario_contabilidad",
            },
            "triage_data": None,
            "vector_embedding": None,
            "accion_ia": None,
            "alert_sent": False,
            "alert_payload": None,
            "rag_context": None,
            "final_response": None,
            "incident_id": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"].requiere_rag is True
        assert result["alert_sent"] is False
        assert result["accion_ia"] == "SUGERENCIA_RAG"
        assert result["rag_context"] is not None
        assert len(result["rag_context"]) == 2
        assert "Para exportar a Excel" in result["final_response"]
        assert result["incident_id"] == 102


@pytest.mark.anyio
async def test_workflow_ruta_b_rag_fallback_to_human():
    """Valida la Ruta B cuando NO hay manuales pertinentes (distancia > 0.55 -> ESCALADO_A_HUMANO)."""
    from unittest.mock import AsyncMock

    mock_analysis = IncidentAnalysis(
        categoria=CategoryEnum.CONSULTA_OPERATIVA,
        impacto=ImpactoEnum.BAJO,
        urgencia=UrgenciaEnum.BAJA,
        prioridad=PriorityEnum.P4,
        sla_horas=48,
        resumen_ejecutivo="Consulta atípica sin manual de referencia",
        requiere_rag=True,
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=mock_analysis)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    dummy_vector = [0.05] * 768

    # search_manuals_with_threshold retorna lista vacía cuando la distancia > 0.55
    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm), patch(
        "graph.nodes.classifier.get_embedding", return_value=dummy_vector
    ), patch(
        "graph.nodes.rag.search_manuals_with_threshold", return_value=[]
    ), patch(
        "graph.nodes.persist.persist_incident_and_state", return_value=105
    ):
        state_input = {
            "texto_original": {
                "titulo": "¿Cómo configurar un clúster cuántico con superconductores?",
                "descripcion": "Requiero manual sobre configuración cuántica en terminales.",
                "usuario": "investigador_dr",
            },
            "triage_data": None,
            "vector_embedding": None,
            "accion_ia": None,
            "alert_sent": False,
            "alert_payload": None,
            "rag_context": None,
            "final_response": None,
            "incident_id": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["accion_ia"] == "ESCALADO_A_HUMANO"
        assert result["rag_context"] is None
        assert "cola de soporte técnico humano" in result["final_response"]
        assert "especialista" in result["final_response"]
        assert result["incident_id"] == 105


@pytest.mark.anyio
async def test_workflow_ruta_c_regular_queue():
    """Valida la ejecución de la Ruta C (cola regular para P2/P3 normal)."""
    from unittest.mock import AsyncMock

    mock_analysis = IncidentAnalysis(
        categoria=CategoryEnum.SOFTWARE_APLICACIONES,
        impacto=ImpactoEnum.MEDIO,
        urgencia=UrgenciaEnum.MEDIA,
        prioridad=PriorityEnum.P3,
        sla_horas=24,
        resumen_ejecutivo="Error en visualización de avatar en CRM",
        requiere_rag=False,
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=mock_analysis)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    dummy_vector = [0.05] * 768

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm), patch(
        "graph.nodes.classifier.get_embedding", return_value=dummy_vector
    ), patch(
        "graph.nodes.persist.persist_incident_and_state", return_value=103
    ):
        state_input = {
            "texto_original": {
                "titulo": "Bug visual en CRM",
                "descripcion": "El avatar de usuario aparece distorsionado en Safari.",
                "usuario": "ventas_juan",
            },
            "triage_data": None,
            "vector_embedding": None,
            "accion_ia": None,
            "alert_sent": False,
            "alert_payload": None,
            "rag_context": None,
            "final_response": None,
            "incident_id": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"].prioridad == PriorityEnum.P3
        assert result["alert_sent"] is False
        assert result["rag_context"] is None
        assert "cola de atención regular" in result["final_response"]
        assert result["incident_id"] == 103
