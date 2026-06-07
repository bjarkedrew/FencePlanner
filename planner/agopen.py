from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

from .models import FenceLine, FieldData, Point

EARTH_RADIUS_M = 6378137.0


def default_fields_path():
    return Path.home() / "Documents" / "AgOpenGPS" / "Fields"


def planner_root_path():
    return Path.home() / "Documents" / "FencePlanner"


def planner_fields_path():
    return planner_root_path() / "Fields"


def find_file(folder, name):
    exact = folder / name
    if exact.exists():
        return exact
    wanted = name.lower()
    for path in folder.iterdir():
        if path.name.lower() == wanted:
            return path
    return None


def list_fields(fields_path):
    if not fields_path.exists():
        return []
    return sorted(
        [p for p in fields_path.iterdir() if p.is_dir() and find_file(p, "Boundary.txt")],
        key=lambda p: p.name.lower(),
    )


def agshare_store_dir(fields_path):
    return fields_path / "_FencePlanner"


def agshare_zip_path(fields_path):
    return agshare_store_dir(fields_path) / "AgShare_Export.zip"


def import_agshare_zip(source_zip, fields_path):
    source_zip = Path(source_zip)
    if not source_zip.exists():
        raise ValueError("AgShare ZIP blev ikke fundet.")

    rings = read_agshare_rings(source_zip)
    count = len(rings)
    if count <= 0:
        raise ValueError("AgShare ZIP indeholder ingen marker med polygon-georeference.")

    root = planner_root_path()
    imports_dir = root / "Imports"
    imports_dir.mkdir(parents=True, exist_ok=True)
    dst = imports_dir / source_zip.name
    shutil.copy2(source_zip, dst)

    fields_dir = planner_fields_path()
    fields_dir.mkdir(parents=True, exist_ok=True)
    created = 0
    for item in rings:
        write_planner_field(fields_dir, item["name"], item["ring"], dst)
        created += 1

    return dst, created


def safe_folder_name(name):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", (name or "Mark").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "Mark"


def unique_path(path):
    if not path.exists():
        return path
    return path


def write_planner_field(fields_dir, name, ring, source_zip):
    folder = fields_dir / safe_folder_name(name)
    folder.mkdir(parents=True, exist_ok=True)
    plans_dir = folder / "FencePlans"
    plans_dir.mkdir(exist_ok=True)

    boundary = geo_ring_to_local_points(ring)
    write_boundary(folder / "Boundary.txt", boundary)
    write_field_kml(folder / "Field.kml", name, ring)
    (folder / "TrackLines.txt").touch(exist_ok=True)
    metadata = {
        "format": "FencePlannerField",
        "version": 1,
        "name": name,
        "source": "AgShare ZIP",
        "source_zip": str(source_zip),
        "georef_points": len(ring),
    }
    (folder / "fenceplanner_field.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return folder


def geo_ring_to_local_points(ring):
    lat0 = sum(lat for lat, lon in ring) / len(ring)
    lon0 = sum(lon for lat, lon in ring) / len(ring)
    cos_lat0 = math.cos(math.radians(lat0))
    return [
        Point(
            math.radians(lon - lon0) * EARTH_RADIUS_M * cos_lat0,
            math.radians(lat - lat0) * EARTH_RADIUS_M,
        )
        for lat, lon in ring
    ]


def write_boundary(path, boundary):
    lines = ["$Boundary"]
    lines.extend(f"{p.x:.3f},{p.y:.3f}" for p in boundary)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_field_kml(path, name, ring):
    coords = [f"{lon:.12f},{lat:.12f},0" for lat, lon in ring]
    if ring and ring[0] != ring[-1]:
        lat, lon = ring[0]
        coords.append(f"{lon:.12f},{lat:.12f},0")
    text = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{xml_escape(name)}</name>
    <Placemark>
      <name>{xml_escape(name)}</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              {' '.join(coords)}
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""
    path.write_text(text, encoding="utf-8")


def xml_escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def count_agshare_fields(zip_path):
    return len(read_agshare_rings(zip_path))


def read_agshare_rings(zip_path, wanted_name=None):
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return []

    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = {name.lower(): name for name in zf.namelist()}
            geojson_name = names.get("geojson/fields.geojson")
            if not geojson_name:
                return []
            with zf.open(geojson_name) as f:
                data = json.loads(f.read().decode("utf-8-sig"))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError):
        return []

    rings = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        if props.get("type") != "field":
            continue

        field_name = props.get("name") or props.get("fieldName") or ""
        coords = best_geojson_ring(geom)
        if len(coords) < 3:
            continue

        ring = []
        for lon, lat, *_ in coords:
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                continue
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                ring.append((lat, lon))

        if len(ring) >= 3:
            if abs(ring[0][0] - ring[-1][0]) < 1e-9 and abs(ring[0][1] - ring[-1][1]) < 1e-9:
                ring.pop()
            rings.append(
                {
                    "name": field_name,
                    "path": zip_path,
                    "ring": ring,
                    "score": name_match_score(field_name, wanted_name),
                }
            )
    return rings


def best_geojson_ring(geom):
    geom_type = geom.get("type")
    coords = geom.get("coordinates") or []
    if geom_type == "Polygon" and coords:
        return max(coords, key=len)
    if geom_type == "MultiPolygon" and coords:
        rings = [ring for polygon in coords for ring in polygon]
        return max(rings, key=len) if rings else []
    return []


def read_boundary(path):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    pts = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("$"):
            continue
        nums = []
        for part in re.split(r"[,;\s]+", line):
            try:
                nums.append(float(part.replace(",", ".")))
            except ValueError:
                pass
        if len(nums) >= 2:
            pts.append(Point(nums[0], nums[1]))
    if len(pts) < 3:
        raise ValueError("Boundary.txt kunne ikke læses")
    if abs(pts[0].x - pts[-1].x) < 1e-6 and abs(pts[0].y - pts[-1].y) < 1e-6:
        pts.pop()
    return pts


def read_field_kml_ring(path, boundary_count=None):
    if not path or not path.exists():
        return None

    text = path.read_text(encoding="utf-8", errors="ignore")
    rings = []
    for match in re.finditer(r"<coordinates>(.*?)</coordinates>", text, re.S | re.I):
        ring = []
        for token in match.group(1).strip().split():
            parts = token.split(",")
            if len(parts) >= 2:
                try:
                    ring.append((float(parts[1]), float(parts[0])))
                except ValueError:
                    pass
        if len(ring) >= 3:
            if abs(ring[0][0] - ring[-1][0]) < 1e-9 and abs(ring[0][1] - ring[-1][1]) < 1e-9:
                ring.pop()
            rings.append(ring)

    if not rings:
        return None
    if boundary_count:
        return min(rings, key=lambda ring: abs(len(ring) - boundary_count))
    return rings[0]


def taskdata_candidates(field_path):
    preferred = [
        field_path / "zISOXML" / "v4" / "TASKDATA.XML",
        field_path / "zISOXML" / "v4" / "TASKDATA.xml",
        field_path / "zISOXML" / "v3" / "TASKDATA.XML",
        field_path / "zISOXML" / "v3" / "TASKDATA.xml",
    ]
    seen = set()
    for path in preferred:
        key = str(path).lower()
        if key not in seen and path.exists():
            seen.add(key)
            yield path

    ziso = field_path / "zISOXML"
    if ziso.exists():
        for path in ziso.rglob("*"):
            if path.is_file() and path.name.lower() == "taskdata.xml":
                key = str(path).lower()
                if key not in seen:
                    seen.add(key)
                    yield path


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def read_taskdata_rings(path, wanted_name=None):
    if not path or not path.exists():
        return []

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []

    rings = []
    for pfd in root.iter():
        if local_name(pfd.tag) != "PFD":
            continue

        field_name = pfd.attrib.get("C", "")
        name_score = 0
        if wanted_name and field_name:
            a = normalize_name(field_name)
            b = normalize_name(wanted_name)
            if a == b:
                name_score = 3
            elif a in b or b in a:
                name_score = 2

        for pln in pfd:
            if local_name(pln.tag) != "PLN":
                continue
            for lsg in pln:
                if local_name(lsg.tag) != "LSG":
                    continue
                ring = []
                for pnt in lsg:
                    if local_name(pnt.tag) != "PNT":
                        continue
                    try:
                        lat = float(pnt.attrib.get("C", "").replace(",", "."))
                        lon = float(pnt.attrib.get("D", "").replace(",", "."))
                    except ValueError:
                        continue
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        ring.append((lat, lon))
                if len(ring) >= 3:
                    if abs(ring[0][0] - ring[-1][0]) < 1e-9 and abs(ring[0][1] - ring[-1][1]) < 1e-9:
                        ring.pop()
                    rings.append(
                        {
                            "name": field_name,
                            "path": path,
                            "ring": ring,
                            "score": name_score,
                        }
                    )
    return rings


def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip().lower())


def name_match_score(field_name, wanted_name=None):
    if not wanted_name or not field_name:
        return 0
    a = normalize_name(field_name)
    b = normalize_name(wanted_name)
    if a == b:
        return 3
    if a in b or b in a:
        return 2
    return 0


def read_taskdata_ring(field_path, boundary_count=None):
    candidates = []
    for path in taskdata_candidates(field_path):
        candidates.extend(read_taskdata_rings(path, field_path.name))

    if not candidates:
        return None, ""

    def rank(candidate):
        ring = candidate["ring"]
        count_penalty = abs(len(ring) - boundary_count) if boundary_count else 0
        version_score = 1 if "\\v4\\" in str(candidate["path"]).lower() or "/v4/" in str(candidate["path"]).lower() else 0
        return (candidate["score"], version_score, -count_penalty, len(ring))

    best = max(candidates, key=rank)
    label = f"TASKDATA.XML ({best['path'].parent.name})"
    return best["ring"], label


def agshare_candidates(field_path):
    fields_path = field_path.parent
    preferred = [agshare_zip_path(fields_path)]
    seen = set()
    for path in preferred:
        key = str(path).lower()
        if key not in seen and path.exists():
            seen.add(key)
            yield path

    store = agshare_store_dir(fields_path)
    if store.exists():
        for path in store.glob("*.zip"):
            key = str(path).lower()
            if key not in seen:
                seen.add(key)
                yield path


def read_agshare_ring(field_path, boundary_count=None):
    candidates = []
    for path in agshare_candidates(field_path):
        candidates.extend(read_agshare_rings(path, field_path.name))

    if not candidates:
        return None, ""

    def rank(candidate):
        ring = candidate["ring"]
        count_penalty = abs(len(ring) - boundary_count) if boundary_count else 0
        return (candidate["score"], -count_penalty, len(ring))

    best = max(candidates, key=rank)
    if best["score"] <= 0:
        return None, ""
    return best["ring"], f"AgShare ZIP ({best['name']})"


def load_field(field_path):
    boundary_path = find_file(field_path, "Boundary.txt")
    if not boundary_path:
        raise ValueError("Boundary.txt blev ikke fundet")

    boundary = read_boundary(boundary_path)
    georef = read_field_kml_ring(find_file(field_path, "Field.kml"), len(boundary))
    georef_source = "Field.kml" if georef else ""
    if not georef:
        georef, georef_source = read_taskdata_ring(field_path, len(boundary))
    if not georef:
        georef, georef_source = read_agshare_ring(field_path, len(boundary))

    track = ""
    track_path = find_file(field_path, "TrackLines.txt")
    if track_path:
        track = track_path.read_text(encoding="utf-8", errors="ignore")

    return FieldData(field_path.name, field_path, boundary, georef, track, georef_source)


def fence_block(f):
    return "\n".join(
        [
            f.name,
            f"{f.angle_rad:.14f}",
            f"{f.start.x:.3f},{f.start.y:.3f}",
            f"{f.end.x:.3f},{f.end.y:.3f}",
            "0",
            "2",
            "True",
            "0",
        ]
    )


def merge_tracklines(original, fences):
    lines = original.splitlines()
    if not lines or lines[0].strip() != "$TrackLines":
        lines = ["$TrackLines"] + lines
    cleaned = []
    i = 0
    while i < len(lines):
        if lines[i].strip().lower().startswith("hegn "):
            i += 8
            continue
        cleaned.append(lines[i])
        i += 1
    if cleaned and cleaned[-1].strip():
        cleaned.append("")
    for f in fences:
        cleaned.extend(fence_block(f).splitlines())
    return "\n".join(cleaned).rstrip() + "\n"


def save_as_new_field(field, fences, fold_count):
    src = field.path
    base = f"{src.name}_HEGN_{fold_count}"
    dst = src.parent / base
    n = 2
    while dst.exists():
        dst = src.parent / f"{base}_{n}"
        n += 1
    shutil.copytree(src, dst)
    track_path = find_file(dst, "TrackLines.txt") or (dst / "TrackLines.txt")
    track_path.write_text(merge_tracklines(field.tracklines_text, fences), encoding="utf-8")
    return dst


def plans_dir(field):
    path = field.path / "FencePlans"
    path.mkdir(exist_ok=True)
    return path


def point_to_data(point):
    return {"x": round(point.x, 6), "y": round(point.y, 6)}


def point_from_data(data):
    return Point(float(data["x"]), float(data["y"]))


def fence_to_data(fence):
    return {
        "name": fence.name,
        "start": point_to_data(fence.start),
        "end": point_to_data(fence.end),
        "angle_rad": fence.angle_rad,
        "length_m": fence.length_m,
    }


def fence_from_data(data):
    return FenceLine(
        data.get("name", "Hegn"),
        point_from_data(data["start"]),
        point_from_data(data["end"]),
        float(data.get("angle_rad", 0.0)),
        float(data.get("length_m", 0.0)),
    )


def save_fence_plan(field, fences, fold_areas, zone_count, stake_spacing_m, a=None, b=None, destination=None):
    if not fences:
        raise ValueError("Der er ingen hegnsplan at gemme.")

    if destination:
        path = Path(destination)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = plans_dir(field) / f"{safe_folder_name(field.name)}_{zone_count}_zoner_{stamp}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "format": "FencePlannerPlan",
        "version": 1,
        "field": field.name,
        "created": datetime.now().isoformat(timespec="seconds"),
        "settings": {
            "zone_count": int(zone_count),
            "stake_spacing_m": float(stake_spacing_m),
        },
        "ab": {
            "a": point_to_data(a) if a else None,
            "b": point_to_data(b) if b else None,
        },
        "fold_areas": [float(area) for area in fold_areas],
        "fences": [fence_to_data(fence) for fence in fences],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_fence_plan(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("format") != "FencePlannerPlan":
        raise ValueError("Filen er ikke en Fence Planner hegnsplan.")
    settings = data.get("settings") or {}
    ab = data.get("ab") or {}
    return {
        "field": data.get("field", ""),
        "zone_count": int(settings.get("zone_count", 2)),
        "stake_spacing_m": float(settings.get("stake_spacing_m", 25.0)),
        "a": point_from_data(ab["a"]) if ab.get("a") else None,
        "b": point_from_data(ab["b"]) if ab.get("b") else None,
        "fold_areas": [float(area) for area in data.get("fold_areas", [])],
        "fences": [fence_from_data(fence) for fence in data.get("fences", [])],
        "path": path,
    }
