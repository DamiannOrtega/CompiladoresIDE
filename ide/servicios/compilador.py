# servicios/compilador.py — Servicio de compilación
#
# Fase 1 (léxica):    analizador léxico real.
# Fase 2 (sintáctico): analizador sintáctico real + construcción del AST.
#   IMPORTANTE: si existen errores léxicos, el análisis sintáctico NO se ejecuta.
# Fases 3-5: pendientes de implementación.

import os

from ide.modelos.datos import (
    Tok, Err, Sim, NodoArb, ResultadoCompilacion
)
from ide.compilador.lexico import analyze as _analyze_lexico
from ide.compilador.sintatico import parse as _parse_sintatico


class ServicioCompilador:
    """Gestiona la comunicación con el compilador."""

    FASES = ["lexical", "syntax", "semantic", "ir", "run"]

    def compilar(self, fase: str, ruta: str = "", texto: str = "") -> ResultadoCompilacion:
        """
        Ejecuta la fase indicada y devuelve un ResultadoCompilacion.

        Parámetros
        ----------
        fase  : "lexical" | "syntax" | "semantic" | "ir" | "run"
        ruta  : ruta del archivo en disco (respaldo si texto está vacío)
        texto : contenido del editor (tiene prioridad sobre ruta)
        """
        res = ResultadoCompilacion(fase=fase)

        def _cargar_texto() -> str:
            src = texto
            if not src and ruta and os.path.isfile(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        src = f.read()
                except Exception:
                    pass
            return src

        # ── Fase 1: Análisis léxico ───────────────────────────────────────────
        if fase == "lexical":
            src = _cargar_texto()
            tokens, errores = _analyze_lexico(src)

            res.tok = [
                Tok(lexema=t.valor, tipo=t.tipo, linea=t.linea, col=t.columna)
                for t in tokens
            ]
            res.err = [
                Err(tipo="léxico", linea=e.linea, col=e.columna,
                    msg=f"{e.error}: '{e.valor}'")
                for e in errores
            ]

        # ── Fase 2: Análisis sintáctico ───────────────────────────────────────
        elif fase == "syntax":
            src = _cargar_texto()

            # Paso 1: léxico
            tokens, errores_lex = _analyze_lexico(src)

            res.tok = [
                Tok(lexema=t.valor, tipo=t.tipo, linea=t.linea, col=t.columna)
                for t in tokens
            ]

            # Si hay errores léxicos → bloquear el análisis sintáctico
            if errores_lex:
                res.err = [
                    Err(tipo="léxico", linea=e.linea, col=e.columna,
                        msg=f"{e.error}: '{e.valor}'")
                    for e in errores_lex
                ]
                res.err.append(Err(
                    tipo="bloqueo",
                    linea=0,
                    col=0,
                    msg=(
                        "El análisis sintáctico no se ejecutó porque existen "
                        "errores léxicos. Corrija todos los errores léxicos "
                        "antes de ejecutar el análisis sintáctico."
                    )
                ))
                return res   # no continúa con el parser

            # Paso 2: sintáctico (solo si no hay errores léxicos)
            arbol, errores_sint = _parse_sintatico(tokens)

            res.err = [
                Err(tipo="sintáctico", linea=e.linea, col=e.columna, msg=e.msg)
                for e in errores_sint
            ]
            res.arb = arbol

        # ── Fases futuras ─────────────────────────────────────────────────────
        elif fase == "semantic":
            res.err = [Err(tipo="info", linea=0, col=0,
                          msg="Análisis semántico aún no implementado.")]

        elif fase == "ir":
            res.ir = "-- Generación de código intermedio aún no implementada. --"

        elif fase == "run":
            res.sal = "-- Ejecución aún no implementada. --"

        return res
