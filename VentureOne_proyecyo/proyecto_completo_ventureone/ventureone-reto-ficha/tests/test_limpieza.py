import unittest

from tests import params
from ficha.limpieza import deduplicar, motivo_invalido, normalizar_estado, preparar


def fila(**kw):
    base = {"id_anuncio": "", "fuente": "fincaraiz", "fecha": "", "zona": "z", "municipio": "medellin",
            "barrio": "b", "area_m2": "70", "precio": "350000000", "habitaciones": "3", "banos": "2",
            "parqueadero": "1", "estado": "REMODELADO", "tipo_precio": "pedido", "origen": "x:1"}
    base.update(kw)
    return base


class NormalizarEstado(unittest.TestCase):
    def test_variantes_de_texto_mapean_al_mismo_estado(self):
        for texto in ["REMODELADA", "remodelado", " Remodelada ? "]:
            self.assertEqual(normalizar_estado(texto, params()["estados"]), "remodelado")

    def test_habitable_y_por_remodelar(self):
        e = params()["estados"]
        self.assertEqual(normalizar_estado("HABITABLE POR REMODELAR", e), "habitable")
        self.assertEqual(normalizar_estado("Ok", e), "habitable")
        self.assertEqual(normalizar_estado("SIN REMODELAR (OBRA NEGRA)", e), "por_remodelar")
        self.assertEqual(normalizar_estado("Reformar", e), "por_remodelar")

    def test_texto_vacio_o_desconocido_queda_sin_clasificar(self):
        e = params()["estados"]
        self.assertEqual(normalizar_estado("", e), "sin_clasificar")
        self.assertEqual(normalizar_estado("lujo", e), "sin_clasificar")


class Preparar(unittest.TestCase):
    def test_calcula_precio_m2_y_convierte_numeros(self):
        a = preparar(fila(area_m2="70", precio="350000000"), params())
        self.assertEqual(a["area_m2"], 70.0)
        self.assertEqual(a["precio_m2"], 5_000_000.0)
        self.assertEqual(a["estado_canonico"], "remodelado")

    def test_area_vacia_deja_precio_m2_vacio(self):
        self.assertIsNone(preparar(fila(area_m2=""), params())["precio_m2"])


class MotivoInvalido(unittest.TestCase):
    def test_fila_valida(self):
        self.assertIsNone(motivo_invalido(preparar(fila(), params()), params()))

    def test_motivos(self):
        p = params()
        self.assertEqual(motivo_invalido(preparar(fila(area_m2=""), p), p), "sin_area")
        self.assertEqual(motivo_invalido(preparar(fila(precio=""), p), p), "sin_precio")
        self.assertEqual(motivo_invalido(preparar(fila(precio="35000000"), p), p), "precio_m2_fuera_de_rango")
        self.assertEqual(motivo_invalido(preparar(fila(estado=""), p), p), "estado_sin_clasificar")
        self.assertEqual(motivo_invalido(preparar(fila(tipo_precio="arriendo"), p), p), "tipo_precio_no_aceptado")


class Deduplicar(unittest.TestCase):
    def test_mismo_id_es_duplicado_y_se_conserva_el_primero(self):
        p = params()
        filas = [preparar(fila(id_anuncio="fr:1", origen="a"), p), preparar(fila(id_anuncio="fr:1", origen="b"), p)]
        unicos = deduplicar(filas, p)
        self.assertEqual(len(unicos), 1)
        self.assertEqual(unicos[0]["origen"], "a")
        self.assertEqual(unicos[0]["origenes_agrupados"], ["a", "b"])

    def test_misma_zona_area_y_precio_sin_id_es_duplicado(self):
        p = params()
        filas = [preparar(fila(id_anuncio="fr:1", fuente="fincaraiz", origen="a"), p),
                 preparar(fila(id_anuncio="", fuente="facebook", area_m2="70.0", origen="b"), p)]
        self.assertEqual(len(deduplicar(filas, p)), 1)

    def test_otra_zona_no_es_duplicado(self):
        p = params()
        filas = [preparar(fila(origen="a"), p), preparar(fila(zona="otra", origen="b"), p)]
        self.assertEqual(len(deduplicar(filas, p)), 2)

    def test_fila_sin_area_solo_se_deduplica_por_id(self):
        p = params()
        filas = [preparar(fila(area_m2="", origen="a"), p), preparar(fila(area_m2="", origen="b"), p)]
        self.assertEqual(len(deduplicar(filas, p)), 2)


if __name__ == "__main__":
    unittest.main()
