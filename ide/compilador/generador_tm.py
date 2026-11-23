# compilador/generador_tm.py — Generación de código para la Tiny Machine (Fase final)
#
# Recorre el árbol anotado (NodoArb) producido por semantico.py y la tabla de
# símbolos, y produce instrucciones TM reales en el formato de tm_formato.py.
#
# Referencia: cgen.c / code.c del compilador TINY de Louden. Se tomó la
# estrategia (acumulador ac, segundo acumulador ac1, temporales respecto a mp,
# variables respecto a gp y reserva/ajuste de saltos), pero el recorrido se
# adaptó a la representación de este compilador: los nodos se reconocen por
# su etiqueta ("Asignar: x", "Op: +", "Mientras (while)", ...) y las
# sentencias son hijos de un bloque (no hay lista 'sibling').
#
# Correspondencia nodo → instrucciones TM:
#   Num / Bool              LDC ac,valor(0)
#   Id                      LD  ac,dir(gp)
#   Op binario              izq → ST ac,tmp(mp) ; der → LD ac1,tmp(mp) ; operación
#   + - * /                 ADD / SUB / MUL / DIV
#   %                       DIV, MUL, SUB          (a - (a/b)*b)
#   ^                       ciclo de MUL con contador (exponente entero)
#   < <= > >= == !=         SUB + JLT/JLE/JGT/JGE/JEQ/JNE → ac = 0/1
#   && ||                   MUL / ADD normalizado a 0/1
#   !                       ac = 1 - ac
#   conversión int→float    MUL por la constante 1.0
#   Decl con inicialización expr → ST ac,dir(gp)
#   Asignar                 expr → ST ac,dir(gp)
#   x++ / x--               LD, LDA ±1, ST
#   Leer (cin)              IN ac,0,tipo ; ST ac,dir(gp)
#   Escribir (cout)         OUT / OUTN / OUTS
#   Si (if)                 cond ; JEQ → else ; then ; LDA pc → fin ; else
#   Mientras (while)        cond ; JEQ → fin ; cuerpo ; LDA pc → inicio
#   Hacer (do-until)        cuerpo ; cond ; JEQ → inicio (repite mientras sea falsa)

from typing import Dict, List, Optional, Tuple

from ide.modelos.datos import NodoArb
from ide.compilador.errores import ErrorGeneracion
from ide.compilador.tm_formato import (
    InstruccionTM, formatear_instruccion, formatear_cadena,
    REG_AC as AC, REG_AC1 as AC1, REG_AUX1 as R2, REG_AUX2 as R3,
    REG_AUX3 as R4, REG_GP as GP, REG_MP as MP, REG_PC as PC,
    TAM_DMEM, TAM_IMEM, TIPO_IN, EXTENSIONES,
)


# ── Emisor: escritura de instrucciones y ajuste de saltos ─────────────────────

class EmisorTM:
    """
    Equivalente en Python a code.c: numera instrucciones, guarda comentarios y
    permite reservar posiciones para saltos cuyo destino aún no se conoce.

    En lugar de emitSkip/emitBackup/emitRestore se usa:
      reservar()           → devuelve la dirección reservada (hueco)
      completar(dir, ...)  → escribe el salto en ese hueco con destino absoluto
    """

    def __init__(self):
        self._instr: Dict[int, InstruccionTM] = {}
        self._coment: List[Tuple[int, str]] = []
        self._loc = 0
        self._huecos: Dict[int, str] = {}

    @property
    def loc(self) -> int:
        return self._loc

    def comentario(self, texto: str) -> None:
        self._coment.append((self._loc, texto))

    def _poner(self, direccion: int, op: str, r: int, a, b: int, c: str) -> None:
        self._instr[direccion] = InstruccionTM(direccion, op, r, a, b, c)

    def ro(self, op: str, r: int, s: int, t: int, c: str = "") -> int:
        d = self._loc
        self._poner(d, op, r, s, t, c)
        self._loc += 1
        return d

    def rm(self, op: str, r: int, d, s: int, c: str = "") -> int:
        dir_ = self._loc
        self._poner(dir_, op, r, d, s, c)
        self._loc += 1
        return dir_

    def rm_abs(self, op: str, r: int, destino: int, c: str = "") -> int:
        """Salto a una dirección absoluta, convertido a relativo al pc."""
        return self.rm(op, r, destino - (self._loc + 1), PC, c)

    def reservar(self, motivo: str) -> int:
        d = self._loc
        self._huecos[d] = motivo
        self.comentario(f"{motivo}: salto reservado en {d}")
        self._loc += 1
        return d

    def completar(self, hueco: int, op: str, r: int, destino: int, c: str = "") -> None:
        if hueco not in self._huecos:
            raise RuntimeError(f"La dirección {hueco} no estaba reservada")
        del self._huecos[hueco]
        self._poner(hueco, op, r, destino - (hueco + 1), PC, f"{c} -> {destino}")

    def huecos_pendientes(self) -> List[int]:
        return sorted(self._huecos)

    def instrucciones(self) -> List[InstruccionTM]:
        return [self._instr[k] for k in sorted(self._instr)]

    def texto(self, encabezado: List[str]) -> str:
        lineas = [f"* {l}" if l and not l.startswith("*") else (l or "*")
                  for l in encabezado]
        coment_por_dir: Dict[int, List[str]] = {}
        for d, txt in self._coment:
            coment_por_dir.setdefault(d, []).append(txt)
        for d in range(self._loc):
            for txt in coment_por_dir.get(d, []):
                lineas.append(f"* {txt}")
            if d in self._instr:
                lineas.append(formatear_instruccion(self._instr[d]))
        for txt in coment_por_dir.get(self._loc, []):
            lineas.append(f"* {txt}")
        return "\n".join(_recortar(l) for l in lineas) + "\n"


# tm.c lee cada línea con un búfer de 121 bytes; una línea más larga se
# partiría y el resto se interpretaría como otra instrucción. Se recortan los
# comentarios (nunca la instrucción ni las líneas *.STR, que tm.exe no usa).
_MAX_BYTES_LINEA = 118


def _recortar(linea: str) -> str:
    if linea.startswith("*.STR") or len(linea.encode("utf-8")) <= _MAX_BYTES_LINEA:
        return linea
    while len(linea.encode("utf-8")) > _MAX_BYTES_LINEA - 3:
        linea = linea[:-1]
    return linea.rstrip() + "..."


# ── Generador ─────────────────────────────────────────────────────────────────

_SALTOS_REL = {"<": "JLT", "<=": "JLE", ">": "JGT", ">=": "JGE", "==": "JEQ", "!=": "JNE"}


def _nombre(etiqueta: str) -> str:
    return etiqueta.split(":", 1)[1].strip() if ":" in etiqueta else ""


class GeneradorTM:
    """Traduce el árbol anotado a un programa TM."""

    def __init__(self, arbol: NodoArb, simbolos: list, nombre_fuente: str = ""):
        self._arbol = arbol
        self._simbolos = list(simbolos)
        self._fuente = nombre_fuente or "(editor)"
        self._e = EmisorTM()
        self._tmp = 0                      # desplazamiento de temporales (≤ 0)
        self._tmp_min = 0
        self._cadenas: List[str] = []
        self.errores: List[ErrorGeneracion] = []

        # Tabla de símbolos → memoria de la TM.
        # La tabla guarda desplazamientos en BYTES (int/float = 4, bool = 1);
        # la TM direcciona por palabra, así que cada variable recibe la
        # siguiente celda en el orden de la tabla: dMem[gp + i].
        self._dir: Dict[str, int] = {}
        self._tipo: Dict[str, str] = {}
        for i, s in enumerate(self._simbolos):
            self._dir[s.nombre] = i
            self._tipo[s.nombre] = s.tipo

    # ── API ───────────────────────────────────────────────────────────────────

    def generar(self) -> Tuple[str, List[ErrorGeneracion]]:
        e = self._e
        e.comentario("Preludio estándar:")
        e.rm("LD", MP, 0, AC, "cargar la dirección máxima desde dMem[0]")
        e.rm("ST", AC, 0, AC, "limpiar dMem[0]")
        e.comentario("Fin del preludio.")

        self._inicializar_float()
        self._sentencia(self._arbol)

        e.comentario("Fin de la ejecución.")
        e.ro("HALT", 0, 0, 0, "")

        if e.huecos_pendientes():
            self._error(f"Saltos sin completar en {e.huecos_pendientes()}")
        if e.loc > TAM_IMEM:
            self._error(f"El programa ocupa {e.loc} instrucciones (máximo {TAM_IMEM})")
        if len(self._dir) + (-self._tmp_min) + 1 >= TAM_DMEM:
            self._error("Las variables y temporales exceden la memoria de datos de la TM")

        return e.texto(self._encabezado()), self.errores

    def instrucciones(self) -> List[InstruccionTM]:
        return self._e.instrucciones()

    # ── Auxiliares ────────────────────────────────────────────────────────────

    def _error(self, msg: str, linea: int = 0) -> None:
        self.errores.append(ErrorGeneracion(msg=msg, linea=linea))

    def _encabezado(self) -> List[str]:
        enc = [
            "Compilación a código TM (Tiny Machine)",
            f"Archivo fuente: {self._fuente}",
            "Registros: ac=0  ac1=1  aux=2,3,4  gp=5 (variables)  mp=6 (temporales)  pc=7",
            "Mapa de memoria (tabla de símbolos -> dMem):",
        ]
        if not self._simbolos:
            enc.append("  (sin variables)")
        for s in self._simbolos:
            enc.append(
                f"  {s.nombre:<12} {s.tipo:<6} -> {self._dir[s.nombre]}({GP})"
                f"   [tabla: desplazamiento {s.desplazamiento} bytes]"
            )
        enc.append(f"Temporales: desde 0({MP}) hacia abajo (mp = tope de dMem)")
        usados = {i.op for i in self._e.instrucciones()} & set(EXTENSIONES)
        if usados or self._cadenas:
            enc.append("Extensiones de este simulador (no reconocidas por tm.exe):")
            for op in sorted(usados):
                enc.append(f"  {op}: {EXTENSIONES[op]}")
        if self._cadenas:
            enc.append("Tabla de cadenas para OUTS:")
            lineas = enc + [formatear_cadena(i, c) for i, c in enumerate(self._cadenas)]
            return lineas
        return enc

    def _cadena(self, texto: str) -> int:
        if texto in self._cadenas:
            return self._cadenas.index(texto)
        self._cadenas.append(texto)
        return len(self._cadenas) - 1

    def _push(self) -> int:
        off = self._tmp
        self._e.rm("ST", AC, off, MP, "op: guardar operando izquierdo")
        self._tmp -= 1
        self._tmp_min = min(self._tmp_min, self._tmp)
        return off

    def _pop(self) -> None:
        self._tmp += 1
        self._e.rm("LD", AC1, self._tmp, MP, "op: recuperar operando izquierdo")

    def _direccion(self, nombre: str, linea: int) -> Optional[int]:
        if nombre not in self._dir:
            self._error(f"La variable '{nombre}' no está en la tabla de símbolos", linea)
            return None
        return self._dir[nombre]

    def _inicializar_float(self) -> None:
        """Las variables float sin inicializador empiezan en 0.0 (no en el entero 0)."""
        reales = [s.nombre for s in self._simbolos if s.tipo == "float"]
        if not reales:
            return
        self._e.comentario("Inicialización de variables float en 0.0")
        self._e.rm("LDC", AC, 0.0, 0, "cargar 0.0")
        for n in reales:
            self._e.rm("ST", AC, self._dir[n], GP, f"{n} = 0.0")

    # ── Sentencias ───────────────────────────────────────────────────────────

    def _sentencia(self, nodo: Optional[NodoArb]) -> None:
        if nodo is None:
            return
        etq = nodo.etiqueta
        e = self._e

        if etq.startswith("Programa") or nodo.tipo_nodo == "bloque":
            for h in nodo.hijos:
                self._sentencia(h)
            return

        if etq.startswith("Decl:"):
            for var in nodo.hijos:
                nombre = _nombre(var.etiqueta)
                if var.hijos:
                    d = self._direccion(nombre, var.linea)
                    e.comentario(f"-> declaración con valor inicial: {nombre}  [L{var.linea}]")
                    self._expresion(var.hijos[0])
                    if d is not None:
                        e.rm("ST", AC, d, GP, f"init: {nombre} = ac")
                    e.comentario("<- declaración")
            return

        if etq.startswith("Asignar:"):
            nombre = _nombre(etq)
            d = self._direccion(nombre, nodo.linea)
            e.comentario(f"-> asignación: {nombre}  [L{nodo.linea}]")
            if not nodo.hijos:
                self._error(f"Asignación a '{nombre}' sin expresión", nodo.linea)
                return
            self._expresion(nodo.hijos[0])
            if d is not None:
                e.rm("ST", AC, d, GP, f"asignar: {nombre} = ac")
            e.comentario("<- asignación")
            return

        if etq.startswith("Incrementar:") or etq.startswith("Decrementar:"):
            inc = etq.startswith("Incrementar:")
            nombre = _nombre(etq).replace("++", "").replace("--", "").strip()
            d = self._direccion(nombre, nodo.linea)
            if d is None:
                return
            op = "++" if inc else "--"
            e.comentario(f"-> {nombre}{op}  [L{nodo.linea}]")
            e.rm("LD", AC, d, GP, f"cargar {nombre}")
            e.rm("LDA", AC, 1 if inc else -1, AC, f"ac = ac {'+' if inc else '-'} 1")
            e.rm("ST", AC, d, GP, f"guardar {nombre}")
            e.comentario(f"<- {nombre}{op}")
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
            d = self._direccion(nombre, nodo.linea)
            if d is None:
                return
            tipo = self._tipo.get(nombre, "int")
            e.comentario(f"-> cin >> {nombre}  [L{nodo.linea}]")
            e.ro("IN", AC, 0, TIPO_IN.get(tipo, 0), f"leer {nombre} ({tipo})")
            e.rm("ST", AC, d, GP, f"cin: guardar en {nombre}")
            e.comentario("<- cin")
            return

        if etq.startswith("Escribir (cout)"):
            self._escribir(nodo)
            return

        self._error(f"Sentencia no soportada por el generador TM: '{etq}'", nodo.linea)

    def _si(self, nodo: NodoArb) -> None:
        e = self._e
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'if' incompleta", nodo.linea)
            return
        cond, entonces = nodo.hijos[0], nodo.hijos[1]
        sino = nodo.hijos[2] if len(nodo.hijos) > 2 else None

        e.comentario(f"-> if  [L{nodo.linea}]")
        self._expresion(cond)
        salto_sino = e.reservar("if: salto a else/fin si la condición es falsa")
        self._sentencia(entonces)
        if sino is not None:
            salto_fin = e.reservar("if: salto al fin")
            e.completar(salto_sino, "JEQ", AC, e.loc, "if: falso, ir a else")
            e.comentario("if: else")
            self._sentencia(sino)
            e.completar(salto_fin, "LDA", PC, e.loc, "if: ir al fin")
        else:
            e.completar(salto_sino, "JEQ", AC, e.loc, "if: falso, ir al fin")
        e.comentario("<- if")

    def _mientras(self, nodo: NodoArb) -> None:
        e = self._e
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'while' incompleta", nodo.linea)
            return
        e.comentario(f"-> while  [L{nodo.linea}]")
        inicio = e.loc
        e.comentario(f"while: evaluación de la condición (inicio = {inicio})")
        self._expresion(nodo.hijos[0])
        salto_fin = e.reservar("while: salir si la condición es falsa")
        self._sentencia(nodo.hijos[1])
        e.rm_abs("LDA", PC, inicio, f"while: regresar a la condición -> {inicio}")
        e.completar(salto_fin, "JEQ", AC, e.loc, "while: falso, salir")
        e.comentario("<- while")

    def _hacer(self, nodo: NodoArb) -> None:
        e = self._e
        if len(nodo.hijos) < 2:
            self._error("Sentencia 'do-until' incompleta", nodo.linea)
            return
        e.comentario(f"-> do-until  [L{nodo.linea}]")
        inicio = e.loc
        e.comentario(f"do: inicio del cuerpo ({inicio})")
        self._sentencia(nodo.hijos[0])
        e.comentario("until: condición")
        self._expresion(nodo.hijos[1])
        e.rm_abs("JEQ", AC, inicio, f"until: falsa, repetir cuerpo -> {inicio}")
        e.comentario("<- do-until")

    def _escribir(self, nodo: NodoArb) -> None:
        e = self._e
        e.comentario(f"-> cout  [L{nodo.linea}]")
        if not nodo.hijos:
            self._error("Sentencia 'cout' sin valor", nodo.linea)
            return
        sal = nodo.hijos[0]

        if sal.etiqueta.startswith("Cadena:"):
            k = self._cadena(self._texto_cadena(sal) + "\n")
            e.rm("OUTS", AC, k, 0, f"imprimir cadena {k}")
        elif sal.etiqueta.startswith("Salida combinada"):
            if len(sal.hijos) < 2:
                self._error("Salida combinada incompleta", nodo.linea)
                return
            a, b = sal.hijos[0], sal.hijos[1]
            if a.etiqueta.startswith("Cadena:"):
                k = self._cadena(self._texto_cadena(a))
                e.rm("OUTS", AC, k, 0, f"imprimir cadena {k}")
                self._expresion(b)
                e.ro("OUT", AC, 0, 0, "imprimir ac y terminar línea")
            else:
                self._expresion(a)
                e.ro("OUTN", AC, 0, 0, "imprimir ac (sin salto de línea)")
                k = self._cadena(self._texto_cadena(b) + "\n")
                e.rm("OUTS", AC, k, 0, f"imprimir cadena {k}")
        else:
            self._expresion(sal)
            e.ro("OUT", AC, 0, 0, "imprimir ac")
        e.comentario("<- cout")

    @staticmethod
    def _texto_cadena(nodo: NodoArb) -> str:
        txt = nodo.etiqueta.split(":", 1)[1].strip()
        if len(txt) >= 2 and txt[0] == '"' and txt[-1] == '"':
            txt = txt[1:-1]
        return txt

    # ── Expresiones ──────────────────────────────────────────────────────────

    def _expresion(self, nodo: Optional[NodoArb]) -> None:
        if nodo is None:
            self._error("Expresión vacía")
            return
        self._expresion_sin_conv(nodo)
        if nodo.conversion == "int -> float":
            self._e.rm("LDC", R2, 1.0, 0, "conversión int -> float: cargar 1.0")
            self._e.ro("MUL", AC, AC, R2, "ac = ac * 1.0")

    def _expresion_sin_conv(self, nodo: NodoArb) -> None:
        e = self._e
        etq = nodo.etiqueta

        if etq.startswith("Num:"):
            txt = _nombre(etq)
            try:
                val = float(txt) if "." in txt else int(txt)
            except ValueError:
                self._error(f"Constante numérica inválida '{txt}'", nodo.linea)
                return
            e.rm("LDC", AC, val, 0, f"cargar constante {txt}")
            return

        if etq.startswith("Bool:"):
            val = 1 if _nombre(etq).lower() == "true" else 0
            e.rm("LDC", AC, val, 0, f"cargar {_nombre(etq)} ({val})")
            return

        if etq.startswith("Id:"):
            nombre = _nombre(etq)
            d = self._direccion(nombre, nodo.linea)
            if d is not None:
                e.rm("LD", AC, d, GP, f"cargar {nombre}")
            return

        if etq.startswith("Cadena:"):
            self._error("Una cadena sólo puede usarse directamente en 'cout'", nodo.linea)
            return

        if not etq.startswith("Op:"):
            self._error(f"Expresión no soportada por el generador TM: '{etq}'", nodo.linea)
            return

        op = _nombre(etq)

        if op == "!":
            if not nodo.hijos:
                self._error("Operador '!' sin operando", nodo.linea)
                return
            self._expresion(nodo.hijos[0])
            e.rm("LDC", AC1, 1, 0, "!: cargar 1")
            e.ro("SUB", AC, AC1, AC, "!: ac = 1 - ac")
            return

        if len(nodo.hijos) < 2:
            self._error(f"Operador '{op}' con operandos incompletos", nodo.linea)
            return

        if op not in ("+", "-", "*", "/", "%", "^", "&&", "||") and op not in _SALTOS_REL:
            self._error(f"Operador '{op}' no soportado en expresiones", nodo.linea)
            return
        if op == "^" and nodo.hijos[1].tipo_dato == "float":
            self._error("El exponente de '^' debe ser entero para generar código TM", nodo.linea)
            return

        izq, der = nodo.hijos
        e.comentario(f"-> op {op}")
        self._expresion(izq)
        self._push()
        self._expresion(der)
        self._pop()

        if op == "+":
            e.ro("ADD", AC, AC1, AC, "op +")
        elif op == "-":
            e.ro("SUB", AC, AC1, AC, "op -")
        elif op == "*":
            e.ro("MUL", AC, AC1, AC, "op *")
        elif op == "/":
            e.ro("DIV", AC, AC1, AC, "op /")
        elif op == "%":
            e.ro("DIV", R2, AC1, AC, "op %: r2 = a / b")
            e.ro("MUL", R2, R2, AC, "op %: r2 = (a / b) * b")
            e.ro("SUB", AC, AC1, R2, "op %: ac = a - r2")
        elif op in _SALTOS_REL:
            e.ro("SUB", AC, AC1, AC, f"op {op}: ac = izq - der")
            e.rm(_SALTOS_REL[op], AC, 2, PC, "saltar si es verdadero")
            e.rm("LDC", AC, 0, 0, "caso falso")
            e.rm("LDA", PC, 1, PC, "salto incondicional")
            e.rm("LDC", AC, 1, 0, "caso verdadero")
        elif op == "&&":
            e.ro("MUL", AC, AC1, AC, "op &&: ac = izq * der (0/1)")
        elif op == "||":
            e.ro("ADD", AC, AC1, AC, "op ||: ac = izq + der")
            e.rm("JEQ", AC, 1, PC, "si es 0 queda falso")
            e.rm("LDC", AC, 1, 0, "normalizar a 1")
        elif op == "^":
            self._potencia(nodo)
        e.comentario(f"<- op {op}")

    def _potencia(self, nodo: NodoArb) -> None:
        """ac1 = base, ac = exponente (entero). Resultado en ac."""
        e = self._e
        uno = 1.0 if nodo.tipo_dato == "float" else 1
        e.rm("LDA", R3, 0, AC, "^: r3 = exponente (contador)")
        e.rm("LDC", R2, uno, 0, "^: r2 = 1 (resultado)")
        no_neg = e.reservar("^: saltar si el exponente >= 0")
        e.rm("LDC", R4, 0, 0, "^: r4 = 0")
        e.ro("SUB", R3, R4, R3, "^: r3 = -r3")
        e.completar(no_neg, "JGE", R3, e.loc, "^: exponente no negativo")
        ciclo = e.loc
        fin = e.reservar("^: salir del ciclo cuando r3 <= 0")
        e.ro("MUL", R2, R2, AC1, "^: r2 = r2 * base")
        e.rm("LDA", R3, -1, R3, "^: r3 = r3 - 1")
        e.rm_abs("LDA", PC, ciclo, f"^: repetir ciclo -> {ciclo}")
        e.completar(fin, "JLE", R3, e.loc, "^: fin del ciclo")
        positivo = e.reservar("^: saltar inversión si el exponente >= 0")
        e.rm("LDC", R4, uno, 0, "^: r4 = 1")
        e.ro("DIV", R2, R4, R2, "^: r2 = 1 / r2 (exponente negativo)")
        e.completar(positivo, "JGE", AC, e.loc, "^: exponente no negativo")
        e.rm("LDA", AC, 0, R2, "^: ac = r2")


# ── Función de interfaz pública ───────────────────────────────────────────────

def generar_codigo_tm(arbol_anotado: NodoArb, simbolos: list,
                      nombre_fuente: str = "") -> Tuple[str, List[ErrorGeneracion]]:
    """
    Genera el texto del archivo .tm a partir del árbol anotado y la lista de
    símbolos (TablaSimbolos.obtener_simbolos()).
    Devuelve (texto_tm, errores_de_generacion). Si hay errores, el texto no
    debe considerarse válido.
    """
    if arbol_anotado is None:
        return "", [ErrorGeneracion(msg="No hay árbol para generar código")]
    gen = GeneradorTM(arbol_anotado, simbolos, nombre_fuente)
    return gen.generar()
