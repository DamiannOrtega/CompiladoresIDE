# servicios/compilador.py — Servicio de compilación (mock para Fase 1)
#
# En Fase 2, compilar() ejecutará:
#   python compiler.py --phase <fase> --in <ruta> --out <sal>
# y leerá los archivos JSON/TXT generados.
#
# Por ahora devuelve datos simulados para probar la UI.

from ide.modelos.datos import (
    Tok, Err, Sim, NodoArb, ResultadoCompilacion
)


class ServicioCompilador:
    """Gestiona la comunicación con el compilador (mock en Fase 1)."""

    # Fases soportadas (igual que el CLI futuro)
    FASES = ["lexical", "syntax", "semantic", "ir", "run"]

    def compilar(self, fase: str, ruta: str = "") -> ResultadoCompilacion:
        """Ejecuta la fase indicada y devuelve un ResultadoCompilacion."""
        res = ResultadoCompilacion(fase=fase)

        if fase == "lexical":
            res.tok = self._mock_tok()
            res.err = []

        elif fase == "syntax":
            res.tok = self._mock_tok()
            res.arb = self._mock_arb()
            res.err = []

        elif fase == "semantic":
            res.tok = self._mock_tok()
            res.arb = self._mock_arb()
            res.sim = self._mock_sim()
            res.err = []

        elif fase == "ir":
            res.tok = self._mock_tok()
            res.arb = self._mock_arb()
            res.sim = self._mock_sim()
            res.ir = self._mock_ir()
            res.err = []

        elif fase == "run":
            res.tok = self._mock_tok()
            res.arb = self._mock_arb()
            res.sim = self._mock_sim()
            res.ir = self._mock_ir()
            res.sal = self._mock_sal()
            res.err = []

        return res

    # ── Datos simulados ──────────────────────────────────────────────────

    def _mock_tok(self):
        return [
            Tok("int",   "KEYWORD",    1, 1),
            Tok("x",     "IDENTIFIER", 1, 5),
            Tok("=",     "OPERATOR",   1, 7),
            Tok("10",    "NUMBER",     1, 9),
            Tok(";",     "DELIMITER",  1, 11),
            Tok("float", "KEYWORD",    2, 1),
            Tok("y",     "IDENTIFIER", 2, 7),
            Tok("=",     "OPERATOR",   2, 9),
            Tok("x",     "IDENTIFIER", 2, 11),
            Tok("+",     "OPERATOR",   2, 13),
            Tok("2.5",   "NUMBER",     2, 15),
            Tok(";",     "DELIMITER",  2, 18),
        ]

    def _mock_err(self):
        return [
            Err("syntax",   3, 10, "Token inesperado '}'"),
            Err("semantic", 5,  1, "Variable 'z' no declarada"),
        ]

    def _mock_sim(self):
        return [
            Sim("x", "int",   "global", 1),
            Sim("y", "float", "global", 2),
        ]

    def _mock_arb(self):
        prog = NodoArb("Programa")
        decl_x = NodoArb("Declaración")
        decl_x.hijos = [NodoArb("int"), NodoArb("x"), NodoArb("= 10")]
        decl_y = NodoArb("Declaración")
        decl_y.hijos = [NodoArb("float"), NodoArb("y"), NodoArb("= x + 2.5")]
        prog.hijos = [decl_x, decl_y]
        return prog

    def _mock_ir(self):
        return (
            "t1 = 10\n"
            "x  = t1\n"
            "t2 = x + 2.5\n"
            "y  = t2\n"
        )

    def _mock_sal(self):
        return (
            "Programa ejecutado correctamente.\n"
            "x = 10\n"
            "y = 12.5\n"
        )
