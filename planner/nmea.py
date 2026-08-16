from dataclasses import dataclass

@dataclass
class GpsFix:
    lat: float
    lon: float
    fix_quality: int = 0
    sats: int = 0
    hdop: float = 0.0
    speed_kmh: float = 0.0
    track_deg: float | None = None
    raw: str = ""

def nmea_coord_to_decimal(value, hemi):
    if not value:
        return None
    try:
        dot = value.find(".")
        deg_len = dot - 2
        deg = float(value[:deg_len])
        mins = float(value[deg_len:])
        dec = deg + mins / 60.0
        if hemi in ("S", "W"):
            dec = -dec
        return dec
    except Exception:
        return None

def parse_nmea_line(line, last=None):
    line = line.strip()
    if not line.startswith("$"):
        return last
    parts = line.split(",")
    typ = parts[0][-3:]
    if typ == "GGA" and len(parts) > 9:
        lat = nmea_coord_to_decimal(parts[2], parts[3])
        lon = nmea_coord_to_decimal(parts[4], parts[5])
        if lat is None or lon is None:
            return last
        try: fixq = int(parts[6] or 0)
        except: fixq = 0
        try: sats = int(parts[7] or 0)
        except: sats = 0
        try: hdop = float(parts[8] or 0)
        except: hdop = 0.0
        speed = last.speed_kmh if last else 0.0
        track = last.track_deg if last else None
        return GpsFix(lat, lon, fixq, sats, hdop, speed, track, line)
    if typ == "RMC" and len(parts) > 8:
        lat = nmea_coord_to_decimal(parts[3], parts[4])
        lon = nmea_coord_to_decimal(parts[5], parts[6])
        if lat is None or lon is None:
            return last
        try: speed_kmh = float(parts[7] or 0) * 1.852
        except: speed_kmh = 0.0
        try: track_deg = float(parts[8] or 0)
        except: track_deg = last.track_deg if last else None
        return GpsFix(lat, lon, last.fix_quality if last else 0, last.sats if last else 0, last.hdop if last else 0, speed_kmh, track_deg, line)
    if typ == "VTG" and len(parts) > 7 and last:
        try: track_deg = float(parts[1] or last.track_deg or 0)
        except: track_deg = last.track_deg
        speed_kmh = last.speed_kmh
        try:
            if parts[7]:
                speed_kmh = float(parts[7])
        except Exception:
            pass
        return GpsFix(last.lat, last.lon, last.fix_quality, last.sats, last.hdop, speed_kmh, track_deg, line)
    if typ in ("HDT", "THS") and len(parts) > 1 and last:
        try: heading = float(parts[1] or last.track_deg or 0)
        except: heading = last.track_deg
        return GpsFix(last.lat, last.lon, last.fix_quality, last.sats, last.hdop, last.speed_kmh, heading, line)
    return last
