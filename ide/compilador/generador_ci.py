# compilador/generador_ci.py — Código intermedio de tres direcciones (.ci)
#
# Recorre el mismo árbol anotado (NodoArb) que usa generador_tm.py y produce
# código de tres direcciones con temporales (t1, t2, ...) y etiquetas
# simbólicas (L1, L2, ...). Es una salida paralela al .tm: NO es la entrada
# del simulador TM, que sólo ejecuta el archivo .tm.
#
# Forma de las instrucciones:
#   x = y                       copia
#   t1 = a op b                 operación binaria (+ - * / % ^ < <= > >= == != && ||)
#   t2 = ! a                    operación unaria
#   t3 = (float) a              conversión int -> float (anotada por el semántico)
#   read x                      lectura (cin)
#   write a | write "texto"     escritura (cout)
#   writeln                     fin de la línea de un cout
#   if_false a goto L1          salto condicional
#   goto L2                     salto incondicional
#   label L1                    definición de etiqueta
#   halt                        fin del programa

from typing import List, Optional, Tuple

from ide.modelos.datos import NodoArb
from ide.compilador.errores import ErrorGeneracion

_OPERADORES = {"+", "-", "*", "/", "%", "^", "<", "<=", ">", ">=", "==", "!=", "&&", "||"}


def _nombre(etiqueta: str) -> str:
    return etiqueta.split(":", 1)[1].strip() if ":" in etiqueta else ""


class GeneradorCI:
    """Traduce el árbol anotado a código de tres direcciones."""

    def __init__(self, arbol: NodoArb, nombre_fuente: str = ""):
        self._arbol = arbol
        self._fuente = nombre_fuente or "(editor)"
        self._codigo: List[Tuple[str, str]] = []   # (tipo, texto): "instr" | "label"
        self._n_temp = 0
        self._n_etiq = 0
        self.errores: List[ErrorGeneracion] = []

    # ── API ───────────────────────────────────────────────────────────────────

    def generar(self) -> Tuple[str, List[ErrorGeneracion]]:
        self._sentencia(self._arbol)
        self._emitir("halt")
        return self._texto(), self.errores

    # ── Auxiliares ────────────────────────────────────────────────────────────

    def _error(self, msg: str, linea: int = 0) -> None:
        self.errores.append(ErrorGeneracion(msg=msg, linea=linea))

    def _emitir(self, texto: str) -> None:
        self._codigo.append(("instr", texto))

    def _etiqueta_def(self, etiqueta: str) -> None:
        self._codigo.append(("label", etiqueta))

    def _temp(self) -> str:
        self._n_temp += 1
        return f"t{self._n_temp}"

    def _nueva_etiqueta(self) -> str:
        self._n_etiq += 1
        return f"L{self._n_etiq}"

    def _texto(self) -> str:
        lineas = [
            "// Código intermedio de tres direcciones",
            f"// Archivo fuente: {self._fuente}",
            f"// Temporales usados: {self._n_temp}   Etiquetas: {self._n_etiq}",
            "",
        ]
        n = 0
        for tipo, texto in self._codigo:
            if tipo == "label":
                lineas.append(f"{texto}:")
            else:
                n += 1
                lineas.append(f"{n:4d}:   {texto}")
        return "\n".join(lineas) + "\n"

    # ── Sentencias ───────────────────────────────────────────────────────────

    def _sentencia(self, nodo: Optional[NodoArb]) -> None:
        if nodo is None:
            return
        etq = nodo.etiqueta

        if etq.startswith("Programa") or nodo.tipo_nodo == "bloque":
            for h in nodo.hijos:
                self._sentencia(h)
            return

        if etq.startswith("Decl:"):
            for var in nodo.hijos:
                if var.hijos:
                    valor = self._expresion(var.hijos[0])
                    self._emitir(f"{_nombre(var.etiqueta)} = {valor}")
            return

        if etq.startswith("Asignar:"):
            if nodo.hijos:
                valor = self._expresion(nodo.hijos[0])
                self._emitir(f"{_nombre(etq)} = {valor}")
            return

        if etq.startswith("Incrementar:") or etq.startswith("Decrementar:"):
            nombre = _nombre(etq).replace("++", "").replace("--", "").strip()
            op = "+" if etq.startswith("Incrementar:") else "-"
            self._emitir(f"{nombre} = {nombre} {op} 1")
            return

        if etq.startswith("Si (if)"):
            self._si(nodo)
            return

        if etq.startswith("Mientras (while)"):
            self._mientras(nodo)
            return

        if etq.startswith("Hacer (do-until)"):
            self._hacer(nodo)
            return

        if etq.startswith("Leer (cin)"):
            nombre = _nombre(etq)
            if not nombre and nodo.hijos:
                nombre = _nombre(nodo.hijos[0].etiqueta)
            self._emitir(f"read {nombre}")
            return

        if etq.startswith("Escribir (cout)"):
            self._escribir(nodo)
            return

        self._error(f"Sentencia no soportada en el código intermedio: '{etq}'", nodo.linea)

    def _si(self, nodo: NodoArb) -> None:
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'if' incompleta", nodo.linea)
            return
        cond = self._expresion(nodo.hijos[0])
        l_sino = self._nueva_etiqueta()
        self._emitir(f"if_false {cond} goto {l_sino}")
        self._sentencia(nodo.hijos[1])
        if len(nodo.hijos) > 2:
            l_fin = self._nueva_etiqueta()
            self._emitir(f"goto {l_fin}")
            self._etiqueta_def(l_sino)
            self._sentencia(nodo.hijos[2])
            self._etiqueta_def(l_fin)
        else:
            self._etiqueta_def(l_sino)

    def _mientras(self, nodo: NodoArb) -> None:
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'while' incompleta", nodo.linea)
            return
        l_inicio = self._nueva_etiqueta()
        l_fin = self._nueva_etiqueta()
        self._etiqueta_def(l_inicio)
        cond = self._expresion(nodo.hijos[0])
        self._emitir(f"if_false {cond} goto {l_fin}")
        self._sentencia(nodo.hijos[1])
        self._emitir(f"goto {l_inicio}")
        self._etiqueta_def(l_fin)

    def _hacer(self, nodo: NodoArb) -> None:
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'do-until' incompleta", nodo.linea)
            return
        l_inicio = self._nueva_etiqueta()
        self._etiqueta_def(l_inicio)
        self._sentencia(nodo.hijos[0])
        cond = self._expresion(nodo.hijos[1])
        self._emitir(f"if_false {cond} goto {l_inicio}")

    def _escribir(self, nodo: NodoArb) -> None:
        if not nodo.hijos:
            self._error("Sentencia 'cout' sin valor", nodo.linea)
            return
        sal = nodo.hijos[0]
        partes = sal.hijos if sal.etiqueta.startswith("Salida combinada") else [sal]
        for p in partes:
            if p.etiqueta.startswith("Cadena:"):
                self._emitir(f"write {_nombre(p.etiqueta)}")
            else:
                self._emitir(f"write {self._expresion(p)}")
        self._emitir("writeln")

    # ── Expresiones: devuelven la dirección (variable, constante o temporal) ──

    def _expresion(self, nodo: Optional[NodoArb]) -> str:
        if nodo is None:
            self._error("Expresión vacía")
            return "?"
        valor = self._expresion_sin_conv(nodo)
        if nodo.conversion == "int -> float":
            t = self._temp()
            self._emitir(f"{t} = (float) {valor}")
            return t
        return valor

    def _expresion_sin_conv(self, nodo: NodoArb) -> str:
        etq = nodo.etiqueta
        if etq.startswith("Num:") or etq.startswith("Id:"):
            return _nombre(etq)
        if etq.startswith("Bool:"):
            return _nombre(etq).lower()
        if not etq.startswith("Op:"):
            self._error(f"Expresión no soportada en el código intermedio: '{etq}'", nodo.linea)
            return "?"

        op = _nombre(etq)
        if op == "!":
            a = self._expresion(nodo.hijos[0]) if nodo.hijos else "?"
            t = self._temp()
            self._emitir(f"{t} = ! {a}")
            return t
        if op not in _OPERADORES or len(nodo.hijos) < 2:
            self._error(f"Operador '{op}' no soportado en expresiones", nodo.linea)
            return "?"
        a = self._expresion(nodo.hijos[0])
        b = self._expresion(nodo.hijos[1])
        t = self._temp()
        self._emitir(f"{t} = {a} {op} {b}")
        return t


def generar_codigo_intermedio(arbol_anotado: NodoArb,
                              nombre_fuente: str = "") -> Tuple[str, List[ErrorGeneracion]]:
    """Genera el texto del archivo .ci a partir del árbol anotado."""
    if arbol_anotado is None:
        return "", [ErrorGeneracion(msg="No hay árbol para generar código intermedio")]
    return GeneradorCI(arbol_anotado, nombre_fuente).generar()
