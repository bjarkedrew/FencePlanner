from __future__ import annotations
from math import atan2, cos, hypot, pi, sin
from typing import List
from .models import Point, FenceLine

def polygon_area(poly: List[Point]) -> float:
    if len(poly) < 3:
        return 0.0
    s = 0.0
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        s += poly[i].x * poly[j].y - poly[j].x * poly[i].y
    return abs(s) / 2.0

def signed_area(poly: List[Point]) -> float:
    s = 0.0
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        s += poly[i].x * poly[j].y - poly[j].x * poly[i].y
    return s / 2.0

def ensure_ccw(poly: List[Point]) -> List[Point]:
    return poly if signed_area(poly) >= 0 else list(reversed(poly))

def dot(p: Point, ux: float, uy: float) -> float:
    return p.x * ux + p.y * uy

def cross_from(a: Point, dx: float, dy: float, p: Point) -> float:
    return dx * (p.y - a.y) - dy * (p.x - a.x)

def clip_polygon_by_projection(poly: List[Point], ux: float, uy: float, limit: float, keep_less_equal: bool) -> List[Point]:
    if not poly:
        return []
    out = []
    def inside(p):
        v = dot(p, ux, uy)
        return v <= limit + 1e-9 if keep_less_equal else v >= limit - 1e-9
    def intersect(a, b):
        da = dot(a, ux, uy) - limit
        db = dot(b, ux, uy) - limit
        t = da / (da - db) if abs(da - db) > 1e-12 else 0.0
        return Point(a.x + t * (b.x - a.x), a.y + t * (b.y - a.y))
    prev = poly[-1]
    prev_in = inside(prev)
    for cur in poly:
        cur_in = inside(cur)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append(cur)
        elif prev_in:
            out.append(intersect(prev, cur))
        prev, prev_in = cur, cur_in
    cleaned = []
    for p in out:
        if not cleaned or hypot(cleaned[-1].x-p.x, cleaned[-1].y-p.y) > 1e-6:
            cleaned.append(p)
    if len(cleaned) > 1 and hypot(cleaned[0].x-cleaned[-1].x, cleaned[0].y-cleaned[-1].y) < 1e-6:
        cleaned.pop()
    return cleaned

def strip_polygon(poly, ux, uy, low, high):
    part = clip_polygon_by_projection(poly, ux, uy, high, True)
    return clip_polygon_by_projection(part, ux, uy, low, False)

def projection_range(poly, ux, uy):
    vals = [dot(p, ux, uy) for p in poly]
    return min(vals), max(vals)

def area_less_equal(poly, ux, uy, limit):
    return polygon_area(clip_polygon_by_projection(poly, ux, uy, limit, True))

def find_cut_for_area(poly, ux, uy, target_area):
    lo, hi = projection_range(poly, ux, uy)
    for _ in range(60):
        mid = (lo + hi) / 2
        if area_less_equal(poly, ux, uy, mid) < target_area:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def line_intersections(poly, ux, uy, cut):
    pts = []
    for i in range(len(poly)):
        a = poly[i]
        b = poly[(i+1) % len(poly)]
        da = dot(a, ux, uy) - cut
        db = dot(b, ux, uy) - cut
        if abs(da) < 1e-8:
            pts.append(a)
        if da * db < -1e-10:
            t = da / (da - db)
            pts.append(Point(a.x + t*(b.x-a.x), a.y + t*(b.y-a.y)))
        elif abs(db) < 1e-8:
            pts.append(b)
    unique = []
    for p in pts:
        if not any(hypot(p.x-q.x, p.y-q.y) < 0.01 for q in unique):
            unique.append(p)
    if len(unique) <= 2:
        return unique
    best = (unique[0], unique[1])
    best_d = -1
    for i in range(len(unique)):
        for j in range(i+1, len(unique)):
            d = hypot(unique[i].x-unique[j].x, unique[i].y-unique[j].y)
            if d > best_d:
                best_d = d
                best = (unique[i], unique[j])
    return [best[0], best[1]]

def generate_equal_area_fences(boundary, a, b, fold_count):
    if fold_count < 2:
        raise ValueError("Antal folde skal være mindst 2")
    boundary = ensure_ccw(boundary)
    dx = b.x - a.x
    dy = b.y - a.y
    length = hypot(dx, dy)
    if length < 0.01:
        raise ValueError("A-B linjen er for kort")
    tx, ty = dx/length, dy/length
    ux, uy = -ty, tx
    total = polygon_area(boundary)
    target = total / fold_count
    cuts = [find_cut_for_area(boundary, ux, uy, target*i) for i in range(1, fold_count)]
    fences = []
    for idx, cut in enumerate(cuts, 1):
        pts = line_intersections(boundary, ux, uy, cut)
        if len(pts) < 2:
            continue
        p1, p2 = pts[0], pts[1]
        if (p2.x-p1.x)*tx + (p2.y-p1.y)*ty < 0:
            p1, p2 = p2, p1
        angle_rad = atan2(p2.x - p1.x, p2.y - p1.y)
        fences.append(FenceLine(f"Hegn {idx}", p1, p2, angle_rad, hypot(p2.x-p1.x, p2.y-p1.y)))
    lo, hi = projection_range(boundary, ux, uy)
    bounds = [lo] + cuts + [hi]
    fold_areas = [polygon_area(strip_polygon(boundary, ux, uy, bounds[i], bounds[i+1])) for i in range(fold_count)]
    return fences, fold_areas

def clip_polygon_by_ray_side(poly: List[Point], origin: Point, angle: float, keep_left: bool) -> List[Point]:
    if not poly:
        return []
    dx, dy = cos(angle), sin(angle)
    out = []

    def inside(p):
        v = cross_from(origin, dx, dy, p)
        return v >= -1e-9 if keep_left else v <= 1e-9

    def intersect(p1, p2):
        v1 = cross_from(origin, dx, dy, p1)
        v2 = cross_from(origin, dx, dy, p2)
        t = v1 / (v1 - v2) if abs(v1 - v2) > 1e-12 else 0.0
        return Point(p1.x + t * (p2.x - p1.x), p1.y + t * (p2.y - p1.y))

    prev = poly[-1]
    prev_in = inside(prev)
    for cur in poly:
        cur_in = inside(cur)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append(cur)
        elif prev_in:
            out.append(intersect(prev, cur))
        prev, prev_in = cur, cur_in
    cleaned = []
    for p in out:
        if not cleaned or hypot(cleaned[-1].x - p.x, cleaned[-1].y - p.y) > 1e-6:
            cleaned.append(p)
    if len(cleaned) > 1 and hypot(cleaned[0].x - cleaned[-1].x, cleaned[0].y - cleaned[-1].y) < 1e-6:
        cleaned.pop()
    return cleaned

def fan_sector_polygon(boundary: List[Point], origin: Point, low_angle: float, high_angle: float) -> List[Point]:
    part = clip_polygon_by_ray_side(boundary, origin, low_angle, keep_left=True)
    return clip_polygon_by_ray_side(part, origin, high_angle, keep_left=False)

def fan_angle_range(boundary: List[Point], a: Point, b: Point):
    center = atan2(b.y - a.y, b.x - a.x)
    unwrapped = []
    for p in boundary:
        angle = atan2(p.y - a.y, p.x - a.x)
        while angle - center <= -pi:
            angle += 2 * pi
        while angle - center > pi:
            angle -= 2 * pi
        unwrapped.append(angle)
    low = min(unwrapped)
    high = max(unwrapped)
    if high - low >= pi * 1.98:
        raise ValueError("Vifte virker bedst, naar A ligger ved kanten/udenfor marken og B peger ind gennem marken.")
    return low, high

def fan_area_less_equal(boundary: List[Point], a: Point, low_angle: float, angle: float) -> float:
    return polygon_area(fan_sector_polygon(boundary, a, low_angle, angle))

def find_fan_cut_for_area(boundary: List[Point], a: Point, low_angle: float, high_angle: float, target_area: float):
    lo, hi = low_angle, high_angle
    for _ in range(60):
        mid = (lo + hi) / 2
        if fan_area_less_equal(boundary, a, low_angle, mid) < target_area:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def ray_polygon_endpoint(boundary: List[Point], origin: Point, angle: float) -> Point | None:
    dx, dy = cos(angle), sin(angle)
    hits = []
    for i in range(len(boundary)):
        p = boundary[i]
        q = boundary[(i + 1) % len(boundary)]
        sx, sy = q.x - p.x, q.y - p.y
        denom = dx * sy - dy * sx
        if abs(denom) < 1e-10:
            continue
        px, py = p.x - origin.x, p.y - origin.y
        t = (px * sy - py * sx) / denom
        u = (px * dy - py * dx) / denom
        if t >= -1e-8 and -1e-8 <= u <= 1 + 1e-8:
            hits.append((t, Point(origin.x + t * dx, origin.y + t * dy)))
    if not hits:
        return None
    return max(hits, key=lambda item: item[0])[1]

def generate_fan_equal_area_fences(boundary, a, b, fold_count, apex_gap_m=0.0):
    if fold_count < 2:
        raise ValueError("Antal zoner skal vaere mindst 2")
    boundary = ensure_ccw(boundary)
    if hypot(b.x - a.x, b.y - a.y) < 0.01:
        raise ValueError("A-B retningen er for kort")
    low, high = fan_angle_range(boundary, a, b)
    total = polygon_area(boundary)
    target = total / fold_count
    cuts = [find_fan_cut_for_area(boundary, a, low, high, target * i) for i in range(1, fold_count)]
    fences = []
    for idx, angle in enumerate(cuts, 1):
        end = ray_polygon_endpoint(boundary, a, angle)
        if not end:
            continue
        start = Point(a.x + cos(angle) * max(0.0, apex_gap_m), a.y + sin(angle) * max(0.0, apex_gap_m))
        if hypot(end.x - start.x, end.y - start.y) < 0.01:
            start = a
        angle_rad = atan2(end.x - start.x, end.y - start.y)
        fences.append(FenceLine(f"Hegn {idx}", start, end, angle_rad, hypot(end.x - start.x, end.y - start.y)))
    bounds = [low] + cuts + [high]
    fold_areas = [polygon_area(fan_sector_polygon(boundary, a, bounds[i], bounds[i + 1])) for i in range(fold_count)]
    return fences, fold_areas

def line_intersection_point(a1: Point, b1: Point, a2: Point, b2: Point) -> Point | None:
    r_x, r_y = b1.x - a1.x, b1.y - a1.y
    s_x, s_y = b2.x - a2.x, b2.y - a2.y
    denom = r_x * s_y - r_y * s_x
    if abs(denom) < 1e-9:
        return None
    q_x, q_y = a2.x - a1.x, a2.y - a1.y
    t = (q_x * s_y - q_y * s_x) / denom
    return Point(a1.x + t * r_x, a1.y + t * r_y)

def lerp_point(a: Point, b: Point, t: float) -> Point:
    return Point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)

def generate_fan_between_guide_lines(boundary, a1, b1, a2, b2, fold_count):
    if fold_count < 2:
        raise ValueError("Antal zoner skal vaere mindst 2")
    boundary = ensure_ccw(boundary)
    origin = line_intersection_point(a1, b1, a2, b2)
    if origin is None:
        raise ValueError("De to viftelinjer maa ikke vaere parallelle. Tegn dem saa de peger mod samme vifte/spids.")

    angle1 = atan2(b1.y - a1.y, b1.x - a1.x)
    angle2 = atan2(b2.y - a2.y, b2.x - a2.x)
    while angle2 <= angle1:
        angle2 += 2 * pi

    start_low, start_high = a1, a2
    low, high = angle1, angle2
    if high - low > pi:
        low, high = angle2 - 2 * pi, angle1
        start_low, start_high = a2, a1

    sector_total = polygon_area(fan_sector_polygon(boundary, origin, low, high))
    if sector_total < 0.01:
        raise ValueError("Viftelinjerne rammer ikke et brugbart areal. Proev at vende eller flytte A/B-linjerne.")

    target = sector_total / fold_count
    cuts = [find_fan_cut_for_area(boundary, origin, low, high, target * i) for i in range(1, fold_count)]
    fences = []
    for idx, angle in enumerate(cuts, 1):
        t = (angle - low) / max(high - low, 1e-9)
        start = lerp_point(start_low, start_high, t)
        end = ray_polygon_endpoint(boundary, origin, angle)
        if not end:
            continue
        if hypot(end.x - start.x, end.y - start.y) < 0.01:
            continue
        angle_rad = atan2(end.x - start.x, end.y - start.y)
        fences.append(FenceLine(f"Hegn {idx}", start, end, angle_rad, hypot(end.x - start.x, end.y - start.y)))

    bounds = [low] + cuts + [high]
    fold_areas = [polygon_area(fan_sector_polygon(boundary, origin, bounds[i], bounds[i + 1])) for i in range(fold_count)]
    return fences, fold_areas

def signed_cross_track(p, a, b):
    vx, vy = b.x-a.x, b.y-a.y
    L = hypot(vx, vy)
    if L < 1e-9:
        return 0.0
    return ((p.x-a.x)*vy - (p.y-a.y)*vx) / L

def stake_points_on_line(a, b, spacing_m):
    length = hypot(b.x-a.x, b.y-a.y)
    if spacing_m <= 0:
        return [a, b]
    count = int(length // spacing_m)
    pts = [a]
    for i in range(1, count+1):
        t = min((i*spacing_m)/length, 1.0)
        pts.append(Point(a.x + t*(b.x-a.x), a.y + t*(b.y-a.y)))
    if hypot(pts[-1].x-b.x, pts[-1].y-b.y) > 0.01:
        pts.append(b)
    return pts
