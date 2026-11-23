"""Geocodifica los inmuebles de prueba con OpenStreetMap (Overpass).

Entrada: data/inmuebles_prueba_fuente.csv (curado a mano) + data/anuncios_muestra.csv
Salida:  data/inmuebles_prueba.csv

- Con via_1 y via_2: el punto es el cruce de las dos vías en OSM.
  Precisión "cruce" (la placa real queda a menos de una cuadra).
- Con referencia_osm: el punto es el nodo o centroide de ese objeto OSM
  (nodo del barrio o un parque del barrio). Precisión "barrio".
Si un cruce no existe en OSM, el script falla: no inventa coordenadas.

Uso: python3 scripts/geocodificar.py
"""
import csv
import functools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from descargar_capas import BBOX, overpass  # noqa: E402
from ficha.geo import haversine_m  # noqa: E402  (descargar_capas agrega src/ al path)

RAIZ = Path(__file__).resolve().parent.parent
MAX_SEPARACION_M = 50
COLUMNAS = ["id_inmueble", "id_anuncio", "origen", "direccion", "zona", "municipio", "barrio",
            "area_m2", "estado", "lat", "lon", "precision_coordenadas", "fuente_coordenadas"]


@functools.lru_cache(maxsize=None)
def puntos_via(nombre):
    b = ",".join(map(str, BBOX))
    r = overpass(f'[out:json][timeout:60];way["highway"]["name"="{nombre}"]({b});out geom;')
    return [(p["lat"], p["lon"]) for w in r["elements"] for p in w["geometry"]]


def cruce(via_1, via_2):
    """Punto medio del par de vértices más cercano entre las dos vías.

    Un cruce real comparte nodo (distancia 0). OSM a veces deja las vías a pocos
    metros sin unirlas: se acepta hasta MAX_SEPARACION_M.
    """
    a, b = puntos_via(via_1), puntos_via(via_2)
    if not a or not b:
        raise LookupError(f"OSM no tiene la vía '{via_1 if not a else via_2}'")
    dist, p, q = min((haversine_m(*p, *q), p, q) for p in a for q in b)
    if dist > MAX_SEPARACION_M:
        raise LookupError(f"'{via_1}' y '{via_2}' no se cruzan (separación mínima {dist:.0f} m)")
    return (p[0] + q[0]) / 2, (p[1] + q[1]) / 2, f"OSM cruce {via_1} x {via_2} (separación {dist:.0f} m)"


@functools.lru_cache(maxsize=None)
def objeto_osm(ref):
    tipo, osm_id = ref.split("/")
    r = overpass(f"[out:json][timeout:60];{tipo}({osm_id});out center tags;")
    e = r["elements"][0]
    c = e if "lat" in e else e["center"]
    return c["lat"], c["lon"], f"OSM {ref} ({e['tags'].get('name', '')})"


def main():
    anuncios = {r["origen"]: r for r in csv.DictReader((RAIZ / "data" / "anuncios_muestra.csv").open(encoding="utf-8"))}
    salida = []
    for f in csv.DictReader((RAIZ / "data" / "inmuebles_prueba_fuente.csv").open(encoding="utf-8")):
        a = anuncios[f["origen"]]
        if f["via_1"]:
            lat, lon, fuente = cruce(f["via_1"], f["via_2"])
            precision = "cruce"
        else:
            lat, lon, fuente = objeto_osm(f["referencia_osm"])
            precision = "barrio"
        salida.append({
            "id_inmueble": f["id_inmueble"], "id_anuncio": a["id_anuncio"], "origen": f["origen"],
            "direccion": f["direccion"], "zona": a["zona"], "municipio": a["municipio"], "barrio": a["barrio"],
            "area_m2": a["area_m2"], "estado": a["estado"], "lat": round(lat, 6), "lon": round(lon, 6),
            "precision_coordenadas": precision, "fuente_coordenadas": fuente,
        })
        print(f["id_inmueble"], precision, round(lat, 6), round(lon, 6), fuente)
        time.sleep(1)  # respeta el uso justo de Overpass
    with (RAIZ / "data" / "inmuebles_prueba.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(salida)


if __name__ == "__main__":
    main()
