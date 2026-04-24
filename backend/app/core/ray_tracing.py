from __future__ import annotations

from math import inf, sin, sqrt, cos

from backend.app.core.math_utils import Vector3, v_add, v_dot, v_norm, v_normalize, v_scale, v_sub

EPSILON = 1e-9


def _reflect(vector: Vector3, normal: Vector3) -> Vector3:
    return v_sub(vector, v_scale(normal, 2 * v_dot(vector, normal)))


class HerriottCell:
    def __init__(
        self,
        mirror_distance_mm: float,
        mirror1_radius_mm: float,
        mirror2_radius_mm: float,
        input_hole: tuple[float, float],
        output_hole: tuple[float, float],
        output_mirror: int,
        hole_radius_mm: float,
        mirror1_tilt: tuple[float, float],
        mirror2_tilt: tuple[float, float],
    ) -> None:
        self.L = mirror_distance_mm
        self.R1 = mirror1_radius_mm
        self.R2 = mirror2_radius_mm
        self.in_hole = input_hole
        self.out_hole = output_hole
        self.out_mirror = output_mirror
        self.hole_radius = hole_radius_mm

        tilt1_x = mirror1_tilt[0] * abs(mirror1_radius_mm)
        tilt1_y = mirror1_tilt[1] * abs(mirror1_radius_mm)
        tilt1_magnitude = sqrt(tilt1_x * tilt1_x + tilt1_y * tilt1_y) / abs(mirror1_radius_mm)
        self.C1 = (
            abs(mirror1_radius_mm) * sin(tilt1_magnitude) * (tilt1_x / (tilt1_magnitude * abs(mirror1_radius_mm)))
            if tilt1_magnitude > EPSILON
            else 0.0,
            abs(mirror1_radius_mm) * sin(tilt1_magnitude) * (tilt1_y / (tilt1_magnitude * abs(mirror1_radius_mm)))
            if tilt1_magnitude > EPSILON
            else 0.0,
            mirror1_radius_mm * cos(tilt1_magnitude),
        )

        tilt2_x = mirror2_tilt[0] * abs(mirror2_radius_mm)
        tilt2_y = mirror2_tilt[1] * abs(mirror2_radius_mm)
        tilt2_magnitude = sqrt(tilt2_x * tilt2_x + tilt2_y * tilt2_y) / abs(mirror2_radius_mm)
        self.C2 = (
            abs(mirror2_radius_mm) * sin(tilt2_magnitude) * (tilt2_x / (tilt2_magnitude * abs(mirror2_radius_mm)))
            if tilt2_magnitude > EPSILON
            else 0.0,
            abs(mirror2_radius_mm) * sin(tilt2_magnitude) * (tilt2_y / (tilt2_magnitude * abs(mirror2_radius_mm)))
            if tilt2_magnitude > EPSILON
            else 0.0,
            mirror_distance_mm - mirror2_radius_mm * cos(tilt2_magnitude),
        )

    def intersect_mirror(self, point: Vector3, direction: Vector3, mirror_number: int) -> dict[str, Vector3 | None]:
        center = self.C1 if mirror_number == 1 else self.C2
        radius = self.R1 if mirror_number == 1 else self.R2

        delta = v_sub(point, center)
        b = v_dot(direction, delta)
        c = v_dot(delta, delta) - radius * radius
        discriminant = b * b - c

        if discriminant < 0:
            return {"P_int": None, "normal": None}

        t1 = -b - sqrt(discriminant)
        t2 = -b + sqrt(discriminant)
        valid_ts = [value for value in (t1, t2) if value > EPSILON]

        if not valid_ts:
            return {"P_int": None, "normal": None}

        distance = min(valid_ts)
        intersection = v_add(point, v_scale(direction, distance))
        normal = v_scale(v_sub(center, intersection), 1 / radius)
        return {"P_int": intersection, "normal": normal}

    def trace_rays(
        self,
        point0: Vector3,
        direction0: Vector3,
        basis_u1: Vector3,
        basis_u2: Vector3,
        max_passes: int = 150,
    ) -> dict[str, object]:
        points: list[Vector3] = [point0]
        mirror_hits: dict[str, list[dict[str, object]]] = {"1": []}
        center_hits: list[dict[str, Vector3]] = []
        mirror2_hits: list[dict[str, object]] = []

        point = point0
        direction = v_normalize(direction0)
        u1 = v_normalize(basis_u1)
        u2 = v_normalize(basis_u2)
        target_mirror = 2
        exit_status = "Trapped (Max Passes)"
        bounce = 0

        for bounce in range(max_passes):
            intersection_data = self.intersect_mirror(point, direction, target_mirror)
            intersection = intersection_data["P_int"]
            normal = intersection_data["normal"]

            if abs(direction[2]) > EPSILON:
                t_center = (self.L / 2 - point[2]) / direction[2]
            else:
                t_center = inf

            t_mirror = v_norm(v_sub(intersection, point)) if intersection is not None else inf

            if t_center > 0 and t_center < t_mirror:
                center_point = v_add(point, v_scale(direction, t_center))
                center_hits.append({"P": center_point, "u1": u1, "u2": u2})

            if intersection is None or normal is None:
                exit_status = f"Escaped cell at pass {bounce}"
                break

            points.append(intersection)
            escaped = False
            reflected_direction = v_normalize(_reflect(direction, normal))
            reflected_u1 = v_normalize(_reflect(u1, normal))
            reflected_u2 = v_normalize(_reflect(u2, normal))
            hit_record: dict[str, object] = {
                "P": intersection,
                "u1": u1,
                "u2": u2,
                "v_in": direction,
                "v_out": reflected_direction,
                "normal": normal,
            }

            if target_mirror == 1:
                mirror_hits["1"].append(hit_record)

                if self.out_mirror == 1:
                    output_distance = sqrt(
                        (intersection[0] - self.out_hole[0]) ** 2 + (intersection[1] - self.out_hole[1]) ** 2,
                    )
                    if output_distance <= self.hole_radius:
                        exit_status = f"Exited cleanly pass {bounce + 1} (Out Hole)"
                        hit_record["v_out"] = None
                        escaped = True

                if not escaped and bounce > 0:
                    input_distance = sqrt(
                        (intersection[0] - self.in_hole[0]) ** 2 + (intersection[1] - self.in_hole[1]) ** 2,
                    )
                    if input_distance <= self.hole_radius:
                        exit_status = f"Escaped pass {bounce + 1} (In Hole)"
                        hit_record["v_out"] = None
                        escaped = True
            else:
                mirror2_hits.append(hit_record)
                if self.out_mirror == 2:
                    output_distance = sqrt(
                        (intersection[0] - self.out_hole[0]) ** 2 + (intersection[1] - self.out_hole[1]) ** 2,
                    )
                    if output_distance <= self.hole_radius:
                        exit_status = f"Exited cleanly pass {bounce + 1} (Out Hole)"
                        hit_record["v_out"] = None
                        escaped = True

            if escaped:
                break

            direction = reflected_direction
            u1 = reflected_u1
            u2 = reflected_u2
            point = intersection
            target_mirror = 2 if target_mirror == 1 else 1

        mirror_hits["2"] = mirror2_hits

        return {
            "points": points,
            "mirror_hits": mirror_hits,
            "center_hits": center_hits,
            "exit_status": exit_status,
            "total_bounces": bounce,
        }
