# compilador/semantico.py — Analizador semántico y tabla de símbolos (Fase 3)
#
# Implementa:
# 1. Tabla de símbolos con registro de identificadores, tipos, desplazamientos en memoria y líneas de uso.
# 2. Asignación y propagación de atributos heredados (ej. dtype en declaraciones) y sintetizados (tipo y valor en expresiones).
# 3. Construcción del AST Anotado (clon enriquecido del AST original).
# 4. Verificación de compatibilidad y conversión de tipos.
# 5. Detección de los 7 errores semánticos obligatorios según el programa de Compiladores II.

from typing import List, Dict, Optional, Tuple, Any
from copy import deepcopy

from ide.modelos.datos import NodoArb, Sim
from ide.compilador.errores import (
    ErrorSemantico,
    ERR_VAR_NO_DECLARADA,
    ERR_DECL_DUPLICADA,
    ERR_TIPO_INCOMPATIBLE,
    ERR_CONVERSION_INVALIDA,
    ERR_OPERADOR_INDEBIDO,
    ERR_ASIGNACION_INCOMPATIBLE,
    ERR_CONDICION_NO_BOOL,
)


# ── Tamaños de memoria por tipo de dato (bytes) ──────────────────────────────
TAMANIOS_TIPO = {
    "int": 4,
    "float": 4,
    "bool": 1,
}

# Operadores válidos
_OPS_ARITMETICOS = {"+", "-", "*", "/", "^"}
_OPS_RELACIONALES = {"<", "<=", ">", ">=", "==", "!="}
_OPS_LOGICOS = {"&&", "||", "!"}


# ── Clase TablaSimbolos ───────────────────────────────────────────────────────

class TablaSimbolos:
    """
    Tabla de símbolos para el análisis semántico.
    Registra variables declaradas, su tipo, ámbito, dirección de memoria y líneas donde se usan.
    """

    def __init__(self, ambito: str = "main"):
        self.ambito: str = ambito
        self._simbolos: Dict[str, Sim] = {}
        self._desplazamiento_actual: int = 0

    def insertar(self, nombre: str, tipo: str, linea: int) -> Tuple[bool, Optional[str]]:
        """
        Inserta un identificador en la tabla de símbolos.
        Retorna (True, None) si fue exitoso o (False, mensaje_error) si es duplicado.
        """
        if nombre in self._simbolos:
            linea_previa = self._simbolos[nombre].linea
            return False, f"La variable '{nombre}' ya fue declarada previamente en la línea {linea_previa}."

        tam = TAMANIOS_TIPO.get(tipo, 4)
        sim = Sim(
            nombre=nombre,
            tipo=tipo,
            ambito=self.ambito,
            linea=linea,
            desplazamiento=self._desplazamiento_actual,
            tam_bytes=tam,
            referencias=[],
        )
        self._simbolos[nombre] = sim
        self._desplazamiento_actual += tam
        return True, None

    def buscar(self, nombre: str) -> Optional[Sim]:
        """Busca un símbolo por su nombre/lexema."""
        return self._simbolos.get(nombre)

    def contiene(self, nombre: str) -> bool:
        return nombre in self._simbolos

    def registrar_uso(self, nombre: str, linea: int) -> None:
        """Registra una línea donde el símbolo fue referenciado (leído o escrito)."""
        sim = self._simbolos.get(nombre)
        if sim is not None and linea > 0:
            if linea not in sim.referencias:
                sim.referencias.append(linea)

    def obtener_simbolos(self) -> List[Sim]:
        """Retorna la lista ordenada de símbolos registrados."""
        return list(self._simbolos.values())

    def limpiar(self) -> None:
        self._simbolos.clear()
        self._desplazamiento_actual = 0


# ── Función para clonar el AST antes de anotar ────────────────────────────────

def clonar_ast(nodo: Optional[NodoArb]) -> Optional[NodoArb]:
    """Crea una copia profunda del árbol sintáctico para no alterar el AST original."""
    if nodo is None:
        return None
    nuevo = NodoArb(
        etiqueta=nodo.etiqueta,
        linea=nodo.linea,
        tipo_nodo=nodo.tipo_nodo,
        tipo_dato=getattr(nodo, "tipo_dato", ""),
        valor=getattr(nodo, "valor", None),
        conversion=getattr(nodo, "conversion", ""),
        atributos=dict(getattr(nodo, "atributos", {})),
    )
    nuevo.hijos = [clonar_ast(h) for h in nodo.hijos if h is not None]
    return nuevo


# ── Renderizador de AST Anotado en ASCII ──────────────────────────────────────

def _formatear_etiqueta_anotada(nodo: NodoArb) -> str:
    """Devuelve la etiqueta con la representación visual de sus atributos semánticos."""
    anotaciones = []
    dtype = nodo.atributos.get("dtype")
    if dtype:
        anotaciones.append(f"dtype: {dtype}")

    dir_mem = nodo.atributos.get("dir")
    if dir_mem is not None:
        anotaciones.append(f"dir: {dir_mem}")

    if nodo.tipo_dato and nodo.tipo_dato not in ("void", ""):
        anotaciones.append(f"tipo: {nodo.tipo_dato}")

    if nodo.valor is not None:
        # Formatear números o booleanos de forma limpia
        if isinstance(nodo.valor, float):
            val_str = f"{nodo.valor:.4g}" if nodo.valor % 1 != 0 else f"{nodo.valor:.1f}"
        else:
            val_str = str(nodo.valor)
        anotaciones.append(f"val: {val_str}")

    if nodo.conversion:
        anotaciones.append(f"conv: {nodo.conversion}")

    if anotaciones:
        return f"{nodo.etiqueta} {{{', '.join(anotaciones)}}}"
    return nodo.etiqueta


def _lineas_ast_anotado(nodo: NodoArb, prefijo: str = "", es_ultimo: bool = True) -> list:
    conector = "+-- "
    sufijo = f"   [L{nodo.linea}]" if getattr(nodo, "linea", 0) else ""
    lineas = [prefijo + conector + _formatear_etiqueta_anotada(nodo) + sufijo]
    extension = "    " if es_ultimo else "|   "
    for i, hijo in enumerate(nodo.hijos):
        lineas.extend(_lineas_ast_anotado(hijo, prefijo + extension, i == len(nodo.hijos) - 1))
    return lineas


def ast_anotado_a_texto(raiz: Optional[NodoArb]) -> str:
    """Convierte el AST Anotado a formato de texto ASCII indentado."""
    if raiz is None:
        return "(árbol vacío)"
    sufijo = f"   [L{raiz.linea}]" if getattr(raiz, "linea", 0) else ""
    lineas = [_formatear_etiqueta_anotada(raiz) + sufijo]
    for i, hijo in enumerate(raiz.hijos):
        lineas.extend(_lineas_ast_anotado(hijo, "", i == len(raiz.hijos) - 1))
    return "\n".join(lineas)


# ── Analizador Semántico ──────────────────────────────────────────────────────

class AnalizadorSemantico:
    """
    Recorre el AST, propaga atributos heredados y sintetizados, construye
    la tabla de símbolos y verifica tipos y semántica.
    """

    def __init__(self, raiz_ast: Optional[NodoArb]):
        self.raiz_original: Optional[NodoArb] = raiz_ast
        self.raiz_anotada: Optional[NodoArb] = None
        self.tabla: TablaSimbolos = TablaSimbolos(ambito="main")
        self.errores: List[ErrorSemantico] = []

    def analizar(self) -> Tuple[Optional[NodoArb], TablaSimbolos, List[ErrorSemantico]]:
        """
        Ejecuta el análisis semántico completo.
        Devuelve (arbol_anotado, tabla_simbolos, lista_errores).
        """
        if self.raiz_original is None:
            return None, self.tabla, self.errores

        # Paso 1: Clonar AST para trabajar en copia anotada
        self.raiz_anotada = clonar_ast(self.raiz_original)

        # Paso 2: Recorrer el programa
        self._analizar_nodo(self.raiz_anotada)

        return self.raiz_anotada, self.tabla, self.errores

    def _agregar_error(self, tipo: str, msg: str, linea: int, valor: str = "") -> None:
        self.errores.append(
            ErrorSemantico(
                error=tipo,
                msg=msg,
                linea=linea,
                columna=0,
                valor=valor,
            )
        )

    # ── Despacho principal por tipo de nodo ────────────────────────────────────

    def _analizar_nodo(self, nodo: NodoArb) -> None:
        if nodo is None:
            return

        etiq = nodo.etiqueta

        # Programa raíz
        if etiq.startswith("Programa"):
            nodo.tipo_nodo = "prog"
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
            return

        # Declaración de variables: Decl: <tipo>
        if etiq.startswith("Decl:"):
            self._procesar_declaracion(nodo)
            return

        # Asignación: Asignar: <id>
        if etiq.startswith("Asignar:"):
            self._procesar_asignacion(nodo)
            return

        # Incremento / Decremento: Incrementar: <id>++ / Decrementar: <id>--
        if etiq.startswith("Incrementar:") or etiq.startswith("Decrementar:"):
            self._procesar_incremento_decremento(nodo)
            return

        # Estructura condicional: Si (if)
        if etiq.startswith("Si (if)"):
            self._procesar_if(nodo)
            return

        # Estructura de iteración: Mientras (while)
        if etiq.startswith("Mientras (while)"):
            self._procesar_while(nodo)
            return

        # Estructura de repetición: Hacer (do-while)
        if etiq.startswith("Hacer (do-while)"):
            self._procesar_do_while(nodo)
            return

        # Sentencia de entrada: Leer (cin)
        if etiq.startswith("Leer (cin)"):
            self._procesar_cin(nodo)
            return

        # Sentencia de salida: Escribir (cout)
        if etiq.startswith("Escribir (cout)"):
            self._procesar_cout(nodo)
            return

        # Bloques internos ("Entonces (then)", "SiNo (else)", "Cuerpo")
        if nodo.tipo_nodo == "bloque":
            for hijo in nodo.hijos:
                self._analizar_nodo(hijo)
            return

        # Si es una expresión libre en un bloque
        if nodo.tipo_nodo == "expr":
            self._evaluar_expresion(nodo)
            return

        # Recorrer hijos por defecto
        for hijo in nodo.hijos:
            self._analizar_nodo(hijo)

    # ── 1. Declaraciones y Atributos Heredados ─────────────────────────────────

    def _procesar_declaracion(self, nodo: NodoArb) -> None:
        """
        Propaga el atributo heredado 'dtype' del nodo 'Decl: <tipo>'
        hacia sus identificadores hijos 'Var: <id>'.
        Inserta cada variable en la Tabla de Símbolos.
        """
        # Extraer tipo base de "Decl: int", "Decl: float", "Decl: bool"
        partes = nodo.etiqueta.split(":", 1)
        tipo_base = partes[1].strip() if len(partes) > 1 else ""

        nodo.atributos["dtype"] = tipo_base

        for var_nodo in nodo.hijos:
            if not var_nodo.etiqueta.startswith("Var:"):
                self._analizar_nodo(var_nodo)
                continue

            id_nombre = var_nodo.etiqueta.split(":", 1)[1].strip()
            var_nodo.atributos["dtype"] = tipo_base
            var_nodo.tipo_dato = tipo_base

            # Inserción en tabla de símbolos
            exito, err_msg = self.tabla.insertar(id_nombre, tipo_base, var_nodo.linea)
            if not exito:
                self._agregar_error(
                    ERR_DECL_DUPLICADA,
                    err_msg or f"Declaración duplicada: la variable '{id_nombre}' ya existe.",
                    var_nodo.linea,
                    valor=id_nombre,
                )
            else:
                sim = self.tabla.buscar(id_nombre)
                if sim:
                    var_nodo.atributos["dir"] = sim.desplazamiento

            # Inicialización opcional si tiene expresión hija: int x = <expr>
            if var_nodo.hijos:
                expr_init = var_nodo.hijos[0]
                self._evaluar_expresion(expr_init)
                self._verificar_compatibilidad_asignacion(
                    tipo_base, expr_init, var_nodo.linea, id_nombre
                )

    # ── 2. Asignaciones ───────────────────────────────────────────────────────

    def _procesar_asignacion(self, nodo: NodoArb) -> None:
        """
        Asignar: <id>
        Verifica existencia del identificador, evalúa la expresión asignada y
        comprueba compatibilidad de tipos (y posibles conversiones).
        """
        partes = nodo.etiqueta.split(":", 1)
        id_nombre = partes[1].strip() if len(partes) > 1 else ""

        sim = self.tabla.buscar(id_nombre)
        if sim is None:
            self._agregar_error(
                ERR_VAR_NO_DECLARADA,
                f"La variable '{id_nombre}' no ha sido declarada.",
                nodo.linea,
                valor=id_nombre,
            )
            tipo_destino = "error"
        else:
            self.tabla.registrar_uso(id_nombre, nodo.linea)
            tipo_destino = sim.tipo
            nodo.tipo_dato = tipo_destino
            nodo.atributos["dir"] = sim.desplazamiento

        if nodo.hijos:
            expr = nodo.hijos[0]
            self._evaluar_expresion(expr)
            if tipo_destino != "error":
                self._verificar_compatibilidad_asignacion(
                    tipo_destino, expr, nodo.linea, id_nombre
                )

    def _verificar_compatibilidad_asignacion(
        self, tipo_var: str, expr_nodo: NodoArb, linea: int, id_nombre: str
    ) -> None:
        """Comprueba si el tipo de la expresión puede asignarse al tipo de la variable."""
        tipo_expr = expr_nodo.tipo_dato

        if tipo_expr in ("error", ""):
            return  # Evitar cascada de errores

        if tipo_var == tipo_expr:
            return  # Mismo tipo: perfectamente compatible

        # Promoción int -> float válida en asignación a float
        if tipo_var == "float" and tipo_expr == "int":
            expr_nodo.conversion = "int -> float"
            return

        # Asignar float a int: pérdida de precisión / conversión inválida
        if tipo_var == "int" and tipo_expr == "float":
            self._agregar_error(
                ERR_ASIGNACION_INCOMPATIBLE,
                f"Inconsistencia de tipos en asignación a '{id_nombre}': no se puede asignar una expresión de tipo 'float' a la variable entera 'int' sin conversión explícita.",
                linea,
                valor=id_nombre,
            )
            return

        # Asignar booleano a número o número a booleano
        if tipo_var == "bool" and tipo_expr != "bool":
            self._agregar_error(
                ERR_ASIGNACION_INCOMPATIBLE,
                f"Inconsistencia de tipos en asignación a '{id_nombre}': no se puede asignar una expresión de tipo '{tipo_expr}' a una variable booleana.",
                linea,
                valor=id_nombre,
            )
            return

        if tipo_var in ("int", "float") and tipo_expr == "bool":
            self._agregar_error(
                ERR_ASIGNACION_INCOMPATIBLE,
                f"Inconsistencia de tipos en asignación a '{id_nombre}': no se puede asignar una expresión booleana a una variable numérica '{tipo_var}'.",
                linea,
                valor=id_nombre,
            )
            return

        self._agregar_error(
            ERR_TIPO_INCOMPATIBLE,
            f"Tipos incompatibles en asignación a '{id_nombre}': variable '{tipo_var}' vs expresión '{tipo_expr}'.",
            linea,
            valor=id_nombre,
        )

    # ── 3. Incremento / Decremento ────────────────────────────────────────────

    def _procesar_incremento_decremento(self, nodo: NodoArb) -> None:
        etiq = nodo.etiqueta.split(":", 1)[1].strip() if ":" in nodo.etiqueta else ""
        # Quitar sufijo ++ o --
        id_nombre = etiq.replace("++", "").replace("--", "").strip()

        sim = self.tabla.buscar(id_nombre)
        if sim is None:
            self._agregar_error(
                ERR_VAR_NO_DECLARADA,
                f"La variable '{id_nombre}' no ha sido declarada.",
                nodo.linea,
                valor=id_nombre,
            )
        else:
            self.tabla.registrar_uso(id_nombre, nodo.linea)
            if sim.tipo == "bool":
                self._agregar_error(
                    ERR_OPERADOR_INDEBIDO,
                    f"Uso indebido de operador de incremento/decremento sobre la variable booleana '{id_nombre}'.",
                    nodo.linea,
                    valor=id_nombre,
                )

    # ── 4. Estructuras de Control (Condicionales y Bucles) ─────────────────────

    def _procesar_if(self, nodo: NodoArb) -> None:
        """
        Hijos de Si (if):
        Hijo 0: condición
        Hijo 1: Entonces (then) [bloque]
        Hijo 2: SiNo (else) [bloque opcional]
        """
        if nodo.hijos:
            cond = nodo.hijos[0]
            self._evaluar_expresion(cond)
            self._verificar_condicion_booleana(cond, "if")

            for bloque in nodo.hijos[1:]:
                self._analizar_nodo(bloque)

    def _procesar_while(self, nodo: NodoArb) -> None:
        """
        Hijos de Mientras (while):
        Hijo 0: condición
        Hijo 1: Cuerpo [bloque]
        """
        if nodo.hijos:
            cond = nodo.hijos[0]
            self._evaluar_expresion(cond)
            self._verificar_condicion_booleana(cond, "while")

            if len(nodo.hijos) > 1:
                self._analizar_nodo(nodo.hijos[1])

    def _procesar_do_while(self, nodo: NodoArb) -> None:
        """
        Hijos de Hacer (do-while):
        Hijo 0: Cuerpo [bloque]
        Hijo 1: condición [expresion]
        """
        if nodo.hijos:
            self._analizar_nodo(nodo.hijos[0])

            if len(nodo.hijos) > 1:
                cond = nodo.hijos[1]
                self._evaluar_expresion(cond)
                self._verificar_condicion_booleana(cond, "do-while")

    def _verificar_condicion_booleana(self, cond_nodo: NodoArb, estructura: str) -> None:
        """Verifica que la condición sea estrictamente de tipo 'bool'."""
        tipo = cond_nodo.tipo_dato
        if tipo in ("error", ""):
            return
        if tipo != "bool":
            self._agregar_error(
                ERR_CONDICION_NO_BOOL,
                f"Tipo no booleano en condición de '{estructura}': se requiere una expresión 'bool', se obtuvo '{tipo}'.",
                cond_nodo.linea,
                valor=estructura,
            )

    # ── 5. Entrada y Salida ───────────────────────────────────────────────────

    def _procesar_cin(self, nodo: NodoArb) -> None:
        # Nodo etiqueta: Leer (cin): <id>
        partes = nodo.etiqueta.split(":", 1)
        id_nombre = partes[1].strip() if len(partes) > 1 else ""

        if not id_nombre and nodo.hijos:
            hijo = nodo.hijos[0]
            if hijo.etiqueta.startswith("Id:"):
                id_nombre = hijo.etiqueta.split(":", 1)[1].strip()

        if id_nombre:
            sim = self.tabla.buscar(id_nombre)
            if sim is None:
                self._agregar_error(
                    ERR_VAR_NO_DECLARADA,
                    f"La variable '{id_nombre}' utilizada en 'cin' no ha sido declarada.",
                    nodo.linea,
                    valor=id_nombre,
                )
            else:
                self.tabla.registrar_uso(id_nombre, nodo.linea)
                nodo.tipo_dato = sim.tipo
                nodo.atributos["dir"] = sim.desplazamiento

    def _procesar_cout(self, nodo: NodoArb) -> None:
        for hijo in nodo.hijos:
            self._evaluar_expresion(hijo)

    # ── 6. Expresiones y Atributos Sintetizados ────────────────────────────────

    def _evaluar_expresion(self, nodo: NodoArb) -> None:
        """
        Evalúa recursivamente expresiones calculando y sintetizando
        los atributos 'tipo_dato' y 'valor' (const folding).
        """
        if nodo is None:
            return

        etiq = nodo.etiqueta

        # Números enteros o reales
        if etiq.startswith("Num:"):
            val_txt = etiq.split(":", 1)[1].strip()
            if "." in val_txt:
                nodo.tipo_dato = "float"
                try:
                    nodo.valor = float(val_txt)
                except ValueError:
                    nodo.valor = None
            else:
                nodo.tipo_dato = "int"
                try:
                    nodo.valor = int(val_txt)
                except ValueError:
                    nodo.valor = None
            return

        # Booleanos literales
        if etiq.startswith("Bool:"):
            val_txt = etiq.split(":", 1)[1].strip().lower()
            nodo.tipo_dato = "bool"
            nodo.valor = (val_txt == "true")
            return

        # Cadenas de texto
        if etiq.startswith("Cadena:"):
            nodo.tipo_dato = "string"
            nodo.valor = etiq.split(":", 1)[1].strip().strip('"')
            return

        # Identificadores (uso en expresiones)
        if etiq.startswith("Id:"):
            id_nombre = etiq.split(":", 1)[1].strip()
            sim = self.tabla.buscar(id_nombre)
            if sim is None:
                self._agregar_error(
                    ERR_VAR_NO_DECLARADA,
                    f"La variable '{id_nombre}' no ha sido declarada.",
                    nodo.linea,
                    valor=id_nombre,
                )
                nodo.tipo_dato = "error"
            else:
                self.tabla.registrar_uso(id_nombre, nodo.linea)
                nodo.tipo_dato = sim.tipo
                nodo.atributos["dir"] = sim.desplazamiento
            return

        # Salida combinada (en cout)
        if etiq.startswith("Salida combinada"):
            nodo.tipo_dato = "string"
            for hijo in nodo.hijos:
                self._evaluar_expresion(hijo)
            return

        # Operaciones: Op: <simbolo>
        if etiq.startswith("Op:"):
            op = etiq.split(":", 1)[1].strip()

            # Operador unario '!'
            if op == "!":
                if nodo.hijos:
                    operando = nodo.hijos[0]
                    self._evaluar_expresion(operando)
                    t_op = operando.tipo_dato
                    if t_op in ("error", ""):
                        nodo.tipo_dato = "error"
                    elif t_op != "bool":
                        self._agregar_error(
                            ERR_OPERADOR_INDEBIDO,
                            f"Uso indebido de operador '!': requiere un operando de tipo 'bool', se obtuvo '{t_op}'.",
                            nodo.linea,
                            valor=op,
                        )
                        nodo.tipo_dato = "error"
                    else:
                        nodo.tipo_dato = "bool"
                        if operando.valor is not None:
                            nodo.valor = not operando.valor
                return

            # Operaciones binarias
            if len(nodo.hijos) >= 2:
                izq = nodo.hijos[0]
                der = nodo.hijos[1]
                self._evaluar_expresion(izq)
                self._evaluar_expresion(der)

                t1 = izq.tipo_dato
                t2 = der.tipo_dato
                v1 = izq.valor
                v2 = der.valor

                # Si alguno ya es error, propagar error sin duplicar avisos
                if t1 == "error" or t2 == "error":
                    nodo.tipo_dato = "error"
                    return

                # Aritméticos: +, -, *, /, ^
                if op in _OPS_ARITMETICOS:
                    if t1 == "bool" or t2 == "bool":
                        self._agregar_error(
                            ERR_OPERADOR_INDEBIDO,
                            f"Uso indebido de operador aritmético '{op}' con operando(s) de tipo 'bool'.",
                            nodo.linea,
                            valor=op,
                        )
                        nodo.tipo_dato = "error"
                        return

                    if t1 == "int" and t2 == "int":
                        nodo.tipo_dato = "int"
                        if v1 is not None and v2 is not None:
                            try:
                                if op == "+": nodo.valor = v1 + v2
                                elif op == "-": nodo.valor = v1 - v2
                                elif op == "*": nodo.valor = v1 * v2
                                elif op == "/":
                                    if v2 == 0:
                                        self._agregar_error(
                                            ERR_OPERADOR_INDEBIDO,
                                            "División entre cero en expresión constante.",
                                            nodo.linea,
                                            valor=op,
                                        )
                                        nodo.valor = None
                                    else:
                                        nodo.valor = v1 // v2
                                elif op == "^": nodo.valor = v1 ** v2
                            except Exception:
                                nodo.valor = None
                    else:
                        # Al menos uno es float -> resultado float
                        nodo.tipo_dato = "float"
                        if t1 == "int":
                            izq.conversion = "int -> float"
                        if t2 == "int":
                            der.conversion = "int -> float"

                        if v1 is not None and v2 is not None:
                            try:
                                f1 = float(v1)
                                f2 = float(v2)
                                if op == "+": nodo.valor = f1 + f2
                                elif op == "-": nodo.valor = f1 - f2
                                elif op == "*": nodo.valor = f1 * f2
                                elif op == "/":
                                    if f2 == 0.0:
                                        self._agregar_error(
                                            ERR_OPERADOR_INDEBIDO,
                                            "División entre cero en expresión constante.",
                                            nodo.linea,
                                            valor=op,
                                        )
                                        nodo.valor = None
                                    else:
                                        nodo.valor = f1 / f2
                                elif op == "^": nodo.valor = f1 ** f2
                            except Exception:
                                nodo.valor = None
                    return

                # Módulo: %
                if op == "%":
                    if t1 != "int" or t2 != "int":
                        self._agregar_error(
                            ERR_OPERADOR_INDEBIDO,
                            f"Uso indebido del operador módulo '%': requiere operandos enteros ('int'), pero se obtuvo '{t1}' y '{t2}'.",
                            nodo.linea,
                            valor=op,
                        )
                        nodo.tipo_dato = "error"
                    else:
                        nodo.tipo_dato = "int"
                        if v1 is not None and v2 is not None:
                            if v2 == 0:
                                self._agregar_error(
                                    ERR_OPERADOR_INDEBIDO,
                                    "Módulo con divisor cero en expresión constante.",
                                    nodo.linea,
                                    valor=op,
                                )
                                nodo.valor = None
                            else:
                                nodo.valor = v1 % v2
                    return

                # Relacionales: <, <=, >, >=, ==, !=
                if op in _OPS_RELACIONALES:
                    if t1 in ("int", "float") and t2 in ("int", "float"):
                        nodo.tipo_dato = "bool"
                        if t1 != t2:
                            if t1 == "int": izq.conversion = "int -> float"
                            if t2 == "int": der.conversion = "int -> float"
                        if v1 is not None and v2 is not None:
                            try:
                                if op == "<": nodo.valor = v1 < v2
                                elif op == "<=": nodo.valor = v1 <= v2
                                elif op == ">": nodo.valor = v1 > v2
                                elif op == ">=": nodo.valor = v1 >= v2
                                elif op == "==": nodo.valor = v1 == v2
                                elif op == "!=": nodo.valor = v1 != v2
                            except Exception:
                                nodo.valor = None
                    elif t1 == "bool" and t2 == "bool":
                        if op in ("==", "!="):
                            nodo.tipo_dato = "bool"
                            if v1 is not None and v2 is not None:
                                nodo.valor = (v1 == v2) if op == "==" else (v1 != v2)
                        else:
                            self._agregar_error(
                                ERR_OPERADOR_INDEBIDO,
                                f"Uso indebido de operador relacional '{op}' con operandos booleanos. Solo se permite '==' y '!='.",
                                nodo.linea,
                                valor=op,
                            )
                            nodo.tipo_dato = "error"
                    else:
                        self._agregar_error(
                            ERR_TIPO_INCOMPATIBLE,
                            f"Incompatibilidad de tipos en operador relacional '{op}': no se puede comparar '{t1}' con '{t2}'.",
                            nodo.linea,
                            valor=op,
                        )
                        nodo.tipo_dato = "error"
                    return

                # Lógicos binarios: &&, ||
                if op in ("&&", "||"):
                    if t1 != "bool" or t2 != "bool":
                        self._agregar_error(
                            ERR_OPERADOR_INDEBIDO,
                            f"Uso indebido de operador lógico '{op}': requiere operandos de tipo 'bool', pero se obtuvo '{t1}' y '{t2}'.",
                            nodo.linea,
                            valor=op,
                        )
                        nodo.tipo_dato = "error"
                    else:
                        nodo.tipo_dato = "bool"
                        if v1 is not None and v2 is not None:
                            nodo.valor = (v1 and v2) if op == "&&" else (v1 or v2)
                    return

            return


# ── Función de interfaz pública ───────────────────────────────────────────────

def analyze_semantics(
    arbol: Optional[NodoArb],
) -> Tuple[Optional[NodoArb], TablaSimbolos, List[ErrorSemantico]]:
    """
    Punto de entrada de la Fase 3 (Análisis Semántico).

    Parámetros
    ----------
    arbol : NodoArb | None
        AST generado por el analizador sintáctico.

    Retorna
    -------
    (arbol_anotado, tabla_simbolos, errores_semanticos)
    """
    analizador = AnalizadorSemantico(arbol)
    return analizador.analizar()
