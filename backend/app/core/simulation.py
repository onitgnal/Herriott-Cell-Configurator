from __future__ import annotations

from math import cos, isfinite, pi, sin, sqrt

from backend.app.core.math_utils import v_add, v_cross, v_dot, v_normalize, v_scale, v_sub
from backend.app.core.modes import build_mode_config
from backend.app.core.optics import compute_abcd_axis
from backend.app.core.ray_tracing import EPSILON, HerriottCell


def finite_or_none(value: float) -> float | None:
    return value if isfinite(value) else None


def simulate_configuration(request: object) -> dict[str, object]:
    mirror_distance_mm = request.mirror_distance_mm
    total_passes = request.total_passes
    revolutions = request.revolutions
    spot_pattern_radius_mm = request.spot_pattern_radius_mm
    wavelength_mm = request.wavelength_nm * 1e-6
    hole_radius_mm = request.hole_radius_mm
    peak_power_gw = request.peak_power_gw
    pulse_energy_mj = request.pulse_energy_mj
    theta_rt = (2 * pi * revolutions) / total_passes

    if request.cell_type == "cav-cav":
        if request.auto_symmetric_radius:
            c_actual = 1 - cos(theta_rt / 2)
            mirror1_radius_mm = mirror_distance_mm / c_actual
            mirror2_radius_mm = mirror1_radius_mm
        else:
            mirror1_radius_mm = request.symmetric_radius_mm
            mirror2_radius_mm = request.symmetric_radius_mm
    elif request.auto_opposite_radii:
        mirror1_radius_mm = mirror_distance_mm / sin(theta_rt / 2)
        mirror2_radius_mm = -mirror_distance_mm / sin(theta_rt / 2)
    else:
        mirror1_radius_mm = request.mirror1_radius_mm
        mirror2_radius_mm = request.mirror2_radius_mm

    g1 = 1 - mirror_distance_mm / mirror1_radius_mm
    g2 = 1 - mirror_distance_mm / mirror2_radius_mm
    stability_product = g1 * g2
    mode = build_mode_config(
        request.mode_type,
        request.hermite_n,
        request.hermite_m,
        request.laguerre_p,
        request.laguerre_l,
        request.custom_m2,
    )

    stable = isfinite(stability_product) and 0 < stability_product < 1
    response: dict[str, object] = {
        "stable": stable,
        "status_message": "Stability Error (g1g2 bounds)",
        "resolved_inputs": {
            "mirror_distance_mm": mirror_distance_mm,
            "total_passes": total_passes,
            "revolutions": revolutions,
            "spot_pattern_radius_mm": spot_pattern_radius_mm,
            "wavelength_nm": request.wavelength_nm,
            "wavelength_mm": wavelength_mm,
            "hole_radius_mm": hole_radius_mm,
            "peak_power_gw": peak_power_gw,
            "pulse_energy_mj": pulse_energy_mj,
            "mirror1_radius_mm": finite_or_none(mirror1_radius_mm),
            "mirror2_radius_mm": finite_or_none(mirror2_radius_mm),
            "input_waist_x_mm": finite_or_none(request.input_waist_x_mm),
            "input_waist_y_mm": finite_or_none(request.input_waist_y_mm),
            "input_waist_z_mm": finite_or_none(request.input_waist_z_mm),
            "input_x_mm": finite_or_none(request.input_x_mm),
            "input_y_mm": finite_or_none(request.input_y_mm),
            "input_theta_x_mrad": finite_or_none(request.input_theta_x_mrad),
            "input_theta_y_mrad": finite_or_none(request.input_theta_y_mrad),
            "input_hole_x_mm": finite_or_none(request.input_x_mm),
            "input_hole_y_mm": finite_or_none(request.input_y_mm),
            "output_hole_x_mm": finite_or_none(request.output_hole_x_mm),
            "output_hole_y_mm": finite_or_none(request.output_hole_y_mm),
            "output_mirror": request.output_mirror,
            "polarization_angle_deg": request.polarization_angle_deg,
            "mirror1_tilt_x_mrad": request.mirror1_tilt_x_mrad,
            "mirror1_tilt_y_mrad": request.mirror1_tilt_y_mrad,
            "mirror2_tilt_x_mrad": request.mirror2_tilt_x_mrad,
            "mirror2_tilt_y_mrad": request.mirror2_tilt_y_mrad,
        },
        "stability": {
            "g1": finite_or_none(g1),
            "g2": finite_or_none(g2),
            "product": finite_or_none(stability_product),
        },
        "mode": mode.as_dict(),
        "cavity": None,
        "ray_trace": None,
        "beam_propagation": None,
    }

    if not stable:
        return response

    g_sum = g1 + g2 - 2 * g1 * g2
    if g_sum == 0:
        g_sum = EPSILON

    cavity_rayleigh_range_mm = sqrt(
        abs(((mirror_distance_mm * mirror_distance_mm) * g1 * g2 * (1 - g1 * g2)) / (g_sum * g_sum)),
    )
    cavity_waist_position_mm = (mirror_distance_mm * g2 * (1 - g1)) / g_sum
    ideal_waist_mm = sqrt((wavelength_mm * cavity_rayleigh_range_mm) / pi)
    mirror1_beam_mm = sqrt(
        abs(((wavelength_mm * mirror_distance_mm) / pi) * sqrt(g2 / (g1 * (1 - g1 * g2)))),
    )
    mirror2_beam_mm = sqrt(
        abs(((wavelength_mm * mirror_distance_mm) / pi) * sqrt(g1 / (g2 * (1 - g1 * g2)))),
    )

    input_waist_x_mm = request.input_waist_x_mm
    input_waist_y_mm = request.input_waist_y_mm
    input_waist_z_mm = request.input_waist_z_mm

    if request.auto_mode_match:
        input_waist_x_mm = ideal_waist_mm * sqrt(mode.M2x)
        input_waist_y_mm = ideal_waist_mm * sqrt(mode.M2y)
        input_waist_z_mm = cavity_waist_position_mm

    if request.auto_injection:
        input_x_mm = spot_pattern_radius_mm
        input_y_mm = 0.0
        m_arrive_00 = 1 - (2 * mirror_distance_mm) / mirror2_radius_mm
        m_arrive_01 = 2 * mirror_distance_mm * g2
        input_theta_x_mrad = ((spot_pattern_radius_mm * (cos(theta_rt) - m_arrive_00)) / m_arrive_01) * 1000
        input_theta_y_mrad = ((spot_pattern_radius_mm * sin(theta_rt)) / m_arrive_01) * 1000
    else:
        input_x_mm = request.input_x_mm
        input_y_mm = request.input_y_mm
        input_theta_x_mrad = request.input_theta_x_mrad
        input_theta_y_mrad = request.input_theta_y_mrad

    if request.auto_output_hole:
        output_hole_x_mm = input_x_mm
        output_hole_y_mm = input_y_mm
        output_mirror = 1
    else:
        output_hole_x_mm = request.output_hole_x_mm
        output_hole_y_mm = request.output_hole_y_mm
        output_mirror = request.output_mirror

    response["cavity"] = {
        "rayleigh_range_mm": cavity_rayleigh_range_mm,
        "waist_position_mm": cavity_waist_position_mm,
        "ideal_waist_mm": ideal_waist_mm,
        "cavity_waist_x_mm": ideal_waist_mm * sqrt(mode.M2x),
        "cavity_waist_y_mm": ideal_waist_mm * sqrt(mode.M2y),
        "mirror1_beam_mm": mirror1_beam_mm,
        "mirror2_beam_mm": mirror2_beam_mm,
        "mirror_beam_x_mm": mirror1_beam_mm * sqrt(mode.M2x) if abs(mirror1_beam_mm - mirror2_beam_mm) < 1e-3 else None,
        "mirror_beam_y_mm": mirror1_beam_mm * sqrt(mode.M2y) if abs(mirror1_beam_mm - mirror2_beam_mm) < 1e-3 else None,
        "mirror1_display_beam_mm": None if abs(mirror1_beam_mm - mirror2_beam_mm) < 1e-3 else mirror1_beam_mm * sqrt(mode.M2x),
        "mirror2_display_beam_mm": None if abs(mirror1_beam_mm - mirror2_beam_mm) < 1e-3 else mirror2_beam_mm * sqrt(mode.M2x),
    }

    response["resolved_inputs"] = {
        **response["resolved_inputs"],
        "input_waist_x_mm": input_waist_x_mm,
        "input_waist_y_mm": input_waist_y_mm,
        "input_waist_z_mm": input_waist_z_mm,
        "input_x_mm": input_x_mm,
        "input_y_mm": input_y_mm,
        "input_theta_x_mrad": input_theta_x_mrad,
        "input_theta_y_mrad": input_theta_y_mrad,
        "input_hole_x_mm": input_x_mm,
        "input_hole_y_mm": input_y_mm,
        "output_hole_x_mm": output_hole_x_mm,
        "output_hole_y_mm": output_hole_y_mm,
        "output_mirror": output_mirror,
    }

    input_hole = (input_x_mm, input_y_mm)
    output_hole = (output_hole_x_mm, output_hole_y_mm)
    mirror1_tilt = (request.mirror1_tilt_x_mrad * 1e-3, request.mirror1_tilt_y_mrad * 1e-3)
    mirror2_tilt = (request.mirror2_tilt_x_mrad * 1e-3, request.mirror2_tilt_y_mrad * 1e-3)

    cell = HerriottCell(
        mirror_distance_mm,
        mirror1_radius_mm,
        mirror2_radius_mm,
        input_hole,
        output_hole,
        output_mirror,
        hole_radius_mm,
        mirror1_tilt,
        mirror2_tilt,
    )

    initial_x = input_x_mm
    initial_y = input_y_mm
    discriminant = cell.R1 * cell.R1 - (initial_x - cell.C1[0]) ** 2 - (initial_y - cell.C1[1]) ** 2
    initial_z = cell.C1[2] - (1.0 if cell.R1 >= 0 else -1.0) * sqrt(discriminant) if discriminant >= 0 else 0.0
    initial_point = (initial_x, initial_y, initial_z)

    initial_direction = v_normalize((input_theta_x_mrad * 1e-3, input_theta_y_mrad * 1e-3, 1.0))
    reference_x = (1.0, 0.0, 0.0)
    reference_u1 = v_normalize(v_sub(reference_x, v_scale(initial_direction, v_dot(reference_x, initial_direction))))
    reference_u2 = v_normalize(v_cross(initial_direction, reference_u1))
    polarization_angle_rad = (request.polarization_angle_deg * pi) / 180
    basis_u1 = v_add(v_scale(reference_u1, cos(polarization_angle_rad)), v_scale(reference_u2, sin(polarization_angle_rad)))
    basis_u2 = v_add(v_scale(reference_u1, -sin(polarization_angle_rad)), v_scale(reference_u2, cos(polarization_angle_rad)))

    max_trace_passes = max(150, 4 * total_passes)
    ray_trace = cell.trace_rays(initial_point, initial_direction, basis_u1, basis_u2, max_trace_passes)
    abcd_passes = max(total_passes, ray_trace["total_bounces"] + 1)
    abcd_x = compute_abcd_axis(
        mirror_distance_mm,
        mirror1_radius_mm,
        mirror2_radius_mm,
        wavelength_mm,
        input_waist_x_mm,
        input_waist_z_mm,
        abcd_passes,
        mode.M2x,
    )
    abcd_y = compute_abcd_axis(
        mirror_distance_mm,
        mirror1_radius_mm,
        mirror2_radius_mm,
        wavelength_mm,
        input_waist_y_mm,
        input_waist_z_mm,
        abcd_passes,
        mode.M2y,
    )

    response["status_message"] = ray_trace["exit_status"]
    response["ray_trace"] = {
        **ray_trace,
        "input_basis": {"u1": basis_u1, "u2": basis_u2},
        "input_point": initial_point,
        "cell_centers": {"mirror1": cell.C1, "mirror2": cell.C2},
    }
    response["beam_propagation"] = {"x": abcd_x, "y": abcd_y}

    return response
