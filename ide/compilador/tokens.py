# compilador/tokens.py — Definiciones de tipos de token (en español)

from dataclasses import dataclass


# ── Tipos de token ────────────────────────────────────────────────────────────

NUMERO_ENTERO    = "NUMERO_ENTERO"
NUMERO_REAL      = "NUMERO_REAL"
IDENTIFICADOR    = "IDENTIFICADOR"
PALABRA_RESERVADA = "PALABRA_RESERVADA"
OPERADOR_ARITMETICO = "OPERADOR_ARITMETICO"
OPERADOR_RELACIONAL = "OPERADOR_RELACIONAL"
OPERADOR_LOGICO  = "OPERADOR_LOGICO"
SIMBOLO          = "SIMBOLO"
ASIGNACION       = "ASIGNACION"
COMENTARIO       = "COMENTARIO"
CADENA           = "CADENA"
OPERADOR_IO      = "OPERADOR_IO"


# ── Palabras reservadas del lenguaje ─────────────────────────────────────────

PALABRAS_RESERVADAS = {
    "if", "then", "else", "end", "do", "while",
    "switch", "case", "int", "float", "bool", "true", "false",
    "main", "cin", "cout",
}


# ── Operadores de dos caracteres ─────────────────────────────────────────────

OPERADORES_ARITMETICOS_DOBLES = {"++", "--"}

OPERADORES_RELACIONALES = {"<=", ">=", "!=", "=="}

OPERADORES_LOGICOS_DOBLES = {"&&", "||"}

OPERADORES_IO = {"<<", ">>"}


# ── Operadores y símbolos de un carácter ─────────────────────────────────────

OPERADORES_ARITMETICOS_SIMPLES = {"+", "-", "*", "/", "%", "^"}

OPERADORES_LOGICOS_SIMPLES = {"!"}

SIMBOLOS = {"(", ")", "{", "}", ",", ";"}


# ── Estructura de un token ────────────────────────────────────────────────────

@dataclass
class Token:
    """Representa un token léxico con posición en el fuente."""
    tipo: str      # tipo en español, p. ej. IDENTIFICADOR
    valor: str     # lexema original
    linea: int     # línea (inicia en 1)
    columna: int   # columna (inicia en 1)

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea,
            "columna": self.columna,
        }
