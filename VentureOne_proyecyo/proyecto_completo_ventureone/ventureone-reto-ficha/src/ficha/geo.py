"""Geometría mínima sin dependencias: distancia haversine y punto en polígono."""
import math

RADIO_TIERRA_M = 6_371_008.8


def haversine_m(lat1, lon1, lat2, lon2):
    """Distancia en metros sobre la esfera entre dos puntos (grados decimales)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * math.asin(math.sqrt(a))


def _en_anillo(lon, lat, anillo):
    dentro, j = False, len(anillo) - 1
    for i in range(len(anillo)):
        xi, yi = anillo[i][0], anillo[i][1]
        xj, yj = anillo[j][0], anillo[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def punto_en_geometria(lat, lon, geometria):
    """True si el punto cae en un Polygon o MultiPolygon GeoJSON (respeta huecos)."""
    if geometria["type"] == "Polygon":
        poligonos = [geometria["coordinates"]]
    elif geometria["type"] == "MultiPolygon":
        poligonos = geometria["coordinates"]
    else:
        raise ValueError(f"Geometría no soportada: {geometria['type']}")
    for exterior, *huecos in poligonos:
        if _en_anillo(lon, lat, exterior) and not any(_en_anillo(lon, lat, h) for h in huecos):
            return True
    return False
