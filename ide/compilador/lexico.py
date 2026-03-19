# compilador/lexico.py — Motor del analizador léxico
#
# Uso:
#   from ide.compilador.lexico import analyze
#   tokens, errores = analyze(codigo_fuente)

from typing import List, Tuple

from ide.compilador.tokens import (
    Token,
    NUMERO_ENTERO, NUMERO_REAL,
    IDENTIFICADOR, PALABRA_RESERVADA,
    OPERADOR_ARITMETICO, OPERADOR_RELACIONAL, OPERADOR_LOGICO,
    SIMBOLO, ASIGNACION, COMENTARIO,
    PALABRAS_RESERVADAS,
    OPERADORES_ARITMETICOS_DOBLES, OPERADORES_RELACIONALES,
    OPERADORES_LOGICOS_DOBLES,
    OPERADORES_ARITMETICOS_SIMPLES, OPERADORES_LOGICOS_SIMPLES,
    SIMBOLOS,
)
from ide.compilador.errores import (
    ErrorLexico,
    CARACTER_INVALIDO, NUMERO_MAL_FORMADO, COMENTARIO_NO_CERRADO,
)


class Lexer:
    """
    Analizador léxico de paso único que recorre el texto carácter
    a carácter y produce listas de Token y ErrorLexico.
    """

    def __init__(self, texto: str):
        self._texto: str = texto
        self._pos: int = 0          # índice actual en el texto
        self._linea: int = 1        # línea actual (inicia en 1)
        self._columna: int = 1      # columna actual (inicia en 1)
        self._tokens: List[Token] = []
        self._errores: List[ErrorLexico] = []

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def analizar(self) -> Tuple[List[Token], List[ErrorLexico]]:
        """Ejecuta el análisis y retorna (tokens, errores)."""
        while not self._fin():
            self._siguiente_token()
        return self._tokens, self._errores

    # ── Helpers de posición ───────────────────────────────────────────────────

    def _fin(self) -> bool:
        return self._pos >= len(self._texto)

    def _actual(self) -> str:
        """Carácter en la posición actual."""
        return self._texto[self._pos]

    def _ver(self, offset: int = 1) -> str:
        """Mira el carácter a 'offset' posiciones adelante sin avanzar."""
        idx = self._pos + offset
        if idx < len(self._texto):
            return self._texto[idx]
        return ""

    def _avanzar(self) -> str:
        """Consume y retorna el carácter actual, actualizando la posición."""
        ch = self._texto[self._pos]
        self._pos += 1
        if ch == "\n":
            self._linea += 1
            self._columna = 1
        else:
            self._columna += 1
        return ch

    # ── Lógica principal ──────────────────────────────────────────────────────

    def _siguiente_token(self):
        """Determina el próximo token, o registra un error."""
        ch = self._actual()

        # ── Espacios en blanco ────────────────────────────────────────────
        if ch in (" ", "\t", "\r", "\n"):
            self._avanzar()
            return

        # ── Comentario de una línea: // ───────────────────────────────────
        if ch == "/" and self._ver() == "/":
            self._leer_comentario_linea()
            return

        # ── Comentario de bloque: /* ... */ ──────────────────────────────
        if ch == "/" and self._ver() == "*":
            self._leer_comentario_bloque()
            return

        # ── Números ───────────────────────────────────────────────────────
        if ch.isdigit():
            self._leer_numero()
            return

        # ── Identificadores y palabras reservadas ─────────────────────────
        if ch.isalpha() or ch == "_":
            self._leer_identificador()
            return

        # ── Operadores de dos caracteres ──────────────────────────────────
        doble = ch + self._ver()

        if doble in OPERADORES_ARITMETICOS_DOBLES:
            col = self._columna
            lin = self._linea
            self._avanzar(); self._avanzar()
            self._tokens.append(Token(OPERADOR_ARITMETICO, doble, lin, col))
            return

        if doble in OPERADORES_RELACIONALES:
            col = self._columna
            lin = self._linea
            self._avanzar(); self._avanzar()
            self._tokens.append(Token(OPERADOR_RELACIONAL, doble, lin, col))
            return

        if doble in OPERADORES_LOGICOS_DOBLES:
            col = self._columna
            lin = self._linea
            self._avanzar(); self._avanzar()
            self._tokens.append(Token(OPERADOR_LOGICO, doble, lin, col))
            return

        # ── Operadores relacionales de un carácter (<, >) ─────────────────
        if ch in ("<", ">"):
            col = self._columna
            lin = self._linea
            self._avanzar()
            self._tokens.append(Token(OPERADOR_RELACIONAL, ch, lin, col))
            return

        # ── Operadores aritméticos de un carácter ─────────────────────────
        if ch in OPERADORES_ARITMETICOS_SIMPLES:
            col = self._columna
            lin = self._linea
            self._avanzar()
            self._tokens.append(Token(OPERADOR_ARITMETICO, ch, lin, col))
            return

        # ── Operadores lógicos de un carácter (!) ────────────────────────
        if ch in OPERADORES_LOGICOS_SIMPLES:
            col = self._columna
            lin = self._linea
            self._avanzar()
            self._tokens.append(Token(OPERADOR_LOGICO, ch, lin, col))
            return

        # ── Asignación (=) ────────────────────────────────────────────────
        if ch == "=":
            col = self._columna
            lin = self._linea
            self._avanzar()
            self._tokens.append(Token(ASIGNACION, ch, lin, col))
            return

        # ── Símbolos ──────────────────────────────────────────────────────
        if ch in SIMBOLOS:
            col = self._columna
            lin = self._linea
            self._avanzar()
            self._tokens.append(Token(SIMBOLO, ch, lin, col))
            return

        # ── Carácter inválido ─────────────────────────────────────────────
        col = self._columna
        lin = self._linea
        self._avanzar()
        self._errores.append(ErrorLexico(CARACTER_INVALIDO, ch, lin, col))

    # ── Lectores especializados ───────────────────────────────────────────────

    def _leer_comentario_linea(self):
        """Consume un comentario de una línea (// hasta fin de línea)."""
        lin = self._linea
        col = self._columna
        lexema = ""
        while not self._fin() and self._actual() != "\n":
            lexema += self._avanzar()
        self._tokens.append(Token(COMENTARIO, lexema, lin, col))

    def _leer_comentario_bloque(self):
        """Consume un comentario de bloque (/* ... */)."""
        lin = self._linea
        col = self._columna
        lexema = ""
        # consumir /*
        lexema += self._avanzar()   # /
        lexema += self._avanzar()   # *
        cerrado = False
        while not self._fin():
            ch = self._avanzar()
            lexema += ch
            if ch == "*" and not self._fin() and self._actual() == "/":
                lexema += self._avanzar()   # /
                cerrado = True
                break
        if cerrado:
            self._tokens.append(Token(COMENTARIO, lexema, lin, col))
        else:
            self._errores.append(ErrorLexico(COMENTARIO_NO_CERRADO, lexema, lin, col))

    def _leer_numero(self):
        """
        Consume un número entero o real.
        Detecta números mal formados como '1.2.3'.
        """
        lin = self._linea
        col = self._columna
        lexema = ""
        puntos = 0

        while not self._fin() and (self._actual().isdigit() or self._actual() == "."):
            ch = self._actual()
            if ch == ".":
                puntos += 1
            lexema += self._avanzar()

        if puntos == 0:
            self._tokens.append(Token(NUMERO_ENTERO, lexema, lin, col))
        elif puntos == 1:
            self._tokens.append(Token(NUMERO_REAL, lexema, lin, col))
        else:
            # más de un punto decimal → número mal formado
            self._errores.append(ErrorLexico(NUMERO_MAL_FORMADO, lexema, lin, col))

    def _leer_identificador(self):
        """
        Consume un identificador o palabra reservada.
        Un identificador empieza con letra o '_' y contiene letras, dígitos o '_'.
        """
        lin = self._linea
        col = self._columna
        lexema = ""

        while not self._fin() and (self._actual().isalnum() or self._actual() == "_"):
            lexema += self._avanzar()

        if lexema in PALABRAS_RESERVADAS:
            self._tokens.append(Token(PALABRA_RESERVADA, lexema, lin, col))
        else:
            self._tokens.append(Token(IDENTIFICADOR, lexema, lin, col))


# ── Función de interfaz pública ───────────────────────────────────────────────

def analyze(texto: str) -> Tuple[List[Token], List[ErrorLexico]]:
    """
    Analiza el texto fuente y retorna (tokens, errores).

    Parámetros
    ----------
    texto : str
        Código fuente a analizar.

    Retorna
    -------
    tokens : list[Token]
        Lista de tokens reconocidos.
    errores : list[ErrorLexico]
        Lista de errores léxicos encontrados.
    """
    lexer = Lexer(texto)
    return lexer.analizar()
