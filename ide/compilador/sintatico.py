# compilador/sintatico.py — Analizador sintáctico descendente recursivo
#
# Gramática implementada:
#   programa          → main { lista_declaracion }
#   lista_declaracion → declaracion*
#   declaracion       → declaracion_variable | sentencia
#   declaracion_variable → tipo identificador [= expresion] {, identificador [= expresion]} ;
#                          Árbol: nodo padre = "Decl: tipo", hijos = "Var: id" [con expr como hijo si hay init]
#   tipo              → int | float | bool
#   lista_sentencias  → sentencia*
#   sentencia         → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion
#   asignacion        → id = sent_expresion | id ++ ; | id -- ;
#   sent_expresion    → expresion ; | ;
#   seleccion         → if expresion then lista_sentencias [else lista_sentencias] end
#   iteracion         → while expresion lista_sentencias end
#   repeticion        → do lista_sentencias while expresion
#   sent_in           → cin >> id ;
#   sent_out          → cout << salida [;]
#   salida            → cadena | expresion | cadena << expresion | expresion << cadena
#   expresion         → expresion_simple [(rel_op | op_logico_bin) expresion_simple]
#   expresion_simple  → termino (suma_op termino)*
#   termino           → factor (mult_op factor)*
#   factor            → componente [^ componente]
#   componente        → ( expresion ) | número | id | true | false | ! componente
#
# Nota: do-while usa 'terminar_en_while=True' en _lista_sentencias.
#       Limitación conocida: un while-end anidado directo dentro del cuerpo
#       de un do se detecta como terminador. Evitar este patrón.

from typing import List, Optional, Tuple

from ide.compilador.tokens import (
    Token,
    PALABRA_RESERVADA, IDENTIFICADOR, NUMERO_ENTERO, NUMERO_REAL,
    OPERADOR_ARITMETICO, OPERADOR_RELACIONAL, OPERADOR_LOGICO,
    SIMBOLO, ASIGNACION, CADENA, OPERADOR_IO,
)
from ide.compilador.errores import ErrorSintactico, SINTAXIS_ERROR
from ide.modelos.datos import NodoArb


# ── Conjuntos de operadores ───────────────────────────────────────────────────

_TIPOS_VALIDOS = {"int", "float", "bool"}
_REL_OPS       = {"<", "<=", ">", ">=", "==", "!="}
_LOGICOS_BIN   = {"&&", "||"}
_SUMA_OPS      = {"+", "-", "++", "--"}
_MULT_OPS      = {"*", "/", "%"}

# Token EOF centinela
_EOF = Token(tipo="EOF", valor="EOF", linea=0, columna=0)


# ── Clase Parser ─────────────────────────────────────────────────────────────

class Parser:
    """
    Analizador sintáctico descendente recursivo.
    Lee una lista de Token (salida del léxico) y construye el AST.
    Los errores se acumulan en self._errores; el parser intenta continuar
    tras cada error no fatal.
    """

    def __init__(self, tokens: List[Token]):
        self._tokens: List[Token] = tokens
        self._pos: int = 0
        self._errores: List[ErrorSintactico] = []

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def parsear(self) -> Tuple[Optional[NodoArb], List[ErrorSintactico]]:
        """Analiza los tokens y devuelve (AST, lista_de_errores)."""
        arbol = self._programa()
        if self._actual().tipo != "EOF":
            self._error("Código inesperado después del cierre del programa principal")
        return arbol, self._errores

    # ── Helpers de navegación ─────────────────────────────────────────────────

    def _actual(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return _EOF

    def _ver(self, offset: int = 1) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return _EOF

    def _avanzar(self) -> Token:
        tok = self._actual()
        if self._pos < len(self._tokens):
            self._pos += 1
        return tok

    def _es(self, tipo: str = None, valor: str = None) -> bool:
        tok = self._actual()
        if tipo is not None and tok.tipo != tipo:
            return False
        if valor is not None and tok.valor != valor:
            return False
        return True

    def _es_tipo(self) -> bool:
        """True si el token actual es un tipo de dato (int/float/bool)."""
        return self._es(PALABRA_RESERVADA) and self._actual().valor in _TIPOS_VALIDOS

    def _es_fin_bloque(self, terminar_en_while: bool = False) -> bool:
        """True si el token actual cierra un bloque (end, else, }, EOF)."""
        tok = self._actual()
        if tok.tipo == "EOF":
            return True
        if tok.tipo == SIMBOLO and tok.valor == "}":
            return True
        if tok.tipo == PALABRA_RESERVADA and tok.valor in ("end", "else"):
            return True
        if terminar_en_while and tok.tipo == PALABRA_RESERVADA and tok.valor == "while":
            return True
        return False

    # ── Helpers de consumo ────────────────────────────────────────────────────

    def _match(self, tipo: str = None, valor: str = None) -> Optional[Token]:
        """
        Consume el token actual si coincide con tipo/valor.
        Si no coincide, registra un error y retorna None (sin avanzar).
        """
        tok = self._actual()
        tipo_ok  = (tipo  is None) or (tok.tipo  == tipo)
        valor_ok = (valor is None) or (tok.valor == valor)
        if tipo_ok and valor_ok:
            return self._avanzar()
        # Error descriptivo
        if valor:
            self._error(f"Se esperaba '{valor}' pero se encontró '{tok.valor}'", tok)
        else:
            self._error(
                f"Se esperaba tipo '{tipo}' pero se encontró "
                f"'{tok.tipo}' ('{tok.valor}')", tok
            )
        return None

    def _match_io(self, op: str) -> bool:
        """
        Consume el operador IO '<<' o '>>' que puede llegar como:
          - OPERADOR_IO  "<<"  (un solo token del léxico), o
          - dos OPERADOR_RELACIONAL consecutivos '<','<' (si llegaron separados).
        Retorna True si se consumió correctamente.
        """
        single = op[0]  # '<' o '>'
        if self._es(OPERADOR_IO, op):
            self._avanzar()
            return True
        elif self._es(OPERADOR_RELACIONAL, single) and self._ver().valor == single:
            self._avanzar()
            self._avanzar()
            return True
        else:
            tok = self._actual()
            self._error(f"Se esperaba '{op}' pero se encontró '{tok.valor}'", tok)
            return False

    def _es_op_io(self, op: str) -> bool:
        """True si el token actual (o par) representa el operador IO dado."""
        single = op[0]
        return (
            self._es(OPERADOR_IO, op)
            or (self._es(OPERADOR_RELACIONAL, single) and self._ver().valor == single)
        )

    def _error(self, msg: str, tok: Token = None):
        """Registra un ErrorSintactico."""
        if tok is None:
            tok = self._actual()
        self._errores.append(
            ErrorSintactico(
                error=SINTAXIS_ERROR,
                msg=msg,
                linea=tok.linea,
                columna=tok.columna,
                valor=tok.valor,
            )
        )

    def _recuperar_hasta(self, *stop):
        """
        Descarta tokens hasta encontrar uno cuyo valor esté en 'stop'.
        Evita consumir tokens que cierran bloques (end, else, }, EOF).
        """
        while self._actual().tipo != "EOF":
            tok = self._actual()
            if tok.valor in stop or tok.tipo in stop:
                return
            if tok.valor in ("end", "else", "}"):
                return
            self._avanzar()

    # ══════════════════════════════════════════════════════════════════════════
    # Reglas gramaticales
    # ══════════════════════════════════════════════════════════════════════════

    # ── programa ──────────────────────────────────────────────────────────────

    def _programa(self) -> Optional[NodoArb]:
        """programa → main { lista_declaracion }"""
        tok = self._actual()

        if not self._es(PALABRA_RESERVADA, "main"):
            self._error("El programa debe comenzar con 'main'", tok)
            return NodoArb(etiqueta="Programa (error)", linea=tok.linea, tipo_nodo="prog")

        self._avanzar()  # consume 'main'
        nodo = NodoArb(etiqueta="Programa: main", linea=tok.linea, tipo_nodo="prog")

        if not self._es(SIMBOLO, "{"):
            self._error("Se esperaba '{' después de 'main'")
        else:
            self._avanzar()

        nodo.hijos.extend(self._lista_declaracion())

        if not self._es(SIMBOLO, "}"):
            self._error("Se esperaba '}' para cerrar el bloque 'main'")
        else:
            self._avanzar()

        return nodo

    # ── lista_declaracion ─────────────────────────────────────────────────────

    def _lista_declaracion(self) -> List[NodoArb]:
        """lista_declaracion → (declaracion_variable | sentencia)*  hasta }"""
        nodos: List[NodoArb] = []
        while not self._es(SIMBOLO, "}") and self._actual().tipo != "EOF":
            _pos_antes = self._pos          # guardia anti-bucle infinito
            resultado = self._declaracion()
            if isinstance(resultado, list):
                nodos.extend(resultado)
            elif resultado is not None:
                nodos.append(resultado)
            # Si ninguna regla avanzó el puntero, forzar avance para no quedar trabado
            if self._pos == _pos_antes:
                tok = self._actual()
                if tok.tipo != "EOF":
                    self._error(
                        f"Token inesperado en el cuerpo de 'main': '{tok.valor}'", tok
                    )
                    self._avanzar()
        return nodos

    def _declaracion(self):
        """declaracion → declaracion_variable | sentencia"""
        if self._es_tipo():
            return self._declaracion_variable()
        return self._sentencia()

    # ── declaracion_variable ──────────────────────────────────────────────────

    def _declaracion_variable(self) -> Optional[NodoArb]:
        """
        declaracion_variable → tipo id [= expr] {, id [= expr]} ;

        Genera un único nodo padre con la etiqueta del tipo (p.ej. "Decl: int")
        y un hijo por cada identificador declarado.  Si una variable tiene
        inicialización, el nodo del identificador lleva la expresión como hijo.
        """
        tipo_tok = self._avanzar()   # consume int / float / bool
        tipo = tipo_tok.valor

        # Nodo padre que representa la declaración completa del tipo
        nodo_padre = NodoArb(
            etiqueta=f"Decl: {tipo}",
            linea=tipo_tok.linea,
            tipo_nodo="decl",
        )

        if not self._es(IDENTIFICADOR):
            self._error(f"Se esperaba un identificador después de '{tipo}'")
            self._recuperar_hasta(";")
            if self._es(SIMBOLO, ";"):
                self._avanzar()
            return None

        while True:
            if not self._es(IDENTIFICADOR):
                self._error("Se esperaba un identificador")
                break
            id_tok = self._avanzar()

            # Nodo hijo: representa cada variable declarada
            nodo_var = NodoArb(
                etiqueta=f"Var: {id_tok.valor}",
                linea=id_tok.linea,
                tipo_nodo="decl",
            )
            # Inicialización opcional: la expresión se agrega como hijo de la variable
            if self._es(ASIGNACION, "="):
                self._avanzar()
                expr = self._expresion()
                if expr:
                    nodo_var.hijos.append(expr)

            nodo_padre.hijos.append(nodo_var)

            if self._es(SIMBOLO, ","):
                self._avanzar()   # consume ',' → siguiente id
            else:
                break

        if not self._es(SIMBOLO, ";"):
            self._error(f"Se esperaba ';' al final de la declaración de '{tipo}'")
        else:
            self._avanzar()

        return nodo_padre

    # ── lista_sentencias ──────────────────────────────────────────────────────

    def _lista_sentencias(self, terminar_en_while: bool = False) -> List[NodoArb]:
        """
        lista_sentencias → sentencia*
        Se detiene al ver: end, else, }, EOF (o 'while' si terminar_en_while=True).
        """
        nodos: List[NodoArb] = []
        while not self._es_fin_bloque(terminar_en_while):
            _pos_antes = self._pos          # guardia anti-bucle infinito
            if self._es_tipo():
                self._error(
                    "Las declaraciones de variables solo se permiten "
                    "en el cuerpo principal de 'main'"
                )
                self._recuperar_hasta(";")
                if self._es(SIMBOLO, ";"):
                    self._avanzar()
                continue
            n = self._sentencia()
            if n:
                nodos.append(n)
            # Guardia: si no se avanzó, forzar avance
            if self._pos == _pos_antes and not self._es_fin_bloque(terminar_en_while):
                tok = self._actual()
                if tok.tipo != "EOF":
                    self._error(f"Token inesperado en sentencia: '{tok.valor}'", tok)
                    self._avanzar()
        return nodos

    # ── sentencia ─────────────────────────────────────────────────────────────

    def _sentencia(self) -> Optional[NodoArb]:
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
        tok = self._actual()

        if self._es(PALABRA_RESERVADA, "if"):
            return self._seleccion()
        if self._es(PALABRA_RESERVADA, "while"):
            return self._iteracion()
        if self._es(PALABRA_RESERVADA, "do"):
            return self._repeticion()
        if self._es(PALABRA_RESERVADA, "cin"):
            return self._sent_in()
        if self._es(PALABRA_RESERVADA, "cout"):
            return self._sent_out()
        if self._es(IDENTIFICADOR):
            return self._asignacion_o_incremento()

        # Token inesperado — recuperación
        self._error(f"Sentencia inesperada: '{tok.valor}' ({tok.tipo})", tok)
        if not self._es_fin_bloque():
            self._avanzar()
        return None

    # ── asignacion / incremento / decremento ──────────────────────────────────

    def _asignacion_o_incremento(self) -> Optional[NodoArb]:
        """
        asignacion  → id = sent_expresion
        incremento  → id ++ ;
        decremento  → id -- ;
        """
        id_tok = self._avanzar()   # consume identificador

        if self._es(ASIGNACION, "="):
            self._avanzar()   # consume '='
            nodo = NodoArb(
                etiqueta=f"Asignar: {id_tok.valor}",
                linea=id_tok.linea,
                tipo_nodo="stmt",
            )
            expr = self._sent_expresion()
            if expr:
                nodo.hijos.append(expr)
            return nodo

        if self._es(OPERADOR_ARITMETICO, "++"):
            self._avanzar()
            nodo = NodoArb(
                etiqueta=f"Incrementar: {id_tok.valor}++",
                linea=id_tok.linea,
                tipo_nodo="stmt",
            )
            if not self._es(SIMBOLO, ";"):
                self._error("Se esperaba ';' después de '++'")
            else:
                self._avanzar()
            return nodo

        if self._es(OPERADOR_ARITMETICO, "--"):
            self._avanzar()
            nodo = NodoArb(
                etiqueta=f"Decrementar: {id_tok.valor}--",
                linea=id_tok.linea,
                tipo_nodo="stmt",
            )
            if not self._es(SIMBOLO, ";"):
                self._error("Se esperaba ';' después de '--'")
            else:
                self._avanzar()
            return nodo

        # Error: nada reconocible después del id
        self._error(
            f"Se esperaba '=', '++' o '--' después del identificador '{id_tok.valor}'"
        )
        self._recuperar_hasta(";")
        if self._es(SIMBOLO, ";"):
            self._avanzar()
        return None

    def _sent_expresion(self) -> Optional[NodoArb]:
        """sent_expresion → expresion ; | ;"""
        if self._es(SIMBOLO, ";"):
            self._avanzar()
            return None
        expr = self._expresion()
        if not self._es(SIMBOLO, ";"):
            self._error("Se esperaba ';' al final de la asignación")
        else:
            self._avanzar()
        return expr

    # ── seleccion (if) ────────────────────────────────────────────────────────

    def _seleccion(self) -> Optional[NodoArb]:
        """seleccion → if expresion then lista_sentencias [else lista_sentencias] end"""
        tok = self._actual()
        nodo = NodoArb(etiqueta="Si (if)", linea=tok.linea, tipo_nodo="stmt")

        self._match(PALABRA_RESERVADA, "if")

        cond = self._expresion()
        if cond:
            nodo.hijos.append(cond)

        if not self._es(PALABRA_RESERVADA, "then"):
            self._error("Se esperaba 'then' después de la condición del 'if'")
        else:
            self._avanzar()

        then_nodo = NodoArb(
            etiqueta="Entonces (then)",
            linea=self._actual().linea,
            tipo_nodo="bloque",
        )
        then_nodo.hijos.extend(self._lista_sentencias())
        nodo.hijos.append(then_nodo)

        if self._es(PALABRA_RESERVADA, "else"):
            self._avanzar()
            else_nodo = NodoArb(
                etiqueta="SiNo (else)",
                linea=self._actual().linea,
                tipo_nodo="bloque",
            )
            else_nodo.hijos.extend(self._lista_sentencias())
            nodo.hijos.append(else_nodo)

        if not self._es(PALABRA_RESERVADA, "end"):
            self._error("Se esperaba 'end' para cerrar el bloque 'if'")
        else:
            self._avanzar()

        return nodo

    # ── iteracion (while) ─────────────────────────────────────────────────────

    def _iteracion(self) -> Optional[NodoArb]:
        """iteracion → while expresion lista_sentencias end"""
        tok = self._actual()
        nodo = NodoArb(etiqueta="Mientras (while)", linea=tok.linea, tipo_nodo="stmt")

        self._match(PALABRA_RESERVADA, "while")

        cond = self._expresion()
        if cond:
            nodo.hijos.append(cond)

        cuerpo = NodoArb(
            etiqueta="Cuerpo",
            linea=self._actual().linea,
            tipo_nodo="bloque",
        )
        cuerpo.hijos.extend(self._lista_sentencias())
        nodo.hijos.append(cuerpo)

        if not self._es(PALABRA_RESERVADA, "end"):
            self._error("Se esperaba 'end' para cerrar el bloque 'while'")
        else:
            self._avanzar()

        return nodo

    # ── repeticion (do-while) ─────────────────────────────────────────────────

    def _repeticion(self) -> Optional[NodoArb]:
        """
        repeticion → do lista_sentencias while expresion
        Nota: _lista_sentencias se llama con terminar_en_while=True para que
        se detenga antes del 'while' del do-while. Limitación: un while-end
        anidado directo dentro del cuerpo también detendría el parsing.
        """
        tok = self._actual()
        nodo = NodoArb(etiqueta="Hacer (do-while)", linea=tok.linea, tipo_nodo="stmt")

        self._match(PALABRA_RESERVADA, "do")

        cuerpo = NodoArb(
            etiqueta="Cuerpo",
            linea=self._actual().linea,
            tipo_nodo="bloque",
        )
        # terminar_en_while=True: la lista se detiene antes del 'while' del do
        cuerpo.hijos.extend(self._lista_sentencias(terminar_en_while=True))
        nodo.hijos.append(cuerpo)

        if not self._es(PALABRA_RESERVADA, "while"):
            self._error("Se esperaba 'while' al final del bloque 'do'")
        else:
            self._avanzar()

        cond = self._expresion()
        if cond:
            nodo.hijos.append(cond)

        # ';' opcional al final del do-while (buena práctica)
        if self._es(SIMBOLO, ";"):
            self._avanzar()

        return nodo

    # ── sent_in (cin) ─────────────────────────────────────────────────────────

    def _sent_in(self) -> Optional[NodoArb]:
        """sent_in → cin >> id ;"""
        tok = self._actual()
        nodo = NodoArb(etiqueta="Leer (cin)", linea=tok.linea, tipo_nodo="stmt")

        self._match(PALABRA_RESERVADA, "cin")
        self._match_io(">>")

        if not self._es(IDENTIFICADOR):
            self._error("Se esperaba un identificador después de 'cin >>'")
        else:
            id_tok = self._avanzar()
            nodo.etiqueta = f"Leer (cin): {id_tok.valor}"
            nodo.hijos.append(
                NodoArb(etiqueta=f"Id: {id_tok.valor}", linea=id_tok.linea, tipo_nodo="expr")
            )

        if not self._es(SIMBOLO, ";"):
            self._error("Se esperaba ';' al final de 'cin'")
        else:
            self._avanzar()

        return nodo

    # ── sent_out (cout) ───────────────────────────────────────────────────────

    def _sent_out(self) -> Optional[NodoArb]:
        """sent_out → cout << salida ;"""
        tok = self._actual()
        nodo = NodoArb(etiqueta="Escribir (cout)", linea=tok.linea, tipo_nodo="stmt")

        self._match(PALABRA_RESERVADA, "cout")
        self._match_io("<<")

        sal = self._salida()
        if sal:
            nodo.hijos.append(sal)

        if not self._es(SIMBOLO, ";"):
            self._error("Se esperaba ';' al final de 'cout'")
        else:
            self._avanzar()

        return nodo

    def _salida(self) -> Optional[NodoArb]:
        """
        salida → cadena [<< expresion]
               | expresion [<< cadena]
        """
        tok = self._actual()

        if self._es(CADENA):
            cadena_nodo = self._cadena()
            if self._es_op_io("<<"):
                self._match_io("<<")
                expr_nodo = self._expresion()
                sal_nodo = NodoArb(
                    etiqueta="Salida combinada", linea=tok.linea, tipo_nodo="expr"
                )
                if cadena_nodo:
                    sal_nodo.hijos.append(cadena_nodo)
                if expr_nodo:
                    sal_nodo.hijos.append(expr_nodo)
                return sal_nodo
            return cadena_nodo

        expr_nodo = self._expresion()
        if self._es_op_io("<<"):
            self._match_io("<<")
            cadena_nodo = self._cadena()
            sal_nodo = NodoArb(
                etiqueta="Salida combinada", linea=tok.linea, tipo_nodo="expr"
            )
            if expr_nodo:
                sal_nodo.hijos.append(expr_nodo)
            if cadena_nodo:
                sal_nodo.hijos.append(cadena_nodo)
            return sal_nodo
        return expr_nodo

    def _cadena(self) -> Optional[NodoArb]:
        """Consume y retorna un nodo CADENA."""
        if self._es(CADENA):
            tok = self._avanzar()
            return NodoArb(etiqueta=f"Cadena: {tok.valor}", linea=tok.linea, tipo_nodo="expr")
        self._error("Se esperaba una cadena de texto entre comillas")
        return None

    # ── Expresiones ───────────────────────────────────────────────────────────

    def _expresion(self) -> Optional[NodoArb]:
        """
        expresion → expresion_simple [rel_op expresion_simple]
                  | expresion_simple [op_logico_bin expresion_simple]
        """
        izq = self._expresion_simple()

        # operadores relacionales
        if self._es(OPERADOR_RELACIONAL) and self._actual().valor in _REL_OPS:
            op_tok = self._avanzar()
            der = self._expresion_simple()
            nodo = NodoArb(etiqueta=f"Op: {op_tok.valor}", linea=op_tok.linea, tipo_nodo="expr")
            if izq:
                nodo.hijos.append(izq)
            if der:
                nodo.hijos.append(der)
            return nodo

        # operadores lógicos binarios (&&, ||)
        if self._es(OPERADOR_LOGICO) and self._actual().valor in _LOGICOS_BIN:
            op_tok = self._avanzar()
            der = self._expresion_simple()
            nodo = NodoArb(etiqueta=f"Op: {op_tok.valor}", linea=op_tok.linea, tipo_nodo="expr")
            if izq:
                nodo.hijos.append(izq)
            if der:
                nodo.hijos.append(der)
            return nodo

        return izq

    def _expresion_simple(self) -> Optional[NodoArb]:
        """expresion_simple → termino (suma_op termino)*"""
        nodo = self._termino()

        while self._es(OPERADOR_ARITMETICO) and self._actual().valor in _SUMA_OPS:
            op_tok = self._avanzar()
            der = self._termino()
            nuevo = NodoArb(etiqueta=f"Op: {op_tok.valor}", linea=op_tok.linea, tipo_nodo="expr")
            if nodo:
                nuevo.hijos.append(nodo)
            if der:
                nuevo.hijos.append(der)
            nodo = nuevo

        return nodo

    def _termino(self) -> Optional[NodoArb]:
        """termino → factor (mult_op factor)*"""
        nodo = self._factor()

        while self._es(OPERADOR_ARITMETICO) and self._actual().valor in _MULT_OPS:
            op_tok = self._avanzar()
            der = self._factor()
            nuevo = NodoArb(etiqueta=f"Op: {op_tok.valor}", linea=op_tok.linea, tipo_nodo="expr")
            if nodo:
                nuevo.hijos.append(nodo)
            if der:
                nuevo.hijos.append(der)
            nodo = nuevo

        return nodo

    def _factor(self) -> Optional[NodoArb]:
        """factor → componente [^ componente]"""
        nodo = self._componente()

        if self._es(OPERADOR_ARITMETICO, "^"):
            op_tok = self._avanzar()
            der = self._componente()
            nuevo = NodoArb(etiqueta="Op: ^", linea=op_tok.linea, tipo_nodo="expr")
            if nodo:
                nuevo.hijos.append(nodo)
            if der:
                nuevo.hijos.append(der)
            return nuevo

        return nodo

    def _componente(self) -> Optional[NodoArb]:
        """
        componente → ( expresion )
                   | NUMERO_ENTERO
                   | NUMERO_REAL
                   | IDENTIFICADOR
                   | true | false
                   | ! componente
        """
        tok = self._actual()

        if self._es(SIMBOLO, "("):
            self._avanzar()
            nodo = self._expresion()
            if not self._es(SIMBOLO, ")"):
                self._error("Se esperaba ')' para cerrar la expresión")
            else:
                self._avanzar()
            return nodo

        if self._es(NUMERO_ENTERO):
            tok = self._avanzar()
            return NodoArb(etiqueta=f"Num: {tok.valor}", linea=tok.linea, tipo_nodo="expr")

        if self._es(NUMERO_REAL):
            tok = self._avanzar()
            return NodoArb(etiqueta=f"Num: {tok.valor}", linea=tok.linea, tipo_nodo="expr")

        if self._es(IDENTIFICADOR):
            tok = self._avanzar()
            return NodoArb(etiqueta=f"Id: {tok.valor}", linea=tok.linea, tipo_nodo="expr")

        if self._es(PALABRA_RESERVADA) and tok.valor in ("true", "false"):
            tok = self._avanzar()
            return NodoArb(etiqueta=f"Bool: {tok.valor}", linea=tok.linea, tipo_nodo="expr")

        if self._es(OPERADOR_LOGICO, "!"):
            op_tok = self._avanzar()
            operando = self._componente()
            nodo = NodoArb(etiqueta="Op: !", linea=op_tok.linea, tipo_nodo="expr")
            if operando:
                nodo.hijos.append(operando)
            return nodo

        # Token irreconocible en posición de componente
        if tok.tipo != "EOF" and not self._es_fin_bloque():
            self._error(f"Expresión inválida: se encontró '{tok.valor}' ({tok.tipo})", tok)
            self._avanzar()   # avanzar para evitar bucle infinito

        return None


# ── Función de interfaz pública ───────────────────────────────────────────────

def parse(tokens: List[Token]) -> Tuple[Optional[NodoArb], List[ErrorSintactico]]:
    """
    Ejecuta el análisis sintáctico sobre la lista de tokens.

    Parámetros
    ----------
    tokens : List[Token]
        Salida del analizador léxico.

    Retorna
    -------
    (arbol, errores) : (NodoArb | None, List[ErrorSintactico])
        arbol   → raíz del AST (puede ser parcial si hubo errores)
        errores → errores sintácticos detectados
    """
    p = Parser(tokens)
    return p.parsear()
