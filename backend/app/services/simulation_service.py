from __future__ import annotations

from backend.app.core.simulation import simulate_configuration
from backend.app.core.wave_optics import compute_wave_optics_result
from backend.app.schemas.simulation import SimulationRequest, SimulationResponse, WaveOpticsSimulationRequest


def run_simulation(request: SimulationRequest) -> SimulationResponse:
    return SimulationResponse.model_validate(simulate_configuration(request))


def run_wave_optics_simulation(request: WaveOpticsSimulationRequest) -> SimulationResponse:
    result = simulate_configuration(request)
    result["wave_optics"] = compute_wave_optics_result(result, request)
    return SimulationResponse.model_validate(result)
