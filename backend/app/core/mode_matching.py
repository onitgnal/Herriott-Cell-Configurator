from __future__ import annotations

from functools import lru_cache
from math import inf, pi, sqrt
from typing import Any

import numpy as np


STANDARD_FOCAL_LENGTHS_MM = np.asarray(
    [50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 750, 1000, 1250, 1500, 2000, 2500],
    dtype=np.float64,
)
MIN_AUTO_DISTANCE_MM = 20.0
MAX_AUTO_DISTANCE_MM = 3000.0
AUTO_PHASE_PLATE_TO_LENS1_MM = 25.0


def thin_lens_q(q_value: complex | np.ndarray, focal_length_mm: float | np.ndarray) -> complex | np.ndarray:
    return q_value / (1.0 - q_value / focal_length_mm)


def beam_radius_from_q(q_value: complex | np.ndarray, wavelength_mm: float, m2: float) -> float | np.ndarray:
    inverse_q = 1.0 / q_value
    return np.sqrt((m2 * wavelength_mm) / (pi * np.maximum(-inverse_q.imag, 1e-18)))


def waist_parameters_from_q(q_value: complex, wavelength_mm: float, m2: float) -> tuple[float, float]:
    waist_mm = sqrt(max(m2 * wavelength_mm * q_value.imag / pi, 1e-18))
    return waist_mm, -q_value.real


def propagate_telescope_q(
    input_q: complex | np.ndarray,
    focal_lengths_mm: tuple[float, float, float] | np.ndarray,
    distances_mm: tuple[float, float, float, float] | np.ndarray,
) -> complex | np.ndarray:
    d0, d12, d23, d3m = distances_mm
    f1, f2, f3 = focal_lengths_mm
    q_value = thin_lens_q(input_q + d0, f1)
    q_value = thin_lens_q(q_value + d12, f2)
    q_value = thin_lens_q(q_value + d23, f3)
    return q_value + d3m


def telescope_q_planes(
    input_q: complex,
    focal_lengths_mm: tuple[float, float, float],
    distances_mm: tuple[float, float, float, float],
) -> tuple[list[complex], list[complex]]:
    """Return incoming and outgoing q at input, each lens, and M1."""
    d0, d12, d23, d3m = distances_mm
    f1, f2, f3 = focal_lengths_mm
    incoming = [input_q]
    outgoing = [input_q]

    q_in = input_q + d0
    q_out = complex(thin_lens_q(q_in, f1))
    incoming.append(q_in)
    outgoing.append(q_out)

    q_in = q_out + d12
    q_out = complex(thin_lens_q(q_in, f2))
    incoming.append(q_in)
    outgoing.append(q_out)

    q_in = q_out + d23
    q_out = complex(thin_lens_q(q_in, f3))
    incoming.append(q_in)
    outgoing.append(q_out)

    q_in = q_out + d3m
    incoming.append(q_in)
    outgoing.append(q_in)
    return incoming, outgoing


def _normalized_match_error(q_x: complex, q_y: complex, target_q: complex) -> float:
    scale = max(abs(target_q), 1.0)
    return max(abs(q_x - target_q), abs(q_y - target_q)) / scale


def _minimum_sampled_radius_mm(
    input_q_x: complex,
    input_q_y: complex,
    focal_lengths_mm: tuple[float, float, float],
    distances_mm: tuple[float, float, float, float],
    wavelength_mm: float,
    m2_x: float,
    m2_y: float,
) -> float:
    incoming_x, outgoing_x = telescope_q_planes(input_q_x, focal_lengths_mm, distances_mm)
    incoming_y, outgoing_y = telescope_q_planes(input_q_y, focal_lengths_mm, distances_mm)
    minimum = inf
    for q_values, m2 in ((incoming_x + outgoing_x, m2_x), (incoming_y + outgoing_y, m2_y)):
        for q_value in q_values:
            minimum = min(minimum, float(beam_radius_from_q(q_value, wavelength_mm, m2)))
    return minimum


def _objective(
    variable_distances_mm: np.ndarray,
    *,
    input_q_x: complex,
    input_q_y: complex,
    target_q: complex,
    focal_lengths_mm: tuple[float, float, float],
    d0_mm: float,
    wavelength_mm: float,
    m2_x: float,
    m2_y: float,
) -> float:
    distances = (d0_mm, *map(float, variable_distances_mm))
    q_x = complex(propagate_telescope_q(input_q_x, focal_lengths_mm, distances))
    q_y = complex(propagate_telescope_q(input_q_y, focal_lengths_mm, distances))
    match_error = _normalized_match_error(q_x, q_y, target_q)
    total_length = sum(distances)
    compactness = 1e-7 * total_length
    return match_error + compactness


def _bounded_nelder_mead(
    objective: Any,
    initial: np.ndarray,
    *,
    lower: float = MIN_AUTO_DISTANCE_MM,
    upper: float = MAX_AUTO_DISTANCE_MM,
    iterations: int = 80,
) -> tuple[np.ndarray, float]:
    dimension = initial.size
    simplex = [np.clip(np.asarray(initial, dtype=np.float64), lower, upper)]
    for axis in range(dimension):
        vertex = simplex[0].copy()
        vertex[axis] = np.clip((vertex[axis] * 1.12) + 3.0, lower, upper)
        simplex.append(vertex)
    values = [float(objective(vertex)) for vertex in simplex]

    for _ in range(iterations):
        order = np.argsort(values)
        simplex = [simplex[index] for index in order]
        values = [values[index] for index in order]
        centroid = sum(simplex[:-1]) / dimension

        reflected = np.clip(centroid + (centroid - simplex[-1]), lower, upper)
        reflected_value = float(objective(reflected))
        if values[0] <= reflected_value < values[-2]:
            simplex[-1], values[-1] = reflected, reflected_value
            continue
        if reflected_value < values[0]:
            expanded = np.clip(centroid + 2.0 * (reflected - centroid), lower, upper)
            expanded_value = float(objective(expanded))
            if expanded_value < reflected_value:
                simplex[-1], values[-1] = expanded, expanded_value
            else:
                simplex[-1], values[-1] = reflected, reflected_value
            continue

        contracted = np.clip(centroid + 0.5 * (simplex[-1] - centroid), lower, upper)
        contracted_value = float(objective(contracted))
        if contracted_value < values[-1]:
            simplex[-1], values[-1] = contracted, contracted_value
            continue

        for index in range(1, dimension + 1):
            simplex[index] = np.clip(simplex[0] + 0.5 * (simplex[index] - simplex[0]), lower, upper)
            values[index] = float(objective(simplex[index]))

    best_index = int(np.argmin(values))
    return simplex[best_index], values[best_index]


def _optimize_distances(
    input_q_x: complex,
    input_q_y: complex,
    target_q: complex,
    focal_lengths_mm: tuple[float, float, float],
    d0_mm: float,
    wavelength_mm: float,
    m2_x: float,
    m2_y: float,
    initial_distances: np.ndarray | None = None,
) -> tuple[tuple[float, float, float, float], float]:
    rng = np.random.default_rng(0x484747 + int(sum(abs(value) for value in focal_lengths_mm)))
    if initial_distances is None:
        candidates = np.exp(
            rng.uniform(
                np.log(MIN_AUTO_DISTANCE_MM),
                np.log(MAX_AUTO_DISTANCE_MM),
                size=(600, 3),
            ),
        )
    else:
        initial = np.asarray(initial_distances, dtype=np.float64)
        jitter = np.exp(rng.normal(0.0, 0.65, size=(160, 3)))
        candidates = np.vstack((initial, np.clip(initial * jitter, MIN_AUTO_DISTANCE_MM, MAX_AUTO_DISTANCE_MM)))

    objective = lambda distances: _objective(
        distances,
        input_q_x=input_q_x,
        input_q_y=input_q_y,
        target_q=target_q,
        focal_lengths_mm=focal_lengths_mm,
        d0_mm=d0_mm,
        wavelength_mm=wavelength_mm,
        m2_x=m2_x,
        m2_y=m2_y,
    )
    scores = np.asarray([objective(candidate) for candidate in candidates])
    best_seed_indices = np.argpartition(scores, min(3, scores.size - 1))[:3]

    best_distances = candidates[int(best_seed_indices[0])]
    best_score = float(objective(best_distances))
    for seed_index in best_seed_indices:
        refined, score = _bounded_nelder_mead(objective, candidates[int(seed_index)])
        if score < best_score:
            best_distances, best_score = refined, score

    distances = (d0_mm, *map(float, best_distances))
    q_x = complex(propagate_telescope_q(input_q_x, focal_lengths_mm, distances))
    q_y = complex(propagate_telescope_q(input_q_y, focal_lengths_mm, distances))
    return distances, _normalized_match_error(q_x, q_y, target_q)


@lru_cache(maxsize=256)
def _auto_design_cached(
    input_q_x: complex,
    input_q_y: complex,
    target_q: complex,
    wavelength_mm: float,
    m2_x: float,
    m2_y: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float, float], float]:
    rng = np.random.default_rng(0x4D5043)
    sample_count = 24000
    catalog_indices = rng.integers(0, STANDARD_FOCAL_LENGTHS_MM.size, size=(sample_count, 3))
    focal_samples = STANDARD_FOCAL_LENGTHS_MM[catalog_indices]
    distance_samples = np.exp(
        rng.uniform(
            np.log(MIN_AUTO_DISTANCE_MM),
            np.log(MAX_AUTO_DISTANCE_MM),
            size=(sample_count, 3),
        ),
    )

    q_x = np.full(sample_count, input_q_x + AUTO_PHASE_PLATE_TO_LENS1_MM, dtype=np.complex128)
    q_y = np.full(sample_count, input_q_y + AUTO_PHASE_PLATE_TO_LENS1_MM, dtype=np.complex128)
    for lens_index in range(3):
        q_x = thin_lens_q(q_x, focal_samples[:, lens_index])
        q_y = thin_lens_q(q_y, focal_samples[:, lens_index])
        q_x = q_x + distance_samples[:, lens_index]
        q_y = q_y + distance_samples[:, lens_index]

    scale = max(abs(target_q), 1.0)
    scores = np.maximum(np.abs(q_x - target_q), np.abs(q_y - target_q)) / scale
    scores += 1e-7 * (AUTO_PHASE_PLATE_TO_LENS1_MM + np.sum(distance_samples, axis=1))
    promising = np.argpartition(scores, 16)[:16]

    unique_lenses: dict[tuple[float, float, float], np.ndarray] = {}
    for index in promising[np.argsort(scores[promising])]:
        focal_lengths = tuple(map(float, focal_samples[int(index)]))
        unique_lenses.setdefault(focal_lengths, distance_samples[int(index)])

    best: tuple[tuple[float, float, float], tuple[float, float, float, float], float] | None = None
    for focal_lengths, initial_distances in list(unique_lenses.items())[:4]:
        distances, match_error = _optimize_distances(
            input_q_x,
            input_q_y,
            target_q,
            focal_lengths,
            AUTO_PHASE_PLATE_TO_LENS1_MM,
            wavelength_mm,
            m2_x,
            m2_y,
            initial_distances,
        )
        candidate = (focal_lengths, distances, match_error)
        if best is None or (match_error, sum(distances)) < (best[2], sum(best[1])):
            best = candidate

    if best is None:
        raise RuntimeError("No practical three-lens mode-matching design could be generated.")
    return best


def resolve_mode_matching(
    *,
    mode: str,
    input_beam_radius_mm: float,
    requested_focal_lengths_mm: tuple[float, float, float],
    requested_distances_mm: tuple[float, float, float, float],
    target_q_medium: complex,
    wavelength_vacuum_mm: float,
    refractive_index: float,
    m2_x: float,
    m2_y: float,
) -> dict[str, Any]:
    target_q_air = target_q_medium / refractive_index
    input_q_x = complex(0.0, pi * input_beam_radius_mm**2 / (m2_x * wavelength_vacuum_mm))
    input_q_y = complex(0.0, pi * input_beam_radius_mm**2 / (m2_y * wavelength_vacuum_mm))

    if mode == "auto":
        focal_lengths, distances, match_error = _auto_design_cached(
            input_q_x,
            input_q_y,
            target_q_air,
            wavelength_vacuum_mm,
            m2_x,
            m2_y,
        )
    elif mode == "fixed_lenses":
        focal_lengths = requested_focal_lengths_mm
        distances, match_error = _optimize_distances(
            input_q_x,
            input_q_y,
            target_q_air,
            focal_lengths,
            requested_distances_mm[0],
            wavelength_vacuum_mm,
            m2_x,
            m2_y,
            np.asarray(requested_distances_mm[1:]),
        )
    else:
        focal_lengths = requested_focal_lengths_mm
        distances = requested_distances_mm
        achieved_x = complex(propagate_telescope_q(input_q_x, focal_lengths, distances))
        achieved_y = complex(propagate_telescope_q(input_q_y, focal_lengths, distances))
        match_error = _normalized_match_error(achieved_x, achieved_y, target_q_air)

    achieved_q_air_x = complex(propagate_telescope_q(input_q_x, focal_lengths, distances))
    achieved_q_air_y = complex(propagate_telescope_q(input_q_y, focal_lengths, distances))
    achieved_q_medium_x = achieved_q_air_x * refractive_index
    achieved_q_medium_y = achieved_q_air_y * refractive_index
    minimum_radius_mm = _minimum_sampled_radius_mm(
        input_q_x,
        input_q_y,
        focal_lengths,
        distances,
        wavelength_vacuum_mm,
        m2_x,
        m2_y,
    )
    success_threshold = 2e-3 if abs(m2_x - m2_y) <= 1e-12 else 2e-2
    success = match_error <= success_threshold
    if success:
        message = "Mode matched to the MPC eigenmode."
    elif abs(m2_x - m2_y) > 1e-12:
        message = "Closest shared spherical-lens solution; unequal x/y M² cannot generally be matched exactly."
    else:
        message = "Closest solution for the selected lenses and mechanical distance limits."

    total_length_mm = float(sum(distances))
    input_plane_z_mm = -total_length_mm
    lens_positions_mm = [
        input_plane_z_mm + distances[0],
        input_plane_z_mm + distances[0] + distances[1],
        input_plane_z_mm + distances[0] + distances[1] + distances[2],
    ]
    return {
        "mode": mode,
        "success": success,
        "message": message,
        "input_beam_radius_mm": input_beam_radius_mm,
        "focal_lengths_mm": list(focal_lengths),
        "distances_mm": list(distances),
        "total_length_mm": total_length_mm,
        "lens_positions_mm": lens_positions_mm,
        "input_plane_z_mm": input_plane_z_mm,
        "relative_q_error": float(match_error),
        "minimum_beam_radius_mm": minimum_radius_mm,
        "target_q_air_real_mm": target_q_air.real,
        "target_q_air_imag_mm": target_q_air.imag,
        "achieved_q_air_x_real_mm": achieved_q_air_x.real,
        "achieved_q_air_x_imag_mm": achieved_q_air_x.imag,
        "achieved_q_air_y_real_mm": achieved_q_air_y.real,
        "achieved_q_air_y_imag_mm": achieved_q_air_y.imag,
        "achieved_q_medium_x": achieved_q_medium_x,
        "achieved_q_medium_y": achieved_q_medium_y,
        "input_q_air_x": input_q_x,
        "input_q_air_y": input_q_y,
    }


def sample_telescope_axis(
    input_q: complex,
    focal_lengths_mm: tuple[float, float, float],
    distances_mm: tuple[float, float, float, float],
    wavelength_mm: float,
    m2: float,
    samples_per_segment: int = 32,
) -> dict[str, list[float]]:
    total_length = sum(distances_mm)
    current_z = -total_length
    current_q = input_q
    z_values: list[float] = []
    radius_values: list[float] = []
    for distance, focal_length in zip(distances_mm[:3], focal_lengths_mm, strict=True):
        for index in range(samples_per_segment + 1):
            if z_values and index == 0:
                continue
            offset = distance * index / samples_per_segment
            q_value = current_q + offset
            z_values.append(current_z + offset)
            radius_values.append(float(beam_radius_from_q(q_value, wavelength_mm, m2)))
        current_q = complex(thin_lens_q(current_q + distance, focal_length))
        current_z += distance

    final_distance = distances_mm[3]
    for index in range(1, samples_per_segment + 1):
        offset = final_distance * index / samples_per_segment
        q_value = current_q + offset
        z_values.append(current_z + offset)
        radius_values.append(float(beam_radius_from_q(q_value, wavelength_mm, m2)))
    return {"z_vals": z_values, "w_vals": radius_values}


def q_at_configured_output(
    start_q_medium: complex,
    mirror_distance_mm: float,
    mirror1_radius_mm: float,
    mirror2_radius_mm: float,
    total_legs: int,
) -> complex:
    q_value = start_q_medium
    for leg_index in range(total_legs):
        q_value += mirror_distance_mm
        if leg_index == total_legs - 1:
            break
        end_mirror_radius = mirror2_radius_mm if leg_index % 2 == 0 else mirror1_radius_mm
        q_value = complex(thin_lens_q(q_value, end_mirror_radius / 2.0))
    return q_value


def sample_free_space_axis(
    start_q: complex,
    distance_mm: float,
    wavelength_mm: float,
    m2: float,
    start_z_mm: float,
    samples: int = 64,
) -> dict[str, list[float]]:
    z_values = np.linspace(0.0, distance_mm, samples + 1)
    radii = beam_radius_from_q(start_q + z_values, wavelength_mm, m2)
    return {
        "z_vals": list(map(float, start_z_mm + z_values)),
        "w_vals": list(map(float, radii)),
    }
