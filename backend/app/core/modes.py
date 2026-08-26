from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import ceil, exp, factorial, pi, sqrt


@dataclass(frozen=True, slots=True)
class ModeConfig:
    type: str
    M2x: float
    M2y: float
    title: str
    norm: float
    peak_factor: float
    n: int | None = None
    m: int | None = None
    p: int | None = None
    l: int | None = None

    def as_dict(self) -> dict[str, float | int | str | None]:
        return {
            "type": self.type,
            "M2x": self.M2x,
            "M2y": self.M2y,
            "title": self.title,
            "norm": self.norm,
            "peak_factor": self.peak_factor,
            "n": self.n,
            "m": self.m,
            "p": self.p,
            "l": self.l,
        }


def hermite(n: int, x: float) -> float:
    if n == 0:
        return 1.0
    if n == 1:
        return 2 * x

    h0 = 1.0
    h1 = 2 * x
    hn = h1

    for index in range(1, n):
        hn = 2 * x * h1 - 2 * index * h0
        h0 = h1
        h1 = hn

    return hn


def laguerre(p: int, l: int, x: float) -> float:
    if p == 0:
        return 1.0
    if p == 1:
        return 1 + l - x

    l0 = 1.0
    l1 = 1 + l - x
    lp = l1

    for index in range(1, p):
        lp = ((2 * index + 1 + l - x) * l1 - (index + l) * l0) / (index + 1)
        l0 = l1
        l1 = lp

    return lp


@lru_cache(maxsize=64)
def compute_mode_norm(
    mode_type: str,
    hermite_n: int,
    hermite_m: int,
    laguerre_p: int,
    laguerre_l: int,
) -> tuple[float, float]:
    def sampled_maximum(function, upper_bound: float, target_spacing: float) -> float:
        sample_count = max(1, int(ceil(upper_bound / target_spacing)))
        maximum = 0.0
        for index in range(sample_count + 1):
            coordinate = (index * upper_bound) / sample_count
            maximum = max(maximum, function(coordinate))
        return maximum

    if mode_type == "hg":
        def hg_axis_peak(order: int) -> float:
            upper_bound = sqrt(2 * order + 1) + 3.0
            return sampled_maximum(
                lambda coordinate: (hermite(order, coordinate) ** 2) * exp(-(coordinate * coordinate)),
                upper_bound,
                1e-3,
            )

        max_intensity = hg_axis_peak(hermite_n) * hg_axis_peak(hermite_m)
        integral = (
            sqrt(pi)
            * (2**hermite_n)
            * factorial(hermite_n)
            * sqrt(pi)
            * (2**hermite_m)
            * factorial(hermite_m)
        )
        return 1.0 / max_intensity, (2 * max_intensity) / integral

    if mode_type == "lg":
        absolute_l = abs(laguerre_l)
        upper_bound = max(16.0, 4.0 * laguerre_p + 2.0 * absolute_l + 20.0)

        def lg_radial_intensity(radius_squared: float) -> float:
            laguerre_value = laguerre(laguerre_p, absolute_l, radius_squared)
            return (radius_squared**absolute_l) * (laguerre_value**2) * exp(-radius_squared)

        max_intensity = sampled_maximum(lg_radial_intensity, upper_bound, 2e-3)
        integral = pi * factorial(laguerre_p + absolute_l) / factorial(laguerre_p)
        return 1.0 / max_intensity, (2 * max_intensity) / integral

    return 1.0, 2 / pi


def build_mode_config(
    mode_type: str,
    hermite_n: int,
    hermite_m: int,
    laguerre_p: int,
    laguerre_l: int,
    custom_m2: float,
) -> ModeConfig:
    if mode_type == "hg":
        m2x = 2 * hermite_n + 1
        m2y = 2 * hermite_m + 1
        title = f"HG<sub>{hermite_n},{hermite_m}</sub>"
        norm, peak_factor = compute_mode_norm(mode_type, hermite_n, hermite_m, laguerre_p, laguerre_l)
        return ModeConfig(
            type=mode_type,
            n=hermite_n,
            m=hermite_m,
            M2x=m2x,
            M2y=m2y,
            title=title,
            norm=norm,
            peak_factor=peak_factor,
        )

    if mode_type == "lg":
        m2 = 2 * laguerre_p + abs(laguerre_l) + 1
        title = f"LG<sub>{laguerre_p},{laguerre_l}</sub>"
        norm, peak_factor = compute_mode_norm(mode_type, hermite_n, hermite_m, laguerre_p, laguerre_l)
        return ModeConfig(
            type=mode_type,
            p=laguerre_p,
            l=laguerre_l,
            M2x=m2,
            M2y=m2,
            title=title,
            norm=norm,
            peak_factor=peak_factor,
        )

    if mode_type == "custom":
        norm, peak_factor = compute_mode_norm(mode_type, hermite_n, hermite_m, laguerre_p, laguerre_l)
        return ModeConfig(
            type=mode_type,
            M2x=custom_m2,
            M2y=custom_m2,
            title=f"Custom M²={custom_m2:.2f}",
            norm=norm,
            peak_factor=peak_factor,
        )

    norm, peak_factor = compute_mode_norm(mode_type, hermite_n, hermite_m, laguerre_p, laguerre_l)
    return ModeConfig(
        type="tem00",
        M2x=1.0,
        M2y=1.0,
        title="Fundamental TEM00",
        norm=norm,
        peak_factor=peak_factor,
    )
