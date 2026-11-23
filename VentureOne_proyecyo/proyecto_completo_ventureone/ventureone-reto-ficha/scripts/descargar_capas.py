"""Descarga capas abiertas de OpenStreetMap (Overpass) recortadas a la zona de prueba.

Salidas (GeoJSON de puntos, una foto fija con fecha de OSM en "metadata"):
- data/geo/transporte.geojson      estaciones de metro, tranvía, metrocable y metroplús
- data/geo/equipamientos.geojson   equipamientos según config/parametros.yaml

Datos © colaboradores de OpenStreetMap, licencia ODbL.
Uso: python3 scripts/descargar_capas.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
from ficha.geo import haversine_m  # noqa: E402

DIST_DUPLICADO_M = 150
OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = "ventureone-reto-ficha/0.1 (open-data research script)"
# Cubre las tres zonas (Ditaires-Itagüí, Castellana-Laureles, Buenos Aires-El Salvador) con margen.
BBOX = (6.14, -75.64, 6.29, -75.52)


def overpass(consulta, intentos=3):
    # curl y no urllib: el Python 3.9 de macOS trae LibreSSL 2.8 y falla el TLS con Overpass.
    # Overpass corta conexiones bajo carga: se reintenta con espera creciente y luego se falla.
    cmd = ["curl", "-sS", "--fail", "-m", "200", "-A", USER_AGENT, OVERPASS, "--data-urlencode", f"data={consulta}"]
    for intento in range(1, intentos + 1):
        try:
            return json.loads(subprocess.run(cmd, check=True, capture_output=True).stdout)
        except subprocess.CalledProcessError as err:
            if intento == intentos:
                raise RuntimeError(f"Overpass falló {intentos} veces: {err.stderr.decode().strip()}") from err
            time.sleep(15 * intento)


def punto(elemento):
    if "lat" in elemento:
        return elemento["lat"], elemento["lon"]
    c = elemento["center"]
    return c["lat"], c["lon"]


def sistema_transporte(tags):
    red = (tags.get("network") or "").lower()
    if "metroplús" in red or "metroplus" in red:
        return "metroplus"
    if "metrocable" in red or tags.get("aerialway") == "station":
        return "metrocable"
    if tags.get("railway") == "tram_stop" or "tranvía" in red or tags.get("station") == "light_rail":
        return "tranvia"
    if "metro de medellín" in red or tags.get("station") == "subway":
        return "metro"
    return None


def feature(lat, lon, props):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


def coleccion(features, respuesta):
    meta = {"fuente": "OpenStreetMap vía Overpass API", "licencia": "ODbL",
            "fecha_osm": respuesta["osm3s"]["timestamp_osm_base"], "bbox": BBOX}
    return {"type": "FeatureCollection", "metadata": meta, "features": features}


def descargar_transporte():
    b = ",".join(map(str, BBOX))
    r = overpass(f"""[out:json][timeout:120];
(nwr["public_transport"="station"]({b});nwr["railway"~"^(station|halt|tram_stop)$"]({b});
 nwr["aerialway"="station"]({b}););out center tags;""")
    features = []
    for e in sorted(r["elements"], key=lambda e: (e["type"] != "node", e["id"])):
        tags = e.get("tags", {})
        sistema, nombre = sistema_transporte(tags), tags.get("name")
        if not sistema or not nombre:
            continue
        lat, lon = punto(e)
        # Una estación aparece como nodo, como área y con nombres distintos: se conserva el primer nodo.
        if any(f["properties"]["sistema"] == sistema
               and haversine_m(lat, lon, f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0]) < DIST_DUPLICADO_M
               for f in features):
            continue
        features.append(feature(lat, lon, {"nombre": nombre, "sistema": sistema, "osm_id": f"{e['type']}/{e['id']}"}))
    return coleccion(features, r)


def descargar_equipamientos(categorias):
    b = ",".join(map(str, BBOX))
    partes = [f'nwr["{clave}"~"^({"|".join(valores)})$"]({b});'
              for reglas in categorias.values() for clave, valores in reglas.items()]
    r = overpass(f"[out:json][timeout:180];({''.join(partes)});out center tags;")
    features = []
    for e in r["elements"]:
        tags = e.get("tags", {})
        categoria = next((cat for cat, reglas in categorias.items()
                          if any(tags.get(k) in v for k, v in reglas.items())), None)
        if categoria is None:
            continue
        lat, lon = punto(e)
        features.append(feature(lat, lon, {"nombre": tags.get("name", ""), "categoria": categoria,
                                           "osm_id": f"{e['type']}/{e['id']}"}))
    return coleccion(features, r)


def main():
    params = yaml.safe_load((RAIZ / "config" / "parametros.yaml").read_text(encoding="utf-8"))
    destino = RAIZ / "data" / "geo"
    for nombre, capa in (("transporte", descargar_transporte()),
                         ("equipamientos", descargar_equipamientos(params["entorno"]["categorias_equipamientos"]))):
        (destino / f"{nombre}.geojson").write_text(json.dumps(capa, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{nombre}: {len(capa['features'])} puntos (OSM {capa['metadata']['fecha_osm']})")


if __name__ == "__main__":
    main()
