from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .agopen import list_fields, load_fence_plan, load_field, planner_fields_path
from .kml_transform import KmlLocalTransform
from .mobile_export import build_mobile_payload


def collect_cloud_guides(fields_path=None):
    fields_path = Path(fields_path) if fields_path else planner_fields_path()
    guides = []
    for field_path in list_fields(fields_path):
        try:
            field = load_field(field_path)
            if not field.field_kml_ring:
                continue
            transform = KmlLocalTransform(field.boundary, field.field_kml_ring)
        except Exception:
            continue

        plans = sorted((field_path / "FencePlans").glob("*.json"))
        for plan_path in plans:
            try:
                plan = load_fence_plan(plan_path)
                if not plan["fences"]:
                    continue
                payload = build_mobile_payload(
                    field,
                    plan["fences"],
                    plan["fold_areas"],
                    transform,
                    plan["zone_count"],
                    plan["stake_spacing_m"],
                    plan["a"],
                    plan["b"],
                    plan.get("zone_mode", "Parallel"),
                    plan.get("fan_gap_m", 0.0),
                )
                payload["plan"] = {
                    "name": plan_path.stem,
                    "path": str(plan_path),
                }
                guides.append(payload)
            except Exception:
                continue
    return guides


def export_mobile_cloud(destination, fields_path=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    data = build_cloud_data(fields_path)
    guides = data["guides"]
    (destination / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (destination / "index.html").write_text(render_cloud_html(), encoding="utf-8")
    return destination, len(guides)


def build_cloud_data(fields_path=None):
    guides = collect_cloud_guides(fields_path)
    if not guides:
        raise ValueError("Der blev ikke fundet gemte hegnsplaner med georeference.")
    return {
        "format": "FencePlannerCloud",
        "version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "guides": guides,
    }


def export_repo_mobile_cloud(repo_root):
    repo_root = Path(repo_root)
    destination = repo_root / "docs" / "mobile"
    if destination.exists():
        shutil.rmtree(destination)
    return export_mobile_cloud(destination)


def render_cloud_html(data_url="data.json"):
    data_url_json = json.dumps(data_url)
    return """<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Fence Planner Mobilsky</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map { height: 100%; margin: 0; background: #101613; font-family: Arial, sans-serif; }
    #top, #panel {
      position: fixed; left: 10px; right: 10px; z-index: 1000;
      background: rgba(20, 30, 24, .94); color: white; border-radius: 8px;
      padding: 10px; box-shadow: 0 8px 26px rgba(0,0,0,.35);
    }
    #top { top: 10px; display: grid; grid-template-columns: 1fr; gap: 8px; }
    #panel { bottom: 10px; }
    select, button {
      min-height: 40px; border: 0; border-radius: 6px; padding: 0 10px;
      color: white; font-size: 15px; font-weight: 700; min-width: 0;
    }
    select { background: #213126; }
    button { background: #237a42; }
    .row { display: flex; gap: 8px; }
    .row select { flex: 1; }
    .big { font-size: 32px; font-weight: 800; color: #54f27c; line-height: 1.05; }
    .meta { color: #dce7dd; margin-top: 5px; font-size: 13px; }
    .warn { color: #ffcf70; margin-top: 5px; font-size: 13px; }
    .gps {
      width: 18px; height: 18px; border-radius: 50%; background: #1d7dff;
      border: 3px solid white; box-shadow: 0 0 0 8px rgba(29,125,255,.24);
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="top">
    <select id="guideSelect"></select>
    <div class="row">
      <select id="fenceSelect"></select>
      <button id="gps">GPS</button>
    </div>
  </div>
  <div id="panel">
    <div class="big" id="distance">Ingen GPS</div>
    <div class="meta" id="meta">Henter marker...</div>
    <div class="warn" id="status"></div>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const R = 6378137;
    let cloud = null, guide = null, selectedGuideIndex = 0, selectedFenceIndex = 0;
    let origin = null, watchId = null, lastPosition = null;
    let boundaryLayer = null, fenceLayers = [], stakeLayer = null, gpsMarker = null, accuracyCircle = null;

    const map = L.map("map", { zoomControl: true }).setView([56, 10], 7);
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 20,
      attribution: "Tiles &copy; Esri"
    }).addTo(map);
    stakeLayer = L.layerGroup().addTo(map);

    function status(text) { document.getElementById("status").textContent = text; }
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

    const DATA_URL = __DATA_URL__;

    async function loadCloud() {
      try {
        const sep = DATA_URL.includes("?") ? "&" : "?";
        const response = await fetch(DATA_URL + sep + "ts=" + Date.now(), { cache: "no-store" });
        cloud = await response.json();
        if (!cloud.guides || !cloud.guides.length) throw new Error("Ingen marker fundet i mobilsky.");
        fillGuides();
        selectGuide(0);
      } catch (err) {
        status("Fejl: " + (err.message || err));
      }
    }

    function guideLabel(item) {
      return item.field.name + " - " + (item.plan && item.plan.name ? item.plan.name : "hegnsplan");
    }

    function fillGuides() {
      const select = document.getElementById("guideSelect");
      select.innerHTML = "";
      cloud.guides.forEach((item, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = guideLabel(item);
        select.appendChild(option);
      });
    }

    function selectGuide(index) {
      selectedGuideIndex = index;
      selectedFenceIndex = 0;
      guide = cloud.guides[index];
      origin = guide.boundary[0] || guide.fences[0].start;
      drawGuide();
      updateDistance();
    }

    function drawGuide() {
      if (boundaryLayer) boundaryLayer.remove();
      fenceLayers.forEach(layer => layer.remove());
      fenceLayers = [];
      stakeLayer.clearLayers();

      const fenceSelect = document.getElementById("fenceSelect");
      fenceSelect.innerHTML = "";
      guide.fences.forEach((fence, index) => {
        const option = document.createElement("option");
        option.value = index;
        option.textContent = fence.name + " · " + fence.stakes.length + " pæle";
        fenceSelect.appendChild(option);
      });
      fenceSelect.value = selectedFenceIndex;

      const bounds = [];
      if (guide.boundary.length) {
        const boundary = guide.boundary.map(toLatLng);
        boundaryLayer = L.polygon(boundary, { color: "#47ff78", weight: 2, fillColor: "#47ff78", fillOpacity: .12 }).addTo(map);
        bounds.push(...boundary);
      }
      guide.fences.forEach((fence, index) => {
        const line = (fence.points && fence.points.length ? fence.points : [fence.start, fence.end]).map(toLatLng);
        const layer = L.polyline(line, { color: index === selectedFenceIndex ? "#1d7dff" : "#a9d4ff", weight: index === selectedFenceIndex ? 5 : 3 }).addTo(map);
        layer.bindTooltip(fence.name);
        fenceLayers.push(layer);
        bounds.push(...line);
      });
      drawSelectedStakes();
      if (bounds.length) map.fitBounds(bounds, { paddingTopLeft: [20, 96], paddingBottomRight: [20, 120], maxZoom: 19 });
      updateMeta();
    }

    function drawSelectedStakes() {
      stakeLayer.clearLayers();
      if (!guide) return;
      guide.fences[selectedFenceIndex].stakes.forEach((stake, index) => {
        L.circleMarker(toLatLng(stake), { radius: 4, color: "#2d2500", weight: 1, fillColor: "#ffd23d", fillOpacity: 1 })
          .bindTooltip("Pæl " + (index + 1))
          .addTo(stakeLayer);
      });
      fenceLayers.forEach((layer, index) => layer.setStyle({ color: index === selectedFenceIndex ? "#1d7dff" : "#a9d4ff", weight: index === selectedFenceIndex ? 5 : 3 }));
      updateMeta();
    }

    function updateMeta() {
      if (!guide) return;
      const fence = guide.fences[selectedFenceIndex];
      const mode = guide.settings.zone_mode || "Parallel";
      document.getElementById("meta").textContent =
        guide.field.name + " · " + mode + " · " + guide.settings.zone_count + " zoner · " + guide.settings.fence_count +
        " hegn · " + guide.settings.stake_spacing_m + " m pæleafstand · valgt: " + fence.name;
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
        accuracyCircle = L.circle(point, { radius: position.coords.accuracy || 0, color: "#1d7dff", weight: 1, fillColor: "#1d7dff", fillOpacity: .12 }).addTo(map);
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
      document.getElementById("distance").textContent = Math.abs(d).toFixed(2) + " m " + (d > 0 ? "VENSTRE" : "HØJRE");
      status("GPS nøjagtighed ca. " + Math.round(lastPosition.coords.accuracy || 0) + " m");
    }

    function startGps() {
      if (!navigator.geolocation) {
        status("Denne browser understøtter ikke GPS.");
        return;
      }
      if (watchId !== null) return;
      status(window.isSecureContext ? "Venter på GPS-tilladelse..." : "GPS kræver normalt HTTPS på mobilen.");
      watchId = navigator.geolocation.watchPosition(updateGps, (err) => {
        watchId = null;
        status(err.code === 1 ? "GPS blev afvist. Tillad placering for browseren." : "GPS-fejl: " + err.message);
      }, { enableHighAccuracy: true, maximumAge: 500, timeout: 15000 });
    }

    document.getElementById("guideSelect").addEventListener("change", event => selectGuide(Number(event.target.value)));
    document.getElementById("fenceSelect").addEventListener("change", event => {
      selectedFenceIndex = Number(event.target.value);
      drawSelectedStakes();
      updateDistance();
    });
    document.getElementById("gps").addEventListener("click", startGps);
    loadCloud();
    startGps();
  </script>
</body>
</html>
""".replace("__DATA_URL__", data_url_json)
