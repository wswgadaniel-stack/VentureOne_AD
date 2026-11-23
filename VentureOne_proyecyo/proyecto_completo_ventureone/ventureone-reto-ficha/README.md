# Ficha automática de mercado y entorno — Venture One SAS

Recursos del **reto empresarial 13** (EstudIA · Análisis de datos · Capa 2 · Nivel básico).
El reto pide generar una ficha por inmueble con precios por m² de comparables según su estado,
transporte, equipamientos cercanos y norma urbanística.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/solhecoo/ventureone-reto-ficha/blob/main/notebooks/reto_ficha_colab.ipynb)

## Entregables

| Recurso pedido en la ficha del reto | Archivo |
|---|---|
| Plantilla de la ficha esperada | [`docs/plantilla_ficha.md`](docs/plantilla_ficha.md) |
| JSON de ejemplo con los campos de salida | [`ejemplos/ficha_ejemplo.json`](ejemplos/ficha_ejemplo.json) |
| Diccionario de datos del CSV | [`docs/diccionario_datos.md`](docs/diccionario_datos.md) |
| Archivo de parámetros (radio, estados, regla de confianza) | [`config/parametros.yaml`](config/parametros.yaml) |
| Cálculo manual de 3 inmuebles | [`validacion/calculo_manual.md`](validacion/calculo_manual.md) + [`validacion/esperado.json`](validacion/esperado.json) |
| Repositorio y entorno en Google Colab | Este repositorio + [`notebooks/reto_ficha_colab.ipynb`](notebooks/reto_ficha_colab.ipynb) |

Datos de trabajo:

| Archivo | Contenido |
|---|---|
| `data/anuncios_muestra.csv` | 117 anuncios públicos de 3 zonas, con duplicados y vacíos reales |
| `data/inmuebles_prueba.csv` | 11 inmuebles de prueba con coordenadas |
| `data/geo/transporte.geojson` | Estaciones de metro, tranvía y metrocable (OpenStreetMap) |
| `data/geo/equipamientos.geojson` | Educación, salud, parques, abastecimiento, seguridad y cultura (OpenStreetMap) |
| `data/geo/pot_tratamientos.geojson` | **Pendiente** — ver "Capa del POT" |

## Estructura

```
config/       parámetros del cálculo
data/         CSV de anuncios, inmuebles de prueba y capas geográficas
docs/         diccionario de datos y plantilla de la ficha
ejemplos/     ficha JSON de ejemplo
notebooks/    notebook de arranque para Colab
validacion/   cálculo manual, valores esperados y validador
src/ficha/    implementación de referencia (organizadores)
scripts/      construcción de los datos desde las fuentes (organizadores)
tests/        pruebas unitarias y prueba contra el cálculo manual
```

## Uso

Requisitos: Python 3.9 o superior y PyYAML. No hay más dependencias.

```bash
# Generar las fichas de referencia en salidas/fichas/
PYTHONPATH=src python3 -m ficha.ficha

# Validar fichas contra el cálculo manual (sirve para cualquier carpeta de fichas)
python3 validacion/validar.py salidas/fichas

# Pruebas
python3 -m unittest discover -s tests -t .
```

En Colab, el notebook clona el repositorio, carga los datos y valida la solución del participante.

## Capa del POT (pendiente)

El geoportal del Distrito (`medellin.gov.co`) respondió **403** a las descargas automáticas durante
la preparación. Sin esa capa, la norma de los inmuebles de Medellín queda en `pendiente_capa`.

Pasos para completarla desde un navegador:

1. Abra la capa "Tratamiento POT vigente" del servicio
   `ServiciosCiudad/MAP6_Indicadores/MapServer/7` del servidor de mapas de Medellín.
   Otra opción es el dato abierto del POT Acuerdo 48 de 2014 en GeoMedellín.
2. Descargue los polígonos de la zona en GeoJSON (WGS84). Para la consulta REST:
   `query?where=1=1&geometry=-75.64,6.14,-75.52,6.29&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&f=geojson`
3. Guarde el archivo como `data/geo/pot_tratamientos.geojson`.
4. Ajuste `norma.campo_tratamiento` en `config/parametros.yaml` al nombre real del campo.
5. Actualice `norma.estado` de INM-04 e INM-06 en `validacion/esperado.json` y en `calculo_manual.md`.

Los pasos 1 y 2 no se pudieron comprobar desde la máquina de preparación, por el bloqueo 403.

## Origen de los datos y privacidad

- Los anuncios salen de 3 hojas internas de Venture One (factibilidad La Castellana, factibilidad
  Proyecto 2 y extensión Polígono). Solo se copiaron datos de mercado de anuncios públicos.
- **No se copiaron** teléfonos, nombres de contacto, comentarios de visitas, presupuestos de obra ni
  cálculos de rentabilidad. Las hojas originales no se versionan (`data/raw/` está en `.gitignore`).
- Los anuncios de Facebook y de letreros no llevan `id_anuncio`, porque el enlace identifica a una persona.
- Capas geográficas: © colaboradores de OpenStreetMap, licencia ODbL.
- No se hizo scraping: los datos de portales vienen de los registros manuales del equipo.

## Limitaciones conocidas

- `fecha` está vacía en todo el CSV y todos los precios son `pedido`. No hay precios de cierre.
- Siete inmuebles de prueba tienen coordenadas de barrio, no de dirección. Su entorno es aproximado.
- La regla de duplicados (`zona`, `area_m2`, `precio`) agrupa anuncios con dirección distinta en
  El Salvador y Ditaires. `validacion/calculo_manual.md` describe los casos.
- Metroplús casi no está mapeado en OSM y no entra en el cálculo de estaciones.

## Para organizadores

`src/ficha/` y `scripts/` son la solución de referencia. Si el repositorio se comparte con los
participantes antes de la hackatón, retire esas carpetas de la copia que reciben.
`tests/test_validacion.py` comprueba que la referencia coincide con el cálculo manual.

Para reconstruir los datos desde las hojas originales:

```bash
# Copiar los .xlsx a data/raw/ con los nombres de scripts/construir_muestra.py
python3 scripts/construir_muestra.py   # CSV de anuncios
python3 scripts/descargar_capas.py     # capas OSM (cambian con el tiempo)
python3 scripts/geocodificar.py        # inmuebles de prueba
```

Después de descargar capas nuevas, el cálculo manual se debe revisar.
