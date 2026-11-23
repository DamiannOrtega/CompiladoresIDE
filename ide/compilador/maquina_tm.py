# compilador/maquina_tm.py — Simulador de la Tiny Machine (TM) en Python
#
# Equivalente al simulador tm.c de TINY (Louden), adaptado a este proyecto.
# Carga un archivo .tm (formato de tm_formato.py), y ejecuta realmente sus
# instrucciones sobre 8 registros, memoria de instrucciones y memoria de
# datos. No interpreta el programa fuente ni código intermedio.
#
# Comportamiento tomado de tm.c:
#   - Al cargar: todos los registros en 0, dMem[0] = tamaño - 1, el resto en 0,
#     y las direcciones de instrucciones no definidas contienen HALT.
#   - Cada paso: pc = reg[7]; reg[7] = pc + 1; se ejecuta iMem[pc].
#   - RM: m = d + reg[s] (LD/ST validan que m esté dentro de dMem).
#   - LDA r = m; LDC r = d; Jxx compara reg[r] con 0 y hace pc = m.
#   - DIV entre cero termina con error.
#
# Extensiones (documentadas en tm_formato.py): valores reales, OUTS, OUTN y
# el tipo esperado en el campo t de IN.
#
# Uso por consola:
#   python -m ide.compilador.maquina_tm programa.tm [--traza]

import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from ide.compilador.tm_formato import (
    InstruccionTM, parsear_programa, ErrorFormatoTM, formatear_valor,
    formatear_instruccion, NUM_REGS, REG_PC, TAM_IMEM, TAM_DMEM,
    IN_INT, IN_FLOAT, IN_BOOL, NOMBRE_TIPO_IN,
)

PASOS_MAXIMOS = 30_000_000   # protege contra ciclos infinitos (~25 s de ejecución)


@dataclass
class SolicitudEntrada:
    """Datos que el simulador entrega cuando una instrucción IN pide un valor."""
    direccion: int
    tipo: str              # "int" | "float" | "bool"
    comentario: str        # comentario de la instrucción (p. ej. "leer x (int)")
    error_previo: str = "" # mensaje si el valor anterior fue inválido


@dataclass
class ResultadoEjecucion:
    estado: str                          # "HALT" | "ERROR" | "CANCELADO" | "LIMITE"
    mensaje: str = ""
    salida: List[str] = field(default_factory=list)   # líneas impresas
    entradas: List[str] = field(default_factory=list) # valores leídos por IN
    pasos: int = 0
    pc: int = 0
    registros: List = field(default_factory=list)
    instruccion: Optional[InstruccionTM] = None       # instrucción del error

    @property
    def correcto(self) -> bool:
        return self.estado == "HALT"


class ErrorEjecucionTM(Exception):
    pass


class _Cancelado(Exception):
    pass


def _leer_valor(texto: str, tipo: int):
    t = texto.strip()
    if tipo == IN_BOOL:
        if t.lower() in ("true", "1"):
            return 1
        if t.lower() in ("false", "0"):
            return 0
        raise ValueError("se esperaba true/false o 1/0")
    if tipo == IN_FLOAT:
        return float(t)
    return int(t)


class MaquinaTM:
    def __init__(self, tam_imem: int = TAM_IMEM, tam_dmem: int = TAM_DMEM):
        self.tam_imem = tam_imem
        self.tam_dmem = tam_dmem
        self.imem: Dict[int, InstruccionTM] = {}
        self.cadenas: Dict[int, str] = {}
        self.reg: List = [0] * NUM_REGS
        self.dmem: List = [0] * tam_dmem

    # ── Carga ─────────────────────────────────────────────────────────────────

    def cargar(self, texto: str) -> None:
        """Lee las instrucciones; lanza ErrorFormatoTM si el archivo es inválido."""
        self.imem, self.cadenas = parsear_programa(texto, self.tam_imem)
        for ins in self.imem.values():
            if ins.op == "OUTS" and ins.a not in self.cadenas:
                raise ErrorFormatoTM(ins.linea_archivo,
                                     f"OUTS usa la cadena {ins.a}, que no está en la tabla *.STR")
        self.reiniciar()

    def cargar_archivo(self, ruta: str) -> None:
        with open(ruta, "r", encoding="utf-8") as f:
            self.cargar(f.read())

    def reiniciar(self) -> None:
        self.reg = [0] * NUM_REGS
        self.dmem = [0] * self.tam_dmem
        self.dmem[0] = self.tam_dmem - 1

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar(
        self,
        leer_entrada: Callable[[SolicitudEntrada], Optional[str]],
        escribir_salida: Optional[Callable[[str], None]] = None,
        max_pasos: int = PASOS_MAXIMOS,
        traza: Optional[Callable[[str], None]] = None,
    ) -> ResultadoEjecucion:
        """
        Ejecuta desde la dirección 0 hasta HALT, un error o max_pasos.
        leer_entrada recibe una SolicitudEntrada y devuelve el texto escrito por
        el usuario, o None para cancelar la ejecución.
        """
        self.reiniciar()
        res = ResultadoEjecucion(estado="HALT")
        linea = []   # línea de salida en construcción

        def emitir(texto: str, terminar: bool):
            linea.append(texto)
            if terminar:
                completa = "".join(linea)
                linea.clear()
                res.salida.append(completa)
                if escribir_salida:
                    escribir_salida(completa)

        def emitir_texto(texto: str):
            partes = texto.split("\n")
            for i, p in enumerate(partes):
                if i < len(partes) - 1:
                    emitir(p, True)
                elif p:
                    emitir(p, False)

        # Las instrucciones más frecuentes (cargas, aritmética y saltos) se
        # ejecutan directamente en este ciclo; IN, OUT*, DIV y HALT pasan por
        # _paso(). La semántica es la misma en ambos caminos.
        reg, dmem = self.reg, self.dmem
        tam_i, tam_d = self.tam_imem, self.tam_dmem
        prog = [None] * tam_i
        for d, i in self.imem.items():
            prog[d] = (i.op, i.r, i.a, i.b, i)
        pasos = 0
        ins = None

        def fallo_datos(m, ins):
            raise ErrorEjecucionTM(
                f"Fallo de memoria de datos: dirección {m} en la instrucción "
                f"{ins.direccion} ({ins.op})")

        try:
            while True:
                if pasos >= max_pasos:
                    res.estado = "LIMITE"
                    res.mensaje = (f"Se alcanzó el límite de {max_pasos} instrucciones "
                                   "ejecutadas (¿ciclo infinito?)")
                    break
                pc = reg[REG_PC]
                if pc < 0 or pc >= tam_i:
                    raise ErrorEjecucionTM(f"Fallo de memoria de instrucciones: pc = {pc}")
                t = prog[pc]
                pasos += 1
                reg[REG_PC] = pc + 1
                if t is None:                       # posición vacía = HALT (como tm.c)
                    ins = InstruccionTM(pc, "HALT", 0, 0, 0)
                    if traza:
                        traza(formatear_instruccion(ins))
                    break
                op, r, a, b, ins = t
                if traza:
                    traza(formatear_instruccion(ins))

                if op == "LD":
                    m = a + reg[b]
                    if m.__class__ is not int or m < 0 or m >= tam_d:
                        fallo_datos(m, ins)
                    reg[r] = dmem[m]
                elif op == "ST":
                    m = a + reg[b]
                    if m.__class__ is not int or m < 0 or m >= tam_d:
                        fallo_datos(m, ins)
                    dmem[m] = reg[r]
                elif op == "LDC":
                    reg[r] = a
                elif op == "LDA":
                    reg[r] = a + reg[b]
                elif op == "SUB":
                    reg[r] = reg[a] - reg[b]
                elif op == "ADD":
                    reg[r] = reg[a] + reg[b]
                elif op == "MUL":
                    reg[r] = reg[a] * reg[b]
                elif op[0] == "J":
                    v = reg[r]
                    if ((op == "JEQ" and v == 0) or (op == "JNE" and v != 0)
                            or (op == "JLT" and v < 0) or (op == "JLE" and v <= 0)
                            or (op == "JGT" and v > 0) or (op == "JGE" and v >= 0)):
                        reg[REG_PC] = a + reg[b]
                else:
                    if self._paso(ins, emitir, emitir_texto, leer_entrada, res):
                        break
                if reg[REG_PC].__class__ is not int:
                    raise ErrorEjecucionTM(
                        f"El pc recibió un valor real en la instrucción {ins.direccion}")
        except ErrorEjecucionTM as ex:
            res.estado = "ERROR"
            res.mensaje = str(ex)
        except _Cancelado:
            res.estado = "CANCELADO"
            res.mensaje = "Ejecución cancelada por el usuario durante una instrucción IN"

        res.pasos = pasos
        res.instruccion = ins
        if linea:
            emitir("", True)
        res.pc = self.reg[REG_PC]
        res.registros = list(self.reg)
        if res.estado == "HALT":
            res.mensaje = f"Programa terminado ({res.pasos} instrucciones ejecutadas)"
        return res

    def _dir_datos(self, m: int, ins: InstruccionTM) -> int:
        if not isinstance(m, int) or m < 0 or m >= self.tam_dmem:
            raise ErrorEjecucionTM(
                f"Fallo de memoria de datos: dirección {m} en la instrucción {ins.direccion} ({ins.op})")
        return m

    def _paso(self, ins: InstruccionTM, emitir, emitir_texto, leer_entrada,
              res: ResultadoEjecucion) -> bool:
        """Ejecuta una instrucción. Devuelve True si debe detenerse (HALT)."""
        reg = self.reg
        op, r = ins.op, ins.r

        # ── Registro-registro ──
        if op == "HALT":
            return True
        if op == "IN":
            tipo = ins.t if ins.t in NOMBRE_TIPO_IN else IN_INT
            error = ""
            while True:
                texto = leer_entrada(SolicitudEntrada(
                    ins.direccion, NOMBRE_TIPO_IN[tipo], ins.comentario, error))
                if texto is None:
                    raise _Cancelado()
                try:
                    reg[r] = _leer_valor(texto, tipo)
                    res.entradas.append(texto.strip())
                    return False
                except ValueError:
                    error = f"Valor inválido '{texto.strip()}' para tipo {NOMBRE_TIPO_IN[tipo]}"
        if op == "OUT":
            emitir(formatear_valor(reg[r]), True)
            return False
        if op == "OUTN":
            emitir(formatear_valor(reg[r]), False)
            return False
        if op in ("ADD", "SUB", "MUL", "DIV"):
            a, b = reg[ins.s], reg[ins.t]
            if op == "ADD":
                reg[r] = a + b
            elif op == "SUB":
                reg[r] = a - b
            elif op == "MUL":
                reg[r] = a * b
            else:
                if b == 0:
                    raise ErrorEjecucionTM(
                        f"División entre cero en la instrucción {ins.direccion}")
                if isinstance(a, int) and isinstance(b, int):
                    q = abs(a) // abs(b)          # truncar hacia cero, como C
                    reg[r] = q if (a >= 0) == (b >= 0) else -q
                else:
                    reg[r] = a / b
            return False

        # ── Registro-memoria ──
        m = ins.a + reg[ins.b] if op != "LDC" else ins.a
        if op == "LD":
            reg[r] = self.dmem[self._dir_datos(m, ins)]
        elif op == "ST":
            self.dmem[self._dir_datos(m, ins)] = reg[r]
        elif op == "OUTS":
            emitir_texto(self.cadenas[ins.a])
        elif op == "LDA":
            reg[r] = m
        elif op == "LDC":
            reg[r] = ins.a
        elif op == "JLT":
            if reg[r] < 0: reg[REG_PC] = m
        elif op == "JLE":
            if reg[r] <= 0: reg[REG_PC] = m
        elif op == "JGT":
            if reg[r] > 0: reg[REG_PC] = m
        elif op == "JGE":
            if reg[r] >= 0: reg[REG_PC] = m
        elif op == "JEQ":
            if reg[r] == 0: reg[REG_PC] = m
        elif op == "JNE":
            if reg[r] != 0: reg[REG_PC] = m
        else:
            raise ErrorEjecucionTM(f"Instrucción desconocida '{op}' en {ins.direccion}")
        if isinstance(reg[REG_PC], float):
            raise ErrorEjecucionTM(f"El pc recibió un valor real en la instrucción {ins.direccion}")
        return False


def ejecutar_archivo(ruta: str, leer_entrada, escribir_salida=None,
                     max_pasos: int = PASOS_MAXIMOS, traza=None) -> ResultadoEjecucion:
    """Carga el archivo .tm indicado y lo ejecuta."""
    maq = MaquinaTM()
    maq.cargar_archivo(ruta)
    return maq.ejecutar(leer_entrada, escribir_salida, max_pasos, traza)


# ── Ejecución por consola ─────────────────────────────────────────────────────

def _entrada_consola(sol: SolicitudEntrada) -> Optional[str]:
    if sol.error_previo:
        print(f"  {sol.error_previo}")
    try:
        return input(f"IN [{sol.direccion}] {sol.comentario} > ")
    except EOFError:
        return None


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    traza = "--traza" in args
    args = [a for a in args if not a.startswith("--")]
    if not args:
        print("Uso: python -m ide.compilador.maquina_tm <programa.tm> [--traza]")
        return 1
    try:
        res = ejecutar_archivo(args[0], _entrada_consola, print,
                               traza=(lambda t: print(f"  > {t}")) if traza else None)
    except (OSError, ErrorFormatoTM) as ex:
        print(f"Error al cargar: {ex}")
        return 1
    print(f"[{res.estado}] {res.mensaje}")
    return 0 if res.correcto else 2


if __name__ == "__main__":
    sys.exit(main())
