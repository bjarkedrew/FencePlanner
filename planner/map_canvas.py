from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QSizePolicy,
)

from .models import Point


class AbHandle(QGraphicsObject):
    moved = Signal(str, QPointF)

    def __init__(self, label: str, color: str):
        super().__init__()
        self.label = label
        self.color = QColor(color)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemSendsGeometryChanges
            | QGraphicsItem.ItemIgnoresTransformations
        )
        self.setCursor(Qt.OpenHandCursor)
        self.setZValue(40)

    def boundingRect(self):
        return QRectF(-12, -12, 46, 34)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(QPointF(0, 0), 8, 8)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(QPointF(12, 5), self.label)

    def mousePressEvent(self, event):
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.moved.emit(self.label, value)
        return super().itemChange(change, value)


class MapCanvas(QGraphicsView):
    clicked = Signal(float, float)
    point_moved = Signal(str, float, float)

    TILE_SIZE = 256
    BASEMAPS = {
        "Esri nyeste": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Esri Clarity": "https://clarity.maptiles.arcgis.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    }

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.boundary = []
        self.transform = None
        self.base_zoom = 17
        self.zoom_boost = 1
        self.basemap_name = "Esri nyeste"
        self.local_scale = 1.0
        self.local_offset_x = 0.0
        self.local_offset_y = 0.0
        self.network = QNetworkAccessManager(self)
        self.tile_items = {}
        self.static_items = []
        self.dynamic_items = []
        self.ab_handles = {}
        self.suppress_handle_signal = False
        self.satellite_enabled = True
        self.panning = False
        self.pan_start = QPoint()
        self.pan_h_start = 0
        self.pan_v_start = 0
        self.press_scene_pos = QPointF()
        self.minimum_view_scale = 0.0
        self.fit_rect = QRectF()
        self.setDragMode(QGraphicsView.NoDrag)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(760, 560)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setBackgroundBrush(QBrush(QColor("#1b2024")))

    def set_basemap(self, name):
        if name in self.BASEMAPS:
            self.basemap_name = name
            if self.boundary:
                self.draw(self.boundary)

    def set_quality(self, quality):
        self.zoom_boost = 1 if str(quality).lower().startswith("h") else 0
        if self.boundary:
            self.draw(self.boundary)

    def fit_to_boundary(self, boundary, transform=None):
        self.boundary = boundary
        if transform is not None:
            self.transform = transform
        if not boundary:
            return
        if self.transform:
            self.base_zoom = self._choose_zoom_for_boundary(boundary)
        else:
            xs = [p.x for p in boundary]
            ys = [p.y for p in boundary]
            self.local_offset_x = min(xs)
            self.local_offset_y = min(ys)
            self.local_scale = 900 / max(max(xs) - min(xs), max(ys) - min(ys), 1)
        self.draw(boundary, [], None, None)

    def draw(self, boundary=None, fences=None, a=None, b=None, gps=None):
        self.scene.clear()
        self.tile_items = {}
        self.static_items = []
        self.dynamic_items = []
        self.ab_handles = {}
        boundary = boundary or self.boundary
        fences = fences or []

        boundary_points = [self.to_scene_point(p) for p in boundary] if boundary else []
        boundary_rect = QRectF(QPolygonF(boundary_points).boundingRect()) if boundary_points else QRectF()

        if boundary and self.transform and self.satellite_enabled:
            self._add_satellite_tiles_for_rect(boundary_rect, margin_tiles=4)

        if boundary:
            item = QGraphicsPolygonItem(QPolygonF([self.to_scene_point(p) for p in boundary]))
            item.setPen(QPen(QColor("#00ff66"), 3))
            item.setBrush(QBrush(QColor(0, 255, 102, 20)))
            item.setZValue(10)
            self.scene.addItem(item)
            self.static_items.append(item)

        self.update_dynamic(fences, a, b, gps, sync_handles=True)

        if boundary_rect.isValid() and not boundary_rect.isEmpty():
            self.fit_rect = boundary_rect.adjusted(-180, -180, 180, 180)
            pan_rect = boundary_rect.adjusted(-2500, -2500, 2500, 2500)
            self.setSceneRect(pan_rect)
        else:
            self.fit_rect = self.scene.itemsBoundingRect().adjusted(-180, -180, 180, 180)
            self.setSceneRect(self.fit_rect)
        self.fit_to_map()

    def fit_to_map(self):
        if self.fit_rect.isEmpty():
            return
        self.resetTransform()
        self.fitInView(self.fit_rect, Qt.KeepAspectRatio)
        self.minimum_view_scale = QGraphicsView.transform(self).m11()
        self.load_visible_tiles()

    def update_dynamic(self, fences=None, a=None, b=None, gps=None, sync_handles=False, extra_points=None):
        fences = fences or []
        extra_points = extra_points or {}
        for item in self.dynamic_items:
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        self.dynamic_items = []

        for first, second in [("A1", "B1"), ("A2", "B2")]:
            p1 = extra_points.get(first)
            p2 = extra_points.get(second)
            if p1 and p2:
                q1 = self.to_scene_point(p1)
                q2 = self.to_scene_point(p2)
                line = QGraphicsLineItem(q1.x(), q1.y(), q2.x(), q2.y())
                pen = QPen(QColor("#ffb000"), 2)
                pen.setStyle(Qt.DashLine)
                line.setPen(pen)
                line.setZValue(19)
                self.scene.addItem(line)
                self.dynamic_items.append(line)

        for f in fences:
            points = getattr(f, "points", None) or [f.start, f.end]
            scene_points = [self.to_scene_point(p) for p in points]
            q1 = scene_points[0]
            q2 = scene_points[-1]
            if len(scene_points) > 2:
                path = QPainterPath(q1)
                for point in scene_points[1:]:
                    path.lineTo(point)
                line = QGraphicsPathItem(path)
            else:
                line = QGraphicsLineItem(q1.x(), q1.y(), q2.x(), q2.y())
            line.setPen(QPen(QColor("#2f8cff"), 3))
            line.setZValue(20)
            self.scene.addItem(line)
            self.dynamic_items.append(line)

            txt = QGraphicsSimpleTextItem(f.name)
            txt.setBrush(QBrush(QColor("#ffffff")))
            txt.setFont(QFont("Arial", 10, QFont.Bold))
            txt.setPos((q1.x() + q2.x()) / 2, (q1.y() + q2.y()) / 2)
            txt.setZValue(25)
            self.scene.addItem(txt)
            self.dynamic_items.append(txt)

        self._sync_handle("A", a, "#ff3333", sync_handles)
        self._sync_handle("B", b, "#cc0000", sync_handles)
        fan_colors = {
            "A1": "#ff8a00",
            "B1": "#ffb000",
            "A2": "#ff8a00",
            "B2": "#ffb000",
        }
        for label, point in extra_points.items():
            self._sync_handle(label, point, fan_colors.get(label, "#ffb000"), sync_handles)

        if gps:
            q = self.to_scene_point(gps)
            el = QGraphicsEllipseItem(q.x() - 8, q.y() - 8, 16, 16)
            el.setPen(QPen(QColor("#1b1b00"), 2))
            el.setBrush(QBrush(QColor("#ffff00")))
            el.setZValue(35)
            self.scene.addItem(el)
            self.dynamic_items.append(el)

    def to_scene_point(self, p):
        if self.transform:
            lat, lon = self.transform.local_to_latlon(p)
            return self._latlon_to_world_point(lat, lon, self.base_zoom)
        return QPointF(
            (p.x - self.local_offset_x) * self.local_scale,
            -(p.y - self.local_offset_y) * self.local_scale,
        )

    def from_scene_point(self, q):
        if self.transform:
            lat, lon = self._world_point_to_latlon(q, self.base_zoom)
            return self.transform.latlon_to_local(lat, lon)
        return Point(q.x() / self.local_scale + self.local_offset_x, -q.y() / self.local_scale + self.local_offset_y)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, AbHandle):
            super().mousePressEvent(event)
            return
        if event.button() == Qt.LeftButton:
            self.panning = True
            self.pan_start = event.pos()
            self.press_scene_pos = self.mapToScene(event.pos())
            self.pan_h_start = self.horizontalScrollBar().value()
            self.pan_v_start = self.verticalScrollBar().value()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.pan_start
            self.horizontalScrollBar().setValue(self.pan_h_start - delta.x())
            self.verticalScrollBar().setValue(self.pan_v_start - delta.y())
            self.load_visible_tiles()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning and event.button() == Qt.LeftButton:
            moved = (event.pos() - self.pan_start).manhattanLength()
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
            if moved < 5:
                p = self.from_scene_point(self.press_scene_pos)
                self.clicked.emit(p.x, p.y)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        current_scale = QGraphicsView.transform(self).m11()
        if factor < 1 and self.minimum_view_scale > 0:
            next_scale = current_scale * factor
            if next_scale <= self.minimum_view_scale:
                factor = self.minimum_view_scale / max(current_scale, 1e-9)
                if factor >= 0.999:
                    event.accept()
                    return
        self.scale(factor, factor)
        self.load_visible_tiles()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.fit_rect.isEmpty() and abs(QGraphicsView.transform(self).m11() - self.minimum_view_scale) < 1e-6:
            self.fit_to_map()
        else:
            self.load_visible_tiles()

    def _sync_handle(self, label, point, color, sync_handles):
        if point:
            if label not in self.ab_handles:
                handle = AbHandle(label, color)
                handle.moved.connect(self._handle_ab_moved)
                self.scene.addItem(handle)
                self.ab_handles[label] = handle
                sync_handles = True
            if sync_handles:
                self.suppress_handle_signal = True
                self.ab_handles[label].setPos(self.to_scene_point(point))
                self.suppress_handle_signal = False
        elif label in self.ab_handles:
            handle = self.ab_handles.pop(label)
            if handle.scene() is self.scene:
                self.scene.removeItem(handle)

    def _handle_ab_moved(self, label, scene_pos):
        if self.suppress_handle_signal:
            return
        p = self.from_scene_point(scene_pos)
        self.point_moved.emit(label, p.x, p.y)

    def load_visible_tiles(self):
        if not self.transform or not self.satellite_enabled:
            return
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        self._add_satellite_tiles_for_rect(view_rect, margin_tiles=2)

    def _add_satellite_tiles_for_rect(self, rect, margin_tiles=1):
        if rect.isEmpty():
            return
        min_x = math.floor(rect.left() / self.TILE_SIZE) - margin_tiles
        max_x = math.floor(rect.right() / self.TILE_SIZE) + margin_tiles
        min_y = math.floor(rect.top() / self.TILE_SIZE) - margin_tiles
        max_y = math.floor(rect.bottom() / self.TILE_SIZE) + margin_tiles
        max_index = 2**self.base_zoom - 1
        min_x = max(0, min(max_index, min_x))
        max_x = max(0, min(max_index, max_x))
        min_y = max(0, min(max_index, min_y))
        max_y = max(0, min(max_index, max_y))

        for tx in range(min_x, max_x + 1):
            for ty in range(min_y, max_y + 1):
                self._add_tile(tx, ty)

    def _add_tile(self, tx, ty):
        key = (self.base_zoom, tx, ty)
        if key in self.tile_items:
            return
        item = QGraphicsPixmapItem()
        item.setPos(tx * self.TILE_SIZE, ty * self.TILE_SIZE)
        item.setZValue(0)
        self.scene.addItem(item)
        self.tile_items[key] = item

        url = self.BASEMAPS[self.basemap_name].format(z=self.base_zoom, x=tx, y=ty)
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda r=reply, key=key: self._tile_loaded(r, key))

    def _tile_loaded(self, reply, key):
        data = reply.readAll()
        reply.deleteLater()
        item = self.tile_items.get(key)
        if item is None:
            return
        pix = QPixmap()
        if pix.loadFromData(data):
            item.setPixmap(pix)
            item.setTransformationMode(Qt.SmoothTransformation)

    def _choose_zoom_for_boundary(self, boundary):
        lats_lons = [self.transform.local_to_latlon(p) for p in boundary]
        lats = [lat for lat, lon in lats_lons]
        lons = [lon for lat, lon in lats_lons]
        span = max(max(lats) - min(lats), max(lons) - min(lons), 0.00001)
        if span < 0.003:
            return min(19, 18 + self.zoom_boost)
        if span < 0.008:
            return min(19, 17 + self.zoom_boost)
        if span < 0.02:
            return min(19, 16 + self.zoom_boost)
        if span < 0.05:
            return min(19, 15 + self.zoom_boost)
        return min(19, 14 + self.zoom_boost)

    def _latlon_to_world_point(self, lat, lon, zoom):
        lat = max(min(lat, 85.05112878), -85.05112878)
        scale = self.TILE_SIZE * (2**zoom)
        x = (lon + 180.0) / 360.0 * scale
        lat_rad = math.radians(lat)
        y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * scale
        return QPointF(x, y)

    def _world_point_to_latlon(self, point, zoom):
        scale = self.TILE_SIZE * (2**zoom)
        lon = point.x() / scale * 360.0 - 180.0
        n = math.pi * (1 - 2 * point.y() / scale)
        lat = math.degrees(math.atan(math.sinh(n)))
        return lat, lon
