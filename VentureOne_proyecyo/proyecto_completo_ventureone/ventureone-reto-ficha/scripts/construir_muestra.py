"""Construye data/anuncios_muestra.csv desde los Excel de data/raw/ (no versionados).

Reglas:
- Solo se copian datos de mercado. Teléfonos, nombres de contacto, comentarios,
  direcciones y presupuestos NO salen del Excel.
- No se corrigen duplicados ni valores sucios: la limpieza es parte del reto.
- tipo_precio = "pedido": todas las filas son precios publicados en anuncios.
- fecha queda vacía: ningún Excel registra la fecha de publicación.

Uso: python3 scripts/construir_muestra.py
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx_lite import read_workbook  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
SALIDA = RAIZ / "data" / "anuncios_muestra.csv"

COLUMNAS = [
    "id_anuncio", "fuente", "fecha", "zona", "municipio", "barrio", "area_m2", "precio",
    "habitaciones", "banos", "parqueadero", "estado", "tipo_precio", "origen",
]
MUNICIPIOS = ("medellin", "itagui", "envigado", "sabaneta", "bello")
URL_RE = re.compile(r"https?://\S+")


def a_numero(valor):
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return valor
    limpio = re.sub(r"[^\d.]", "", str(valor))
    return float(limpio) if limpio.count(".") <= 1 and limpio not in ("", ".") else None


def fuente_e_id(texto):
    """(fuente, id_anuncio). Facebook y letreros no llevan id: enlazan a personas."""
    url_m = URL_RE.search(str(texto or ""))
    if not url_m:
        return ("aviso_calle", "") if str(texto or "").strip().lower().startswith("aviso") else ("desconocida", "")
    url = url_m.group(0)
    if "fincaraiz" in url:
        return "fincaraiz", "fincaraiz:" + url.rstrip("/").split("/")[-1]
    if "metrocuadrado" in url:
        return "metrocuadrado", "metrocuadrado:" + url.split("?")[0].rstrip("/").split("/")[-1]
    if "ciencuadras" in url:
        return "ciencuadras", "ciencuadras:" + url.rstrip("/").split("-")[-1]
    if "arrendamientossantafe" in url:
        return "arrendamientos_santafe", "arrendamientos_santafe:" + url.rstrip("/").split("/")[-1]
    if "facebook" in url:
        return "facebook", ""
    return "otra", ""


def ubicacion_desde_url(url):
    """(municipio, barrio) desde el slug del portal. Barrio vacío si el slug no lo trae."""
    slug = str(url).lower()
    m = re.search(r"venta-en-([a-z0-9-]+?)(?:-(\d+))?(?:/|$)", slug)
    partes = m.group(1).split("-") if m else []
    if "metrocuadrado" in slug:
        m2 = re.search(r"venta-apartamento-([a-z]+)-([a-z-]+?)-\d+-habitaciones", slug)
        return (m2.group(1), m2.group(2).replace("-", " ")) if m2 else ("", "")
    municipio = next((p for p in reversed(partes) if p in MUNICIPIOS), "")
    barrio = " ".join(p for p in partes if p != municipio)
    return municipio, barrio


def filas_sectorial(archivo, zona):
    """Hojas SECTORIAL de las factibilidades: solo filas con link (las demás son resúmenes)."""
    filas = read_workbook(RAW / archivo)["SECTORIAL"]
    cab = {k: str(v).strip() for k, v in filas[0].items() if k != "_row"}
    for r in filas[1:]:
        d = {cab[k]: v for k, v in r.items() if k in cab}
        link = str(d.get("Link", ""))
        if not link.startswith("http"):
            continue
        fuente, id_anuncio = fuente_e_id(link)
        municipio, barrio = ubicacion_desde_url(link)
        yield {
            "id_anuncio": id_anuncio, "fuente": fuente, "zona": zona,
            "municipio": municipio, "barrio": barrio,
            "area_m2": a_numero(d.get("Área (m²)")), "precio": a_numero(d.get("Valor Total (COP)")),
            "habitaciones": d.get("Habitaciones"), "banos": d.get("Baños"),
            "parqueadero": d.get("Parqueadero"), "estado": str(d.get("Estado") or "").strip(),
            "origen": f"{archivo}:SECTORIAL:{r['_row']}",
        }


def filas_poligono(archivo, zona):
    libro = read_workbook(RAW / archivo)
    for hoja in ("REMODELAR", "Bombona", "El salvador", "VIVIR"):
        filas = libro[hoja]
        i_cab = next(i for i, r in enumerate(filas) if r.get("A") == "# Propiedad")
        cab = {k: str(v).strip() for k, v in filas[i_cab].items() if k != "_row"}
        for r in filas[i_cab + 1:]:
            d = {cab[k]: v for k, v in r.items() if k in cab}
            if not isinstance(d.get("# Propiedad"), (int, float)):
                continue  # celdas auxiliares bajo la tabla (promedios, notas), no anuncios
            area, precio = a_numero(d.get("Área (M2)")), a_numero(d.get("Valor inmueble"))
            if not (area or precio):
                continue  # sin datos de mercado: la fila solo trae contacto
            fuente, id_anuncio = fuente_e_id(d.get("Link del inmueble"))
            yield {
                "id_anuncio": id_anuncio, "fuente": fuente, "zona": zona,
                "municipio": "medellin", "barrio": str(d.get("Barrio") or "").strip(),
                "area_m2": area or None, "precio": precio or None,
                "habitaciones": d.get("Hab"), "banos": d.get("Baño", d.get("Bañ")),
                "parqueadero": None, "estado": str(d.get("Vivir / Reformar") or "").strip(),
                "origen": f"{archivo}:{hoja}:{r['_row']}",
            }


def main():
    filas = [
        *filas_sectorial("factibilidad_castellana.xlsx", "castellana_laureles"),
        *filas_sectorial("factibilidad_proyecto2.xlsx", "ditaires_itagui"),
        *filas_poligono("extension_poligono.xlsx", "buenos_aires_el_salvador"),
    ]
    with SALIDA.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            fila.update(fecha="", tipo_precio="pedido")
            w.writerow({k: ("" if fila.get(k) is None else fila[k]) for k in COLUMNAS})
    print(f"{len(filas)} filas -> {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
