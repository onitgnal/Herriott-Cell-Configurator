from __future__ import annotations

from math import isclose

from backend.app.core.wave_optics import AdaptiveWaveOpticsSolver, PlanePlan
from backend.app.schemas.simulation import WaveOpticsSimulationRequest
from backend.app.schemas.simulation import WaveOpticsSettings
from backend.app.services.simulation_service import run_wave_optics_simulation

from tests.helpers import load_fixture


def build_wave_request(**wave_overrides) -> WaveOpticsSimulationRequest:
    config = load_fixture("default_tem00.json")
    config["wave_optics"] = {
        "profile_type": "gaussian",
        "max_grid_points": 160,
        "max_memory_mb": 128,
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


def test_wave_optics_segment_uses_mirror_focus_mirror_path_with_adaptive_window() -> None:
    result = run_wave_optics_simulation(build_wave_request())
    assert result.wave_optics is not None

    segment = result.wave_optics.segments[0]
    assert 0 < segment.focus_distance_mm < result.resolved_inputs.mirror_distance_mm
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
