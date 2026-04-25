from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.schemas.simulation import (
    ErrorResponse,
    SimulationRequest,
    SimulationResponse,
    WaveOpticsJobStatusResponse,
    WaveOpticsSimulationRequest,
)
from backend.app.services.simulation_service import (
    get_wave_optics_job,
    run_simulation,
    run_wave_optics_simulation,
    start_wave_optics_job,
)

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


@router.post(
    "/api/simulate-wave-optics/jobs",
    response_model=WaveOpticsJobStatusResponse,
    response_model_exclude_none=True,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_wave_optics_job(payload: WaveOpticsSimulationRequest) -> WaveOpticsJobStatusResponse:
    return WaveOpticsJobStatusResponse.model_validate(start_wave_optics_job(payload))


@router.get(
    "/api/simulate-wave-optics/jobs/{job_id}",
    response_model=WaveOpticsJobStatusResponse,
    response_model_exclude_none=True,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def read_wave_optics_job(job_id: str) -> WaveOpticsJobStatusResponse | JSONResponse:
    job = get_wave_optics_job(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "wave_optics_job_not_found",
                    "message": f"Wave-optics job '{job_id}' was not found.",
                }
            },
        )
    return WaveOpticsJobStatusResponse.model_validate(job)
