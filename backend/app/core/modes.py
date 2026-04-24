from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp, pi


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
    max_intensity = 0.0
    sum_intensity = 0.0
    ds = 0.1
    sx = -4.0

    while sx <= 4.0:
        sy = -4.0
        while sy <= 4.0:
            exp_term = exp(-0.5 * (sx * sx + sy * sy))

            if mode_type == "hg":
                hx = hermite(hermite_n, sx)
                hy = hermite(hermite_m, sy)
                field = hx * hy * exp_term
                intensity = field * field
            elif mode_type == "lg":
                r2 = sx * sx + sy * sy
                laguerre_value = laguerre(laguerre_p, laguerre_l, r2)
                field = (r2 ** (abs(laguerre_l) / 2)) * laguerre_value * exp_term
                intensity = field * field
            else:
                intensity = exp_term * exp_term

            if intensity > max_intensity:
                max_intensity = intensity
            sum_intensity += intensity
            sy += ds
        sx += ds

    sum_intensity *= ds * ds

    if max_intensity > 0:
        return (1.0 / max_intensity, (2 * max_intensity) / sum_intensity)

    return (1.0, 2 / pi)


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
