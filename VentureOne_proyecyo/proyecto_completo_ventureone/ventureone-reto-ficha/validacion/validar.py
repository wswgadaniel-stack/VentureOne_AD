"""Compara fichas JSON contra el cálculo manual (validacion/esperado.json).

Uso: python3 validacion/validar.py <carpeta_con_fichas>
     La carpeta debe tener INM-04.json, INM-06.json e INM-09.json con el esquema
     de ejemplos/ficha_ejemplo.json. Sale con código 1 si hay diferencias.
"""
import json
import sys
from pathlib import Path

ESPERADO = Path(__file__).with_name("esperado.json")


def _cerca(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def validar(ficha, esp, tol):
    """Lista de diferencias (vacía si la ficha coincide)."""
    errores = []

    def revisar(nombre, obtenido, esperado, tolerancia=None):
        ok = _cerca(obtenido, esperado, tolerancia) if tolerancia is not None else obtenido == esperado
        if not ok:
            errores.append(f"{nombre}: esperado {esperado!r}, obtenido {obtenido!r}")

    m, me = ficha["mercado"], esp["mercado"]
    revisar("mercado.estado_referencia", m["estado_referencia"], me["estado_referencia"])
    revisar("mercado.precio_m2.n", m["precio_m2"]["n"], me["n"])
    for campo in ("mediana", "promedio", "desviacion"):
        revisar(f"mercado.precio_m2.{campo}", m["precio_m2"][campo], me[campo], tol["precio_cop"])
    revisar("mercado.precio_m2.coef_variacion", m["precio_m2"]["coef_variacion"], me["coef_variacion"], tol["coef_variacion"])
    revisar("mercado.confianza.nivel", m["confianza"]["nivel"], me["confianza"])
    revisar("mercado.comparables", sorted(c["origen"] for c in m["comparables"]), sorted(me["comparables"]))
    for campo, valor in esp["calidad_datos_zona"].items():
        revisar(f"calidad_datos_zona.{campo}", ficha["calidad_datos_zona"][campo], valor)

    e, ee = ficha["entorno"], esp["entorno"]
    cercana = e["estacion_mas_cercana"] or {}
    revisar("entorno.estacion_mas_cercana.nombre", cercana.get("nombre"), ee["estacion_mas_cercana"]["nombre"])
    revisar("entorno.estacion_mas_cercana.distancia_m", cercana.get("distancia_m"),
            ee["estacion_mas_cercana"]["distancia_m"], tol["distancia_m"])
    revisar("entorno.estaciones_en_radio", e["estaciones_en_radio"], ee["estaciones_en_radio"])
    revisar("entorno.equipamientos_en_radio", e["equipamientos_en_radio"], ee["equipamientos_en_radio"])
    revisar("norma.estado", ficha["norma"]["estado"], esp["norma"]["estado"])
    revisar("datos_faltantes", sorted(ficha["datos_faltantes"]), sorted(esp["datos_faltantes"]))
    return errores


def main(carpeta):
    esperado = json.loads(ESPERADO.read_text(encoding="utf-8"))
    total = 0
    for id_inmueble, esp in esperado["inmuebles"].items():
        ruta = Path(carpeta) / f"{id_inmueble}.json"
        if not ruta.exists():
            print(f"✗ {id_inmueble}: falta {ruta}")
            total += 1
            continue
        errores = validar(json.loads(ruta.read_text(encoding="utf-8")), esp, esperado["_tolerancias"])
        print(f"{'✓' if not errores else '✗'} {id_inmueble}" + "".join(f"\n    - {e}" for e in errores))
        total += len(errores)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "salidas/fichas"))
