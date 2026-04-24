from __future__ import annotations

import pytest

from backend.app.schemas.simulation import SimulationRequest
from backend.app.services.simulation_service import run_simulation

from tests.helpers import assert_nested_close, load_fixture, run_js_reference, strip_none

REFERENCE_CASES = [
    "default_tem00.json",
    "tilted_hg_manual.json",
    "cav_vex_lg_auto.json",
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
    assert result.beam_propagation is None
    assert result.status_message == "Stability Error (g1g2 bounds)"
