from __future__ import annotations

from math import sqrt

import pytest

from backend.app.core.modes import build_mode_config
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


def test_uniform_refractive_index_scales_diffraction_but_not_ray_geometry() -> None:
    vacuum_config = load_fixture("default_tem00.json")
    medium_config = {**vacuum_config, "refractive_index": 1.6}

    vacuum = run_simulation(SimulationRequest.model_validate(vacuum_config))
    medium = run_simulation(SimulationRequest.model_validate(medium_config))

    assert medium.resolved_inputs.wavelength_mm == pytest.approx(vacuum.resolved_inputs.wavelength_mm)
    assert medium.resolved_inputs.wavelength_medium_mm == pytest.approx(
        vacuum.resolved_inputs.wavelength_mm / 1.6,
    )
    assert medium.cavity is not None
    assert vacuum.cavity is not None
    assert medium.cavity.ideal_waist_mm == pytest.approx(vacuum.cavity.ideal_waist_mm / sqrt(1.6))
    assert medium.cavity.mirror1_beam_mm == pytest.approx(vacuum.cavity.mirror1_beam_mm / sqrt(1.6))
    assert medium.ray_trace is not None
    assert vacuum.ray_trace is not None
    assert medium.ray_trace.points == pytest.approx(vacuum.ray_trace.points)


def test_round_trip_count_drives_two_legs_and_continuous_abcd_sampling() -> None:
    config = load_fixture("default_tem00.json")
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.ray_trace is not None
    assert result.beam_propagation is not None
    expected_legs = 2 * config["total_passes"]
    assert result.ray_trace.total_bounces == expected_legs
    assert f"{expected_legs} legs" in result.ray_trace.exit_status
    assert len(result.beam_propagation.x.z_vals) == expected_legs * 20 + 1
    assert result.beam_propagation.x.z_vals[-1] == pytest.approx(expected_legs * config["mirror_distance_mm"])


def test_high_order_mode_normalization_and_lg_sign_symmetry() -> None:
    hg = build_mode_config("hg", 10, 10, 0, 0, 1.0)
    lg_positive = build_mode_config("lg", 0, 0, 3, 4, 1.0)
    lg_negative = build_mode_config("lg", 0, 0, 3, -4, 1.0)

    assert hg.peak_factor == pytest.approx(0.1572138371, rel=1e-6)
    assert hg.norm > 0
    assert lg_positive.norm == pytest.approx(lg_negative.norm)
    assert lg_positive.peak_factor == pytest.approx(lg_negative.peak_factor)
