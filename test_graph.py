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
    """Valida la ejecución completa de la Ruta A (alerta Webhook P1)."""
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
    mock_structured_llm.invoke.return_value = mock_analysis

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm):
        state_input = {
            "texto_original": {
                "titulo": "Pasarela de pagos caída",
                "descripcion": "El checkout no responde y los clientes no pueden pagar.",
                "usuario": "admin_checkout",
            },
            "triage_data": None,
            "alert_sent": False,
            "rag_context": None,
            "final_response": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"] is not None
        assert result["triage_data"].prioridad == PriorityEnum.P1
        assert result["alert_sent"] is True
        assert result["rag_context"] is None
        assert "🚨 ALERTA P1" in result["final_response"]
        assert "SLA: 2 horas" in result["final_response"]


@pytest.mark.anyio
async def test_workflow_ruta_b_rag():
    """Valida la ejecución de la Ruta B (recuperación de manuales y solución con RAG)."""
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
    mock_structured_llm.invoke.return_value = mock_analysis

    mock_rag_response = MagicMock()
    mock_rag_response.content = "Para exportar a Excel, diríjase a Reportes Contables > Exportar > XLSX."

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_llm.invoke.return_value = mock_rag_response

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm), patch(
        "graph.nodes.rag.get_llm", return_value=mock_llm
    ):
        state_input = {
            "texto_original": {
                "titulo": "Exportar facturas a Excel",
                "descripcion": "¿Cómo puedo exportar los reportes contables a Excel?",
                "usuario": "usuario_contabilidad",
            },
            "triage_data": None,
            "alert_sent": False,
            "rag_context": None,
            "final_response": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"].requiere_rag is True
        assert result["alert_sent"] is False
        assert result["rag_context"] is not None
        assert len(result["rag_context"]) == 2
        assert "Para exportar a Excel" in result["final_response"]


@pytest.mark.anyio
async def test_workflow_ruta_c_regular_queue():
    """Valida la ejecución de la Ruta C (cola regular para P2/P3 normal)."""
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
    mock_structured_llm.invoke.return_value = mock_analysis

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm):
        state_input = {
            "texto_original": {
                "titulo": "Bug visual en CRM",
                "descripcion": "El avatar de usuario aparece distorsionado en Safari.",
                "usuario": "ventas_juan",
            },
            "triage_data": None,
            "alert_sent": False,
            "rag_context": None,
            "final_response": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["triage_data"].prioridad == PriorityEnum.P3
        assert result["alert_sent"] is False
        assert result["rag_context"] is None
        assert "cola de atención regular" in result["final_response"]
