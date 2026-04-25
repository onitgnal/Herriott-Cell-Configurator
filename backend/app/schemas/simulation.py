from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Vector3 = tuple[float, float, float]


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_type: Literal["cav-cav", "cav-vex"] = "cav-cav"
    mirror_distance_mm: float = Field(1132.0, gt=0)
    total_passes: int = Field(14, ge=2)
    revolutions: int = Field(5, ge=1)
    spot_pattern_radius_mm: float = Field(15.0, ge=0)
    wavelength_nm: float = Field(1030.0, gt=0)
    hole_radius_mm: float = Field(1.5, ge=0)
    peak_power_gw: float = Field(1.0, ge=0)
    pulse_energy_mj: float = Field(1.0, ge=0)
    auto_symmetric_radius: bool = True
    auto_opposite_radii: bool = True
    symmetric_radius_mm: float = Field(1999.6, gt=0)
    mirror1_radius_mm: float = 2500.0
    mirror2_radius_mm: float = -2500.0
    auto_output_hole: bool = True
    output_mirror: Literal[1, 2] = 1
    output_hole_x_mm: float = 15.0
    output_hole_y_mm: float = 0.0
    mode_type: Literal["tem00", "hg", "lg", "custom"] = "tem00"
    hermite_n: int = Field(0, ge=0)
    hermite_m: int = Field(1, ge=0)
    laguerre_p: int = Field(0, ge=0)
    laguerre_l: int = 1
    custom_m2: float = Field(1.0, ge=1.0)
    auto_mode_match: bool = True
    input_waist_x_mm: float = Field(1.0, gt=0)
    input_waist_y_mm: float = Field(1.0, gt=0)
    input_waist_z_mm: float = 566.0
    polarization_angle_deg: float = 0.0
    auto_injection: bool = True
    input_x_mm: float = 15.0
    input_y_mm: float = 0.0
    input_theta_x_mrad: float = -7.5
    input_theta_y_mrad: float = 11.9
    mirror1_tilt_x_mrad: float = 0.0
    mirror1_tilt_y_mrad: float = 0.0
    mirror2_tilt_x_mrad: float = 0.0
    mirror2_tilt_y_mrad: float = 0.0


class WaveOpticsSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_type: Literal["gaussian", "super_gaussian", "round_super_gaussian"] = "gaussian"
    super_gaussian_order: float = Field(4.0, ge=1.0, le=20.0)
    window_safety_factor: float = Field(4.0, gt=1.0, le=12.0)
    samples_per_radius: int = Field(14, ge=4, le=64)
    guard_band_fraction: float = Field(0.12, ge=0.02, lt=0.45)
    kernel_nyquist_margin: float = Field(0.85, gt=0.1, lt=1.0)
    curvature_nyquist_margin: float = Field(0.85, gt=0.1, lt=1.0)
    max_grid_points: int = Field(256, ge=32, le=1024)
    max_memory_mb: float = Field(192.0, ge=16.0, le=4096.0)
    display_grid_points: int = Field(72, ge=24, le=256)
    display_safety_factor: float = Field(2.0, gt=1.0, le=6.0)


class WaveOpticsSimulationRequest(SimulationRequest):
    wave_optics: WaveOpticsSettings = Field(default_factory=WaveOpticsSettings)


class ResolvedInputs(BaseModel):
    mirror_distance_mm: float
    total_passes: int
    revolutions: int
    spot_pattern_radius_mm: float
    wavelength_nm: float
    wavelength_mm: float
    hole_radius_mm: float
    peak_power_gw: float
    pulse_energy_mj: float
    mirror1_radius_mm: float | None
    mirror2_radius_mm: float | None
    input_waist_x_mm: float | None
    input_waist_y_mm: float | None
    input_waist_z_mm: float | None
    input_x_mm: float | None
    input_y_mm: float | None
    input_theta_x_mrad: float | None
    input_theta_y_mrad: float | None
    input_hole_x_mm: float | None
    input_hole_y_mm: float | None
    output_hole_x_mm: float | None
    output_hole_y_mm: float | None
    output_mirror: int
    polarization_angle_deg: float
    mirror1_tilt_x_mrad: float
    mirror1_tilt_y_mrad: float
    mirror2_tilt_x_mrad: float
    mirror2_tilt_y_mrad: float


class StabilityResult(BaseModel):
    g1: float | None
    g2: float | None
    product: float | None


class ModeResult(BaseModel):
    type: str
    title: str
    M2x: float
    M2y: float
    norm: float
    peak_factor: float
    n: int | None = None
    m: int | None = None
    p: int | None = None
    l: int | None = None


class CavityResult(BaseModel):
    rayleigh_range_mm: float
    waist_position_mm: float
    ideal_waist_mm: float
    cavity_waist_x_mm: float
    cavity_waist_y_mm: float
    mirror1_beam_mm: float
    mirror2_beam_mm: float
    mirror_beam_x_mm: float | None
    mirror_beam_y_mm: float | None
    mirror1_display_beam_mm: float | None
    mirror2_display_beam_mm: float | None


class CenterHit(BaseModel):
    P: Vector3
    u1: Vector3
    u2: Vector3


class RayHit(BaseModel):
    P: Vector3
    u1: Vector3
    u2: Vector3
    v_in: Vector3
    v_out: Vector3 | None
    normal: Vector3


class InputBasis(BaseModel):
    u1: Vector3
    u2: Vector3


class CellCenters(BaseModel):
    mirror1: Vector3
    mirror2: Vector3


class RayTraceResult(BaseModel):
    points: list[Vector3]
    mirror_hits: dict[str, list[RayHit]]
    center_hits: list[CenterHit]
    exit_status: str
    total_bounces: int
    input_basis: InputBasis
    input_point: Vector3
    cell_centers: CellCenters


class AxisPropagation(BaseModel):
    z_vals: list[float]
    w_vals: list[float]
    w_mirrors_w: list[float]
    w_center_w: list[float]


class BeamPropagation(BaseModel):
    x: AxisPropagation
    y: AxisPropagation


class WaveOpticsGridDiagnostic(BaseModel):
    half_width_x_mm: float
    half_width_y_mm: float
    dx_mm: float
    dy_mm: float
    nx: int
    ny: int
    predicted_radius_x_mm: float
    predicted_radius_y_mm: float


class WaveOpticsFrame(BaseModel):
    plane_kind: Literal["launch", "mirror", "focus"]
    mirror_number: int | None = None
    segment_index: int
    bounce_index: int | None = None
    label: str
    position: Vector3
    u1: Vector3
    u2: Vector3
    display_half_width_x_mm: float
    display_half_width_y_mm: float
    display_box_size_mm: float
    intensity_map: list[list[float]]
    equivalent_radius_x_mm: float
    equivalent_radius_y_mm: float
    peak_density_per_mm2: float
    power_fraction: float
    edge_power_fraction: float
    spectral_edge_fraction: float


class WaveOpticsSegmentDiagnostic(BaseModel):
    segment_index: int
    start_mirror: int
    end_mirror: int
    focus_distance_mm: float
    start_grid: WaveOpticsGridDiagnostic
    focus_grid: WaveOpticsGridDiagnostic
    end_grid: WaveOpticsGridDiagnostic
    start_radius_x_mm: float
    start_radius_y_mm: float
    focus_radius_x_mm: float
    focus_radius_y_mm: float
    end_radius_x_mm: float
    end_radius_y_mm: float
    warnings: list[str]


class WaveOpticsResult(BaseModel):
    method: str
    profile_type: Literal["gaussian", "super_gaussian", "round_super_gaussian"]
    super_gaussian_order: float | None = None
    settings: WaveOpticsSettings
    warnings: list[str]
    launch_profile: WaveOpticsFrame
    mirror1_profiles: list[WaveOpticsFrame]
    mirror2_profiles: list[WaveOpticsFrame]
    focus_profiles: list[WaveOpticsFrame]
    segments: list[WaveOpticsSegmentDiagnostic]


class SimulationResponse(BaseModel):
    stable: bool
    status_message: str
    resolved_inputs: ResolvedInputs
    stability: StabilityResult
    mode: ModeResult
    cavity: CavityResult | None
    ray_trace: RayTraceResult | None
    beam_propagation: BeamPropagation | None
    wave_optics: WaveOpticsResult | None = None


class WaveOpticsJobProgress(BaseModel):
    completed_steps: int = Field(0, ge=0)
    total_steps: int = Field(1, ge=1)
    progress_fraction: float = Field(0.0, ge=0.0, le=1.0)
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    current_step: str
    current_segment: int | None = None
    segment_count: int | None = None
    elapsed_seconds: float = Field(0.0, ge=0.0)
    estimated_remaining_seconds: float | None = Field(default=None, ge=0.0)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ValidationDetail(BaseModel):
    loc: list[str | int]
    message: str
    type: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
    details: list[ValidationDetail] | None = None


class WaveOpticsJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: WaveOpticsJobProgress
    result: SimulationResponse | None = None
    error: ErrorDetail | None = None
