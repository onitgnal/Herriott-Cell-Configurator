from __future__ import annotations

import time

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


def test_wave_optics_endpoint_returns_profiles(client) -> None:
    config = load_fixture("default_tem00.json")
    config["wave_optics"] = {
        "profile_type": "round_super_gaussian",
        "super_gaussian_order": 6.0,
        "max_grid_points": 256,
        "max_memory_mb": 128,
        "display_grid_points": 48,
    }

    response = client.post("/api/simulate-wave-optics", json=config)

    assert response.status_code == 200
    body = response.json()
    assert "wave_optics" in body
    assert body["wave_optics"]["method"] == "Adaptive-grid 2D Collins/Fresnel diffraction integral"
    assert body["wave_optics"]["profile_type"] == "round_super_gaussian"
    assert body["wave_optics"]["super_gaussian_order"] == 6.0
    assert body["wave_optics"]["launch_profile"]["plane_kind"] == "launch"
    assert body["wave_optics"]["center_profiles"]
    assert body["wave_optics"]["center_profiles"][0]["plane_kind"] == "center"
    assert body["wave_optics"]["mirror2_profiles"]
    assert body["wave_optics"]["focus_profiles"]


def test_wave_optics_endpoint_reports_sampling_limit_errors(client) -> None:
    config = load_fixture("default_tem00.json")
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 96,
        "max_memory_mb": 64,
        "display_grid_points": 48,
    }

    response = client.post("/api/simulate-wave-optics", json=config)

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "wave_optics_sampling_error"
    assert "configured limit of 96" in body["error"]["message"]
    assert "at least 256" in body["error"]["message"]


def _wait_for_wave_optics_job(client, job_id: str, timeout_seconds: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    latest_body: dict | None = None
    while time.monotonic() < deadline:
        response = client.get(f"/api/simulate-wave-optics/jobs/{job_id}")
        assert response.status_code == 200
        latest_body = response.json()
        if latest_body["status"] in {"completed", "failed"}:
            return latest_body
        time.sleep(0.01)

    raise AssertionError(f"Wave-optics job {job_id} did not finish within {timeout_seconds} s. Latest={latest_body}")


def test_wave_optics_job_endpoint_reports_progress_and_result(client) -> None:
    config = load_fixture("default_tem00.json")
    config["wave_optics"] = {
        "profile_type": "round_super_gaussian",
        "super_gaussian_order": 6.0,
        "max_grid_points": 256,
        "max_memory_mb": 128,
        "display_grid_points": 48,
    }

    start_response = client.post("/api/simulate-wave-optics/jobs", json=config)

    assert start_response.status_code == 200
    start_body = start_response.json()
    assert start_body["status"] in {"pending", "running"}
    assert 0.0 <= start_body["progress"]["progress_fraction"] <= 1.0
    assert start_body["progress"]["current_step"]

    final_body = _wait_for_wave_optics_job(client, start_body["job_id"])

    assert final_body["status"] == "completed"
    assert final_body["progress"]["progress_fraction"] == 1.0
    assert final_body["progress"]["completed_steps"] == final_body["progress"]["total_steps"]
    assert final_body["progress"]["elapsed_seconds"] >= 0.0
    assert final_body["result"]["wave_optics"]["profile_type"] == "round_super_gaussian"
    assert "error" not in final_body
