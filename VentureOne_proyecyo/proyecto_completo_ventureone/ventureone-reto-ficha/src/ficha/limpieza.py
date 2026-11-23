"""Normalización, validación y deduplicación de anuncios."""
import unicodedata


def _texto_normalizado(texto):
    sin_tildes = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.replace("?", " ").lower().split())


def normalizar_estado(texto, estados):
    """Estado canónico según config/parametros.yaml; "sin_clasificar" si no hay mapeo."""
    limpio = _texto_normalizado(texto)
    for canonico, variantes in estados.items():
        if limpio in (_texto_normalizado(v) for v in variantes):
            return canonico
    return "sin_clasificar"


def _numero(valor):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def preparar(fila, params):
    """Copia de la fila con números convertidos, precio_m2 y estado canónico."""
    area, precio = _numero(fila.get("area_m2")), _numero(fila.get("precio"))
    return {
        **fila,
        "area_m2": area,
        "precio": precio,
        "precio_m2": precio / area if area and precio else None,
        "estado_canonico": normalizar_estado(fila.get("estado"), params["estados"]),
    }


def motivo_invalido(anuncio, params):
    """Primer motivo por el que el anuncio no sirve como comparable, o None."""
    if anuncio["area_m2"] is None:
        return "sin_area"
    if anuncio["precio"] is None:
        return "sin_precio"
    minimo, maximo = params["comparables"]["rango_precio_m2_valido"]
    if not minimo <= anuncio["precio_m2"] <= maximo:
        return "precio_m2_fuera_de_rango"
    if anuncio["estado_canonico"] == "sin_clasificar":
        return "estado_sin_clasificar"
    if anuncio.get("tipo_precio") not in params["comparables"]["tipos_precio"]:
        return "tipo_precio_no_aceptado"
    return None


def _clave_sin_id(anuncio, columnas):
    valores = tuple(anuncio.get(c) for c in columnas)
    return None if any(v in (None, "") for v in valores) else valores


def deduplicar(anuncios, params):
    """Conserva la primera aparición. Cada único lista los orígenes e ids que absorbió."""
    columnas = params["deduplicacion"]["claves_sin_id"]
    unicos, por_id, por_clave = [], {}, {}
    for a in anuncios:
        clave = _clave_sin_id(a, columnas)
        destino = por_id.get(a["id_anuncio"]) if a["id_anuncio"] else None
        if destino is None and clave is not None:
            destino = por_clave.get(clave)
        if destino is None:
            destino = {**a, "origenes_agrupados": [], "ids_agrupados": []}
            unicos.append(destino)
        destino["origenes_agrupados"].append(a["origen"])
        if a["id_anuncio"] and a["id_anuncio"] not in destino["ids_agrupados"]:
            destino["ids_agrupados"].append(a["id_anuncio"])
        if a["id_anuncio"]:
            por_id.setdefault(a["id_anuncio"], destino)
        if clave is not None:
            por_clave.setdefault(clave, destino)
    return unicos
