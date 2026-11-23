# Diccionario de datos

## 1. `data/anuncios_muestra.csv` — anuncios públicos de la zona de prueba

**Origen:** 3 hojas de cálculo internas de Venture One con anuncios de portales, Facebook y letreros.
`scripts/construir_muestra.py` genera el archivo. Las hojas originales no están en el repositorio,
porque tienen teléfonos y nombres de contacto.

**Tamaño:** 117 filas, 14 columnas. Codificación UTF-8, separador coma.

**Suciedad intencional:** el archivo conserva los duplicados, los campos vacíos y las variantes de
texto de las hojas originales. La limpieza es parte del reto. El archivo no tiene datos inventados.

| Columna | Tipo | Descripción | Valores y calidad |
|---|---|---|---|
| `id_anuncio` | texto | `fuente:código` tomado de la URL del anuncio | Vacío en Facebook y letreros (el enlace identifica a una persona). 10 ids se repiten. |
| `fuente` | categoría | Origen del anuncio | `fincaraiz` 56, `facebook` 31, `aviso_calle` 18 (letrero en la calle), `arrendamientos_santafe` 6, `metrocuadrado` 4, `ciencuadras` 1, `otra` 1 |
| `fecha` | fecha ISO | Fecha de publicación | **Vacía en todas las filas.** Ninguna hoja la registró. |
| `zona` | categoría | Estudio de mercado al que pertenece la fila | `buenos_aires_el_salvador` 82, `ditaires_itagui` 19, `castellana_laureles` 16 |
| `municipio` | texto | Municipio según la URL o la hoja | `medellin`, `itagui`, `envigado` |
| `barrio` | texto libre | Barrio, tal como lo escribió el analista o el portal | Mayúsculas mezcladas, errores ("salvadror/palmas") y vacíos. |
| `area_m2` | número | Área en m² | 1 fila vacía. |
| `precio` | número (COP) | Precio publicado | Sin vacíos. |
| `habitaciones` | entero | Número de habitaciones | Vacíos en varias filas. |
| `banos` | entero | Número de baños | Vacíos en varias filas. |
| `parqueadero` | texto | Número de parqueaderos | `1`, `2`, `0`, `?`, `-` o vacío. Las filas de El Salvador no lo registran. |
| `estado` | texto libre | Estado del inmueble, tal como aparece en la hoja | 13 variantes ("REMODELADA", "Remodelar", "OK", "HABITABLE POR REMODELAR"…) y 25 vacíos. `config/parametros.yaml` las mapea a 3 estados. |
| `tipo_precio` | categoría | `pedido` (precio publicado) o `cierre` (precio de venta real) | Todas las filas son `pedido`. |
| `origen` | texto | `archivo:hoja:fila` de la hoja original | Trazabilidad. Clave única de cada fila. |

### Estados canónicos

| Estado | Significado | Textos de origen |
|---|---|---|
| `remodelado` | Listo para vender, con acabados nuevos | REMODELADO, REMODELADA, REMODELADA ? |
| `habitable` | Se puede habitar sin obra; puede necesitar remodelación | HABITABLE POR REMODELAR, Vivir, OK |
| `por_remodelar` | Necesita obra antes de habitar o vender | SIN REMODELAR, SIN REMODELAR (OBRA NEGRA), Remodelar, Reformar |

## 2. `data/inmuebles_prueba.csv` — inmuebles de prueba

11 inmuebles tomados de anuncios de portales (sin Facebook ni letreros). `scripts/geocodificar.py` genera el archivo.

| Columna | Descripción |
|---|---|
| `id_inmueble` | INM-01 a INM-11 |
| `id_anuncio`, `origen` | Enlace con la fila de `anuncios_muestra.csv` |
| `direccion` | Dirección del anuncio. Vacía si el anuncio no la trae (INM-05 a INM-11) |
| `zona`, `municipio`, `barrio`, `area_m2`, `estado` | Copiados del anuncio |
| `lat`, `lon` | Coordenadas WGS84 |
| `precision_coordenadas` | `cruce`: cruce de las dos vías de la dirección (error menor a una cuadra). `barrio`: nodo del barrio en OSM, o un parque del barrio si OSM no tiene el nodo |
| `fuente_coordenadas` | Objeto de OSM usado |

`data/inmuebles_prueba_fuente.csv` es la entrada curada a mano: vías de cada dirección o referencia OSM.

## 3. Capas geográficas — `data/geo/`

| Archivo | Contenido | Propiedades | Fuente |
|---|---|---|---|
| `transporte.geojson` | 42 estaciones (puntos) | `nombre`, `sistema` (`metro`, `tranvia`, `metrocable`, `metroplus`), `osm_id` | OSM, ODbL |
| `equipamientos.geojson` | 2714 equipamientos (puntos; las áreas se reducen a su centro) | `nombre`, `categoria`, `osm_id` | OSM, ODbL |
| `pot_tratamientos.geojson` | **Pendiente.** Polígonos de tratamientos del POT (Acuerdo 48 de 2014) | Campo de tratamiento según `norma.campo_tratamiento` | Geoportal del Distrito de Medellín |

Cada GeoJSON de OSM trae `metadata.fecha_osm`: la fecha de la foto de OpenStreetMap.

**Limitaciones conocidas:**
- Metroplús tiene 1 sola estación en OSM. Por eso no entra en `sistemas_transporte`.
- Las categorías de equipamientos dependen de lo que mapearon los voluntarios de OSM. Pueden faltar sitios.
- La capa POT cubre solo Medellín. Itagüí y Envigado quedan como `no_disponible`.
