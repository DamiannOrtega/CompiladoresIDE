# compilador/errores.py — Mensajes de error léxico (en español)

from dataclasses import dataclass


# ── Mensajes de error ─────────────────────────────────────────────────────────

CARACTER_INVALIDO     = "Carácter inválido"
NUMERO_MAL_FORMADO    = "Número mal formado"
COMENTARIO_NO_CERRADO = "Comentario sin cerrar"


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
