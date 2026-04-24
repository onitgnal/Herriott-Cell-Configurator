from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.simulation import ErrorResponse, SimulationRequest, SimulationResponse, WaveOpticsSimulationRequest
from backend.app.services.simulation_service import run_simulation, run_wave_optics_simulation

router = APIRouter(tags=["simulation"])


@router.post(
    "/api/simulate",
    response_model=SimulationResponse,
    response_model_exclude_none=True,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def simulate(payload: SimulationRequest) -> SimulationResponse:
    return run_simulation(payload)


@router.post(
    "/api/simulate-wave-optics",
    response_model=SimulationResponse,
    response_model_exclude_none=True,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def simulate_wave_optics(payload: WaveOpticsSimulationRequest) -> SimulationResponse:
    return run_wave_optics_simulation(payload)
