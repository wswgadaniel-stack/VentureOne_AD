"""Lector mínimo de .xlsx con la librería estándar (sin openpyxl).

Devuelve cada hoja como lista de filas; cada fila es un dict {columna: valor}.
Solo lee valores cacheados: no evalúa fórmulas.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")) for si in root.findall("m:si", NS)]


def _sheet_paths(zf):
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels.iter(f"{REL_NS}Relationship")}
    out = {}
    for s in wb.find("m:sheets", NS):
        target = targets[s.get(f"{{{NS['r']}}}id")].lstrip("/")
        out[s.get("name")] = target if target.startswith("xl/") else f"xl/{target}"
    return out


def _cell_value(c, strings):
    t = c.get("t")
    if t == "inlineStr":
        return "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
    v = c.find("m:v", NS)
    if v is None or v.text is None:
        return None
    if t == "s":
        return strings[int(v.text)]
    if t in ("str", "e"):
        return v.text
    if t == "b":
        return v.text == "1"
    num = float(v.text)
    return int(num) if num.is_integer() else num


def read_workbook(path):
    """{nombre_hoja: [ {"A": valor, "B": valor, ...}, ... ]} con el número de fila en "_row"."""
    with zipfile.ZipFile(path) as zf:
        strings = _shared_strings(zf)
        book = {}
        for name, sheet_path in _sheet_paths(zf).items():
            root = ET.fromstring(zf.read(sheet_path))
            rows = []
            for r in root.iter(f"{{{NS['m']}}}row"):
                row = {"_row": int(r.get("r"))}
                for c in r.findall("m:c", NS):
                    col = re.match(r"[A-Z]+", c.get("r")).group(0)
                    val = _cell_value(c, strings)
                    if val not in (None, ""):
                        row[col] = val
                if len(row) > 1:
                    rows.append(row)
            book[name] = rows
        return book
