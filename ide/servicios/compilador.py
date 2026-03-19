# servicios/compilador.py — Servicio de compilación
#
# Fase 1 (léxica): llama al analizador léxico real.
# Fases 2-5: pendientes de implementación.

import os

from ide.modelos.datos import (
    Tok, Err, Sim, NodoArb, ResultadoCompilacion
)
from ide.compilador.lexico import analyze as _analyze_lexico


class ServicioCompilador:
    """Gestiona la comunicación con el compilador."""

    # Fases soportadas
    FASES = ["lexical", "syntax", "semantic", "ir", "run"]

    def compilar(self, fase: str, ruta: str = "", texto: str = "") -> ResultadoCompilacion:
        """
        Ejecuta la fase indicada y devuelve un ResultadoCompilacion.

        Parámetros
        ----------
        fase  : fase de compilación ("lexical", "syntax", ...)
        ruta  : ruta del archivo en disco (usada como respaldo si texto está vacío)
        texto : contenido del editor — tiene prioridad sobre ruta
        """
        res = ResultadoCompilacion(fase=fase)

        if fase == "lexical":
            # ── Obtener el código fuente ───────────────────────────────
            # Prioridad: texto del editor → archivo en disco
            if not texto and ruta and os.path.isfile(ruta):
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        texto = f.read()
                except Exception:
                    pass

            # ── Ejecutar el analizador léxico real ─────────────────────
            tokens, errores = _analyze_lexico(texto)

            # Convertir Token → Tok
            res.tok = [
                Tok(lexema=t.valor, tipo=t.tipo, linea=t.linea, col=t.columna)
                for t in tokens
            ]
            # Convertir ErrorLexico → Err
            res.err = [
                Err(tipo="lexico", linea=e.linea, col=e.columna, msg=f"{e.error}: '{e.valor}'")
                for e in errores
            ]

        # Las siguientes fases aún no están implementadas.
        # Devuelven resultados vacíos hasta que se desarrollen.
        elif fase == "syntax":
            res.err = [Err(tipo="info", linea=0, col=0, msg="Análisis sintáctico aún no implementado.")]

        elif fase == "semantic":
            res.err = [Err(tipo="info", linea=0, col=0, msg="Análisis semántico aún no implementado.")]

        elif fase == "ir":
            res.ir = "-- Generación de código intermedio aún no implementada. --"

        elif fase == "run":
            res.sal = "-- Ejecución aún no implementada. --"

        return res
