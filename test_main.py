import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_submit_incident_form():
    form_data = {
        "titulo": "Caída del servicio de base de datos",
        "descripcion": "El cluster de PostgreSQL no responde a nuevas conexiones.",
        "usuario": "admin_ops",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/incidents", data=form_data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["message"] == "Formulario recibido correctamente"
    assert json_resp["data"]["titulo"] == form_data["titulo"]
    assert json_resp["data"]["descripcion"] == form_data["descripcion"]
    assert json_resp["data"]["usuario"] == form_data["usuario"]
    assert json_resp["status"] == "received"


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
async def test_submit_incident_json():
    json_data = {
        "titulo": "Latencia alta en el gateway",
        "descripcion": "Los tiempos de respuesta aumentaron a 1500ms.",
        "usuario": "dev_juan",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/incidents/json", json=json_data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["message"] == "Datos en formato JSON recibidos correctamente"
    assert json_resp["data"] == json_data
