from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class Point:
    x: float
    y: float

@dataclass
class FenceLine:
    name: str
    start: Point
    end: Point
    angle_rad: float
    length_m: float

@dataclass
class FieldData:
    name: str
    path: Path
    boundary: List[Point]
    field_kml_ring: Optional[list] = None
    tracklines_text: str = ""
    georef_source: str = ""
