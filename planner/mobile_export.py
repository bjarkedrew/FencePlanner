from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .geometry import fence_points, polygon_area, stake_points_on_fence


FORMAT_VERSION = 1


def point_payload(point, transform=None):
    payload = {"x": round(point.x, 3), "y": round(point.y, 3)}
    if transform:
        lat, lon = transform.local_to_latlon(point)
        payload["lat"] = round(lat, 8)
        payload["lon"] = round(lon, 8)
    return payload


def build_mobile_payload(
    field,
    fences,
    fold_areas,
    transform,
    zone_count,
    stake_spacing_m,
    a=None,
    b=None,
    zone_mode="Parallel",
    fan_gap_m=0.0,
):
    if not transform:
        raise ValueError("Mobil-eksport kræver Field.kml, TASKDATA.XML eller AgShare ZIP/georeference.")
    if not fences:
        raise ValueError("Generér zoner/hegn før mobil-eksport.")

    fence_payloads = []
    total_stakes = 0
    for fence in fences:
        points = fence_points(fence)
        stakes = stake_points_on_fence(fence, stake_spacing_m)
        total_stakes += len(stakes)
        fence_payloads.append(
            {
                "name": fence.name,
                "length_m": round(fence.length_m, 2),
                "start": point_payload(fence.start, transform),
                "end": point_payload(fence.end, transform),
                "points": [point_payload(point, transform) for point in points],
                "stakes": [point_payload(point, transform) for point in stakes],
            }
        )

    return {
        "format": "FenceGuide",
        "version": FORMAT_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "field": {
            "name": field.name,
            "area_ha": round(polygon_area(field.boundary) / 10000, 4),
        },
        "settings": {
            "zone_count": int(zone_count),
            "fence_count": len(fences),
            "stake_spacing_m": float(stake_spacing_m),
            "total_stakes": total_stakes,
            "zone_mode": zone_mode,
            "fan_gap_m": float(fan_gap_m),
        },
        "ab_line": {
            "a": point_payload(a, transform) if a else None,
            "b": point_payload(b, transform) if b else None,
        },
        "boundary": [point_payload(point, transform) for point in field.boundary],
        "zones": [
            {"name": f"Zone {index}", "area_ha": round(area / 10000, 4)}
            for index, area in enumerate(fold_areas, 1)
        ],
        "fences": fence_payloads,
    }


def export_mobile_html(
    destination,
    field,
    fences,
    fold_areas,
    transform,
    zone_count,
    stake_spacing_m,
    a=None,
    b=None,
    zone_mode="Parallel",
    fan_gap_m=0.0,
):
    destination = Path(destination)
    payload = build_mobile_payload(field, fences, fold_areas, transform, zone_count, stake_spacing_m, a, b, zone_mode, fan_gap_m)
    destination.write_text(render_mobile_html(payload), encoding="utf-8")
    return destination


def render_mobile_html(payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    title = html.escape(f"Fence Guide - {payload['field']['name']}")
    return f"""<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title}</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map {{ height: 100%; margin: 0; background: #111; font-family: Arial, sans-serif; }}
    #panel {{
      position: fixed; left: 10px; right: 10px; bottom: 10px; z-index: 1000;
      background: rgba(22, 27, 32, 0.94); color: white; border-radius: 8px;
      padding: 10px; box-shadow: 0 8px 26px rgba(0,0,0,.35);
    }}
    #top {{
      position: fixed; left: 10px; right: 10px; top: 10px; z-index: 1000;
      display: flex; gap: 8px; align-items: center;
    }}
    select {{
      min-height: 40px; border: 0; border-radius: 6px; padding: 0 10px;
      font-size: 15px; color: white; font-weight: 700;
    }}
    select {{ flex: 1; background: #202a34; }}
    button {{
      margin-top: 8px; min-height: 38px; border: 0; border-radius: 6px; padding: 0 12px;
      font-size: 14px; background: #1f7aff; color: white; font-weight: 700;
    }}
    button[hidden] {{ display: none; }}
    .big {{ font-size: 34px; font-weight: 800; color: #40f27b; line-height: 1.05; }}
    .meta {{ color: #d7dee5; margin-top: 5px; font-size: 13px; }}
    .warn {{ color: #ffcc66; margin-top: 5px; font-size: 13px; }}
    .stake {{ background: #ffcc00; border: 2px solid #2d2500; border-radius: 50%; width: 10px; height: 10px; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="top">
    <select id="fenceSelect"></select>
  </div>
  <div id="panel">
    <div class="big" id="distance">Ingen GPS</div>
    <div class="meta" id="meta"></div>
    <div class="warn" id="status">GPS starter. Tillad placering når browseren spørger.</div>
    <button id="gpsRetry" hidden>Prøv GPS igen</button>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const GUIDE = {data};
    const R = 6378137;
    let selectedFenceIndex = 0;
    let gpsMarker = null;
    let accuracyCircle = null;
    let watchId = null;
    let stakeLayer = L.layerGroup();
    const origin = GUIDE.boundary[0] || GUIDE.fences[0].start;

    function toLatLng(p) {{ return [p.lat, p.lon]; }}
    function toMeters(p) {{
      const cos0 = Math.cos(origin.lat * Math.PI / 180);
      return {{
        east: (p.lon - origin.lon) * Math.PI * R * cos0 / 180,
        north: (p.lat - origin.lat) * Math.PI * R / 180
      }};
    }}
    function crossTrackMeters(pos, start, end) {{
      const p = toMeters(pos), a = toMeters(start), b = toMeters(end);
      const vx = b.east - a.east, vy = b.north - a.north;
      const len = Math.hypot(vx, vy);
      if (len < 0.001) return 0;
      return ((p.east - a.east) * vy - (p.north - a.north) * vx) / len;
    }}
    function distanceToFenceMeters(pos, fence) {{
      const pts = fence.points && fence.points.length ? fence.points : [fence.start, fence.end];
      let best = null;
      for (let i = 0; i < pts.length - 1; i++) {{
        const d = crossTrackMeters(pos, pts[i], pts[i + 1]);
        if (best === null || Math.abs(d) < Math.abs(best)) best = d;
      }}
      return best ?? 0;
    }}

    const map = L.map('map');
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 20,
      attribution: 'Tiles &copy; Esri'
    }}).addTo(map);

    const boundary = L.polygon(GUIDE.boundary.map(toLatLng), {{
      color: '#31ff6a', weight: 2, fillColor: '#31ff6a', fillOpacity: 0.12
    }}).addTo(map);
    map.fitBounds(boundary.getBounds(), {{ padding: [20, 20] }});

    const fenceLayers = GUIDE.fences.map((fence, index) => {{
      const linePoints = (fence.points && fence.points.length ? fence.points : [fence.start, fence.end]);
      const layer = L.polyline(linePoints.map(toLatLng), {{
        color: index === 0 ? '#1f7aff' : '#8ec5ff',
        weight: index === 0 ? 5 : 3
      }}).addTo(map);
      layer.bindTooltip(fence.name);
      return layer;
    }});
    stakeLayer.addTo(map);

    const select = document.getElementById('fenceSelect');
    GUIDE.fences.forEach((fence, index) => {{
      const option = document.createElement('option');
      option.value = index;
      option.textContent = `${{fence.name}} · ${{fence.stakes.length}} pæle`;
      select.appendChild(option);
    }});
    select.addEventListener('change', () => {{
      selectedFenceIndex = Number(select.value);
      redrawSelectedFence();
    }});

    function redrawSelectedFence() {{
      fenceLayers.forEach((layer, index) => {{
        layer.setStyle({{
          color: index === selectedFenceIndex ? '#1f7aff' : '#8ec5ff',
          weight: index === selectedFenceIndex ? 5 : 3
        }});
      }});
      stakeLayer.clearLayers();
      GUIDE.fences[selectedFenceIndex].stakes.forEach((stake, index) => {{
        L.circleMarker(toLatLng(stake), {{
          radius: 4, color: '#2d2500', weight: 1, fillColor: '#ffcc00', fillOpacity: 1
        }}).bindTooltip(`Pæl ${{index + 1}}`).addTo(stakeLayer);
      }});
      updateMeta();
    }}

    function updateMeta() {{
      const f = GUIDE.fences[selectedFenceIndex];
      const mode = GUIDE.settings.zone_mode || 'Parallel';
      document.getElementById('meta').textContent =
        `${{GUIDE.field.name}} · ${{mode}} · ${{GUIDE.settings.zone_count}} zoner · ${{GUIDE.settings.fence_count}} hegn · ${{GUIDE.settings.stake_spacing_m}} m pæleafstand · valgt: ${{f.name}} (${{f.length_m}} m)`;
    }}

    function updateGps(position) {{
      document.getElementById('gpsRetry').hidden = true;
      const lat = position.coords.latitude, lon = position.coords.longitude;
      const point = {{ lat, lon }};
      if (!gpsMarker) {{
        gpsMarker = L.circleMarker([lat, lon], {{
          radius: 10,
          color: '#ffffff',
          weight: 3,
          fillColor: '#0b7cff',
          fillOpacity: 1
        }}).addTo(map);
        gpsMarker.bindTooltip('Du er her', {{ permanent: false }});
      }} else {{
        gpsMarker.setLatLng([lat, lon]);
      }}
      if (!accuracyCircle) {{
        accuracyCircle = L.circle([lat, lon], {{
          radius: position.coords.accuracy || 0,
          color: '#0b7cff',
          weight: 1,
          fillColor: '#0b7cff',
          fillOpacity: 0.12
        }}).addTo(map);
      }} else {{
        accuracyCircle.setLatLng([lat, lon]);
        accuracyCircle.setRadius(position.coords.accuracy || 0);
      }}
      const fence = GUIDE.fences[selectedFenceIndex];
      const d = distanceToFenceMeters(point, fence);
      const side = d > 0 ? 'VENSTRE' : 'HØJRE';
      document.getElementById('distance').textContent = `${{Math.abs(d).toFixed(2)}} m ${{side}}`;
      document.getElementById('status').textContent =
        `GPS nøjagtighed ca. ${{Math.round(position.coords.accuracy || 0)}} m`;
    }}

    function gpsErrorText(err) {{
      if (!window.isSecureContext) {{
        return 'GPS er blokeret fordi siden ikke er åbnet som en sikker side. Chrome giver ofte ingen popup for lokale HTML-filer. Brug Chrome med placering slået til, eller brug en HTTPS-hostet mobilside.';
      }}
      if (err && err.code === 1) {{
        return 'GPS blev afvist. Slå placering til for Chrome: Android Indstillinger > Apps > Chrome > Tilladelser > Placering. Åbn derefter filen igen eller tryk Prøv GPS igen.';
      }}
      if (err && err.code === 2) return 'GPS-position kunne ikke findes. Tjek at telefonens placering er slået til.';
      if (err && err.code === 3) return 'GPS timeout. Gå udendørs og prøv igen.';
      return 'GPS fejl: ' + (err && err.message ? err.message : 'ukendt fejl');
    }}

    function startGps() {{
      if (!navigator.geolocation) {{
        document.getElementById('status').textContent = 'Denne browser understøtter ikke GPS.';
        return;
      }}
      if (watchId !== null) return;
      document.getElementById('gpsRetry').hidden = true;
      document.getElementById('status').textContent = 'GPS starter. Tillad placering når browseren spørger.';
      watchId = navigator.geolocation.watchPosition(updateGps, (err) => {{
        watchId = null;
        document.getElementById('status').textContent = gpsErrorText(err);
        document.getElementById('gpsRetry').hidden = false;
      }}, {{ enableHighAccuracy: true, maximumAge: 500, timeout: 10000 }});
    }}

    document.getElementById('gpsRetry').addEventListener('click', startGps);
    redrawSelectedFence();
    startGps();
  </script>
</body>
</html>
"""
