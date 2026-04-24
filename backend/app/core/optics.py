from __future__ import annotations

from math import pi, sqrt


def propagate_q(q: dict[str, float], a: float, b: float, c: float, d: float) -> dict[str, float]:
    numerator_real = a * q["r"] + b
    numerator_imag = a * q["i"]
    denominator_real = c * q["r"] + d
    denominator_imag = c * q["i"]
    denominator_magnitude_squared = denominator_real * denominator_real + denominator_imag * denominator_imag

    return {
        "r": (numerator_real * denominator_real + numerator_imag * denominator_imag) / denominator_magnitude_squared,
        "i": (numerator_imag * denominator_real - numerator_real * denominator_imag) / denominator_magnitude_squared,
    }


def get_waist(q: dict[str, float], wavelength_mm: float, m2: float) -> float:
    magnitude_squared = q["r"] * q["r"] + q["i"] * q["i"]
    inverse_q_imaginary = -q["i"] / magnitude_squared
    return sqrt((m2 * wavelength_mm) / (pi * -inverse_q_imaginary))


def compute_abcd_axis(
    mirror_distance_mm: float,
    mirror1_radius_mm: float,
    mirror2_radius_mm: float,
    wavelength_mm: float,
    input_waist_mm: float,
    input_waist_position_mm: float,
    max_passes: int,
    m2: float,
) -> dict[str, list[float]]:
    rayleigh_range = (pi * input_waist_mm * input_waist_mm) / (m2 * wavelength_mm)
    q = {"r": -input_waist_position_mm, "i": rayleigh_range}

    z_vals: list[float] = []
    w_vals: list[float] = []
    mirror_waists: list[float] = []
    center_waists: list[float] = []
    steps_per_pass = 20
    total_z = 0.0

    for current_pass in range(max_passes):
        for step in range(steps_per_pass + 1):
            distance = (step / steps_per_pass) * mirror_distance_mm
            propagated = {"r": q["r"] + distance, "i": q["i"]}
            waist = get_waist(propagated, wavelength_mm, m2)

            z_vals.append(total_z + distance)
            w_vals.append(waist)

            if step == 0:
                mirror_waists.append(waist)
            if step == steps_per_pass // 2:
                center_waists.append(waist)

        total_z += mirror_distance_mm
        q_end = {"r": q["r"] + mirror_distance_mm, "i": q["i"]}
        current_radius = mirror2_radius_mm if current_pass % 2 == 0 else mirror1_radius_mm
        q = propagate_q(q_end, 1, 0, -2 / current_radius, 1)

    mirror_waists.append(get_waist(q, wavelength_mm, m2))

    return {
        "z_vals": z_vals,
        "w_vals": w_vals,
        "w_mirrors_w": mirror_waists,
        "w_center_w": center_waists,
    }
