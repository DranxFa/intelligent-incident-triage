from unittest.mock import MagicMock, patch
import pytest
from graph.workflow import triage_graph
from schemas import (
    CategoryEnum,
    ImpactoEnum,
    IncidentAnalysis,
    PriorityEnum,
    UrgenciaEnum,
    calculate_priority_and_sla,
)


def test_priority_matrix_and_sla_combinations():
    """Valida que la matriz 3x3 de Impacto y Urgencia asigne correctamente la prioridad y SLA."""
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


@pytest.mark.anyio
async def test_langgraph_first_node_execution():
    """Valida la ejecución del primer nodo de LangGraph usando un mock del LLM estructurado."""
    mock_analysis = IncidentAnalysis(
        categoria=CategoryEnum.INFRAESTRUCTURA_RED,
        impacto=ImpactoEnum.ALTO,
        urgencia=UrgenciaEnum.ALTA,
        prioridad=PriorityEnum.P1,
        sla_horas=2,
        resumen_ejecutivo="Caída total del core de red del datacenter.",
        requiere_rag=False,
    )

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = mock_analysis

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    with patch("graph.nodes.classifier.get_llm", return_value=mock_llm):
        state_input = {
            "titulo": "Caída del switch central",
            "descripcion": "Ningún equipo de la empresa tiene conectividad a internet ni VPN.",
            "usuario": "ops_monitor",
            "analisis": None,
            "error": None,
        }

        result = await triage_graph.ainvoke(state_input)

        assert result["analisis"] is not None
        analysis: IncidentAnalysis = result["analisis"]
        assert analysis.categoria == CategoryEnum.INFRAESTRUCTURA_RED
        assert analysis.impacto == ImpactoEnum.ALTO
        assert analysis.urgencia == UrgenciaEnum.ALTA
        assert analysis.prioridad == PriorityEnum.P1
        assert analysis.sla_horas == 2
        assert analysis.requiere_rag is False
        assert "Caída total" in analysis.resumen_ejecutivo
