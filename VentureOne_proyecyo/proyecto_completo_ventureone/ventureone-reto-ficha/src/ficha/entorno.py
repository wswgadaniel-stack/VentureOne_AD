"""Bloque de entorno: transporte y equipamientos dentro del radio de búsqueda."""
from ficha.geo import haversine_m


def _distancia(lat, lon, feature):
    flon, flat = feature["geometry"]["coordinates"]
    return haversine_m(lat, lon, flat, flon)


def bloque_entorno(lat, lon, precision, transporte, equipamientos, params_entorno):
    radio = params_entorno["radio_busqueda_m"]
    estaciones = sorted(
        ((_distancia(lat, lon, f), f) for f in transporte
         if f["properties"]["sistema"] in params_entorno["sistemas_transporte"]),
        key=lambda par: par[0],
    )
    cercana = None
    if estaciones:
        d, f = estaciones[0]
        cercana = {"nombre": f["properties"]["nombre"], "sistema": f["properties"]["sistema"], "distancia_m": round(d)}
    conteo = {cat: 0 for cat in params_entorno["categorias_equipamientos"]}
    for f in equipamientos:
        if f["properties"]["categoria"] in conteo and _distancia(lat, lon, f) <= radio:
            conteo[f["properties"]["categoria"]] += 1
    return {
        "radio_busqueda_m": radio,
        "estacion_mas_cercana": cercana,
        "estaciones_en_radio": sum(1 for d, _ in estaciones if d <= radio),
        "equipamientos_en_radio": conteo,
        "aproximado": precision != "cruce",
    }
