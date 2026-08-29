from __future__ import annotations

from math import cos, pi, sqrt

import pytest

from backend.app.core.modes import build_mode_config
from backend.app.schemas.simulation import SimulationRequest
from backend.app.services.simulation_service import run_simulation

from tests.helpers import assert_nested_close, load_fixture, run_js_config, run_js_reference, strip_none

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
    python_result.pop("mode_matching", None)
    python_result.pop("external_beam_propagation", None)
    if fixture_name == "tilted_hg_manual.json":
        # The new shared spherical-lens telescope supersedes the legacy direct-at-M1 waist controls.  For an
        # astigmatic HG beam its closest x/y q match is intentionally different; geometry and ray tracing must
        # still retain parity with the old JavaScript reference.
        python_result.pop("beam_propagation", None)
        js_result.pop("beam_propagation", None)
        for key in ("input_waist_x_mm", "input_waist_y_mm", "input_waist_z_mm"):
            python_result["resolved_inputs"].pop(key, None)
            js_result["resolved_inputs"].pop(key, None)

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


def test_cav_vex_auto_r2_preserves_requested_round_trip_phase() -> None:
    config = load_fixture("cav_vex_lg_auto.json")
    config.pop("auto_opposite_radii")
    config.update({"opposite_radius_mode": "auto_r2", "mirror1_radius_mm": 1500.0})

    python_result = strip_none(run_simulation(SimulationRequest.model_validate(config)).model_dump())
    js_result = strip_none(run_js_config(config))
    python_result.pop("mode_matching", None)
    python_result.pop("external_beam_propagation", None)

    assert_nested_close(python_result, js_result)
    target_g_product = cos(pi * config["revolutions"] / config["total_passes"]) ** 2
    assert python_result["resolved_inputs"]["mirror1_radius_mm"] == pytest.approx(1500.0)
    assert python_result["resolved_inputs"]["mirror2_radius_mm"] < 0
    assert python_result["stability"]["product"] == pytest.approx(target_g_product)
    assert python_result["ray_trace"]["total_bounces"] == 2 * config["total_passes"]


def test_legacy_opposite_radius_boolean_maps_to_new_modes() -> None:
    auto_config = load_fixture("cav_vex_lg_auto.json")
    manual_config = {**auto_config, "auto_opposite_radii": False}

    assert SimulationRequest.model_validate(auto_config).opposite_radius_mode == "auto_equal"
    assert SimulationRequest.model_validate(manual_config).opposite_radius_mode == "manual"


def test_auto_mode_matching_selects_standard_lenses_and_matches_the_cavity() -> None:
    config = load_fixture("default_tem00.json")
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.mode_matching is not None
    assert result.mode_matching.success is True
    assert result.mode_matching.relative_q_error < 2e-3
    assert all(focal_length % 25 == 0 for focal_length in result.mode_matching.focal_lengths_mm)
    assert all(distance >= 20 for distance in result.mode_matching.distances_mm[1:])
    assert result.cavity is not None
    assert result.resolved_inputs.input_waist_x_mm == pytest.approx(result.cavity.cavity_waist_x_mm)
    assert result.resolved_inputs.input_waist_z_mm == pytest.approx(result.cavity.waist_position_mm)


def test_fixed_lens_mode_keeps_lenses_and_refits_distances() -> None:
    config = load_fixture("default_tem00.json")
    config.update(
        {
            "mode_matching_mode": "fixed_lenses",
            "lens1_focal_length_mm": 150.0,
            "lens2_focal_length_mm": 250.0,
            "lens3_focal_length_mm": 50.0,
        },
    )
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.mode_matching is not None
    assert result.mode_matching.focal_lengths_mm == pytest.approx([150.0, 250.0, 50.0])
    assert result.mode_matching.distances_mm[0] == pytest.approx(config.get("phase_plate_to_lens1_mm", 25.0))
    assert result.mode_matching.distances_mm[1:] != pytest.approx([175.0, 30.0, 30.0])


def test_fixed_lens_mismatch_launches_the_achieved_q_instead_of_the_ideal_target() -> None:
    config = load_fixture("default_tem00.json")
    config.update(
        {
            "mode_matching_mode": "fixed_lenses",
            "lens1_focal_length_mm": 10_000.0,
            "lens2_focal_length_mm": 10_000.0,
            "lens3_focal_length_mm": 10_000.0,
        },
    )
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.mode_matching is not None
    assert result.mode_matching.success is False
    assert result.mode_matching.relative_q_error > 0.1
    assert result.cavity is not None
    assert result.resolved_inputs.input_waist_x_mm != pytest.approx(result.cavity.cavity_waist_x_mm, rel=1e-2)
    assert result.external_beam_propagation is not None
    assert result.beam_propagation is not None
    assert result.external_beam_propagation.input_section.x.w_vals[-1] == pytest.approx(
        result.beam_propagation.x.w_vals[0],
    )


def test_manual_telescope_propagates_its_actual_q_and_external_sections() -> None:
    config = load_fixture("default_tem00.json")
    config.update(
        {
            "mode_matching_mode": "manual",
            "lens1_focal_length_mm": 100.0,
            "lens2_focal_length_mm": 200.0,
            "lens3_focal_length_mm": 100.0,
            "phase_plate_to_lens1_mm": 25.0,
            "lens1_to_lens2_mm": 100.0,
            "lens2_to_lens3_mm": 100.0,
            "lens3_to_mirror1_mm": 100.0,
            "output_propagation_mm": 750.0,
        },
    )
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.mode_matching is not None
    assert result.mode_matching.mode == "manual"
    assert result.mode_matching.relative_q_error > 1e-3
    assert result.cavity is not None
    assert result.resolved_inputs.input_waist_x_mm != pytest.approx(result.cavity.cavity_waist_x_mm)
    assert result.external_beam_propagation is not None
    assert result.external_beam_propagation.input_section.x.z_vals[0] < 0
    expected_cell_end = 2 * config["total_passes"] * config["mirror_distance_mm"]
    assert result.external_beam_propagation.output_section.x.z_vals[0] == pytest.approx(expected_cell_end)
    assert result.external_beam_propagation.output_section.x.z_vals[-1] == pytest.approx(expected_cell_end + 750.0)


def test_out_coupling_section_starts_at_the_actual_exit_leg() -> None:
    config = load_fixture("default_tem00.json")
    config.update(
        {
            "auto_output_hole": False,
            "output_mirror": 2,
            "output_hole_x_mm": 0.0,
            "output_hole_y_mm": 0.0,
            "hole_radius_mm": 1_000.0,
        },
    )
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.ray_trace is not None
    assert result.ray_trace.total_bounces == 1
    assert result.external_beam_propagation is not None
    assert result.external_beam_propagation.cell_output_position_mm == pytest.approx(config["mirror_distance_mm"])
    assert result.external_beam_propagation.output_section.x.z_vals[0] == pytest.approx(config["mirror_distance_mm"])


def test_failed_first_leg_keeps_the_external_output_origin_at_m1() -> None:
    result = run_simulation(
        SimulationRequest(
            auto_injection=False,
            input_x_mm=10_000.0,
            input_y_mm=0.0,
            input_theta_x_mrad=0.0,
            input_theta_y_mrad=0.0,
        ),
    )

    assert result.ray_trace is not None
    assert result.ray_trace.total_bounces == 0
    assert result.external_beam_propagation is not None
    assert result.external_beam_propagation.cell_output_position_mm == pytest.approx(0.0)


def test_mode_matching_accounts_for_planar_air_to_cell_index_transition() -> None:
    config = {**load_fixture("default_tem00.json"), "refractive_index": 1.5}
    result = run_simulation(SimulationRequest.model_validate(config))

    assert result.mode_matching is not None
    assert result.cavity is not None
    assert result.mode_matching.target_q_air_real_mm == pytest.approx(-result.cavity.waist_position_mm / 1.5)
    assert result.mode_matching.target_q_air_imag_mm == pytest.approx(result.cavity.rayleigh_range_mm / 1.5)
