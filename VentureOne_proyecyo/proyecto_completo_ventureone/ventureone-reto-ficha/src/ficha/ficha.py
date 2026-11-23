"""Genera la ficha de mercado y entorno de cada inmueble de prueba.

Uso: python3 -m ficha.ficha            (desde src/, o con src/ en PYTHONPATH)
Salida: salidas/fichas/<id_inmueble>.json
"""
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from ficha.entorno import bloque_entorno
from ficha.limpieza import deduplicar, motivo_invalido, normalizar_estado, preparar
from ficha.mercado import bloque_mercado
from ficha.norma import bloque_norma

RAIZ = Path(__file__).resolve().parents[2]


def cargar_contexto(raiz=RAIZ):
    params = yaml.safe_load((raiz / "config" / "parametros.yaml").read_text(encoding="utf-8"))
    with (raiz / "data" / "anuncios_muestra.csv").open(encoding="utf-8") as f:
        crudos = [preparar(r, params) for r in csv.DictReader(f)]
    anuncios = deduplicar(crudos, params)
    for a in anuncios:
        a["motivo_invalido"] = motivo_invalido(a, params)
    capa_pot = raiz / params["norma"]["archivo_pot"]
    return {
        "params": params,
        "crudos": crudos,
        "anuncios": anuncios,
        "transporte": json.loads((raiz / "data" / "geo" / "transporte.geojson").read_text(encoding="utf-8")),
        "equipamientos": json.loads((raiz / "data" / "geo" / "equipamientos.geojson").read_text(encoding="utf-8")),
        "pot": json.loads(capa_pot.read_text(encoding="utf-8")) if capa_pot.exists() else None,
    }


def cargar_inmuebles(params, raiz=RAIZ):
    with (raiz / "data" / "inmuebles_prueba.csv").open(encoding="utf-8") as f:
        return [{**r, "area_m2": float(r["area_m2"]), "lat": float(r["lat"]), "lon": float(r["lon"]),
                 "estado_canonico": normalizar_estado(r["estado"], params["estados"])}
                for r in csv.DictReader(f)]


def calidad_zona(zona, ctx):
    crudos = [a for a in ctx["crudos"] if a["zona"] == zona]
    unicos = [a for a in ctx["anuncios"] if a["zona"] == zona]
    invalidos = Counter(a["motivo_invalido"] for a in unicos if a["motivo_invalido"])
    return {
        "anuncios_en_zona": len(crudos),
        "duplicados_eliminados": len(crudos) - len(unicos),
        "anuncios_unicos": len(unicos),
        "anuncios_invalidos": dict(sorted(invalidos.items())),
        "anuncios_validos": len(unicos) - sum(invalidos.values()),
    }


def datos_faltantes(inmueble, mercado, ctx):
    faltantes = []
    if not inmueble["direccion"]:
        faltantes.append("direccion")
    if inmueble["precision_coordenadas"] != "cruce":
        faltantes.append("coordenadas_exactas")
    ids = {c["origen"] for c in mercado["comparables"]}
    comparables = [a for a in ctx["anuncios"] if a["origen"] in ids]
    if not any(a["fecha"] for a in comparables):
        faltantes.append("fecha_publicacion_comparables")
    if not any(a["tipo_precio"] == "cierre" for a in comparables):
        faltantes.append("precios_de_cierre")
    return faltantes


def generar_ficha(inmueble, ctx):
    p = ctx["params"]
    mercado = bloque_mercado(inmueble, ctx["anuncios"], p)
    return {
        "id_inmueble": inmueble["id_inmueble"],
        "inmueble": {
            "direccion": inmueble["direccion"] or None,
            "barrio": inmueble["barrio"],
            "municipio": inmueble["municipio"],
            "zona": inmueble["zona"],
            "area_m2": inmueble["area_m2"],
            "estado_texto": inmueble["estado"],
            "estado": inmueble["estado_canonico"],
            "coordenadas": {"lat": inmueble["lat"], "lon": inmueble["lon"],
                            "precision": inmueble["precision_coordenadas"],
                            "fuente": inmueble["fuente_coordenadas"]},
        },
        "mercado": mercado,
        "calidad_datos_zona": calidad_zona(inmueble["zona"], ctx),
        "entorno": bloque_entorno(inmueble["lat"], inmueble["lon"], inmueble["precision_coordenadas"],
                                  ctx["transporte"]["features"], ctx["equipamientos"]["features"], p["entorno"]),
        "norma": bloque_norma(inmueble["lat"], inmueble["lon"], inmueble["municipio"], ctx["pot"], p["norma"]),
        "datos_faltantes": datos_faltantes(inmueble, mercado, ctx),
        "metadatos": {
            "version_parametros": p["version"],
            "fecha_generacion": date.today().isoformat(),
            "fecha_capas_osm": ctx["transporte"]["metadata"]["fecha_osm"],
            "fuentes": ["data/anuncios_muestra.csv", "OpenStreetMap (ODbL)"]
                       + ([p["norma"]["archivo_pot"]] if ctx["pot"] else []),
        },
    }


def main():
    ctx = cargar_contexto()
    destino = RAIZ / "salidas" / "fichas"
    destino.mkdir(parents=True, exist_ok=True)
    for inmueble in cargar_inmuebles(ctx["params"]):
        ficha = generar_ficha(inmueble, ctx)
        (destino / f"{inmueble['id_inmueble']}.json").write_text(
            json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        m = ficha["mercado"]
        print(f"{inmueble['id_inmueble']}: {m['estado_referencia']:<13} n={m['precio_m2']['n']:<2} "
              f"mediana={m['precio_m2']['mediana']} confianza={m['confianza']['nivel']}")


if __name__ == "__main__":
    main()
