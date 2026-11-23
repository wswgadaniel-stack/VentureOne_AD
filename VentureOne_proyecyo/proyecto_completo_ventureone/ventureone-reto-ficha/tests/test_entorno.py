import unittest

from tests import params
from ficha.entorno import bloque_entorno
from ficha.geo import haversine_m, punto_en_geometria
from ficha.norma import bloque_norma


def punto(lat, lon, **props):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


# ~0.009 grados de latitud = ~1000 m
TRANSPORTE = [punto(6.2400, -75.56, nombre="Cerca", sistema="metro"),
              punto(6.2450, -75.56, nombre="Media", sistema="tranvia"),
              punto(6.2405, -75.56, nombre="Excluida", sistema="metroplus")]
EQUIPAMIENTOS = [punto(6.2401, -75.56, nombre="Escuela", categoria="educacion"),
                 punto(6.2402, -75.56, nombre="Parque", categoria="parques"),
                 punto(6.2600, -75.56, nombre="Lejos", categoria="salud")]
CUADRADO = {"type": "Polygon", "coordinates": [[[-75.57, 6.23], [-75.55, 6.23], [-75.55, 6.25], [-75.57, 6.25], [-75.57, 6.23]]]}


class Geo(unittest.TestCase):
    def test_haversine_un_grado_de_latitud(self):
        self.assertAlmostEqual(haversine_m(6.0, -75.0, 7.0, -75.0), 111_195, delta=5)

    def test_punto_en_poligono_y_hueco(self):
        self.assertTrue(punto_en_geometria(6.24, -75.56, CUADRADO))
        self.assertFalse(punto_en_geometria(6.26, -75.56, CUADRADO))
        con_hueco = {"type": "Polygon", "coordinates": CUADRADO["coordinates"] + [
            [[-75.565, 6.235], [-75.555, 6.235], [-75.555, 6.245], [-75.565, 6.245], [-75.565, 6.235]]]}
        self.assertFalse(punto_en_geometria(6.24, -75.56, con_hueco))


class Entorno(unittest.TestCase):
    def test_estacion_cercana_y_conteos_en_radio(self):
        e = bloque_entorno(6.2400, -75.56, "cruce", TRANSPORTE, EQUIPAMIENTOS, params()["entorno"])
        self.assertEqual(e["estacion_mas_cercana"]["nombre"], "Cerca")
        self.assertEqual(e["estacion_mas_cercana"]["distancia_m"], 0)
        self.assertEqual(e["estaciones_en_radio"], 2)  # metroplus no cuenta; "Media" a ~556 m
        self.assertEqual(e["equipamientos_en_radio"]["educacion"], 1)
        self.assertEqual(e["equipamientos_en_radio"]["parques"], 1)
        self.assertEqual(e["equipamientos_en_radio"]["salud"], 0)
        self.assertFalse(e["aproximado"])

    def test_precision_barrio_marca_aproximado(self):
        e = bloque_entorno(6.24, -75.56, "barrio", TRANSPORTE, EQUIPAMIENTOS, params()["entorno"])
        self.assertTrue(e["aproximado"])


class Norma(unittest.TestCase):
    CAPA = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": CUADRADO, "properties": {"TRATAMIENTO": "CN2"}}]}

    def test_municipio_sin_capa(self):
        n = bloque_norma(6.24, -75.56, "itagui", self.CAPA, params()["norma"])
        self.assertEqual(n["estado"], "no_disponible")
        self.assertIsNone(n["tratamiento_pot"])

    def test_capa_pendiente(self):
        n = bloque_norma(6.24, -75.56, "medellin", None, params()["norma"])
        self.assertEqual(n["estado"], "pendiente_capa")

    def test_tratamiento_encontrado_y_fuera_de_capa(self):
        p = params()["norma"]
        self.assertEqual(bloque_norma(6.24, -75.56, "medellin", self.CAPA, p)["tratamiento_pot"], "CN2")
        self.assertEqual(bloque_norma(6.30, -75.56, "medellin", self.CAPA, p)["estado"], "fuera_de_capa")


if __name__ == "__main__":
    unittest.main()
