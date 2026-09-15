from unittest.mock import MagicMock, patch
import pytest
from services.embeddings import get_embedding
from services.knowledge_service import parse_markdown_manuals


def test_markdown_manuals_parsing():
    """Verifica que el archivo data/manuales_ti.md contenga al menos 10 soluciones de TI bien estructuradas."""
    manuals = parse_markdown_manuals()
    assert len(manuals) >= 10

    for m in manuals:
        assert "titulo" in m and len(m["titulo"]) > 5
        assert "categoria" in m and len(m["categoria"]) > 0
        assert "contenido" in m and len(m["contenido"]) > 20

    # Comprobar algunos temas requeridos específicamente
    titles = [m["titulo"].lower() for m in manuals]
    assert any("base de datos" in t or "postgresql" in t for t in titles)
    assert any("sap" in t for t in titles)
    assert any("impresora" in t for t in titles)


def test_embedding_generation_768d():
    """Valida que el servicio de embeddings devuelva vectores normalizados de 768 dimensiones."""
    vector = get_embedding("Cómo reiniciar la base de datos PostgreSQL")
    assert isinstance(vector, list)
    assert len(vector) == 768
    # Verificar que los elementos sean números flotantes
    assert all(isinstance(x, float) for x in vector)


@pytest.mark.anyio
async def test_persist_ticket_node():
    """Valida que el nodo de persistencia invoque el servicio correspondiente."""
    from graph.nodes.persist import persist_ticket
    from schemas import CategoryEnum, ImpactoEnum, IncidentAnalysis, PriorityEnum, UrgenciaEnum

    state = {
        "texto_original": {
            "titulo": "Falla en base de datos",
            "descripcion": "PostgreSQL no responde en el puerto 5432",
            "usuario": "ops_user",
        },
        "triage_data": IncidentAnalysis(
            categoria=CategoryEnum.INFRAESTRUCTURA_RED,
            impacto=ImpactoEnum.ALTO,
            urgencia=UrgenciaEnum.ALTA,
            prioridad=PriorityEnum.P1,
            sla_horas=2,
            resumen_ejecutivo="Caída de PostgreSQL",
            requiere_rag=False,
        ),
        "alert_sent": True,
        "rag_context": None,
        "final_response": "🚨 ALERTA P1: Caída de PostgreSQL. SLA: 2 horas.",
        "incident_id": None,
        "error": None,
    }

    with patch("graph.nodes.persist.persist_incident_and_state", return_value=42) as mock_persist:
        res = persist_ticket(state)
        mock_persist.assert_called_once_with(state)
        assert res["incident_id"] == 42
