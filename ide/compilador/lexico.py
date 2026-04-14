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
    SIMBOLO, ASIGNACION,
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

    def _ver_sin_blancos(self, desde: int = 1) -> Tuple[str, int]:
        """
        Busca el siguiente carácter no-blanco a partir de 'desde' posiciones
        adelante. Retorna (caracter, offset_real) o ('', -1) si no encuentra.
        Los blancos considerados son: espacio, tab, \r, \n.
        """
        idx = self._pos + desde
        while idx < len(self._texto):
            ch = self._texto[idx]
            if ch not in (" ", "\t", "\r", "\n"):
                return ch, idx - self._pos
            idx += 1
        return "", -1

    def _avanzar_hasta(self, offset: int):
        """Avanza el puntero hasta la posición self._pos + offset (excluido)."""
        veces = offset
        for _ in range(veces):
            self._avanzar()

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

        # ── Operadores de dos caracteres (con tolerancia a blancos) ─────────
        # Primero intentamos el carácter siguiente inmediato.
        siguiente_inmediato = self._ver()          # puede ser blanco
        doble_inmediato = ch + siguiente_inmediato

        # Si no forma doble directo, buscamos el siguiente no-blanco.
        sig_nb, offset_nb = self._ver_sin_blancos(1)
        doble_nb = ch + sig_nb

        # Determinamos qué "doble" usar: primero el inmediato (sin blancos),
        # luego el que salta blancos.
        def _intentar_doble(doble: str, offset: int) -> bool:
            """Registra el operador doble consumiendo 'offset+1' chars totales."""
            col = self._columna
            lin = self._linea
            self._avanzar_hasta(offset + 1)   # consume ch + blancos + sig
            if doble in OPERADORES_ARITMETICOS_DOBLES:
                self._tokens.append(Token(OPERADOR_ARITMETICO, doble, lin, col))
            elif doble in OPERADORES_RELACIONALES:
                self._tokens.append(Token(OPERADOR_RELACIONAL, doble, lin, col))
            elif doble in OPERADORES_LOGICOS_DOBLES:
                self._tokens.append(Token(OPERADOR_LOGICO, doble, lin, col))
            return True

        # Caso 1: el siguiente carácter inmediato forma operador doble
        if doble_inmediato in OPERADORES_ARITMETICOS_DOBLES | OPERADORES_RELACIONALES | OPERADORES_LOGICOS_DOBLES:
            _intentar_doble(doble_inmediato, 1)
            return

        # Caso 2: hay blancos entre los dos caracteres pero juntos forman doble
        if offset_nb > 1 and doble_nb in OPERADORES_ARITMETICOS_DOBLES | OPERADORES_RELACIONALES | OPERADORES_LOGICOS_DOBLES:
            _intentar_doble(doble_nb, offset_nb)
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
        """Consume un comentario de una línea (// hasta fin de línea) sin tokenizarlo."""
        while not self._fin() and self._actual() != "\n":
            self._avanzar()

    def _leer_comentario_bloque(self):
        """Consume un comentario de bloque (/* ... */) sin tokenizarlo."""
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
        if not cerrado:
            self._errores.append(ErrorLexico(COMENTARIO_NO_CERRADO, lexema, lin, col))

    def _leer_numero(self):
        """
        Consume un número entero o real modelando el autómata correctamente.

        Casos:
          - '32'      → NUMERO_ENTERO
          - '3.14'    → NUMERO_REAL
          - '32.algo' → el autómata consume '32.' esperando dígitos, ve 'a' →
                        descarta '32.' completo como NUMERO_MAL_FORMADO,
                        'algo' lo procesa la siguiente iteración como IDENTIFICADOR
          - '34.34.34.34' → emite '34.34' como NUMERO_REAL, el '.' que sigue
                        es error por sí solo ('.'), luego '34.34' se procesa
                        normalmente en la siguiente iteración
        """
        lin = self._linea
        col = self._columna

        # ── Estado 1: leer parte entera ───────────────────────────────────────
        entero = ""
        while not self._fin() and self._actual().isdigit():
            entero += self._avanzar()

        # ── Estado 2: ¿hay un punto? ──────────────────────────────────────────
        if self._fin() or self._actual() != ".":
            # No hay punto → NUMERO_ENTERO puro
            self._tokens.append(Token(NUMERO_ENTERO, entero, lin, col))
            return

        # Hay un punto; guardamos su posición exacta para el error
        punto_lin = self._linea
        punto_col = self._columna

        # ── Estado 3: consumir el punto y verificar que sigue un dígito ───────
        self._avanzar()          # consume '.'
        sig = self._actual() if not self._fin() else ""

        if not sig.isdigit():
            # El autómata esperaba un dígito tras el punto pero no llegó
            # → '32.' se descarta completo como error; la siguiente parte
            #   ('algo', operador, etc.) se procesa en la siguiente iteración.
            self._errores.append(
                ErrorLexico(NUMERO_MAL_FORMADO, entero + ".", punto_lin, punto_col)
            )
            return

        # ── Estado 4: leer dígitos de la parte decimal ────────────────────────
        decimal = ""
        while not self._fin() and self._actual().isdigit():
            decimal += self._avanzar()

        # Emitir el número real válido
        self._tokens.append(Token(NUMERO_REAL, entero + "." + decimal, lin, col))

        # ── Estado 5: ¿viene otro punto inmediatamente? ('34.34.34.34') ───────
        if not self._fin() and self._actual() == ".":
            error_lin = self._linea
            error_col = self._columna
            self._avanzar()      # consume el punto extra
            # Solo el '.' es el error; lo que sigue ('34.34') se procesa solo
            self._errores.append(
                ErrorLexico(NUMERO_MAL_FORMADO, ".", error_lin, error_col)
            )

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
