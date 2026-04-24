from __future__ import annotations

from backend.app.schemas.simulation import SimulationRequest
from backend.app.services.simulation_service import run_simulation

from tests.helpers import assert_nested_close, load_fixture, strip_none


def test_simulation_endpoint_matches_service_output(client) -> None:
    config = load_fixture("default_tem00.json")
    response = client.post("/api/simulate", json=config)

    assert response.status_code == 200

    api_result = strip_none(response.json())
    service_result = strip_none(run_simulation(SimulationRequest.model_validate(config)).model_dump(mode="json"))

    assert_nested_close(api_result, service_result)


def test_simulation_endpoint_rejects_invalid_payload(client) -> None:
    response = client.post("/api/simulate", json={"wavelength_nm": -1})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["details"]
