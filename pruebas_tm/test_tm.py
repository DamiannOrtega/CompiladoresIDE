# pruebas_tm/test_tm.py — Pruebas de generación y ejecución de código TM
#
# Ejecutar desde la raíz del proyecto:
#   python -m unittest pruebas_tm.test_tm -v
#
# Cada programa válido se verifica en dos partes independientes:
#   1. Generación: el .tm existe, es legible, las direcciones son contiguas,
#      los registros son válidos y todos los saltos tienen destino válido.
#   2. Ejecución: el simulador carga ese mismo archivo .tm, pide las entradas
#      y produce exactamente la salida esperada (calculada a mano).
# Los programas sólo con enteros y sin cadenas se ejecutan además en el
# simulador original tm.exe de TINY (si existe) para comparar resultados.

import os
import re
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from ide.servicios.compilador import ServicioCompilador            # noqa: E402
from ide.compilador.tm_formato import parsear_programa, REG_PC     # noqa: E402
from ide.compilador.maquina_tm import MaquinaTM                    # noqa: E402

DIR_PRUEBAS = os.path.dirname(os.path.abspath(__file__))
TM_EXE = os.path.join(RAIZ, "Tiny_Corregido", "tm.exe")

# Los .tm de las pruebas se escriben en una carpeta temporal, no en outputs/
_TMP = tempfile.TemporaryDirectory()
_dir_salida_original = ServicioCompilador.dir_salida


def setUpModule():
    ServicioCompilador.dir_salida = staticmethod(lambda: _TMP.name)


def tearDownModule():
    ServicioCompilador.dir_salida = _dir_salida_original
    _TMP.cleanup()

# programa → lista de (entradas, salida esperada)
CASOS = {
    "p01_aritmetica.src": [([], ["11", "20", "2", "1024", "-205"])],
    "p02_entrada_salida.src": [
        (["7", "4"], ["Suma: 11", "Producto: 28", "Promedio: 5.5"]),
        (["-3", "10"], ["Suma: 7", "Producto: -30", "Promedio: 3.5"]),
    ],
    "p03_condicional.src": [
        (["5"], ["positivo"]),
        (["-4"], ["negativo", "par"]),
        (["0"], ["cero", "par"]),
    ],
    "p04_while.src": [(["10"], ["55"]), (["0"], ["0"]), (["100"], ["5050"])],
    "p05_factorial.src": [(["5"], ["120"]), (["3"], ["6"]), (["0"], []), (["10"], ["3628800"])],
    "p06_combinado.src": [(
        ["20"],
        ["2", "3", "5", "7", "11", "13", "17", "19",
         "Primos encontrados: 8", "Fibonacci(10) = 55", "fin"],
    )],
    "p07_reales.src": [(
        ["2"],
        ["Area: 12.56636", "3.0", "3.5", "8.0 es real", "menor o igual"],
    )],
    "p08_potencia_modulo.src": [([], ["0", "0.25", "2.25", "-1", "1"])],
    "p09_bool_entrada.src": [
        (["true", "1.5"], ["v = 12.0", "3", "1"]),
        (["false", "2"], ["v = 2.0", "0", "0"]),
    ],
}

# Programas compatibles con tm.exe (sólo enteros, sin cadenas)
COMPATIBLES_TM_EXE = ["p01_aritmetica.src", "p04_while.src", "p05_factorial.src"]

ERRONEOS = {
    "e01_semantico.src": "semántico",
    "e02_sintactico.src": "sintáctico",
    "e03_lexico.src": "léxico",
}


def compilar(nombre):
    ruta = os.path.join(DIR_PRUEBAS, nombre)
    return ServicioCompilador().compilar("tm", ruta=ruta)


def destino_salto(ins):
    """Dirección absoluta a la que salta la instrucción (o None si no salta)."""
    if ins.op.startswith("J") or (ins.op == "LDA" and ins.r == REG_PC):
        if ins.b != REG_PC:
            return "no-relativo"
        return ins.direccion + 1 + ins.a
    return None


class TestGeneracionTM(unittest.TestCase):

    def test_generacion_programas_validos(self):
        for nombre in CASOS:
            with self.subTest(programa=nombre):
                res = compilar(nombre)
                self.assertEqual([e.msg for e in res.err], [], "no debe haber errores")
                self.assertTrue(os.path.isfile(res.ruta_tm), "debe existir el archivo .tm")
                with open(res.ruta_tm, encoding="utf-8") as f:
                    self.assertEqual(f.read(), res.tm, "lo mostrado debe ser el archivo en disco")

                instr, cadenas = parsear_programa(res.tm)
                n = len(instr)
                self.assertEqual(sorted(instr), list(range(n)), "direcciones contiguas desde 0")
                self.assertEqual(instr[n - 1].op, "HALT")
                self.assertEqual((instr[0].op, instr[1].op), ("LD", "ST"), "preludio estándar")
                for ins in instr.values():
                    d = destino_salto(ins)
                    if d is not None:
                        self.assertNotEqual(d, "no-relativo", f"salto no relativo al pc en {ins.direccion}")
                        self.assertTrue(0 <= d < n, f"salto de {ins.direccion} a {d} fuera del programa")
                    if ins.op == "OUTS":
                        self.assertIn(ins.a, cadenas)

    def test_variables_usan_tabla_de_simbolos(self):
        res = compilar("p04_while.src")
        orden = [s.nombre for s in res.sim]
        self.assertEqual(orden, ["n", "i", "suma"])
        # cin >> n guarda en 0(5); suma = ... guarda en 2(5)
        self.assertRegex(res.tm, r"ST\s+0,0\(5\)\s+\tcin: guardar en n")
        self.assertRegex(res.tm, r"ST\s+0,2\(5\)\s+\tasignar: suma = ac")

    def test_salto_while_regresa_a_la_condicion(self):
        res = compilar("p04_while.src")
        instr, _ = parsear_programa(res.tm)
        regreso = [i for i in instr.values() if i.op == "LDA" and i.r == REG_PC and i.a < 0]
        self.assertEqual(len(regreso), 1)
        inicio = destino_salto(regreso[0])
        # la condición empieza cargando i (1(5))
        self.assertEqual((instr[inicio].op, instr[inicio].a, instr[inicio].b), ("LD", 1, 5))

    def test_errores_no_generan_tm(self):
        for nombre, tipo in ERRONEOS.items():
            with self.subTest(programa=nombre):
                destino = ServicioCompilador.ruta_tm_para(nombre)
                # Dejar un .tm viejo con ese nombre: no debe sobrevivir
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(destino, "w", encoding="utf-8") as f:
                    f.write("  0:   HALT  0,0,0\n")
                res = compilar(nombre)
                tipos = {e.tipo for e in res.err}
                self.assertIn(tipo, tipos)
                self.assertIn("bloqueo", tipos)
                self.assertEqual(res.tm, "")
                self.assertFalse(os.path.isfile(destino), "no debe quedar un .tm previo")

    def test_operador_no_soportado_es_error_de_generacion(self):
        res = ServicioCompilador().compilar(
            "tm", ruta="op_invalido.src",
            texto="main { int a, b; a = 1; b = a ++ 2; }")
        self.assertIn("generación", {e.tipo for e in res.err})
        self.assertEqual(res.tm, "")


class TestCodigoIntermedio(unittest.TestCase):
    """Código intermedio de tres direcciones (.ci), generado en paralelo al .tm."""

    FACTORIAL = [
        "read x", "fact = 1", "t1 = 0 < x", "if_false t1 goto L1", "L2:",
        "t2 = fact * x", "fact = t2", "x = x - 1", "t3 = x == 0", "if_false t3 goto L2",
        "write fact", "writeln", "L1:", "halt",
    ]

    @staticmethod
    def instrucciones(texto):
        """Líneas de código sin comentarios ni numeración."""
        res = []
        for l in texto.splitlines():
            if not l.strip() or l.startswith("//"):
                continue
            m = re.match(r"\s*\d+:\s+(.*)$", l)
            res.append(m.group(1).strip() if m else l.strip())
        return res

    def test_factorial_como_en_el_libro(self):
        res = compilar("p05_factorial.src")
        self.assertEqual(self.instrucciones(res.ir), self.FACTORIAL)

    def test_estructura_de_todos_los_programas(self):
        programas = [os.path.join(DIR_PRUEBAS, n) for n in CASOS]
        dir_ej = os.path.join(RAIZ, "ejercicios")
        for g in range(1, 13):
            for k in range(1, 6):
                programas.append(os.path.join(dir_ej, f"grupo{g}", f"ej{k}.src"))
        for ruta in programas:
            with self.subTest(programa=os.path.relpath(ruta, RAIZ)):
                res = ServicioCompilador().compilar("tm", ruta=ruta)
                self.assertEqual(res.err, [])
                with open(res.ruta_ci, encoding="utf-8") as f:
                    self.assertEqual(f.read(), res.ir, "lo mostrado debe ser el archivo en disco")
                lineas = self.instrucciones(res.ir)
                self.assertEqual(lineas[-1], "halt")
                definidas = {l[:-1] for l in lineas if re.fullmatch(r"L\d+:", l)}
                usadas = set(re.findall(r"goto (L\d+)", res.ir))
                self.assertEqual(usadas - definidas, set(), "saltos a etiquetas inexistentes")
                asignados = set()
                for l in lineas:
                    m = re.match(r"(t\d+) = (.*)", l)
                    usados = set(re.findall(r"\bt\d+\b", m.group(2) if m else l))
                    self.assertEqual(usados - asignados, set(), f"temporal usado antes de asignarse: {l}")
                    if m:
                        asignados.add(m.group(1))

    def test_errores_no_generan_ci(self):
        for nombre in ERRONEOS:
            with self.subTest(programa=nombre):
                destino = ServicioCompilador.ruta_ci_para(nombre)
                with open(destino, "w", encoding="utf-8") as f:
                    f.write("// viejo\n")
                res = compilar(nombre)
                self.assertEqual(res.ir, "")
                self.assertFalse(os.path.isfile(destino), "no debe quedar un .ci previo")


class TestEjecucionTM(unittest.TestCase):

    def ejecutar(self, ruta_tm, entradas):
        cola = list(entradas)
        pedidas = []

        def leer(sol):
            pedidas.append(sol)
            return cola.pop(0) if cola else None

        maq = MaquinaTM()
        maq.cargar_archivo(ruta_tm)
        return maq.ejecutar(leer), pedidas

    def test_ejecucion_programas_validos(self):
        for nombre, casos in CASOS.items():
            res_c = compilar(nombre)
            for entradas, esperado in casos:
                with self.subTest(programa=nombre, entradas=entradas):
                    res, pedidas = self.ejecutar(res_c.ruta_tm, entradas)
                    self.assertEqual(res.estado, "HALT", res.mensaje)
                    self.assertEqual(len(pedidas), len(entradas), "IN pedidas")
                    self.assertEqual(res.salida, esperado)

    def test_tipo_de_entrada_y_reintento(self):
        res_c = compilar("p02_entrada_salida.src")
        res, pedidas = self.ejecutar(res_c.ruta_tm, ["abc", "7", "4"])
        self.assertEqual(res.salida[0], "Suma: 11")
        self.assertEqual(pedidas[0].tipo, "int")
        self.assertIn("leer a", pedidas[0].comentario)
        self.assertTrue(pedidas[1].error_previo, "debe avisar del valor inválido")

    def test_division_entre_cero_en_ejecucion(self):
        res_c = ServicioCompilador().compilar(
            "tm", ruta="div_cero.src",
            texto="main { int a, b; cin >> a; b = 10 / a; cout << b; }")
        self.assertEqual(res_c.err, [])
        res, _ = self.ejecutar(res_c.ruta_tm, ["0"])
        self.assertEqual(res.estado, "ERROR")
        self.assertIn("División entre cero", res.mensaje)

    def test_ciclo_infinito_se_detiene(self):
        res_c = ServicioCompilador().compilar(
            "tm", ruta="infinito.src",
            texto="main { int a; a = 0; while a == 0 a = 0; end }")
        maq = MaquinaTM()
        maq.cargar_archivo(res_c.ruta_tm)
        res = maq.ejecutar(lambda s: None, max_pasos=10_000)
        self.assertEqual(res.estado, "LIMITE")

    def test_cancelar_entrada(self):
        res_c = compilar("p04_while.src")
        res, _ = self.ejecutar(res_c.ruta_tm, [])
        self.assertEqual(res.estado, "CANCELADO")

    @unittest.skipUnless(os.path.isfile(TM_EXE), "tm.exe de TINY no disponible")
    def test_compatibilidad_con_tm_exe(self):
        """El .tm de programas enteros sin cadenas corre igual en tm.exe."""
        for nombre in COMPATIBLES_TM_EXE:
            res_c = compilar(nombre)
            for entradas, esperado in CASOS[nombre]:
                with self.subTest(programa=nombre, entradas=entradas):
                    comandos = "g\n" + "".join(f"{e}\n" for e in entradas) + "q\n"
                    proc = subprocess.run(
                        [TM_EXE, res_c.ruta_tm], input=comandos, capture_output=True,
                        text=True, timeout=30, cwd=os.path.dirname(TM_EXE))
                    salidas = re.findall(r"OUT instruction prints: (-?\d+)", proc.stdout)
                    self.assertIn("HALT", proc.stdout.upper(), proc.stdout[-500:])
                    self.assertEqual(salidas, esperado, proc.stdout[-500:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
