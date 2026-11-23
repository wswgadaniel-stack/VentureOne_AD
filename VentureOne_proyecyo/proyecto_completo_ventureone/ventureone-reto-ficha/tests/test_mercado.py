import unittest

from tests import params
from ficha.mercado import estadisticas, nivel_confianza, seleccionar_comparables


def anuncio(origen, area, precio_m2, zona="z", estado="remodelado", id_anuncio=""):
    return {"origen": origen, "origenes_agrupados": [origen], "ids_agrupados": [id_anuncio] if id_anuncio else [],
            "zona": zona, "estado_canonico": estado, "area_m2": float(area), "precio_m2": float(precio_m2),
            "precio": float(area) * precio_m2, "motivo_invalido": None}


INMUEBLE = {"origen": "s", "id_anuncio": "fr:s", "zona": "z", "estado_canonico": "remodelado", "area_m2": 100.0}


class Seleccion(unittest.TestCase):
    def test_filtra_zona_estado_area_y_validez(self):
        p = params()
        anuncios = [
            anuncio("ok", 100, 5e6),
            anuncio("otra_zona", 100, 5e6, zona="w"),
            anuncio("otro_estado", 100, 5e6, estado="habitable"),
            anuncio("muy_grande", 131, 5e6),
            {**anuncio("invalido", 100, 5e6), "motivo_invalido": "sin_precio"},
            anuncio("limite_inferior", 70, 5e6),
        ]
        sel = [a["origen"] for a in seleccionar_comparables(INMUEBLE, anuncios, p)]
        self.assertEqual(sel, ["ok", "limite_inferior"])

    def test_excluye_el_anuncio_del_propio_inmueble_aunque_este_agrupado(self):
        p = params()
        propio = {**anuncio("dup", 100, 5e6), "origenes_agrupados": ["dup", "s"]}
        por_id = anuncio("x", 100, 5e6, id_anuncio="fr:s")
        self.assertEqual(seleccionar_comparables(INMUEBLE, [propio, por_id], p), [])


class Estadisticas(unittest.TestCase):
    def test_valores_conocidos(self):
        e = estadisticas([4e6, 5e6, 6e6, 9e6])
        self.assertEqual(e["n"], 4)
        self.assertEqual(e["mediana"], 5_500_000)
        self.assertEqual(e["promedio"], 6_000_000)
        self.assertEqual(e["minimo"], 4_000_000)
        self.assertEqual(e["maximo"], 9_000_000)
        # desviación muestral = sqrt(14e12/3) = 2_160_246.9
        self.assertEqual(e["desviacion"], 2_160_247)
        self.assertAlmostEqual(e["coef_variacion"], 0.3600, places=4)

    def test_un_solo_valor_no_tiene_dispersion(self):
        e = estadisticas([5e6])
        self.assertIsNone(e["desviacion"])
        self.assertIsNone(e["coef_variacion"])

    def test_sin_valores(self):
        self.assertEqual(estadisticas([])["n"], 0)
        self.assertIsNone(estadisticas([])["mediana"])


class Confianza(unittest.TestCase):
    def test_niveles(self):
        c = params()["confianza"]
        self.assertEqual(nivel_confianza(5, 0.15, c)[0], "alta")
        self.assertEqual(nivel_confianza(5, 0.16, c)[0], "media")
        self.assertEqual(nivel_confianza(3, 0.25, c)[0], "media")
        self.assertEqual(nivel_confianza(2, 0.05, c)[0], "baja")
        self.assertEqual(nivel_confianza(10, 0.30, c)[0], "baja")
        self.assertEqual(nivel_confianza(1, None, c)[0], "baja")

    def test_el_motivo_explica_el_nivel(self):
        nivel, motivo = nivel_confianza(2, 0.05, params()["confianza"])
        self.assertIn("2 comparables", motivo)


if __name__ == "__main__":
    unittest.main()
