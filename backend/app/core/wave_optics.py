from __future__ import annotations

from dataclasses import dataclass
from math import ceil, inf, pi, sqrt
from typing import Any

import numpy as np

from backend.app.core.math_utils import v_dot, v_sub
from backend.app.schemas.simulation import WaveOpticsSettings

EPSILON = 1e-9
SPECTRAL_WARNING_THRESHOLD = 5e-3
EDGE_WARNING_THRESHOLD = 5e-3
FAST_GRID_SIZES = (
    32,
    40,
    48,
    56,
    64,
    72,
    80,
    96,
    112,
    128,
    144,
    160,
    192,
    224,
    256,
    320,
    384,
    448,
    512,
    640,
    768,
    896,
    1024,
)


class WaveOpticsSamplingError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PlanePlan:
    half_width_x_mm: float
    half_width_y_mm: float
    nx: int
    ny: int
    dx_mm: float
    dy_mm: float
    predicted_radius_x_mm: float
    predicted_radius_y_mm: float


@dataclass(frozen=True, slots=True)
class SegmentState:
    segment_index: int
    start_mirror: int
    end_mirror: int
    focus_distance_mm: float
    focus_boundary_warning: str | None
    start_q_x: complex
    start_q_y: complex
    end_q_x: complex
    end_q_y: complex
    reflected_q_x: complex
    reflected_q_y: complex
    start_radius_x_mm: float
    start_radius_y_mm: float
    focus_radius_x_mm: float
    focus_radius_y_mm: float
    end_radius_x_mm: float
    end_radius_y_mm: float
    start_curvature_x_mm: float
    start_curvature_y_mm: float
    focus_curvature_x_mm: float
    focus_curvature_y_mm: float
    end_curvature_x_mm: float
    end_curvature_y_mm: float
    reflected_curvature_x_mm: float
    reflected_curvature_y_mm: float


@dataclass(frozen=True, slots=True)
class FieldGrid:
    x_mm: np.ndarray
    y_mm: np.ndarray
    dx_mm: float
    dy_mm: float
    half_width_x_mm: float
    half_width_y_mm: float


def _reflect(vector: tuple[float, float, float], normal: tuple[float, float, float]) -> tuple[float, float, float]:
    scale = 2 * v_dot(vector, normal)
    return (
        vector[0] - scale * normal[0],
        vector[1] - scale * normal[1],
        vector[2] - scale * normal[2],
    )


def _q_from_waist(waist_mm: float, waist_position_mm: float, wavelength_mm: float, m2: float) -> complex:
    rayleigh_range_mm = (pi * waist_mm * waist_mm) / (m2 * wavelength_mm)
    return complex(-waist_position_mm, rayleigh_range_mm)


def _propagate_q(q_value: complex, distance_mm: float) -> complex:
    return q_value + distance_mm


def _mirror_q(q_value: complex, mirror_radius_mm: float) -> complex:
    return q_value / (1 - (2 * q_value) / mirror_radius_mm)


def _beam_radius_mm(q_value: complex | np.ndarray, wavelength_mm: float, m2: float) -> float | np.ndarray:
    inverse_q = 1.0 / q_value
    curvature_term = np.maximum(-inverse_q.imag, 1e-18)
    return np.sqrt((m2 * wavelength_mm) / (pi * curvature_term))


def _curvature_radius_mm(q_value: complex) -> float:
    inverse_q = 1.0 / q_value
    if abs(inverse_q.real) <= EPSILON:
        return inf
    return 1.0 / inverse_q.real


def _find_focus_distance_mm(
    q_x: complex,
    q_y: complex,
    distance_mm: float,
    wavelength_mm: float,
    m2_x: float,
    m2_y: float,
) -> tuple[float, str | None]:
    sample_count = 513
    z_samples = np.linspace(0.0, distance_mm, sample_count)
    area_samples = _beam_radius_mm(q_x + z_samples, wavelength_mm, m2_x) * _beam_radius_mm(
        q_y + z_samples,
        wavelength_mm,
        m2_y,
    )
    focus_index = int(np.argmin(area_samples))
    focus_distance_mm = float(z_samples[focus_index])
    clamp_margin_mm = max(distance_mm * 1e-3, 1e-4)
    warning: str | None = None

    if focus_distance_mm <= clamp_margin_mm or focus_distance_mm >= distance_mm - clamp_margin_mm:
        focus_distance_mm = min(max(focus_distance_mm, clamp_margin_mm), distance_mm - clamp_margin_mm)
        warning = (
            "The minimum-area ABCD plane collapsed onto a mirror. "
            "The adaptive solver clamped the internal focus plane to keep the two-step propagation well-posed."
        )

    return focus_distance_mm, warning


def _efficient_grid_size(required_points: int, max_grid_points: int) -> int:
    for size in FAST_GRID_SIZES:
        if size >= required_points and size <= max_grid_points:
            return size
    if required_points <= max_grid_points:
        return required_points
    raise WaveOpticsSamplingError(
        f"Wave-optics sampling would require {required_points} points on one axis, exceeding the configured "
        f"limit of {max_grid_points}. Increase the grid limit or relax the sampling margins.",
    )


def _plane_half_width_mm(radius_mm: float, settings: WaveOpticsSettings) -> float:
    return max(settings.window_safety_factor * radius_mm, radius_mm * 1.5, 0.05)


def _dx_from_curvature(curvature_mm: float, half_width_mm: float, wavelength_mm: float, margin: float) -> float:
    if curvature_mm == inf or abs(curvature_mm) <= EPSILON:
        return inf
    return margin * wavelength_mm * abs(curvature_mm) / (2 * half_width_mm)


def _dx_from_kernel(distance_mm: float, opposite_half_width_mm: float, wavelength_mm: float, margin: float) -> float:
    return margin * wavelength_mm * distance_mm / (2 * opposite_half_width_mm)


def _grid_requirement_points(half_width_mm: float, dx_limit_mm: float) -> int:
    return max(32, int(ceil((2 * half_width_mm) / dx_limit_mm)) + 1)


def _estimate_segment_memory_bytes(start: PlanePlan, focus: PlanePlan, end: PlanePlan) -> int:
    complex_bytes = 16
    float_bytes = 8
    field_bytes = complex_bytes * (
        (start.nx * start.ny) + (focus.nx * focus.ny) + (end.nx * end.ny)
    )
    kernel_bytes = complex_bytes * (
        (start.nx * focus.nx)
        + (start.ny * focus.ny)
        + (focus.nx * end.nx)
        + (focus.ny * end.ny)
    )
    diagnostic_bytes = float_bytes * ((focus.nx * focus.ny) + (end.nx * end.ny))
    return field_bytes + kernel_bytes + diagnostic_bytes


def _normalize_field(field: np.ndarray, grid: FieldGrid) -> np.ndarray:
    power = float(np.sum(np.abs(field) ** 2) * grid.dx_mm * grid.dy_mm)
    if power <= EPSILON:
        raise WaveOpticsSamplingError("The generated launch field has zero power on the adaptive grid.")
    return field / sqrt(power)


class AdaptiveWaveOpticsSolver:
    def __init__(self, wavelength_mm: float, settings: WaveOpticsSettings) -> None:
        self.wavelength_mm = wavelength_mm
        self.settings = settings
        self.wave_number_mm = (2 * pi) / wavelength_mm
        self._axis_cache: dict[tuple[int, float], tuple[np.ndarray, float]] = {}
        self._kernel_cache: dict[tuple[float, int, float, int, float], np.ndarray] = {}

    def _axis_coordinates(self, points: int, half_width_mm: float) -> tuple[np.ndarray, float]:
        key = (points, round(half_width_mm, 9))
        cached = self._axis_cache.get(key)
        if cached is not None:
            return cached
        coordinates = np.linspace(-half_width_mm, half_width_mm, points, dtype=np.float64)
        spacing = float(coordinates[1] - coordinates[0])
        coordinates.setflags(write=False)
        self._axis_cache[key] = (coordinates, spacing)
        return coordinates, spacing

    def grid(self, plan: PlanePlan) -> FieldGrid:
        x_mm, dx_mm = self._axis_coordinates(plan.nx, plan.half_width_x_mm)
        y_mm, dy_mm = self._axis_coordinates(plan.ny, plan.half_width_y_mm)
        return FieldGrid(
            x_mm=x_mm,
            y_mm=y_mm,
            dx_mm=dx_mm,
            dy_mm=dy_mm,
            half_width_x_mm=plan.half_width_x_mm,
            half_width_y_mm=plan.half_width_y_mm,
        )

    def _collins_kernel(
        self,
        in_points: int,
        in_half_width_mm: float,
        out_points: int,
        out_half_width_mm: float,
        distance_mm: float,
    ) -> np.ndarray:
        key = (
            round(distance_mm, 9),
            in_points,
            round(in_half_width_mm, 9),
            out_points,
            round(out_half_width_mm, 9),
        )
        cached = self._kernel_cache.get(key)
        if cached is not None:
            return cached

        x_in, dx_in = self._axis_coordinates(in_points, in_half_width_mm)
        x_out, _ = self._axis_coordinates(out_points, out_half_width_mm)
        x_in_squared = x_in * x_in
        x_out_squared = x_out * x_out
        cross_term = np.outer(x_out, x_in)

        # Collins/Fresnel sign convention for exp(-iwt):
        # U2(x2) = 1/sqrt(i lambda B) * exp(i k x2^2 / 2B) *
        #          ∫ U1(x1) exp(i k x1^2 / 2B) exp(-i k x1 x2 / B) dx1
        kernel = (
            (1.0 / np.sqrt(1j * self.wavelength_mm * distance_mm))
            * np.exp(
                1j
                * self.wave_number_mm
                / (2 * distance_mm)
                * (x_out_squared[:, None] + x_in_squared[None, :] - 2 * cross_term),
            )
            * dx_in
        )
        kernel.setflags(write=False)
        self._kernel_cache[key] = kernel
        return kernel

    def propagate(self, field: np.ndarray, in_grid: FieldGrid, out_plan: PlanePlan, distance_mm: float) -> tuple[np.ndarray, FieldGrid]:
        out_grid = self.grid(out_plan)
        kernel_x = self._collins_kernel(
            field.shape[0],
            in_grid.half_width_x_mm,
            out_plan.nx,
            out_plan.half_width_x_mm,
            distance_mm,
        )
        kernel_y = self._collins_kernel(
            field.shape[1],
            in_grid.half_width_y_mm,
            out_plan.ny,
            out_plan.half_width_y_mm,
            distance_mm,
        )
        propagated = kernel_x @ field @ kernel_y.T
        return propagated, out_grid

    def build_launch_field(
        self,
        plan: PlanePlan,
        profile_type: str,
        super_gaussian_order: float,
        radius_x_mm: float,
        radius_y_mm: float,
        curvature_x_mm: float,
        curvature_y_mm: float,
    ) -> tuple[np.ndarray, FieldGrid]:
        grid = self.grid(plan)
        x_grid = grid.x_mm[:, None]
        y_grid = grid.y_mm[None, :]

        if profile_type == "super_gaussian":
            amplitude = np.exp(-((np.abs(x_grid) / radius_x_mm) ** (2 * super_gaussian_order))) * np.exp(
                -((np.abs(y_grid) / radius_y_mm) ** (2 * super_gaussian_order)),
            )
        elif profile_type == "round_super_gaussian":
            # Use the geometric-mean beam radius so the round launch profile keeps the same first-order area scale
            # as the existing x/y beam conventions while remaining radially symmetric in the transverse plane.
            round_radius_mm = sqrt(radius_x_mm * radius_y_mm)
            radial_coordinate = np.sqrt((x_grid * x_grid) + (y_grid * y_grid))
            amplitude = np.exp(-((radial_coordinate / round_radius_mm) ** (2 * super_gaussian_order)))
        else:
            amplitude = np.exp(-((x_grid / radius_x_mm) ** 2) - ((y_grid / radius_y_mm) ** 2))

        phase = np.ones_like(amplitude, dtype=np.complex128)
        if curvature_x_mm != inf:
            phase *= np.exp(-0.5j * self.wave_number_mm * (x_grid * x_grid) / curvature_x_mm)
        if curvature_y_mm != inf:
            phase *= np.exp(-0.5j * self.wave_number_mm * (y_grid * y_grid) / curvature_y_mm)

        field = amplitude.astype(np.complex128) * phase
        return _normalize_field(field, grid), grid

    def apply_mirror(
        self,
        field: np.ndarray,
        grid: FieldGrid,
        mirror_radius_mm: float,
        hole_masks: list[tuple[float, float, float]],
    ) -> np.ndarray:
        x_grid = grid.x_mm[:, None]
        y_grid = grid.y_mm[None, :]
        transformed = field

        if hole_masks:
            aperture = np.ones_like(field, dtype=np.float64)
            for hole_x_mm, hole_y_mm, hole_radius_mm in hole_masks:
                aperture *= (
                    ((x_grid - hole_x_mm) ** 2 + (y_grid - hole_y_mm) ** 2) >= (hole_radius_mm * hole_radius_mm)
                ).astype(np.float64)
            transformed = transformed * aperture

        # Thin spherical mirror phase for the same exp(-iwt) convention used in the Collins kernel.
        transformed *= np.exp(-1j * self.wave_number_mm * ((x_grid * x_grid) + (y_grid * y_grid)) / mirror_radius_mm)
        return transformed

    def summarize_field(
        self,
        field: np.ndarray,
        grid: FieldGrid,
        position: tuple[float, float, float],
        u1: tuple[float, float, float],
        u2: tuple[float, float, float],
        plane_kind: str,
        mirror_number: int | None,
        segment_index: int,
        bounce_index: int | None,
        label: str,
    ) -> dict[str, Any]:
        intensity = np.abs(field) ** 2
        power = float(np.sum(intensity) * grid.dx_mm * grid.dy_mm)
        if power <= EPSILON:
            raise WaveOpticsSamplingError("The propagated field collapsed to zero power on the adaptive grid.")

        x_second_moment = float(
            np.sum((grid.x_mm[:, None] ** 2) * intensity) * grid.dx_mm * grid.dy_mm / power,
        )
        y_second_moment = float(
            np.sum((grid.y_mm[None, :] ** 2) * intensity) * grid.dx_mm * grid.dy_mm / power,
        )
        equivalent_radius_x_mm = 2 * sqrt(max(x_second_moment, 0.0))
        equivalent_radius_y_mm = 2 * sqrt(max(y_second_moment, 0.0))
        peak_density_per_mm2 = float(np.max(intensity) / power)

        display_half_width_x_mm = min(
            grid.half_width_x_mm,
            max(equivalent_radius_x_mm * self.settings.display_safety_factor, equivalent_radius_x_mm * 1.5, 0.1),
        )
        display_half_width_y_mm = min(
            grid.half_width_y_mm,
            max(equivalent_radius_y_mm * self.settings.display_safety_factor, equivalent_radius_y_mm * 1.5, 0.1),
        )
        intensity_map = self._display_intensity_map(
            intensity,
            grid,
            display_half_width_x_mm,
            display_half_width_y_mm,
            self.settings.display_grid_points,
        )

        return {
            "plane_kind": plane_kind,
            "mirror_number": mirror_number,
            "segment_index": segment_index,
            "bounce_index": bounce_index,
            "label": label,
            "position": position,
            "u1": u1,
            "u2": u2,
            "display_half_width_x_mm": display_half_width_x_mm,
            "display_half_width_y_mm": display_half_width_y_mm,
            "display_box_size_mm": 2 * max(display_half_width_x_mm, display_half_width_y_mm),
            "intensity_map": intensity_map,
            "equivalent_radius_x_mm": equivalent_radius_x_mm,
            "equivalent_radius_y_mm": equivalent_radius_y_mm,
            "peak_density_per_mm2": peak_density_per_mm2,
            "power_fraction": power,
            "edge_power_fraction": self._edge_fraction(intensity),
            "spectral_edge_fraction": self._spectral_edge_fraction(field),
        }

    def _display_intensity_map(
        self,
        intensity: np.ndarray,
        grid: FieldGrid,
        half_width_x_mm: float,
        half_width_y_mm: float,
        display_points: int,
    ) -> list[list[float]]:
        target_x = np.linspace(-half_width_x_mm, half_width_x_mm, display_points, dtype=np.float64)
        target_y = np.linspace(-half_width_y_mm, half_width_y_mm, display_points, dtype=np.float64)

        x_interp = np.empty((grid.y_mm.size, display_points), dtype=np.float64)
        for y_index in range(grid.y_mm.size):
            x_interp[y_index, :] = np.interp(target_x, grid.x_mm, intensity[:, y_index], left=0.0, right=0.0)

        display = np.empty((display_points, display_points), dtype=np.float64)
        for x_index in range(display_points):
            display[:, x_index] = np.interp(target_y, grid.y_mm, x_interp[:, x_index], left=0.0, right=0.0)

        max_value = float(np.max(display))
        if max_value > EPSILON:
            display /= max_value
        return display.tolist()

    def _edge_fraction(self, intensity: np.ndarray) -> float:
        border_x = max(1, int(round(intensity.shape[0] * self.settings.guard_band_fraction)))
        border_y = max(1, int(round(intensity.shape[1] * self.settings.guard_band_fraction)))
        if border_x * 2 >= intensity.shape[0] or border_y * 2 >= intensity.shape[1]:
            return 1.0
        edge_power = float(np.sum(intensity))
        core_power = float(np.sum(intensity[border_x:-border_x, border_y:-border_y]))
        if edge_power <= EPSILON:
            return 0.0
        return max((edge_power - core_power) / edge_power, 0.0)

    def _spectral_edge_fraction(self, field: np.ndarray) -> float:
        spectrum = np.abs(np.fft.fftshift(np.fft.fft2(field))) ** 2
        border_x = max(1, int(round(spectrum.shape[0] * self.settings.guard_band_fraction)))
        border_y = max(1, int(round(spectrum.shape[1] * self.settings.guard_band_fraction)))
        if border_x * 2 >= spectrum.shape[0] or border_y * 2 >= spectrum.shape[1]:
            return 1.0
        edge_power = float(np.sum(spectrum))
        core_power = float(np.sum(spectrum[border_x:-border_x, border_y:-border_y]))
        if edge_power <= EPSILON:
            return 0.0
        return max((edge_power - core_power) / edge_power, 0.0)


def _mirror_hit_for_segment(ray_trace: dict[str, Any], segment_index: int) -> dict[str, Any]:
    if segment_index % 2 == 0:
        return ray_trace["mirror_hits"]["2"][segment_index // 2]
    return ray_trace["mirror_hits"]["1"][segment_index // 2]


def _segment_start_basis(ray_trace: dict[str, Any], segment_index: int) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if segment_index == 0:
        basis = ray_trace["input_basis"]
        return basis["u1"], basis["u2"]
    previous_hit = _mirror_hit_for_segment(ray_trace, segment_index - 1)
    return _reflect(previous_hit["u1"], previous_hit["normal"]), _reflect(previous_hit["u2"], previous_hit["normal"])


def _segment_start_point(ray_trace: dict[str, Any], segment_index: int) -> tuple[float, float, float]:
    if segment_index == 0:
        return ray_trace["input_point"]
    return _mirror_hit_for_segment(ray_trace, segment_index - 1)["P"]


def _surface_point(
    mirror_center: tuple[float, float, float],
    mirror_radius_mm: float,
    x_mm: float,
    y_mm: float,
) -> tuple[float, float, float] | None:
    dx_mm = x_mm - mirror_center[0]
    dy_mm = y_mm - mirror_center[1]
    discriminant = (mirror_radius_mm * mirror_radius_mm) - (dx_mm * dx_mm) - (dy_mm * dy_mm)
    if discriminant < 0:
        return None
    z_mm = mirror_center[2] - (1.0 if mirror_radius_mm >= 0 else -1.0) * sqrt(discriminant)
    return (x_mm, y_mm, z_mm)


def _hole_local_coordinates(
    hole_xy_mm: tuple[float, float],
    hit_record: dict[str, Any],
    mirror_center: tuple[float, float, float],
    mirror_radius_mm: float,
) -> tuple[float, float] | None:
    hole_point = _surface_point(mirror_center, mirror_radius_mm, hole_xy_mm[0], hole_xy_mm[1])
    if hole_point is None:
        return None
    delta = v_sub(hole_point, hit_record["P"])
    return v_dot(delta, hit_record["u1"]), v_dot(delta, hit_record["u2"])


def _frame_sampling_warnings(frame: dict[str, Any], label: str) -> list[str]:
    warnings: list[str] = []
    if frame["edge_power_fraction"] > EDGE_WARNING_THRESHOLD:
        warnings.append(
            f"{label}: {frame['edge_power_fraction'] * 100:.2f}% of the power reached the outer guard band, "
            "so the adaptive real-space window is likely too small for this segment.",
        )
    if frame["spectral_edge_fraction"] > SPECTRAL_WARNING_THRESHOLD:
        warnings.append(
            f"{label}: {frame['spectral_edge_fraction'] * 100:.2f}% of the spectrum reached the Nyquist guard band, "
            "so the sampling pitch is likely too coarse for this segment.",
        )
    return warnings


def _plan_dict(plan: PlanePlan) -> dict[str, Any]:
    return {
        "half_width_x_mm": plan.half_width_x_mm,
        "half_width_y_mm": plan.half_width_y_mm,
        "dx_mm": plan.dx_mm,
        "dy_mm": plan.dy_mm,
        "nx": plan.nx,
        "ny": plan.ny,
        "predicted_radius_x_mm": plan.predicted_radius_x_mm,
        "predicted_radius_y_mm": plan.predicted_radius_y_mm,
    }


def _segment_states(
    mirror_distance_mm: float,
    mirror1_radius_mm: float,
    mirror2_radius_mm: float,
    wavelength_mm: float,
    input_waist_x_mm: float,
    input_waist_y_mm: float,
    input_waist_z_mm: float,
    segment_count: int,
    m2_x: float,
    m2_y: float,
) -> list[SegmentState]:
    states: list[SegmentState] = []
    q_x = _q_from_waist(input_waist_x_mm, input_waist_z_mm, wavelength_mm, m2_x)
    q_y = _q_from_waist(input_waist_y_mm, input_waist_z_mm, wavelength_mm, m2_y)

    for segment_index in range(segment_count):
        start_mirror = 1 if segment_index % 2 == 0 else 2
        end_mirror = 2 if start_mirror == 1 else 1
        end_mirror_radius_mm = mirror2_radius_mm if end_mirror == 2 else mirror1_radius_mm

        focus_distance_mm, focus_warning = _find_focus_distance_mm(
            q_x,
            q_y,
            mirror_distance_mm,
            wavelength_mm,
            m2_x,
            m2_y,
        )
        q_focus_x = _propagate_q(q_x, focus_distance_mm)
        q_focus_y = _propagate_q(q_y, focus_distance_mm)
        q_end_x = _propagate_q(q_x, mirror_distance_mm)
        q_end_y = _propagate_q(q_y, mirror_distance_mm)
        q_reflected_x = _mirror_q(q_end_x, end_mirror_radius_mm)
        q_reflected_y = _mirror_q(q_end_y, end_mirror_radius_mm)

        states.append(
            SegmentState(
                segment_index=segment_index,
                start_mirror=start_mirror,
                end_mirror=end_mirror,
                focus_distance_mm=focus_distance_mm,
                focus_boundary_warning=focus_warning,
                start_q_x=q_x,
                start_q_y=q_y,
                end_q_x=q_end_x,
                end_q_y=q_end_y,
                reflected_q_x=q_reflected_x,
                reflected_q_y=q_reflected_y,
                start_radius_x_mm=float(_beam_radius_mm(q_x, wavelength_mm, m2_x)),
                start_radius_y_mm=float(_beam_radius_mm(q_y, wavelength_mm, m2_y)),
                focus_radius_x_mm=float(_beam_radius_mm(q_focus_x, wavelength_mm, m2_x)),
                focus_radius_y_mm=float(_beam_radius_mm(q_focus_y, wavelength_mm, m2_y)),
                end_radius_x_mm=float(_beam_radius_mm(q_end_x, wavelength_mm, m2_x)),
                end_radius_y_mm=float(_beam_radius_mm(q_end_y, wavelength_mm, m2_y)),
                start_curvature_x_mm=_curvature_radius_mm(q_x),
                start_curvature_y_mm=_curvature_radius_mm(q_y),
                focus_curvature_x_mm=_curvature_radius_mm(q_focus_x),
                focus_curvature_y_mm=_curvature_radius_mm(q_focus_y),
                end_curvature_x_mm=_curvature_radius_mm(q_end_x),
                end_curvature_y_mm=_curvature_radius_mm(q_end_y),
                reflected_curvature_x_mm=_curvature_radius_mm(q_reflected_x),
                reflected_curvature_y_mm=_curvature_radius_mm(q_reflected_y),
            ),
        )
        q_x = q_reflected_x
        q_y = q_reflected_y

    return states


def _plan_planes(
    states: list[SegmentState],
    mirror_distance_mm: float,
    wavelength_mm: float,
    settings: WaveOpticsSettings,
) -> tuple[list[PlanePlan], list[PlanePlan]]:
    mirror_half_widths: list[tuple[float, float]] = []
    focus_half_widths: list[tuple[float, float]] = []

    for plane_index in range(len(states) + 1):
        if plane_index == len(states):
            radius_x_mm = states[-1].end_radius_x_mm
            radius_y_mm = states[-1].end_radius_y_mm
        else:
            radius_x_mm = states[plane_index].start_radius_x_mm
            radius_y_mm = states[plane_index].start_radius_y_mm
        mirror_half_widths.append(
            (
                _plane_half_width_mm(radius_x_mm, settings),
                _plane_half_width_mm(radius_y_mm, settings),
            ),
        )

    for state in states:
        focus_half_widths.append(
            (
                _plane_half_width_mm(state.focus_radius_x_mm, settings),
                _plane_half_width_mm(state.focus_radius_y_mm, settings),
            ),
        )

    mirror_plans: list[PlanePlan] = []
    for plane_index, (half_width_x_mm, half_width_y_mm) in enumerate(mirror_half_widths):
        if plane_index == len(states):
            radius_x_mm = states[-1].end_radius_x_mm
            radius_y_mm = states[-1].end_radius_y_mm
            outgoing_curvature_x_mm = inf
            outgoing_curvature_y_mm = inf
            incoming_curvature_x_mm = states[-1].end_curvature_x_mm
            incoming_curvature_y_mm = states[-1].end_curvature_y_mm
        else:
            radius_x_mm = states[plane_index].start_radius_x_mm
            radius_y_mm = states[plane_index].start_radius_y_mm
            outgoing_curvature_x_mm = states[plane_index].start_curvature_x_mm
            outgoing_curvature_y_mm = states[plane_index].start_curvature_y_mm
            incoming_curvature_x_mm = inf if plane_index == 0 else states[plane_index - 1].end_curvature_x_mm
            incoming_curvature_y_mm = inf if plane_index == 0 else states[plane_index - 1].end_curvature_y_mm

        # The adaptive grid must satisfy both real-space resolution and phase / kernel Nyquist limits.
        dx_limit_x_mm = radius_x_mm / settings.samples_per_radius
        dx_limit_y_mm = radius_y_mm / settings.samples_per_radius
        dx_limit_x_mm = min(
            dx_limit_x_mm,
            _dx_from_curvature(outgoing_curvature_x_mm, half_width_x_mm, wavelength_mm, settings.curvature_nyquist_margin),
            _dx_from_curvature(incoming_curvature_x_mm, half_width_x_mm, wavelength_mm, settings.curvature_nyquist_margin),
        )
        dx_limit_y_mm = min(
            dx_limit_y_mm,
            _dx_from_curvature(outgoing_curvature_y_mm, half_width_y_mm, wavelength_mm, settings.curvature_nyquist_margin),
            _dx_from_curvature(incoming_curvature_y_mm, half_width_y_mm, wavelength_mm, settings.curvature_nyquist_margin),
        )

        if plane_index > 0:
            prev_state = states[plane_index - 1]
            prev_focus_half_x_mm, prev_focus_half_y_mm = focus_half_widths[plane_index - 1]
            dx_limit_x_mm = min(
                dx_limit_x_mm,
                _dx_from_kernel(
                    mirror_distance_mm - prev_state.focus_distance_mm,
                    prev_focus_half_x_mm,
                    wavelength_mm,
                    settings.kernel_nyquist_margin,
                ),
            )
            dx_limit_y_mm = min(
                dx_limit_y_mm,
                _dx_from_kernel(
                    mirror_distance_mm - prev_state.focus_distance_mm,
                    prev_focus_half_y_mm,
                    wavelength_mm,
                    settings.kernel_nyquist_margin,
                ),
            )

        if plane_index < len(states):
            next_state = states[plane_index]
            next_focus_half_x_mm, next_focus_half_y_mm = focus_half_widths[plane_index]
            dx_limit_x_mm = min(
                dx_limit_x_mm,
                _dx_from_kernel(
                    next_state.focus_distance_mm,
                    next_focus_half_x_mm,
                    wavelength_mm,
                    settings.kernel_nyquist_margin,
                ),
            )
            dx_limit_y_mm = min(
                dx_limit_y_mm,
                _dx_from_kernel(
                    next_state.focus_distance_mm,
                    next_focus_half_y_mm,
                    wavelength_mm,
                    settings.kernel_nyquist_margin,
                ),
            )

        nx = _efficient_grid_size(_grid_requirement_points(half_width_x_mm, dx_limit_x_mm), settings.max_grid_points)
        ny = _efficient_grid_size(_grid_requirement_points(half_width_y_mm, dx_limit_y_mm), settings.max_grid_points)
        mirror_plans.append(
            PlanePlan(
                half_width_x_mm=half_width_x_mm,
                half_width_y_mm=half_width_y_mm,
                nx=nx,
                ny=ny,
                dx_mm=(2 * half_width_x_mm) / (nx - 1),
                dy_mm=(2 * half_width_y_mm) / (ny - 1),
                predicted_radius_x_mm=radius_x_mm,
                predicted_radius_y_mm=radius_y_mm,
            ),
        )

    focus_plans: list[PlanePlan] = []
    for state_index, state in enumerate(states):
        half_width_x_mm, half_width_y_mm = focus_half_widths[state_index]
        start_half_width_x_mm, start_half_width_y_mm = mirror_half_widths[state_index]
        end_half_width_x_mm, end_half_width_y_mm = mirror_half_widths[state_index + 1]

        dx_limit_x_mm = state.focus_radius_x_mm / settings.samples_per_radius
        dx_limit_y_mm = state.focus_radius_y_mm / settings.samples_per_radius
        dx_limit_x_mm = min(
            dx_limit_x_mm,
            _dx_from_curvature(state.focus_curvature_x_mm, half_width_x_mm, wavelength_mm, settings.curvature_nyquist_margin),
            _dx_from_kernel(
                state.focus_distance_mm,
                start_half_width_x_mm,
                wavelength_mm,
                settings.kernel_nyquist_margin,
            ),
            _dx_from_kernel(
                mirror_distance_mm - state.focus_distance_mm,
                end_half_width_x_mm,
                wavelength_mm,
                settings.kernel_nyquist_margin,
            ),
        )
        dx_limit_y_mm = min(
            dx_limit_y_mm,
            _dx_from_curvature(state.focus_curvature_y_mm, half_width_y_mm, wavelength_mm, settings.curvature_nyquist_margin),
            _dx_from_kernel(
                state.focus_distance_mm,
                start_half_width_y_mm,
                wavelength_mm,
                settings.kernel_nyquist_margin,
            ),
            _dx_from_kernel(
                mirror_distance_mm - state.focus_distance_mm,
                end_half_width_y_mm,
                wavelength_mm,
                settings.kernel_nyquist_margin,
            ),
        )

        nx = _efficient_grid_size(_grid_requirement_points(half_width_x_mm, dx_limit_x_mm), settings.max_grid_points)
        ny = _efficient_grid_size(_grid_requirement_points(half_width_y_mm, dx_limit_y_mm), settings.max_grid_points)
        focus_plans.append(
            PlanePlan(
                half_width_x_mm=half_width_x_mm,
                half_width_y_mm=half_width_y_mm,
                nx=nx,
                ny=ny,
                dx_mm=(2 * half_width_x_mm) / (nx - 1),
                dy_mm=(2 * half_width_y_mm) / (ny - 1),
                predicted_radius_x_mm=state.focus_radius_x_mm,
                predicted_radius_y_mm=state.focus_radius_y_mm,
            ),
        )

    for index, state in enumerate(states):
        bytes_required = _estimate_segment_memory_bytes(mirror_plans[index], focus_plans[index], mirror_plans[index + 1])
        if bytes_required > settings.max_memory_mb * 1024 * 1024:
            raise WaveOpticsSamplingError(
                f"Segment {index + 1} would require roughly {bytes_required / (1024 * 1024):.1f} MiB, exceeding the "
                f"configured wave-optics budget of {settings.max_memory_mb:.1f} MiB. Increase the memory budget or "
                "loosen the grid settings.",
            )

    return mirror_plans, focus_plans


def compute_wave_optics_result(base_result: dict[str, Any], request: Any) -> dict[str, Any] | None:
    if not base_result.get("stable") or base_result.get("ray_trace") is None or base_result.get("beam_propagation") is None:
        return None

    resolved_inputs = base_result["resolved_inputs"]
    ray_trace = base_result["ray_trace"]
    mode = base_result["mode"]
    settings: WaveOpticsSettings = request.wave_optics
    wavelength_mm = resolved_inputs["wavelength_mm"]
    mirror_distance_mm = resolved_inputs["mirror_distance_mm"]
    mirror1_radius_mm = resolved_inputs["mirror1_radius_mm"]
    mirror2_radius_mm = resolved_inputs["mirror2_radius_mm"]
    segment_count = len(ray_trace["points"]) - 1
    if segment_count < 1:
        return None

    states = _segment_states(
        mirror_distance_mm,
        mirror1_radius_mm,
        mirror2_radius_mm,
        wavelength_mm,
        resolved_inputs["input_waist_x_mm"],
        resolved_inputs["input_waist_y_mm"],
        resolved_inputs["input_waist_z_mm"],
        segment_count,
        mode["M2x"],
        mode["M2y"],
    )
    mirror_plans, focus_plans = _plan_planes(states, mirror_distance_mm, wavelength_mm, settings)
    solver = AdaptiveWaveOpticsSolver(wavelength_mm, settings)

    launch_u1, launch_u2 = _segment_start_basis(ray_trace, 0)
    launch_point = _segment_start_point(ray_trace, 0)
    field, current_grid = solver.build_launch_field(
        mirror_plans[0],
        settings.profile_type,
        settings.super_gaussian_order,
        states[0].start_radius_x_mm,
        states[0].start_radius_y_mm,
        states[0].start_curvature_x_mm,
        states[0].start_curvature_y_mm,
    )
    launch_profile = solver.summarize_field(
        field,
        current_grid,
        launch_point,
        launch_u1,
        launch_u2,
        "launch",
        1,
        0,
        0,
        "In",
    )
    field = solver.apply_mirror(field, current_grid, mirror1_radius_mm, [])

    cell_centers = ray_trace["cell_centers"]
    mirror_centers = {
        1: cell_centers["mirror1"],
        2: cell_centers["mirror2"],
    }
    mirror_radii = {
        1: mirror1_radius_mm,
        2: mirror2_radius_mm,
    }

    mirror1_profiles: list[dict[str, Any]] = []
    mirror2_profiles: list[dict[str, Any]] = []
    focus_profiles: list[dict[str, Any]] = []
    segment_diagnostics: list[dict[str, Any]] = []
    overall_warnings: list[str] = []

    for segment_index, state in enumerate(states):
        focus_field, focus_grid = solver.propagate(
            field,
            current_grid,
            focus_plans[segment_index],
            state.focus_distance_mm,
        )
        segment_start = _segment_start_point(ray_trace, segment_index)
        segment_end = ray_trace["points"][segment_index + 1]
        start_u1, start_u2 = _segment_start_basis(ray_trace, segment_index)
        focus_fraction = state.focus_distance_mm / mirror_distance_mm
        focus_point = (
            segment_start[0] + focus_fraction * (segment_end[0] - segment_start[0]),
            segment_start[1] + focus_fraction * (segment_end[1] - segment_start[1]),
            segment_start[2] + focus_fraction * (segment_end[2] - segment_start[2]),
        )
        focus_profile = solver.summarize_field(
            focus_field,
            focus_grid,
            focus_point,
            start_u1,
            start_u2,
            "focus",
            None,
            segment_index,
            None,
            str(segment_index + 1),
        )
        focus_profiles.append(focus_profile)

        mirror_field, mirror_grid = solver.propagate(
            focus_field,
            focus_grid,
            mirror_plans[segment_index + 1],
            mirror_distance_mm - state.focus_distance_mm,
        )
        end_hit = _mirror_hit_for_segment(ray_trace, segment_index)
        bounce_index = segment_index + 1
        mirror_profile = solver.summarize_field(
            mirror_field,
            mirror_grid,
            end_hit["P"],
            end_hit["u1"],
            end_hit["u2"],
            "mirror",
            state.end_mirror,
            segment_index,
            bounce_index,
            str(bounce_index),
        )
        if state.end_mirror == 1:
            mirror1_profiles.append(mirror_profile)
        else:
            mirror2_profiles.append(mirror_profile)

        segment_warnings: list[str] = []
        if state.focus_boundary_warning:
            segment_warnings.append(f"Segment {segment_index + 1}: {state.focus_boundary_warning}")
        segment_warnings.extend(_frame_sampling_warnings(focus_profile, f"Focus plane {segment_index + 1}"))
        segment_warnings.extend(_frame_sampling_warnings(mirror_profile, f"Mirror bounce {bounce_index}"))
        overall_warnings.extend(segment_warnings)

        segment_diagnostics.append(
            {
                "segment_index": segment_index,
                "start_mirror": state.start_mirror,
                "end_mirror": state.end_mirror,
                "focus_distance_mm": state.focus_distance_mm,
                "start_grid": _plan_dict(mirror_plans[segment_index]),
                "focus_grid": _plan_dict(focus_plans[segment_index]),
                "end_grid": _plan_dict(mirror_plans[segment_index + 1]),
                "start_radius_x_mm": state.start_radius_x_mm,
                "start_radius_y_mm": state.start_radius_y_mm,
                "focus_radius_x_mm": state.focus_radius_x_mm,
                "focus_radius_y_mm": state.focus_radius_y_mm,
                "end_radius_x_mm": state.end_radius_x_mm,
                "end_radius_y_mm": state.end_radius_y_mm,
                "warnings": segment_warnings,
            },
        )

        if segment_index == len(states) - 1:
            continue

        hole_masks: list[tuple[float, float, float]] = []
        if state.end_mirror == 1:
            input_hole_local = _hole_local_coordinates(
                (resolved_inputs["input_hole_x_mm"], resolved_inputs["input_hole_y_mm"]),
                end_hit,
                mirror_centers[1],
                mirror_radii[1],
            )
            if input_hole_local is not None:
                hole_masks.append((input_hole_local[0], input_hole_local[1], resolved_inputs["hole_radius_mm"]))
        if resolved_inputs["output_mirror"] == state.end_mirror:
            output_hole_local = _hole_local_coordinates(
                (resolved_inputs["output_hole_x_mm"], resolved_inputs["output_hole_y_mm"]),
                end_hit,
                mirror_centers[state.end_mirror],
                mirror_radii[state.end_mirror],
            )
            if output_hole_local is not None:
                hole_masks.append((output_hole_local[0], output_hole_local[1], resolved_inputs["hole_radius_mm"]))

        field = solver.apply_mirror(mirror_field, mirror_grid, mirror_radii[state.end_mirror], hole_masks)
        current_grid = mirror_grid

    deduplicated_warnings = list(dict.fromkeys(overall_warnings))
    return {
        "method": "Adaptive-grid 2D Collins/Fresnel diffraction integral",
        "profile_type": settings.profile_type,
        "super_gaussian_order": (
            settings.super_gaussian_order
            if settings.profile_type in {"super_gaussian", "round_super_gaussian"}
            else None
        ),
        "settings": settings.model_dump(),
        "warnings": deduplicated_warnings,
        "launch_profile": launch_profile,
        "mirror1_profiles": mirror1_profiles,
        "mirror2_profiles": mirror2_profiles,
        "focus_profiles": focus_profiles,
        "segments": segment_diagnostics,
    }
