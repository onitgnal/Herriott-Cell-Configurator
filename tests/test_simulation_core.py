from __future__ import annotations

import pytest

from backend.app.schemas.simulation import SimulationRequest
from backend.app.services.simulation_service import run_simulation

from tests.helpers import assert_nested_close, load_fixture, run_js_reference, strip_none

REFERENCE_CASES = [
    "default_tem00.json",
    "tilted_hg_manual.json",
    "cav_vex_lg_auto.json",
    "dual_beam_manual.json",
]


@pytest.mark.parametrize("fixture_name", REFERENCE_CASES)
def test_python_core_matches_js_reference(fixture_name: str) -> None:
    config = load_fixture(fixture_name)
    python_result = strip_none(run_simulation(SimulationRequest.model_validate(config)).model_dump())
    js_result = strip_none(run_js_reference(fixture_name))

    assert_nested_close(python_result, js_result)


def test_unstable_configuration_short_circuits_heavy_outputs() -> None:
    config = load_fixture("unstable_manual.json")
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.stable is False
    assert result.cavity is None
    assert result.ray_trace is None
    assert result.secondary_ray_trace is None
    assert result.beam_propagation is None
    assert result.status_message == "Stability Error (g1g2 bounds)"


def test_second_beam_returns_independent_trace() -> None:
    config = load_fixture("dual_beam_manual.json")
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.secondary_ray_trace is not None
    assert result.resolved_inputs.second_beam_enabled is True
    assert result.secondary_ray_trace.input_point[0] == pytest.approx(config["second_input_x_mm"])
    assert result.secondary_ray_trace.input_point[1] == pytest.approx(config["second_input_y_mm"])
    assert result.ray_trace.input_point[:2] != result.secondary_ray_trace.input_point[:2]
    assert len(result.secondary_ray_trace.points) > 1
