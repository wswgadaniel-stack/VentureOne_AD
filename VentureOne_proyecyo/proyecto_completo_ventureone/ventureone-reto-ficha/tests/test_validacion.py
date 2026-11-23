"""La implementación de referencia debe coincidir con el cálculo manual de 3 inmuebles."""
import copy
import importlib.util
import json
import unittest

from tests import RAIZ
from ficha.ficha import cargar_contexto, cargar_inmuebles, generar_ficha

_spec = importlib.util.spec_from_file_location("validar", RAIZ / "validacion" / "validar.py")
validar_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validar_mod)

ESPERADO = json.loads((RAIZ / "validacion" / "esperado.json").read_text(encoding="utf-8"))


class CalculoManual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctx = cargar_contexto()
        if ctx["pot"] is not None:
            raise unittest.SkipTest("Con la capa POT cargada, norma.estado cambia: actualizar esperado.json")
        inmuebles = {i["id_inmueble"]: i for i in cargar_inmuebles(ctx["params"])}
        cls.fichas = {k: generar_ficha(inmuebles[k], ctx) for k in ESPERADO["inmuebles"]}

    def test_cada_inmueble_coincide_con_el_calculo_manual(self):
        for id_inmueble, esp in ESPERADO["inmuebles"].items():
            with self.subTest(id_inmueble):
                self.assertEqual(validar_mod.validar(self.fichas[id_inmueble], esp, ESPERADO["_tolerancias"]), [])

    def test_el_validador_detecta_una_mediana_equivocada(self):
        ficha = copy.deepcopy(self.fichas["INM-04"])
        ficha["mercado"]["precio_m2"]["mediana"] += 10
        errores = validar_mod.validar(ficha, ESPERADO["inmuebles"]["INM-04"], ESPERADO["_tolerancias"])
        self.assertEqual(len(errores), 1)
        self.assertIn("mediana", errores[0])


if __name__ == "__main__":
    unittest.main()
