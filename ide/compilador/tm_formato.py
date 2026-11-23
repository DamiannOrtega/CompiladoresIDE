# compilador/tm_formato.py — Formato de instrucciones de la Tiny Machine (TM)
#
# Módulo compartido por el generador de código (generador_tm.py) y el
# simulador (maquina_tm.py). Ambos usan exactamente estas definiciones para
# escribir y leer el archivo .tm, de modo que el código que se muestra en la
# interfaz es el mismo que se ejecuta.
#
# Formato de línea (idéntico al que produce code.c de TINY y lee tm.c):
#   Registro-registro (RO):  "  12:    ADD  0,1,0 \tcomentario"
#   Registro-memoria (RM/RA): "  13:     LD  0,2(5) \tcomentario"
#   Comentarios:             "* texto"
#
# Extensiones respecto a la TM original (tm.c de Louden) — documentadas:
#   1. Valores reales: LDC acepta una constante real ("LDC 0,2.5(0)") y los
#      registros/memoria pueden contener reales. La TM original sólo maneja
#      enteros. Los programas que sólo usan enteros conservan el
#      comportamiento original (DIV entera truncada hacia cero).
#   2. OUTS r,k(s): imprime la cadena número k de la tabla de cadenas
#      (líneas "*.STR k "texto"" del propio archivo .tm). No es reconocida
#      por tm.exe.
#   3. OUTN r,s,t: imprime reg[r] SIN terminar la línea (OUT sí la termina).
#      No es reconocida por tm.exe.
#   4. IN r,s,t: el campo t indica el tipo esperado (0=int, 1=float, 2=bool).
#      tm.exe ignora s y t en IN, por lo que el formato sigue siendo válido.
#   5. La tabla de cadenas se guarda en líneas de comentario "*.STR", que
#      tm.exe ignora como cualquier otro comentario.

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

Numero = Union[int, float]

# ── Registros (misma convención que code.h de TINY) ──────────────────────────
NUM_REGS = 8
REG_AC   = 0   # acumulador
REG_AC1  = 1   # segundo acumulador
REG_AUX1 = 2   # auxiliar (potencia, módulo, conversiones)
REG_AUX2 = 3   # auxiliar (contador de la potencia)
REG_AUX3 = 4   # auxiliar (constantes de la potencia)
REG_GP   = 5   # base de variables globales
REG_MP   = 6   # base de temporales (tope de la memoria de datos)
REG_PC   = 7   # contador de programa

# ── Tamaños de memoria ────────────────────────────────────────────────────────
# tm.c usa 1024 para ambas memorias; aquí se amplían para programas más
# grandes. Un programa de menos de 1024 instrucciones cabe en ambos.
TAM_IMEM = 4096
TAM_DMEM = 4096

# ── Conjunto de instrucciones ────────────────────────────────────────────────
OPCODES_RO = ("HALT", "IN", "OUT", "OUTN", "ADD", "SUB", "MUL", "DIV")
OPCODES_RM = ("LD", "ST", "OUTS")
OPCODES_RA = ("LDA", "LDC", "JLT", "JLE", "JGT", "JGE", "JEQ", "JNE")
OPCODES = OPCODES_RO + OPCODES_RM + OPCODES_RA

EXTENSIONES = {
    "OUTS": "Imprime la cadena k de la tabla *.STR (no existe en tm.exe)",
    "OUTN": "Imprime reg[r] sin salto de línea (no existe en tm.exe)",
}

# Tipo esperado por IN (campo t)
IN_INT, IN_FLOAT, IN_BOOL = 0, 1, 2
TIPO_IN = {"int": IN_INT, "float": IN_FLOAT, "bool": IN_BOOL}
NOMBRE_TIPO_IN = {IN_INT: "int", IN_FLOAT: "float", IN_BOOL: "bool"}

PREFIJO_CADENA = "*.STR"


def es_ro(op: str) -> bool:
    return op in OPCODES_RO


@dataclass
class InstruccionTM:
    """
    Una instrucción TM.
      RO: op r,s,t      → a = s, b = t
      RM: op r,d(s)     → a = d, b = s
    """
    direccion: int
    op: str
    r: int
    a: Numero
    b: int
    comentario: str = ""
    linea_archivo: int = 0   # línea del .tm donde se leyó (para errores)

    @property
    def d(self) -> Numero:
        return self.a

    @property
    def s(self) -> int:
        return self.a if es_ro(self.op) else self.b

    @property
    def t(self) -> int:
        return self.b

    def operandos(self) -> str:
        if es_ro(self.op):
            return f"{self.r},{self.a},{self.b}"
        return f"{self.r},{formatear_numero(self.a)}({self.b})"


# ── Escritura ─────────────────────────────────────────────────────────────────

def formatear_numero(v: Numero) -> str:
    """Escribe una constante para el .tm (enteros sin punto, reales con repr)."""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return repr(v)
    return str(v)


def formatear_instruccion(ins: InstruccionTM) -> str:
    texto = f"{ins.direccion:3d}:  {ins.op:>5s}  {ins.operandos()} "
    if ins.comentario:
        texto += f"\t{ins.comentario}"
    return texto


def formatear_cadena(indice: int, texto: str) -> str:
    return f"{PREFIJO_CADENA} {indice} {json.dumps(texto, ensure_ascii=False)}"


def formatear_valor(v: Numero) -> str:
    """Formato de un valor para la salida del programa (OUT/OUTN)."""
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return str(v)
        s = format(v, ".10g")
        if "." not in s and "e" not in s:
            s += ".0"
        return s
    return str(v)


# ── Lectura ───────────────────────────────────────────────────────────────────

class ErrorFormatoTM(Exception):
    """Error al leer un archivo .tm."""

    def __init__(self, linea: int, msg: str):
        super().__init__(f"Línea {linea} del archivo .tm: {msg}")
        self.linea = linea
        self.msg = msg


_RE_INSTR = re.compile(r"^\s*(\d+)\s*:\s*([A-Za-z]+)\s*(.*)$")
_NUM = r"[-+]?(?:\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)"
_RE_RO = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(.*)$")
_RE_RM = re.compile(r"^\s*(\d+)\s*,\s*(" + _NUM + r")\s*\(\s*(\d+)\s*\)(.*)$")
_RE_STR = re.compile(r"^\*\.STR\s+(\d+)\s+(.*)$")


def _a_numero(txt: str) -> Numero:
    try:
        return int(txt)
    except ValueError:
        return float(txt)


def parsear_programa(texto: str, tam_imem: int = TAM_IMEM
                     ) -> Tuple[Dict[int, InstruccionTM], Dict[int, str]]:
    """
    Lee el texto de un archivo .tm.
    Devuelve (instrucciones por dirección, tabla de cadenas).
    Lanza ErrorFormatoTM ante cualquier línea inválida.
    """
    instrucciones: Dict[int, InstruccionTM] = {}
    cadenas: Dict[int, str] = {}

    for n, linea in enumerate(texto.splitlines(), 1):
        limpia = linea.strip()
        if not limpia:
            continue
        if limpia.startswith("*"):
            m = _RE_STR.match(limpia)
            if m:
                try:
                    cadenas[int(m.group(1))] = json.loads(m.group(2))
                except json.JSONDecodeError:
                    raise ErrorFormatoTM(n, "cadena *.STR mal formada")
            continue

        m = _RE_INSTR.match(linea)
        if not m:
            raise ErrorFormatoTM(n, f"instrucción no reconocida: '{limpia}'")
        direccion = int(m.group(1))
        op = m.group(2).upper()
        resto = m.group(3)

        if direccion < 0 or direccion >= tam_imem:
            raise ErrorFormatoTM(n, f"dirección {direccion} fuera de la memoria de instrucciones")
        if op not in OPCODES:
            raise ErrorFormatoTM(n, f"código de operación desconocido '{op}'")
        if direccion in instrucciones:
            raise ErrorFormatoTM(n, f"dirección {direccion} definida dos veces")

        if es_ro(op):
            mo = _RE_RO.match(resto)
            if not mo:
                raise ErrorFormatoTM(n, f"operandos inválidos para {op} (se esperaba r,s,t)")
            r, a, b = int(mo.group(1)), int(mo.group(2)), int(mo.group(3))
            coment = mo.group(4)
        else:
            mo = _RE_RM.match(resto)
            if not mo:
                raise ErrorFormatoTM(n, f"operandos inválidos para {op} (se esperaba r,d(s))")
            r, a, b = int(mo.group(1)), _a_numero(mo.group(2)), int(mo.group(3))
            coment = mo.group(4)
            if isinstance(a, float) and op != "LDC":
                raise ErrorFormatoTM(n, f"{op} requiere un desplazamiento entero")

        for reg in ((r, a, b) if es_ro(op) else (r, b)):
            if not (0 <= reg < NUM_REGS):
                raise ErrorFormatoTM(n, f"registro {reg} inválido (0..{NUM_REGS - 1})")

        instrucciones[direccion] = InstruccionTM(
            direccion=direccion, op=op, r=r, a=a, b=b,
            comentario=coment.strip(), linea_archivo=n,
        )

    return instrucciones, cadenas


def lista_ordenada(instrucciones: Dict[int, InstruccionTM]) -> List[InstruccionTM]:
    return [instrucciones[k] for k in sorted(instrucciones)]
