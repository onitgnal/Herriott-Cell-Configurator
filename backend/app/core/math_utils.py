from __future__ import annotations

from math import sqrt

Vector3 = tuple[float, float, float]


def v_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_norm(a: Vector3) -> float:
    return sqrt(v_dot(a, a))


def v_scale(a: Vector3, scalar: float) -> Vector3:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def v_normalize(a: Vector3) -> Vector3:
    norm = v_norm(a)
    return (a[0] / norm, a[1] / norm, a[2] / norm)


def v_cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
