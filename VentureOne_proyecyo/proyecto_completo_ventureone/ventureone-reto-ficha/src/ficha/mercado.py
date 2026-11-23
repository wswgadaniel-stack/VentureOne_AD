"""Comparables, estadísticas de precio/m² y regla de confianza."""
import statistics


def es_el_mismo_inmueble(anuncio, inmueble):
    return (inmueble["origen"] in anuncio["origenes_agrupados"]
            or (inmueble.get("id_anuncio") and inmueble["id_anuncio"] in anuncio["ids_agrupados"]))


def seleccionar_comparables(inmueble, anuncios, params):
    """Anuncios válidos de la misma zona y estado, con área dentro de la tolerancia."""
    tol = params["comparables"]["tolerancia_area"]
    return [
        a for a in anuncios
        if a["motivo_invalido"] is None
        and a["zona"] == inmueble["zona"]
        and a["estado_canonico"] == inmueble["estado_canonico"]
        and abs(a["area_m2"] - inmueble["area_m2"]) <= tol * inmueble["area_m2"]
        and not es_el_mismo_inmueble(a, inmueble)
    ]


def estadisticas(precios_m2):
    """Precios en COP redondeados a peso entero; coeficiente de variación a 4 decimales."""
    n = len(precios_m2)
    if n == 0:
        return {"n": 0, "mediana": None, "promedio": None, "minimo": None, "maximo": None,
                "desviacion": None, "coef_variacion": None}
    promedio = statistics.mean(precios_m2)
    desviacion = statistics.stdev(precios_m2) if n >= 2 else None
    return {
        "n": n,
        "mediana": round(statistics.median(precios_m2)),
        "promedio": round(promedio),
        "minimo": round(min(precios_m2)),
        "maximo": round(max(precios_m2)),
        "desviacion": round(desviacion) if desviacion is not None else None,
        "coef_variacion": round(desviacion / promedio, 4) if desviacion is not None else None,
    }


def nivel_confianza(n, coef_variacion, reglas):
    """(nivel, motivo). Se evalúa alta, luego media; si ninguna se cumple, baja."""
    for nivel in ("alta", "media"):
        r = reglas[nivel]
        if n >= r["min_comparables"] and coef_variacion is not None and coef_variacion <= r["max_coef_variacion"]:
            return nivel, (f"{n} comparables (mínimo {r['min_comparables']}) y coeficiente de variación "
                           f"{coef_variacion:.2%} (máximo {r['max_coef_variacion']:.0%})")
    cv = "sin dato" if coef_variacion is None else f"{coef_variacion:.2%}"
    m = reglas["media"]
    return "baja", (f"{n} comparables y coeficiente de variación {cv}: no cumple el nivel media "
                    f"(mínimo {m['min_comparables']} comparables, máximo {m['max_coef_variacion']:.0%})")


def bloque_mercado(inmueble, anuncios, params):
    comparables = seleccionar_comparables(inmueble, anuncios, params)
    est = estadisticas([a["precio_m2"] for a in comparables])
    nivel, motivo = nivel_confianza(est["n"], est["coef_variacion"], params["confianza"])
    return {
        "estado_referencia": inmueble["estado_canonico"],
        "precio_m2": est,
        "confianza": {"nivel": nivel, "motivo": motivo},
        "comparables": [
            {"origen": a["origen"], "id_anuncio": a["id_anuncio"], "fuente": a["fuente"],
             "area_m2": a["area_m2"], "precio": round(a["precio"]), "precio_m2": round(a["precio_m2"])}
            for a in sorted(comparables, key=lambda a: a["precio_m2"])
        ],
        "precio_m2_por_estado_en_zona": resumen_por_estado(inmueble, anuncios, params),
    }


def resumen_por_estado(inmueble, anuncios, params):
    """Mediana de precio/m² por estado en toda la zona (sin filtro de área), como contexto."""
    resumen = {}
    for estado in params["estados"]:
        valores = [a["precio_m2"] for a in anuncios
                   if a["motivo_invalido"] is None and a["zona"] == inmueble["zona"]
                   and a["estado_canonico"] == estado and not es_el_mismo_inmueble(a, inmueble)]
        e = estadisticas(valores)
        resumen[estado] = {"n": e["n"], "mediana": e["mediana"]}
    return resumen
