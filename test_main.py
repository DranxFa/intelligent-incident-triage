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
        resumen_ejecutivo="Usuario bloqueado por contraseña expirada.",
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
        "texto_original": form_data,
        "triage_data": sample_analysis,
        "accion_ia": "SUGERENCIA_RAG",
        "alert_sent": False,
        "alert_payload": None,
        "rag_context": ["Fragmento 1: Manual de contraseñas", "Fragmento 2: Autoservicio VPN"],
        "final_response": "Solución sugerida: ingrese a portal de autoservicio.",
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
    assert json_resp["status"] == "processed"
    assert json_resp["texto_original"]["titulo"] == form_data["titulo"]
    assert json_resp["texto_original"]["usuario"] == form_data["usuario"]
    assert json_resp["triage_data"]["categoria"] == "ACCESOS_Y_SEGURIDAD"
    assert json_resp["triage_data"]["prioridad"] == "P4"
    assert json_resp["accion_ia"] == "SUGERENCIA_RAG"
    assert json_resp["alert_sent"] is False
    assert len(json_resp["rag_context"]) == 2
    assert "Solución sugerida" in json_resp["final_response"]


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
        "titulo": "Pasarela de pagos caída",
        "descripcion": "Error crítico al procesar tarjetas de crédito.",
        "usuario": "admin_checkout",
    }

    alert_payload = {
        "alert_message": "🚨 ALERTA P1: Pasarela de pagos caída. SLA: 2 horas. Responsable: Turno de guardia.",
        "resumen": "Pasarela de pagos caída",
        "sla_horas": 2,
        "categoria": "INFRAESTRUCTURA_RED",
        "usuario": "admin_checkout",
        "titulo": "Pasarela de pagos caída",
        "descripcion": "Error crítico al procesar tarjetas de crédito.",
    }

    mock_result_state = {
        "texto_original": json_data,
        "triage_data": sample_analysis,
        "accion_ia": "ALERTA_P1",
        "alert_sent": True,
        "alert_payload": alert_payload,
        "rag_context": None,
        "final_response": "🚨 ALERTA P1: Pasarela de pagos caída. SLA: 2 horas. Responsable: Turno de guardia.",
        "error": None,
    }

    with patch("main.triage_graph.ainvoke", new_callable=AsyncMock) as mock_graph, patch(
        "main.dispatch_alert_notifications"
    ) as mock_dispatch:
        mock_graph.return_value = mock_result_state

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.post("/incidents/json", json=json_data)

        # BackgroundTasks ejecuta la función al finalizar el ciclo de respuesta
        mock_dispatch.assert_called_once_with(alert_payload)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["status"] == "processed"
    assert json_resp["texto_original"] == json_data
    assert json_resp["accion_ia"] == "ALERTA_P1"
    assert json_resp["alert_sent"] is True
    assert "🚨 ALERTA P1" in json_resp["final_response"]
