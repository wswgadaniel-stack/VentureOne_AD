"""Bloque de norma urbanística: tratamiento del POT en el punto del inmueble."""
from ficha.geo import punto_en_geometria


def bloque_norma(lat, lon, municipio, capa_pot, params_norma):
    """capa_pot es el GeoJSON cargado, o None si el archivo todavía no existe."""
    if municipio not in params_norma["municipios_cubiertos"]:
        return {"tratamiento_pot": None, "estado": "no_disponible",
                "motivo": f"La capa POT cubre solo: {', '.join(params_norma['municipios_cubiertos'])}"}
    if capa_pot is None:
        return {"tratamiento_pot": None, "estado": "pendiente_capa",
                "motivo": f"Falta el archivo {params_norma['archivo_pot']}"}
    campo = params_norma["campo_tratamiento"]
    for f in capa_pot["features"]:
        if f.get("geometry") and punto_en_geometria(lat, lon, f["geometry"]):
            return {"tratamiento_pot": f["properties"].get(campo), "estado": "encontrado", "motivo": ""}
    return {"tratamiento_pot": None, "estado": "fuera_de_capa", "motivo": "El punto no cae en ningún polígono"}
