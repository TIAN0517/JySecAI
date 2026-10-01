"""TWD97 TM2 zone 121 → WGS84。"""
from __future__ import annotations

import math

_A = 6378137.0
_B = 6356752.31414036
_K0 = 0.9999
_FALSE_EASTING = 250000.0
_CENTRAL_MERIDIAN = 121.0


def tm2_121_to_wgs84(x: float, y: float) -> tuple[float, float]:
    e2 = (_A**2 - _B**2) / _A**2
    ep2 = e2 / (1 - e2)
    meridian = float(y) / _K0
    mu = meridian / (_A * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    footprint = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
    )
    sin_f = math.sin(footprint)
    cos_f = math.cos(footprint)
    tan_f = math.tan(footprint)
    c1 = ep2 * cos_f**2
    t1 = tan_f**2
    r1 = _A * (1 - e2) / (1 - e2 * sin_f**2) ** 1.5
    n1 = _A / math.sqrt(1 - e2 * sin_f**2)
    d = (float(x) - _FALSE_EASTING) / (n1 * _K0)
    latitude = footprint - (n1 * tan_f / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 3 * c1**2 - 252 * ep2) * d**6 / 720
    )
    longitude = math.radians(_CENTRAL_MERIDIAN) + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / cos_f
    return math.degrees(latitude), math.degrees(longitude)
