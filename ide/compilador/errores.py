# compilador/errores.py — Mensajes de error (léxico y sintáctico)

from dataclasses import dataclass, field


# ── Constantes de tipo de error ───────────────────────────────────────────────

CARACTER_INVALIDO     = "Carácter inválido"
NUMERO_MAL_FORMADO    = "Número mal formado"
COMENTARIO_NO_CERRADO = "Comentario sin cerrar"
CADENA_NO_CERRADA     = "Cadena sin cerrar"
SINTAXIS_ERROR        = "Error sintáctico"

# ── Constantes de errores semánticos (Fase 3) ─────────────────────────────────
ERR_VAR_NO_DECLARADA       = "Uso de variable no declarada"
ERR_DECL_DUPLICADA         = "Declaración duplicada"
ERR_TIPO_INCOMPATIBLE      = "Incompatibilidad de tipos"
ERR_CONVERSION_INVALIDA    = "Conversión de tipos no válida"
ERR_OPERADOR_INDEBIDO      = "Uso indebido de operadores"
ERR_ASIGNACION_INCOMPATIBLE = "Inconsistencia de tipos en asignación"
ERR_CONDICION_NO_BOOL      = "Tipo no booleano en condición"


# ── Estructura de un error léxico ─────────────────────────────────────────────

@dataclass
class ErrorLexico:
    """Representa un error encontrado durante el análisis léxico."""
    error: str     # mensaje de error en español
    valor: str     # lexema o carácter problemático
    linea: int     # línea donde ocurrió (inicia en 1)
    columna: int   # columna donde ocurrió (inicia en 1)

    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "valor": self.valor,
            "linea": self.linea,
            "columna": self.columna,
        }


# ── Estructura de un error sintáctico ─────────────────────────────────────────

@dataclass
class ErrorSintactico:
    """Representa un error encontrado durante el análisis sintáctico."""
    error: str        # tipo (SINTAXIS_ERROR)
    msg: str          # descripción detallada
    linea: int        # línea donde ocurrió
    columna: int      # columna donde ocurrió
    valor: str = ""   # token problemático

    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "msg": self.msg,
            "valor": self.valor,
            "linea": self.linea,
            "columna": self.columna,
        }


# ── Estructura de un error semántico ─────────────────────────────────────────

@dataclass
class ErrorSemantico:
    """Representa un error encontrado durante el análisis semántico."""
    error: str        # categoría del error semántico
    msg: str          # descripción detallada
    linea: int        # línea donde ocurrió
    columna: int = 0  # columna donde ocurrió (si está disponible)
    valor: str = ""   # identificador u operador involucrado

    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "msg": self.msg,
            "valor": self.valor,
            "linea": self.linea,
            "columna": self.columna,
        }
