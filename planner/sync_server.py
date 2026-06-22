from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class FenceSyncServer:
    def __init__(self, payload_factory, port=8765):
        self.payload_factory = payload_factory
        self.port = port
        self.httpd = None
        self.thread = None

    @property
    def url(self):
        return f"http://{local_ip()}:{self.port}/"

    @property
    def guide_url(self):
        return f"http://{local_ip()}:{self.port}/guide.json"

    def start(self):
        if self.httpd:
            return

        payload_factory = self.payload_factory

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def _send(self, status, body, content_type="text/plain; charset=utf-8"):
                raw = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                route = self.path.split("?", 1)[0]
                if route == "/":
                    self._send(200, render_web_guide(), "text/html; charset=utf-8")
                    return
                if route == "/status":
                    self._send(200, "Fence Planner sync er klar.\nBrug /guide.json")
                    return
                if route != "/guide.json":
                    self._send(404, "Ikke fundet")
                    return
                try:
                    payload = payload_factory()
                    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                    self._send(200, body, "application/json; charset=utf-8")
                except Exception as exc:
                    self._send(500, json.dumps({"error": str(exc)}, ensure_ascii=False), "application/json; charset=utf-8")

        self.httpd = ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.httpd:
            return
        self.httpd.shutdown()
        self.httpd.server_close()
        self.httpd = None
        self.thread = None


def render_web_guide():
    return """<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Fence Guide</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map { height: 100%; margin: 0; background: #12171d; font-family: Arial, sans-serif; }
    #top, #panel {
      position: fixed; left: 10px; right: 10px; z-index: 1000;
      background: rgba(25, 31, 38, .94); color: white; border-radius: 8px;
      padding: 10px; box-shadow: 0 8px 26px rgba(0,0,0,.35);
    }
    #top { top: 10px; display: flex; gap: 8px; }
    #panel { bottom: 10px; }
    select, button {
      min-height: 40px; border: 0; border-radius: 6px; padding: 0 10px;
      color: white; font-size: 15px; font-weight: 700;
    }
    select { flex: 1; background: #202a34; min-width: 0; }
    button { background: #1f7aff; }
    .big { font-size: 32px; font-weight: 800; color: #40f27b; line-height: 1.05; }
    .meta { color: #d7dee5; margin-top: 5px; font-size: 13px; }
    .warn { color: #ffcc66; margin-top: 5px; font-size: 13px; }
    .gps {
      width: 18px; height: 18px; border-radius: 50%; background: #1f7aff;
      border: 3px solid white; box-shadow: 0 0 0 8px rgba(31,122,255,.24);
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="top">
    <select id="fenceSelect"></select>
    <button id="reload">Opdatér</button>
    <button id="gps">GPS</button>
  </div>
  <div id="panel">
    <div class="big" id="distance">Ingen GPS</div>
    <div class="meta" id="meta">Henter markdata...</div>
    <div class="warn" id="status"></div>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const R = 6378137;
    let guide = null, selectedFenceIndex = 0, origin = null, watchId = null;
    let boundaryLayer = null, fenceLayers = [], stakeLayer = null, gpsMarker = null, accuracyCircle = null;
    let lastPosition = null;

    const map = L.map("map", { zoomControl: true }).setView([56, 10], 7);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 20,
      attribution: "Tiles &copy; Esri"
    }).addTo(map);
    stakeLayer = L.layerGroup().addTo(map);

    function toLatLng(p) { return [p.lat, p.lon]; }
    function toMeters(p) {
      const cos0 = Math.cos(origin.lat * Math.PI / 180);
      return {
        east: (p.lon - origin.lon) * Math.PI * R * cos0 / 180,
        north: (p.lat - origin.lat) * Math.PI * R / 180
      };
    }
    function crossTrackMeters(pos, start, end) {
      const p = toMeters(pos), a = toMeters(start), b = toMeters(end);
      const vx = b.east - a.east, vy = b.north - a.north;
      const len = Math.hypot(vx, vy);
      if (len < 0.001) return 0;
      return ((p.east - a.east) * vy - (p.north - a.north) * vx) / len;
    }
    function distanceToFenceMeters(pos, fence) {
      const pts = fence.points && fence.points.length ? fence.points : [fence.start, fence.end];
      let best = null;
      for (let i = 0; i < pts.length - 1; i++) {
        const d = crossTrackMeters(pos, pts[i], pts[i + 1]);
        if (best === null || Math.abs(d) < Math.abs(best)) best = d;
      }
      return best ?? 0;
    }
    function status(text) { document.getElementById("status").textContent = text; }

    async function loadGuide() {
      try {
        status("");
        const response = await fetch("/guide.json", { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok || payload.error) throw new Error(payload.error || "Kunne ikke hente markdata.");
        guide = payload;
        origin = guide.boundary[0] || guide.fences[0].start;
        selectedFenceIndex = Math.min(selectedFenceIndex, Math.max(guide.fences.length - 1, 0));
        drawGuide();
        updateDistance();
      } catch (err) {
        status("Fejl: " + (err.message || err));
      }
    }

    function drawGuide() {
      if (boundaryLayer) boundaryLayer.remove();
      fenceLayers.forEach(layer => layer.remove());
      fenceLayers = [];
      stakeLayer.clearLayers();

      const select = document.getElementById("fenceSelect");
      select.innerHTML = "";
      guide.fences.forEach((fence, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = `${fence.name} · ${fence.stakes.length} pæle`;
        select.appendChild(option);
      });
      select.value = selectedFenceIndex;

      const bounds = [];
      if (guide.boundary.length) {
        const boundary = guide.boundary.map(toLatLng);
        boundaryLayer = L.polygon(boundary, { color: "#31ff6a", weight: 2, fillColor: "#31ff6a", fillOpacity: .12 }).addTo(map);
        bounds.push(...boundary);
      }
      guide.fences.forEach((fence, index) => {
        const line = (fence.points && fence.points.length ? fence.points : [fence.start, fence.end]).map(toLatLng);
        const layer = L.polyline(line, { color: index === selectedFenceIndex ? "#1f7aff" : "#8ec5ff", weight: index === selectedFenceIndex ? 5 : 3 }).addTo(map);
        fenceLayers.push(layer);
        bounds.push(...line);
      });
      drawSelectedStakes();
      if (bounds.length) map.fitBounds(bounds, { padding: [30, 30], maxZoom: 19 });
      document.getElementById("meta").textContent =
        `${guide.field.name} · ${guide.settings.zone_count} zoner · ${guide.settings.fence_count} hegn · ${guide.settings.stake_spacing_m} m pæleafstand`;
    }

    function drawSelectedStakes() {
      stakeLayer.clearLayers();
      if (!guide) return;
      guide.fences[selectedFenceIndex].stakes.forEach((stake, index) => {
        L.circleMarker(toLatLng(stake), { radius: 4, color: "#2d2500", weight: 1, fillColor: "#ffcc00", fillOpacity: 1 })
          .bindTooltip(`Pæl ${index + 1}`)
          .addTo(stakeLayer);
      });
      fenceLayers.forEach((layer, index) => layer.setStyle({ color: index === selectedFenceIndex ? "#1f7aff" : "#8ec5ff", weight: index === selectedFenceIndex ? 5 : 3 }));
    }

    function updateGps(position) {
      lastPosition = position;
      const lat = position.coords.latitude, lon = position.coords.longitude;
      const point = [lat, lon];
      if (!gpsMarker) {
        gpsMarker = L.marker(point, { icon: L.divIcon({ className: "", html: "<div class='gps'></div>", iconSize: [24, 24], iconAnchor: [12, 12] }) }).addTo(map);
      } else {
        gpsMarker.setLatLng(point);
      }
      if (!accuracyCircle) {
        accuracyCircle = L.circle(point, { radius: position.coords.accuracy || 0, color: "#0b7cff", weight: 1, fillColor: "#0b7cff", fillOpacity: .12 }).addTo(map);
      } else {
        accuracyCircle.setLatLng(point);
        accuracyCircle.setRadius(position.coords.accuracy || 0);
      }
      updateDistance();
    }

    function updateDistance() {
      if (!guide || !lastPosition) return;
      const fence = guide.fences[selectedFenceIndex];
      const d = distanceToFenceMeters({ lat: lastPosition.coords.latitude, lon: lastPosition.coords.longitude }, fence);
      document.getElementById("distance").textContent = `${Math.abs(d).toFixed(2)} m ${d > 0 ? "VENSTRE" : "HØJRE"}`;
      status(`GPS nøjagtighed ca. ${Math.round(lastPosition.coords.accuracy || 0)} m`);
    }

    function startGps() {
      if (!navigator.geolocation) {
        status(window.isSecureContext
          ? "Denne browser understøtter ikke GPS."
          : "Browseren tilbyder ikke GPS på denne adresse. Hvis der ikke kommer GPS-popup, brug HTTPS-link/tunnel.");
        return;
      }
      if (watchId !== null) return;
      status(window.isSecureContext
        ? "Venter på GPS-tilladelse..."
        : "Prøver GPS. Hvis browseren nægter, brug HTTPS-link/tunnel.");
      watchId = navigator.geolocation.watchPosition(updateGps, (err) => {
        watchId = null;
        status(err.code === 1
          ? "GPS blev afvist i browseren. Tjek placeringstilladelse - eller brug HTTPS-link/tunnel."
          : "GPS-fejl: " + err.message);
      }, { enableHighAccuracy: true, maximumAge: 500, timeout: 15000 });
    }

    document.getElementById("reload").addEventListener("click", loadGuide);
    document.getElementById("gps").addEventListener("click", startGps);
    document.getElementById("fenceSelect").addEventListener("change", (event) => {
      selectedFenceIndex = Number(event.target.value);
      drawSelectedStakes();
      updateDistance();
    });
    loadGuide();
  </script>
</body>
</html>"""
