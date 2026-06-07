from __future__ import annotations
from math import hypot, atan2
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
