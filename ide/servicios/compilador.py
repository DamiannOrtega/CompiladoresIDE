# servicios/compilador.py — Servicio de compilación
#
# Fase 1 (léxica):    analizador léxico real.
# Fase 2 (sintáctico): analizador sintáctico real + construcción del AST.
#   IMPORTANTE: si existen errores léxicos, el análisis sintáctico NO se ejecuta.
# Fase 3 (semántico):  analizador semántico real + tabla de símbolos.
# Fase final ("tm" / "run"): generación de código TM (generador_tm.py) y
#   escritura del archivo outputs/<programa>.tm; sólo si no hubo errores.
#   La ejecución en el simulador (maquina_tm.py) se hace con ejecutar_tm().

import os
import sys

from ide.compilador.generador_tm import generar_codigo_tm as _generar_tm
from ide.compilador.maquina_tm import ejecutar_archivo as _ejecutar_archivo_tm
from ide.modelos.datos import (
    Tok, Err, Sim, NodoArb, ResultadoCompilacion
)
from ide.compilador.lexico import analyze as _analyze_lexico
from ide.compilador.sintatico import parse as _parse_sintatico
from ide.compilador.semantico import analyze_semantics as _analyze_semantico


class ServicioCompilador:
    """Gestiona la comunicación con el compilador."""

    FASES = ["lexical", "syntax", "semantic", "ir", "tm", "run"]

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

        # ── Fase 3: Análisis semántico ───────────────────────────────────────
        elif fase == "semantic":
            src = _cargar_texto()

            # Paso 1: léxico
            tokens, errores_lex = _analyze_lexico(src)
            res.tok = [
                Tok(lexema=t.valor, tipo=t.tipo, linea=t.linea, col=t.columna)
                for t in tokens
            ]

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
                    msg="El análisis semántico no se ejecutó porque existen errores léxicos. Corrija los errores léxicos primero."
                ))
                return res

            # Paso 2: sintáctico
            arbol, errores_sint = _parse_sintatico(tokens)
            res.arb = arbol

            # Paso 3: semántico (se ejecuta sobre el AST generado incluso con recuperación de errores)
            if arbol is not None:
                arbol_anotado, tabla, errores_sem = _analyze_semantico(arbol)
                res.arb_anotado = arbol_anotado
                res.sim = tabla.obtener_simbolos()
                res.err = [
                    Err(tipo="sintáctico", linea=e.linea, col=e.columna, msg=e.msg)
                    for e in errores_sint
                ] + [
                    Err(tipo="semántico", linea=e.linea, col=e.columna,
                        msg=f"{e.error}: {e.msg}")
                    for e in errores_sem
                ]
            else:
                res.err = [
                    Err(tipo="sintáctico", linea=e.linea, col=e.columna, msg=e.msg)
                    for e in errores_sint
                ]

        elif fase == "ir":
            res.ir = "-- Generación de código intermedio aún no implementada. --"

        elif fase in ("tm", "run"):
            # Compilar todo: Léxico -> Sintáctico -> Semántico -> Código TM.
            # La ejecución del .tm la realiza la interfaz con ejecutar_tm(),
            # porque las instrucciones IN necesitan pedir datos al usuario.
            src = _cargar_texto()
            tokens, errores_lex = _analyze_lexico(src)
            res.tok = [
                Tok(lexema=t.valor, tipo=t.tipo, linea=t.linea, col=t.columna)
                for t in tokens
            ]
            if errores_lex:
                res.err = [
                    Err(tipo="léxico", linea=e.linea, col=e.columna,
                        msg=f"{e.error}: '{e.valor}'")
                    for e in errores_lex
                ]
                self._borrar_tm(ruta)
                res.err.append(Err(
                    tipo="bloqueo", linea=0, col=0,
                    msg="No se generó código TM porque existen errores léxicos."
                ))
                return res

            arbol, errores_sint = _parse_sintatico(tokens)
            res.arb = arbol

            if arbol is not None:
                arbol_anotado, tabla, errores_sem = _analyze_semantico(arbol)
                res.arb_anotado = arbol_anotado
                res.sim = tabla.obtener_simbolos()
                res.err = [
                    Err(tipo="sintáctico", linea=e.linea, col=e.columna, msg=e.msg)
                    for e in errores_sint
                ] + [
                    Err(tipo="semántico", linea=e.linea, col=e.columna,
                        msg=f"{e.error}: {e.msg}")
                    for e in errores_sem
                ]
            else:
                res.err = [
                    Err(tipo="sintáctico", linea=e.linea, col=e.columna, msg=e.msg)
                    for e in errores_sint
                ]

            if res.err or res.arb_anotado is None:
                # Nunca dejar un .tm anterior como si correspondiera a este fuente
                self._borrar_tm(ruta)
                res.err.append(Err(
                    tipo="bloqueo", linea=0, col=0,
                    msg="No se generó código TM porque existen errores en las fases de análisis."
                ))
            else:
                self._generar_tm(res, tabla, ruta)

        return res

    # ── Generación y ejecución de código TM ──────────────────────────────────

    @staticmethod
    def dir_salida() -> str:
        """Carpeta outputs/ del proyecto (o junto al ejecutable si está empaquetado)."""
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, "outputs")

    @classmethod
    def ruta_tm_para(cls, ruta_fuente: str) -> str:
        nombre = os.path.splitext(os.path.basename(ruta_fuente))[0] if ruta_fuente else "programa"
        return os.path.join(cls.dir_salida(), f"{nombre or 'programa'}.tm")

    def _borrar_tm(self, ruta_fuente: str) -> None:
        destino = self.ruta_tm_para(ruta_fuente)
        try:
            if os.path.isfile(destino):
                os.remove(destino)
        except OSError:
            pass

    def _generar_tm(self, res: ResultadoCompilacion, tabla, ruta_fuente: str) -> None:
        nombre = os.path.basename(ruta_fuente) if ruta_fuente else "(editor sin guardar)"
        texto, errores_gen = _generar_tm(res.arb_anotado, tabla.obtener_simbolos(), nombre)
        if errores_gen:
            self._borrar_tm(ruta_fuente)
            res.err.extend(
                Err(tipo="generación", linea=e.linea, col=0, msg=f"{e.error}: {e.msg}")
                for e in errores_gen
            )
            return

        destino = self.ruta_tm_para(ruta_fuente)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write(texto)
        # Se muestra lo que realmente quedó en disco: el mismo archivo que se ejecuta
        with open(destino, "r", encoding="utf-8") as f:
            res.tm = f.read()
        res.ruta_tm = destino

    @staticmethod
    def ejecutar_tm(ruta_tm: str, leer_entrada, escribir_salida=None, interrumpir=None):
        """Carga el archivo .tm del disco y lo ejecuta en el simulador TM."""
        return _ejecutar_archivo_tm(ruta_tm, leer_entrada, escribir_salida,
                                    interrumpir=interrumpir)
