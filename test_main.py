from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from schemas import (
    CategoryEnum,
    ImpactoEnum,
    IncidentAnalysis,
    PriorityEnum,
    UrgenciaEnum,
)


@pytest.fixture
def sample_analysis():
    return IncidentAnalysis(
        categoria=CategoryEnum.ACCESOS_Y_SEGURIDAD,
        impacto=ImpactoEnum.BAJO,
        urgencia=UrgenciaEnum.MEDIA,
        prioridad=PriorityEnum.P4,
        sla_horas=48,
        resumen_ejecutivo="Usuario bloqueado por contraseña expirada en el directorio activo.",
        requiere_rag=True,
    )


@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_submit_incident_form(sample_analysis):
    form_data = {
        "titulo": "No puedo ingresar con mi contraseña",
        "descripcion": "Aparece un mensaje que mi contraseña ha caducado en Windows.",
        "usuario": "marta_ventas",
    }

    mock_result_state = {
        "titulo": form_data["titulo"],
        "descripcion": form_data["descripcion"],
        "usuario": form_data["usuario"],
        "analisis": sample_analysis,
        "error": None,
    }

    with patch("main.triage_graph.ainvoke", new_callable=AsyncMock) as mock_graph:
        mock_graph.return_value = mock_result_state

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/incidents", data=form_data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["status"] == "classified"
    assert json_resp["data"]["titulo"] == form_data["titulo"]
    assert json_resp["data"]["usuario"] == form_data["usuario"]
    assert json_resp["analisis"]["categoria"] == "ACCESOS_Y_SEGURIDAD"
    assert json_resp["analisis"]["prioridad"] == "P4"
    assert json_resp["analisis"]["sla_horas"] == 48
    assert json_resp["analisis"]["requiere_rag"] is True


@pytest.mark.anyio
async def test_submit_incident_form_missing_field():
    # Falta el campo requerido 'usuario'
    form_data = {
        "titulo": "Error 500 en checkout",
        "descripcion": "Los usuarios no pueden completar el pago.",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/incidents", data=form_data)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_incident_json(sample_analysis):
    json_data = {
        "titulo": "Duda sobre exportación a Excel",
        "descripcion": "¿Existe algún manual para exportar las facturas a formato xlsx?",
        "usuario": "carlos_finanzas",
    }

    mock_result_state = {
        "titulo": json_data["titulo"],
        "descripcion": json_data["descripcion"],
        "usuario": json_data["usuario"],
        "analisis": sample_analysis,
        "error": None,
    }

    with patch("main.triage_graph.ainvoke", new_callable=AsyncMock) as mock_graph:
        mock_graph.return_value = mock_result_state

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/incidents/json", json=json_data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["status"] == "classified"
    assert json_resp["data"] == json_data
    assert json_resp["analisis"]["categoria"] == "ACCESOS_Y_SEGURIDAD"
