from __future__ import annotations

from backend.app.core.simulation import simulate_configuration
from backend.app.schemas.simulation import SimulationRequest, SimulationResponse


def run_simulation(request: SimulationRequest) -> SimulationResponse:
    return SimulationResponse.model_validate(simulate_configuration(request))
