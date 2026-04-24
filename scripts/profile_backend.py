from __future__ import annotations

import argparse
import cProfile
import json
import pstats
from pathlib import Path

from backend.app.schemas.simulation import SimulationRequest
from backend.app.services.simulation_service import run_simulation

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT_DIR / "tests" / "fixtures" / "configs" / "default_tem00.json"


def load_request(path: Path) -> SimulationRequest:
    with path.open("r", encoding="utf-8") as fixture_file:
        return SimulationRequest.model_validate(json.load(fixture_file))


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile backend simulation hot spots.")
    parser.add_argument("--config", type=Path, default=DEFAULT_FIXTURE, help="Path to a simulation request JSON fixture.")
    parser.add_argument("--iterations", type=int, default=100, help="Number of simulation runs.")
    parser.add_argument("--limit", type=int, default=25, help="How many rows to print.")
    args = parser.parse_args()

    request = load_request(args.config)
    profiler = cProfile.Profile()
    profiler.enable()

    for _ in range(args.iterations):
        run_simulation(request)

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("tottime")
    stats.print_stats(args.limit)


if __name__ == "__main__":
    main()
