# Cálculo manual de 3 inmuebles

Este documento calcula a mano la ficha de 3 inmuebles de prueba. Los resultados están en
`validacion/esperado.json`. El script `validacion/validar.py` compara cualquier ficha contra esos valores.

**Entradas:** `data/anuncios_muestra.csv`, `data/inmuebles_prueba.csv`, `data/geo/*.geojson`
(OSM del 2026-11-13) y `config/parametros.yaml` versión 1.0.

| Inmueble | Zona | Estado | Precisión | Por qué se eligió |
|---|---|---|---|---|
| INM-04 | Buenos Aires – El Salvador | habitable | cruce de vías | Zona con muchos duplicados y estados sucios |
| INM-06 | Castellana – Laureles | remodelado | barrio | Confianza media por dispersión alta |
| INM-09 | Ditaires (Itagüí) | remodelado | barrio | Confianza alta; municipio sin capa POT |

## Procedimiento común

1. **Normalizar el estado.** Pasar el texto a minúsculas, quitar tildes, "?" y espacios extremos.
   Buscar el texto en `estados` de los parámetros. Ejemplo: "REMODELADA ?" → "remodelada" → `remodelado`.
2. **Deduplicar la zona.** Recorrer el CSV en orden. Una fila es duplicada si su `id_anuncio` ya apareció.
   También es duplicada si su combinación (`zona`, `area_m2`, `precio`) ya apareció. Se conserva la primera fila.
3. **Validar.** Descartar filas sin área, sin precio, con precio/m² fuera de [1.000.000; 20.000.000],
   con estado sin clasificar o con un tipo de precio no aceptado.
4. **Filtrar comparables.** Conservar las filas válidas con el mismo estado que el inmueble.
   El área debe quedar dentro de ±30 % del área del inmueble.
   Excluir el grupo de duplicados que contiene el anuncio del propio inmueble.
5. **Calcular precio/m²:** precio ÷ área de cada comparable.
6. **Calcular estadísticas:** mediana, promedio, desviación estándar muestral (divisor n − 1)
   y coeficiente de variación (CV = desviación ÷ promedio).
7. **Aplicar la regla de confianza:** alta si n ≥ 5 y CV ≤ 15 %. Media si n ≥ 3 y CV ≤ 25 %. Si no, baja.
8. **Calcular el entorno:** distancia haversine (radio terrestre 6.371.008,8 m) a cada estación de
   metro, tranvía y metrocable. Contar estaciones y equipamientos a 800 m o menos.

---

## INM-04 — El Salvador, Calle 37 con Cra 33B

**Datos del inmueble:** 71 m², estado "OK" → `habitable`. Coordenadas 6.234861, −75.560101
(cruce Calle 37 × Carrera 33B en OSM, separación 0 m).

### Calidad de datos de la zona

| Paso | Filas |
|---|---|
| Filas de la zona `buenos_aires_el_salvador` | 82 |
| Duplicados eliminados | 28 |
| Filas únicas | 54 |
| Inválidas: estado vacío (sin clasificar) | 20 |
| Inválidas: sin área | 1 |
| Válidas | 33 |

La hoja REMODELAR del Excel repite filas de las hojas Bombona, El salvador y VIVIR. Por eso hay 28 duplicados.

### Comparables

Rango de área: 71 × 0,70 = 49,7 m² hasta 71 × 1,30 = 92,3 m².
Seis anuncios habitables quedan fuera por área: 47, 48, 105, 37, 47 y 126 m².

| # | Origen | Fuente | Área m² | Precio COP | Precio/m² |
|---|---|---|---|---|---|
| 1 | REMODELAR:88 | facebook | 64 | 245.000.000 | 3.828.125 |
| 2 | Bombona:9 | fincaraiz | 82 | 320.000.000 | 3.902.439 |
| 3 | REMODELAR:85 | facebook | 64 | 250.000.000 | 3.906.250 |
| 4 | REMODELAR:35 | aviso_calle | 55 | 215.000.000 | 3.909.091 |
| 5 | REMODELAR:89 | facebook | 80 | 350.000.000 | 4.375.000 |
| 6 | REMODELAR:84 | fincaraiz | 62 | 315.000.000 | 5.080.645 |
| 7 | Bombona:12 | fincaraiz | 78 | 450.000.000 | 5.769.231 |
| 8 | Bombona:10 | fincaraiz | 65 | 420.000.000 | 6.461.538 |
| 9 | Bombona:15 | fincaraiz | 65 | 430.000.000 | 6.615.385 |

(Origen abreviado: el archivo es `extension_poligono.xlsx`.)

### Estadísticas

- n = 9. La lista ya está ordenada. La mediana es el valor 5: **4.375.000**.
- Suma = 43.847.703,94. Promedio = 43.847.703,94 ÷ 9 = **4.871.967**.
- Suma de cuadrados de las desviaciones = 10.551.177.765.620,8.
  Varianza = 10.551.177.765.620,8 ÷ 8 = 1.318.897.220.702,6. Desviación = **1.148.433**.
- CV = 1.148.433 ÷ 4.871.967 = **0,2357** (23,57 %).
- Confianza: n = 9 ≥ 5, pero CV > 15 %. No es alta. n ≥ 3 y CV ≤ 25 %: **media**.

### Entorno

Estación más cercana: **Buenos Aires (tranvía)**, en 6.241398, −75.553889.

- Δlat = 0,00011409 rad. Δlon = 0,00010842 rad.
- a = sin²(Δlat/2) + cos(lat₁)·cos(lat₂)·sin²(Δlon/2) = 6,158274 × 10⁻⁹
- c = 2·asin(√a) = 1,56949344 × 10⁻⁴
- d = 6.371.008,8 × c = 999,9 m → **1000 m**

Estaciones a 800 m o menos: **0**. Equipamientos a 800 m o menos: educación 22, salud 2,
parques 12, abastecimiento 1, seguridad 1, cultura 0.

**Norma:** `pendiente_capa` (falta `data/geo/pot_tratamientos.geojson`).
**Datos faltantes:** fecha de publicación de los comparables y precios de cierre.

---

## INM-06 — La Castellana (sin dirección)

**Datos del inmueble:** 90 m², estado "REMODELADO" → `remodelado`. Coordenadas del nodo OSM del barrio
La Castellana: 6.240226, −75.605418. Precisión `barrio`: el entorno es aproximado.

### Calidad de datos de la zona

16 filas, 3 duplicados (fincaraiz 10710482, 193287983 y 193440669 aparecen dos veces), 13 únicas, 13 válidas.

### Comparables

Rango de área: 63 m² hasta 117 m². Se excluye la fila SECTORIAL:17, que es el propio inmueble.

| # | Origen | Área m² | Precio COP | Precio/m² |
|---|---|---|---|---|
| 1 | SECTORIAL:4 | 92 | 497.000.000 | 5.402.174 |
| 2 | SECTORIAL:7 | 90 | 550.000.000 | 6.111.111 |
| 3 | SECTORIAL:2 | 94 | 610.000.000 | 6.489.362 |
| 4 | SECTORIAL:3 | 99 | 690.000.000 | 6.969.697 |
| 5 | SECTORIAL:8 | 94 | 720.000.000 | 7.659.574 |
| 6 | SECTORIAL:9 | 100 | 870.000.000 | 8.700.000 |

(Archivo `factibilidad_castellana.xlsx`. Todas las filas son de fincaraiz.)

### Estadísticas

- n = 6 (par). Mediana = (6.489.362 + 6.969.697) ÷ 2 = **6.729.529**.
- Suma = 41.331.918,16. Promedio = **6.888.653**.
- Desviación = **1.170.939**. CV = **0,1700**.
- Confianza: n ≥ 5, pero CV = 17 % > 15 %. Cumple media: **media**.

### Entorno

Estación más cercana: **Santa Lucía (metro)**, en 6.258082, −75.603745.
a = 2,449143 × 10⁻⁸. c = 3,12994767 × 10⁻⁴. d = **1994 m**.
Estaciones a 800 m o menos: **0**. Equipamientos: educación 23, salud 6, parques 11,
abastecimiento 13, seguridad 1, cultura 5.

**Norma:** `pendiente_capa`.
**Datos faltantes:** dirección, coordenadas exactas, fecha de publicación y precios de cierre.

---

## INM-09 — Ditaires, Itagüí (sin dirección)

**Datos del inmueble:** 73 m², estado "REMODELADA" → `remodelado`. Coordenadas del centroide del
Parque Ditaires (OSM way/553803506): 6.168608, −75.627492. OSM no tiene un nodo para el barrio.

### Calidad de datos de la zona

19 filas, 2 duplicados, 17 únicas, 17 válidas.
Las filas SECTORIAL:5, :7 y :9 tienen ids distintos, pero la misma área (73 m²) y el mismo precio (490 M).
La regla (`zona`, `area_m2`, `precio`) las agrupa. El grupo contiene el propio inmueble, así que se excluye completo.

### Comparables

Rango de área: 51,1 m² hasta 94,9 m². Quedan fuera por área los anuncios de 123 y 101 m².

| # | Origen | Fuente | Área m² | Precio COP | Precio/m² |
|---|---|---|---|---|---|
| 1 | SECTORIAL:2 | fincaraiz | 66 | 400.000.000 | 6.060.606 |
| 2 | SECTORIAL:8 | fincaraiz | 67 | 460.000.000 | 6.865.672 |
| 3 | SECTORIAL:6 | fincaraiz | 61 | 421.000.000 | 6.901.639 |
| 4 | SECTORIAL:10 | fincaraiz | 62 | 430.000.000 | 6.935.484 |
| 5 | SECTORIAL:15 | metrocuadrado | 68 | 480.000.000 | 7.058.824 |
| 6 | SECTORIAL:3 | fincaraiz | 60 | 430.000.000 | 7.166.667 |
| 7 | SECTORIAL:14 | metrocuadrado | 70 | 510.000.000 | 7.285.714 |
| 8 | SECTORIAL:13 | metrocuadrado | 61 | 451.900.000 | 7.408.197 |
| 9 | SECTORIAL:11 | fincaraiz | 62 | 475.000.000 | 7.661.290 |

(Archivo `factibilidad_proyecto2.xlsx`.)

### Estadísticas

- n = 9. Mediana = valor 5 = **7.058.824**.
- Suma = 63.344.092,44. Promedio = **7.038.232**.
- Desviación = **449.720**. CV = **0,0639**.
- Confianza: n = 9 ≥ 5 y CV = 6,39 % ≤ 15 %: **alta**.

### Entorno

Estación más cercana: **Sabaneta (metro)**, en 6.157738, −75.616138. d ≈ 1742,5 m → **1743 m**.
Estaciones a 800 m o menos: **0**. Equipamientos: educación 13, salud 3, parques 1,
abastecimiento 0, seguridad 3, cultura 1.

**Norma:** `no_disponible`. La capa POT del Distrito cubre solo Medellín.
**Datos faltantes:** dirección, coordenadas exactas, fecha de publicación y precios de cierre.

---

## Casos para discutir en la hackatón

1. **Duplicado ambiguo en El Salvador.** fincaraiz:7387557 (Cra 36A con Calle 41) y
   arrendamientos_santafe:V10746 (Cra 38A # 39-74) tienen 73 m² y 300 M. La regla los agrupa,
   pero las direcciones difieren. Por eso INM-01 e INM-03 dan el mismo resultado de mercado.
2. **Tres ids con el mismo inmueble en Ditaires.** Puede ser un mismo apartamento publicado por
   varias inmobiliarias, o varias unidades iguales del mismo edificio.
3. **Ninguna estación a 800 m.** Los 3 inmuebles quedan a 1–2 km del Metro. El radio es un parámetro;
   se puede probar con 1500 m.

## Cuándo se actualiza este cálculo

- Al cambiar `config/parametros.yaml`.
- Al volver a descargar las capas OSM (`scripts/descargar_capas.py`).
- Al agregar `data/geo/pot_tratamientos.geojson`: INM-04 e INM-06 pasan de `pendiente_capa` a un tratamiento.
