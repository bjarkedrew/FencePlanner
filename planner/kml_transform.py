from __future__ import annotations

import math

from .models import Point


EARTH_RADIUS_M = 6378137.0


class KmlLocalTransform:
    def __init__(self, boundary, kml_ring):
        if len(boundary) < 3 or len(kml_ring) < 3:
            raise ValueError("Georeference har for få punkter")

        self.lat0 = sum(lat for lat, lon in kml_ring) / len(kml_ring)
        self.lon0 = sum(lon for lat, lon in kml_ring) / len(kml_ring)
        self.cos_lat0 = math.cos(math.radians(self.lat0))

        local_points, projected_points = self._matched_points(boundary, kml_ring)
        self.east_coeff = self._fit_affine(local_points, [p[0] for p in projected_points])
        self.north_coeff = self._fit_affine(local_points, [p[1] for p in projected_points])

        a, b, _ = self.east_coeff
        d, e, _ = self.north_coeff
        det = a * e - b * d
        if abs(det) < 1e-12:
            raise ValueError("Georeference kunne ikke beregnes")
        self.inverse_det = det

    def local_to_latlon(self, p):
        east = self.east_coeff[0] * p.x + self.east_coeff[1] * p.y + self.east_coeff[2]
        north = self.north_coeff[0] * p.x + self.north_coeff[1] * p.y + self.north_coeff[2]
        return self._projected_to_latlon(east, north)

    def latlon_to_local(self, lat, lon):
        east, north = self._latlon_to_projected(lat, lon)
        a, b, c = self.east_coeff
        d, e, f = self.north_coeff
        east -= c
        north -= f
        x = (e * east - b * north) / self.inverse_det
        y = (-d * east + a * north) / self.inverse_det
        return Point(x, y)

    def _matched_points(self, boundary, kml_ring):
        local = self._drop_duplicate_end(boundary)
        geo = self._drop_duplicate_end_latlon(kml_ring)

        if abs(len(local) - len(geo)) <= 2:
            count = min(len(local), len(geo))
            local = local[:count]
            geo = geo[:count]
        else:
            count = min(len(local), len(geo), 600)
            local = self._resample_by_index(local, count)
            geo = self._resample_by_index(geo, count)

        projected = [self._latlon_to_projected(lat, lon) for lat, lon in geo]
        return local, projected

    def _latlon_to_projected(self, lat, lon):
        east = math.radians(lon - self.lon0) * EARTH_RADIUS_M * self.cos_lat0
        north = math.radians(lat - self.lat0) * EARTH_RADIUS_M
        return east, north

    def _projected_to_latlon(self, east, north):
        lat = self.lat0 + math.degrees(north / EARTH_RADIUS_M)
        lon = self.lon0 + math.degrees(east / (EARTH_RADIUS_M * self.cos_lat0))
        return lat, lon

    def _fit_affine(self, local_points, target_values):
        s_xx = s_xy = s_x = s_yy = s_y = 0.0
        b0 = b1 = b2 = 0.0
        n = len(local_points)

        for p, target in zip(local_points, target_values):
            x = p.x
            y = p.y
            s_xx += x * x
            s_xy += x * y
            s_x += x
            s_yy += y * y
            s_y += y
            b0 += x * target
            b1 += y * target
            b2 += target

        matrix = [
            [s_xx, s_xy, s_x],
            [s_xy, s_yy, s_y],
            [s_x, s_y, float(n)],
        ]
        return self._solve_3x3(matrix, [b0, b1, b2])

    def _solve_3x3(self, matrix, values):
        rows = [matrix[i][:] + [values[i]] for i in range(3)]
        for col in range(3):
            pivot = max(range(col, 3), key=lambda row: abs(rows[row][col]))
            rows[col], rows[pivot] = rows[pivot], rows[col]
            divisor = rows[col][col]
            if abs(divisor) < 1e-12:
                raise ValueError("Georeference kunne ikke beregnes")
            for j in range(col, 4):
                rows[col][j] /= divisor
            for row in range(3):
                if row == col:
                    continue
                factor = rows[row][col]
                for j in range(col, 4):
                    rows[row][j] -= factor * rows[col][j]
        return rows[0][3], rows[1][3], rows[2][3]

    def _drop_duplicate_end(self, points):
        if len(points) > 1 and self._point_distance(points[0], points[-1]) < 0.01:
            return list(points[:-1])
        return list(points)

    def _drop_duplicate_end_latlon(self, points):
        if len(points) > 1:
            a = points[0]
            b = points[-1]
            if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
                return list(points[:-1])
        return list(points)

    def _resample_by_index(self, points, count):
        if count >= len(points):
            return list(points)
        if count <= 1:
            return [points[0]]
        last = len(points) - 1
        return [points[round(i * last / (count - 1))] for i in range(count)]

    def _point_distance(self, a, b):
        return math.hypot(a.x - b.x, a.y - b.y)
