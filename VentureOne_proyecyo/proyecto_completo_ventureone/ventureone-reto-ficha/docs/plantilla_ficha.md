# Plantilla de la ficha de mercado y entorno

La ficha es un JSON por inmueble. `ejemplos/ficha_ejemplo.json` muestra una ficha completa (INM-04).
Esta página define cada campo y una vista de lectura para la dirección.

## Vista de lectura (una página por inmueble)

```
FICHA DE MERCADO Y ENTORNO                         {id_inmueble} · {metadatos.fecha_generacion}
────────────────────────────────────────────────────────────────────────────────────────────
INMUEBLE   {inmueble.direccion | "Sin dirección"} · {inmueble.barrio}, {inmueble.municipio}
           {inmueble.area_m2} m² · Estado: {inmueble.estado} ("{inmueble.estado_texto}")
           Ubicación: {coordenadas.lat}, {coordenadas.lon} (precisión: {coordenadas.precision})

MERCADO    Precio/m² de comparables en estado {mercado.estado_referencia}
           Mediana {precio_m2.mediana}   Rango {precio_m2.minimo} – {precio_m2.maximo}
           Comparables: {precio_m2.n}    Dispersión (CV): {precio_m2.coef_variacion}
           CONFIANZA: {confianza.nivel}  →  {confianza.motivo}

           Contexto de la zona (mediana por estado):
           remodelado {..mediana} (n={..n}) · habitable {..} · por remodelar {..}

ENTORNO    Radio de búsqueda: {entorno.radio_busqueda_m} m   {"(aproximado)" si entorno.aproximado}
           Estación más cercana: {estacion_mas_cercana.nombre} ({sistema}) a {distancia_m} m
           Estaciones en el radio: {estaciones_en_radio}
           Equipamientos en el radio: educación {..} · salud {..} · parques {..}
                                      abastecimiento {..} · seguridad {..} · cultura {..}

NORMA      Tratamiento POT: {norma.tratamiento_pot | norma.estado}  {norma.motivo}

CALIDAD    Zona: {anuncios_en_zona} anuncios · {duplicados_eliminados} duplicados ·
           {anuncios_validos} válidos · inválidos: {anuncios_invalidos}
           Datos faltantes: {datos_faltantes}
────────────────────────────────────────────────────────────────────────────────────────────
Fuentes: {metadatos.fuentes} · Parámetros v{version_parametros} · OSM {fecha_capas_osm}
```

## Campos del JSON

| Campo | Tipo | Descripción |
|---|---|---|
| `id_inmueble` | texto | Identificador del inmueble de prueba |
| **`inmueble`** | objeto | Datos de entrada del inmueble |
| `.direccion` | texto o null | Dirección del anuncio |
| `.barrio`, `.municipio`, `.zona` | texto | Ubicación administrativa y zona de mercado |
| `.area_m2` | número | Área en m² |
| `.estado_texto` | texto | Estado tal como venía en la fuente |
| `.estado` | categoría | Estado canónico: `remodelado`, `habitable`, `por_remodelar` |
| `.coordenadas` | objeto | `lat`, `lon`, `precision` (`cruce` o `barrio`) y `fuente` |
| **`mercado`** | objeto | Resultado del análisis de comparables |
| `.estado_referencia` | categoría | Estado usado para elegir comparables (igual al del inmueble) |
| `.precio_m2` | objeto | `n`, `mediana`, `promedio`, `minimo`, `maximo`, `desviacion` (COP enteros) y `coef_variacion` (4 decimales) |
| `.confianza` | objeto | `nivel` (`alta`, `media`, `baja`) y `motivo` en texto |
| `.comparables` | lista | Cada comparable: `origen`, `id_anuncio`, `fuente`, `area_m2`, `precio`, `precio_m2`. Orden ascendente por precio/m² |
| `.precio_m2_por_estado_en_zona` | objeto | Por estado: `n` y `mediana` de toda la zona, sin filtro de área |
| **`calidad_datos_zona`** | objeto | `anuncios_en_zona`, `duplicados_eliminados`, `anuncios_unicos`, `anuncios_invalidos` (conteo por motivo), `anuncios_validos` |
| **`entorno`** | objeto | Resultado del análisis geográfico |
| `.radio_busqueda_m` | número | Radio usado |
| `.estacion_mas_cercana` | objeto o null | `nombre`, `sistema`, `distancia_m` (entero) |
| `.estaciones_en_radio` | entero | Estaciones a una distancia menor o igual al radio |
| `.equipamientos_en_radio` | objeto | Conteo por categoría de `parametros.yaml` |
| `.aproximado` | booleano | `true` si las coordenadas son de barrio |
| **`norma`** | objeto | `tratamiento_pot`, `estado` (`encontrado`, `fuera_de_capa`, `pendiente_capa`, `no_disponible`) y `motivo` |
| **`datos_faltantes`** | lista | Códigos: `direccion`, `coordenadas_exactas`, `fecha_publicacion_comparables`, `precios_de_cierre` |
| **`metadatos`** | objeto | `version_parametros`, `fecha_generacion`, `fecha_capas_osm`, `fuentes` |

## Reglas que la ficha debe cumplir

1. Todo valor sale de los datos entregados. Un dato que no existe queda `null` y se registra en `datos_faltantes`.
2. La ficha no recomienda comprar ni da un valor de inversión. La evaluación de inversión está fuera del alcance del reto.
3. La ficha nombra siempre las fuentes y la versión de los parámetros, para que el análisis se pueda repetir.
