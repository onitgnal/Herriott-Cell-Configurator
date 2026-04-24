from __future__ import annotations

from fastapi import APIRouter

from backend.app.schemas.simulation import ErrorResponse, SimulationRequest, SimulationResponse
from backend.app.services.simulation_service import run_simulation

router = APIRouter(tags=["simulation"])


@router.post(
    "/api/simulate",
    response_model=SimulationResponse,
    response_model_exclude_none=True,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def simulate(payload: SimulationRequest) -> SimulationResponse:
    return run_simulation(payload)
