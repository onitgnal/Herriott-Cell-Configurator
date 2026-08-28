from __future__ import annotations

from math import isclose, sqrt

import numpy as np

from backend.app.core.wave_optics import (
    AdaptiveWaveOpticsSolver,
    PlanePlan,
    _launch_profile_grid_factors,
    _plan_planes,
    _segment_states,
)
from backend.app.schemas.simulation import WaveOpticsSimulationRequest
from backend.app.schemas.simulation import WaveOpticsSettings
from backend.app.services.simulation_service import run_simulation, run_wave_optics_simulation

from tests.helpers import load_fixture


def build_wave_request(**wave_overrides) -> WaveOpticsSimulationRequest:
    config = load_fixture("default_tem00.json")
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 256,
        "max_memory_mb": 128,
        "display_grid_points": 48,
        **wave_overrides,
    }
    return WaveOpticsSimulationRequest.model_validate(config)


def build_cav_vex_wave_request(**wave_overrides) -> WaveOpticsSimulationRequest:
    config = load_fixture("cav_vex_lg_auto.json")
    config["mode_type"] = "tem00"
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 640,
        "max_memory_mb": 192,
        "display_grid_points": 48,
        **wave_overrides,
    }
    return WaveOpticsSimulationRequest.model_validate(config)


def test_gaussian_wave_optics_matches_abcd_mirror_radii() -> None:
    result = run_wave_optics_simulation(build_wave_request())
    assert result.wave_optics is not None

    launch_expected_x = result.beam_propagation.x.w_mirrors_w[0]
    launch_expected_y = result.beam_propagation.y.w_mirrors_w[0]
    assert isclose(result.wave_optics.launch_profile.equivalent_radius_x_mm, launch_expected_x, rel_tol=1e-6, abs_tol=1e-8)
    assert isclose(result.wave_optics.launch_profile.equivalent_radius_y_mm, launch_expected_y, rel_tol=1e-6, abs_tol=1e-8)

    for index, frame in enumerate(result.wave_optics.mirror2_profiles):
        waist_index = (2 * index) + 1
        assert isclose(
            frame.equivalent_radius_x_mm,
            result.beam_propagation.x.w_mirrors_w[waist_index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )
        assert isclose(
            frame.equivalent_radius_y_mm,
            result.beam_propagation.y.w_mirrors_w[waist_index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )

    for index, frame in enumerate(result.wave_optics.mirror1_profiles):
        waist_index = (2 * index) + 2
        assert isclose(
            frame.equivalent_radius_x_mm,
            result.beam_propagation.x.w_mirrors_w[waist_index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )
        assert isclose(
            frame.equivalent_radius_y_mm,
            result.beam_propagation.y.w_mirrors_w[waist_index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )

    for index, frame in enumerate(result.wave_optics.center_profiles):
        assert frame.plane_kind == "center"
        assert isclose(
            frame.equivalent_radius_x_mm,
            result.beam_propagation.x.w_center_w[index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )
        assert isclose(
            frame.equivalent_radius_y_mm,
            result.beam_propagation.y.w_center_w[index],
            rel_tol=1e-6,
            abs_tol=1e-8,
        )


def test_wave_optics_uses_the_in_medium_wavelength() -> None:
    request = build_wave_request().model_copy(update={"refractive_index": 1.5})
    result = run_wave_optics_simulation(request)

    assert result.wave_optics is not None
    assert result.resolved_inputs.wavelength_medium_mm == result.resolved_inputs.wavelength_mm / 1.5
    assert isclose(
        result.wave_optics.mirror2_profiles[0].equivalent_radius_x_mm,
        result.beam_propagation.x.w_mirrors_w[1],
        rel_tol=1e-6,
        abs_tol=1e-8,
    )


def test_wave_optics_segment_uses_mirror_focus_mirror_path_with_adaptive_window() -> None:
    result = run_wave_optics_simulation(build_wave_request())
    assert result.wave_optics is not None

    segment = result.wave_optics.segments[0]
    assert segment.propagation_mode == "split_focus"
    assert segment.focus_distance_mm is not None
    assert 0 < segment.focus_distance_mm < result.resolved_inputs.mirror_distance_mm
    assert segment.focus_grid is not None
    assert segment.focus_radius_x_mm is not None
    assert segment.center_grid.half_width_x_mm >= segment.focus_grid.half_width_x_mm
    assert segment.focus_radius_x_mm < segment.start_radius_x_mm
    assert segment.focus_radius_x_mm < segment.end_radius_x_mm
    assert segment.focus_grid.half_width_x_mm < segment.start_grid.half_width_x_mm
    assert segment.focus_grid.half_width_x_mm < segment.end_grid.half_width_x_mm
    assert isclose(result.wave_optics.focus_profiles[0].power_fraction, 1.0, rel_tol=1e-6, abs_tol=1e-8)
    assert isclose(result.wave_optics.mirror2_profiles[0].power_fraction, 1.0, rel_tol=1e-6, abs_tol=1e-8)


def test_super_gaussian_profile_propagates_as_distinct_launch_shape() -> None:
    gaussian_result = run_wave_optics_simulation(build_wave_request(profile_type="gaussian"))
    super_gaussian_result = run_wave_optics_simulation(
        build_wave_request(profile_type="super_gaussian", super_gaussian_order=6.0),
    )

    assert gaussian_result.wave_optics is not None
    assert super_gaussian_result.wave_optics is not None
    assert super_gaussian_result.wave_optics.profile_type == "super_gaussian"
    assert super_gaussian_result.wave_optics.super_gaussian_order == 6.0
    assert (
        super_gaussian_result.wave_optics.launch_profile.peak_density_per_mm2
        < gaussian_result.wave_optics.launch_profile.peak_density_per_mm2
    )


def test_round_super_gaussian_is_radially_symmetric_for_astigmatic_input_radii() -> None:
    settings = WaveOpticsSettings(
        profile_type="round_super_gaussian",
        super_gaussian_order=6.0,
        display_grid_points=48,
    )
    solver = AdaptiveWaveOpticsSolver(1030e-6, settings)
    plan = PlanePlan(
        half_width_x_mm=6.0,
        half_width_y_mm=6.0,
        nx=128,
        ny=128,
        dx_mm=(12.0 / 127.0),
        dy_mm=(12.0 / 127.0),
        predicted_radius_x_mm=0.8,
        predicted_radius_y_mm=1.4,
    )
    field, grid = solver.build_launch_field(
        plan,
        "round_super_gaussian",
        6.0,
        0.8,
        1.4,
        float("inf"),
        float("inf"),
    )
    round_summary = solver.summarize_field(
        field,
        grid,
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        "launch",
        1,
        0,
        0,
        "In",
    )

    separable_field, separable_grid = solver.build_launch_field(
        plan,
        "super_gaussian",
        6.0,
        0.8,
        1.4,
        float("inf"),
        float("inf"),
    )
    separable_summary = solver.summarize_field(
        separable_field,
        separable_grid,
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        "launch",
        1,
        0,
        0,
        "In",
    )

    assert isclose(
        round_summary["equivalent_radius_x_mm"],
        round_summary["equivalent_radius_y_mm"],
        rel_tol=1e-6,
        abs_tol=1e-8,
    )
    assert not isclose(
        separable_summary["equivalent_radius_x_mm"],
        separable_summary["equivalent_radius_y_mm"],
        rel_tol=1e-2,
        abs_tol=1e-3,
    )
    assert round_summary["peak_density_per_mm2"] != separable_summary["peak_density_per_mm2"]


def test_laguerre_gaussian_p0_l0_matches_the_gaussian_launch_field() -> None:
    settings = WaveOpticsSettings(profile_type="laguerre_gaussian", laguerre_p=0, laguerre_l=0)
    solver = AdaptiveWaveOpticsSolver(1030e-6, settings)
    plan = PlanePlan(
        half_width_x_mm=5.0,
        half_width_y_mm=5.0,
        nx=193,
        ny=193,
        dx_mm=10.0 / 192.0,
        dy_mm=10.0 / 192.0,
        predicted_radius_x_mm=1.0,
        predicted_radius_y_mm=1.0,
    )

    gaussian_field, _ = solver.build_launch_field(
        plan,
        "gaussian",
        4.0,
        1.0,
        1.0,
        float("inf"),
        float("inf"),
    )
    lg_field, _ = solver.build_launch_field(
        plan,
        "laguerre_gaussian",
        4.0,
        1.0,
        1.0,
        float("inf"),
        float("inf"),
        0,
        0,
    )

    assert np.allclose(lg_field, gaussian_field, rtol=1e-13, atol=1e-13)


def test_laguerre_gaussian_uses_radial_polynomial_and_signed_helical_phase() -> None:
    settings = WaveOpticsSettings(profile_type="laguerre_gaussian", laguerre_p=2, laguerre_l=2)
    solver = AdaptiveWaveOpticsSolver(1030e-6, settings)
    plan = PlanePlan(
        half_width_x_mm=8.0,
        half_width_y_mm=8.0,
        nx=257,
        ny=257,
        dx_mm=16.0 / 256.0,
        dy_mm=16.0 / 256.0,
        predicted_radius_x_mm=sqrt(7.0),
        predicted_radius_y_mm=sqrt(7.0),
    )
    common_arguments = (
        plan,
        "laguerre_gaussian",
        4.0,
        1.0,
        1.0,
        float("inf"),
        float("inf"),
        2,
    )
    positive_field, grid = solver.build_launch_field(*common_arguments, 2)
    negative_field, _ = solver.build_launch_field(*common_arguments, -2)

    assert np.allclose(np.abs(positive_field) ** 2, np.abs(negative_field) ** 2, rtol=1e-13, atol=1e-13)
    assert np.allclose(negative_field, np.conjugate(positive_field), rtol=1e-13, atol=1e-13)
    assert abs(positive_field[128, 128]) < 1e-14

    summary = solver.summarize_field(
        positive_field,
        grid,
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        "launch",
        1,
        0,
        0,
        "In",
    )
    assert isclose(summary["equivalent_radius_x_mm"], sqrt(7.0), rel_tol=1e-8, abs_tol=1e-10)
    assert isclose(summary["equivalent_radius_y_mm"], sqrt(7.0), rel_tol=1e-8, abs_tol=1e-10)


def test_laguerre_gaussian_profile_propagates_with_mode_aware_adaptive_windows() -> None:
    result = run_wave_optics_simulation(
        build_wave_request(
            profile_type="laguerre_gaussian",
            laguerre_p=0,
            laguerre_l=-1,
            max_grid_points=512,
            max_memory_mb=256,
        ),
    )
    assert result.wave_optics is not None

    wave_optics = result.wave_optics
    expected_launch_radius = result.beam_propagation.x.w_mirrors_w[0] * sqrt(2.0)
    assert wave_optics.profile_type == "laguerre_gaussian"
    assert wave_optics.super_gaussian_order is None
    assert wave_optics.laguerre_p == 0
    assert wave_optics.laguerre_l == -1
    assert isclose(wave_optics.launch_profile.equivalent_radius_x_mm, expected_launch_radius, rel_tol=1e-8)
    assert isclose(wave_optics.segments[0].start_grid.predicted_radius_x_mm, expected_launch_radius, rel_tol=1e-12)


def test_scaled_fft_collins_transform_matches_dense_integral_on_unequal_grids() -> None:
    solver = AdaptiveWaveOpticsSolver(1030e-6, WaveOpticsSettings())
    input_plan = PlanePlan(
        half_width_x_mm=2.0,
        half_width_y_mm=3.0,
        nx=32,
        ny=40,
        dx_mm=4.0 / 31.0,
        dy_mm=6.0 / 39.0,
        predicted_radius_x_mm=1.0,
        predicted_radius_y_mm=1.0,
    )
    output_plan = PlanePlan(
        half_width_x_mm=4.0,
        half_width_y_mm=2.5,
        nx=641,
        ny=35,
        dx_mm=8.0 / 640.0,
        dy_mm=5.0 / 34.0,
        predicted_radius_x_mm=1.0,
        predicted_radius_y_mm=1.0,
    )
    input_grid = solver.grid(input_plan)
    random = np.random.default_rng(7)
    field = random.normal(size=(input_plan.nx, input_plan.ny)) + 1j * random.normal(
        size=(input_plan.nx, input_plan.ny),
    )

    dense = solver._propagate_dense(field, input_grid, output_plan, 1000.0)
    scaled_fft, _ = solver.propagate(field, input_grid, output_plan, 1000.0)

    assert solver.propagation_backends_used == {"scaled_fft"}
    assert np.allclose(scaled_fft, dense, rtol=1e-11, atol=1e-11)


def test_lg20_20_plans_within_the_hybrid_solver_limit() -> None:
    request = build_wave_request(
        profile_type="laguerre_gaussian",
        laguerre_p=20,
        laguerre_l=20,
        max_grid_points=2048,
        max_memory_mb=1024,
    )
    result = run_simulation(request)
    assert result.ray_trace is not None
    resolved = result.resolved_inputs
    states = _segment_states(
        resolved.mirror_distance_mm,
        resolved.mirror1_radius_mm,
        resolved.mirror2_radius_mm,
        resolved.wavelength_medium_mm,
        resolved.input_waist_x_mm,
        resolved.input_waist_y_mm,
        resolved.input_waist_z_mm,
        len(result.ray_trace.points) - 1,
        result.mode.M2x,
        result.mode.M2y,
    )
    window_factor, radius_factor = _launch_profile_grid_factors(request.wave_optics)
    mirror_plans, focus_plans, center_plans = _plan_planes(
        states,
        resolved.mirror_distance_mm,
        resolved.wavelength_medium_mm,
        request.wave_optics,
        window_factor,
        radius_factor,
    )

    all_plans = [*mirror_plans, *center_plans, *(plan for plan in focus_plans if plan is not None)]
    assert max(max(plan.nx, plan.ny) for plan in all_plans) <= 2048
    assert radius_factor == sqrt(61.0)
    assert mirror_plans[0].half_width_x_mm < 2 * mirror_plans[0].predicted_radius_x_mm


def test_moderately_high_lg_mode_uses_scaled_fft_without_sampling_warnings() -> None:
    result = run_wave_optics_simulation(
        build_wave_request(
            profile_type="laguerre_gaussian",
            laguerre_p=5,
            laguerre_l=5,
            max_grid_points=2048,
            max_memory_mb=1024,
        ),
    )
    assert result.wave_optics is not None
    assert result.wave_optics.propagation_backends == ["scaled_fft"]
    assert result.wave_optics.warnings == []
    assert result.wave_optics.launch_profile.edge_power_fraction < 1e-8
    assert isclose(result.wave_optics.center_profiles[0].power_fraction, 1.0, rel_tol=1e-6, abs_tol=1e-8)
    assert isclose(result.wave_optics.mirror2_profiles[0].power_fraction, 1.0, rel_tol=1e-6, abs_tol=1e-8)
    assert all(
        frame.power_fraction <= 1.0 + 1e-6
        for frame in [*result.wave_optics.mirror1_profiles, *result.wave_optics.mirror2_profiles]
    )


def test_wave_optics_reports_guard_band_pressure() -> None:
    result = run_wave_optics_simulation(
        build_wave_request(
            profile_type="super_gaussian",
            super_gaussian_order=6.0,
            window_safety_factor=2.5,
            max_grid_points=192,
        ),
    )
    assert result.wave_optics is not None
    assert result.wave_optics.warnings
    assert any("guard band" in warning for warning in result.wave_optics.warnings)


def test_cav_vex_wave_optics_uses_direct_segments_without_forced_focus() -> None:
    result = run_wave_optics_simulation(build_cav_vex_wave_request())
    assert result.wave_optics is not None

    assert result.wave_optics.focus_profiles == []
    assert len(result.wave_optics.center_profiles) == len(result.wave_optics.segments)
    assert result.wave_optics.mirror1_profiles
    assert result.wave_optics.mirror2_profiles
    assert all(segment.propagation_mode == "direct" for segment in result.wave_optics.segments)
    assert all(segment.focus_distance_mm is None for segment in result.wave_optics.segments)
    assert all(segment.focus_grid is None for segment in result.wave_optics.segments)
    assert all(segment.focus_radius_x_mm is None for segment in result.wave_optics.segments)
    assert all(frame.plane_kind == "center" for frame in result.wave_optics.center_profiles)


def test_wave_optics_is_not_fabricated_for_analytic_higher_order_modes() -> None:
    config = load_fixture("cav_vex_lg_auto.json")
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 256,
        "max_memory_mb": 128,
        "display_grid_points": 48,
    }

    result = run_wave_optics_simulation(WaveOpticsSimulationRequest.model_validate(config))

    assert result.stable is True
    assert result.mode.type == "lg"
    assert result.wave_optics is None


def test_manual_launch_phase_matches_abcd_without_a_fictitious_first_mirror() -> None:
    config = load_fixture("default_tem00.json")
    config.update(
        {
            "mirror_distance_mm": 1000.0,
            "auto_symmetric_radius": False,
            "symmetric_radius_mm": 2000.0,
            "auto_mode_match": False,
            "input_waist_x_mm": 0.5,
            "input_waist_y_mm": 0.5,
            "input_waist_z_mm": 200.0,
            "auto_injection": False,
            "input_x_mm": 0.0,
            "input_y_mm": 0.0,
            "input_theta_x_mrad": 0.0,
            "input_theta_y_mrad": 0.0,
            "auto_output_hole": False,
            "output_mirror": 2,
            "output_hole_x_mm": 0.0,
            "output_hole_y_mm": 0.0,
            "hole_radius_mm": 0.0,
            "total_passes": 2,
            "revolutions": 1,
        },
    )
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 512,
        "max_memory_mb": 192,
        "display_grid_points": 48,
    }

    result = run_wave_optics_simulation(WaveOpticsSimulationRequest.model_validate(config))

    assert result.wave_optics is not None
    assert isclose(
        result.wave_optics.launch_profile.equivalent_radius_x_mm,
        result.beam_propagation.x.w_mirrors_w[0],
        rel_tol=1e-6,
        abs_tol=1e-8,
    )
    assert isclose(
        result.wave_optics.mirror2_profiles[0].equivalent_radius_x_mm,
        result.beam_propagation.x.w_mirrors_w[1],
        rel_tol=1e-6,
        abs_tol=1e-8,
    )
