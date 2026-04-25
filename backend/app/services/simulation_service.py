from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from backend.app.core.simulation import simulate_configuration
from backend.app.core.wave_optics import WaveOpticsSamplingError, compute_wave_optics_result
from backend.app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    WaveOpticsJobStatusResponse,
    WaveOpticsSimulationRequest,
)

TERMINAL_WAVE_OPTICS_JOB_STATES = {"completed", "failed"}
MAX_STORED_WAVE_OPTICS_JOBS = 24


def run_simulation(request: SimulationRequest) -> SimulationResponse:
    return SimulationResponse.model_validate(simulate_configuration(request))


def run_wave_optics_simulation(
    request: WaveOpticsSimulationRequest,
    progress_callback=None,
) -> SimulationResponse:
    result = simulate_configuration(request)
    result["wave_optics"] = compute_wave_optics_result(result, request, progress_callback=progress_callback)
    return SimulationResponse.model_validate(result)


@dataclass(slots=True)
class _WaveOpticsJobRecord:
    job_id: str
    status: str
    progress: dict[str, object]
    result: dict[str, object] | None = None
    error: dict[str, str] | None = None


class _WaveOpticsJobManager:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wave-optics")
        self._lock = Lock()
        self._jobs: dict[str, _WaveOpticsJobRecord] = {}

    def start(self, request: WaveOpticsSimulationRequest) -> dict:
        job_id = uuid4().hex
        record = _WaveOpticsJobRecord(
            job_id=job_id,
            status="pending",
            progress={
                "completed_steps": 0,
                "total_steps": 1,
                "progress_fraction": 0.0,
                "progress_percent": 0.0,
                "current_step": "Queued for wave-optics propagation",
                "current_segment": None,
                "segment_count": None,
                "elapsed_seconds": 0.0,
                "estimated_remaining_seconds": None,
            },
        )
        with self._lock:
            self._jobs[job_id] = record
            self._prune_terminal_jobs_locked()

        self._executor.submit(self._run_job, job_id, request.model_copy(deep=True))
        return self.get(job_id)

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            return self._serialize(record)

    def _run_job(self, job_id: str, request: WaveOpticsSimulationRequest) -> None:
        self._update(job_id, status="running", progress={"current_step": "Starting wave-optics propagation"})
        try:
            result = run_wave_optics_simulation(
                request,
                progress_callback=lambda progress: self._update(job_id, status="running", progress=progress),
            )
        except WaveOpticsSamplingError as exc:
            self._update(
                job_id,
                status="failed",
                error={
                    "code": "wave_optics_sampling_error",
                    "message": str(exc),
                },
            )
            return
        except Exception as exc:
            self._update(
                job_id,
                status="failed",
                error={
                    "code": "internal_error",
                    "message": str(exc),
                },
            )
            return

        current_status = self.get(job_id)
        current_progress = current_status["progress"] if current_status is not None else None
        total_steps = int(current_progress["total_steps"]) if current_progress is not None else 1
        elapsed_seconds = float(current_progress["elapsed_seconds"]) if current_progress is not None else 0.0
        self._update(
            job_id,
            status="completed",
            progress={
                "completed_steps": total_steps,
                "total_steps": total_steps,
                "progress_fraction": 1.0,
                "progress_percent": 100.0,
                "current_step": "Wave-optics propagation completed",
                "elapsed_seconds": elapsed_seconds,
                "estimated_remaining_seconds": 0.0,
            },
            result=result.model_dump(mode="json"),
        )

    def _update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        progress: dict[str, object] | None = None,
        result: dict[str, object] | None = None,
        error: dict[str, str] | None = None,
    ) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return

            if status is not None:
                record.status = status
            if progress is not None:
                record.progress = {
                    **record.progress,
                    **progress,
                }
            if result is not None:
                record.result = result
            if error is not None:
                record.error = error

            if record.status in TERMINAL_WAVE_OPTICS_JOB_STATES:
                self._prune_terminal_jobs_locked()

    def _prune_terminal_jobs_locked(self) -> None:
        terminal_job_ids = [
            job_id
            for job_id, record in self._jobs.items()
            if record.status in TERMINAL_WAVE_OPTICS_JOB_STATES
        ]
        if len(terminal_job_ids) <= MAX_STORED_WAVE_OPTICS_JOBS:
            return
        for job_id in terminal_job_ids[: len(terminal_job_ids) - MAX_STORED_WAVE_OPTICS_JOBS]:
            self._jobs.pop(job_id, None)

    @staticmethod
    def _serialize(record: _WaveOpticsJobRecord) -> dict:
        payload = {
            "job_id": record.job_id,
            "status": record.status,
            "progress": record.progress,
            "result": record.result,
            "error": record.error,
        }
        return WaveOpticsJobStatusResponse.model_validate(payload).model_dump(mode="json")


_wave_optics_job_manager = _WaveOpticsJobManager()


def start_wave_optics_job(request: WaveOpticsSimulationRequest) -> dict:
    return _wave_optics_job_manager.start(request)


def get_wave_optics_job(job_id: str) -> dict | None:
    return _wave_optics_job_manager.get(job_id)
