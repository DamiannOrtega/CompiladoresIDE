# modelos/datos.py — Estructuras de datos del compilador

from dataclasses import dataclass, field
from typing import List


@dataclass
class Tok:
    """Token léxico."""
    lexema: str
    tipo: str
    linea: int
    col: int


@dataclass
class Err:
    """Error de compilación."""
    tipo: str
    linea: int
    col: int
    msg: str


@dataclass
class Sim:
    """Entrada de la tabla de símbolos."""
    nombre: str
    tipo: str
    ambito: str
    linea: int


@dataclass
class NodoArb:
    """Nodo del árbol sintáctico abstracto (AST)."""
    etiqueta: str
    hijos: List["NodoArb"] = field(default_factory=list)
    linea: int = 0          # línea en el fuente donde se origina
    tipo_nodo: str = ""     # "prog" | "decl" | "stmt" | "bloque" | "expr"


@dataclass
class ResultadoCompilacion:
    """Resultado completo de una fase de compilación."""
    fase: str
    tok: List[Tok] = field(default_factory=list)
    err: List[Err] = field(default_factory=list)
    sim: List[Sim] = field(default_factory=list)
    arb: NodoArb = None
    ir: str = ""
    sal: str = ""
