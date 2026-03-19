# compilador/__init__.py
# Expone la función principal del analizador léxico.

from ide.compilador.lexico import analyze
from ide.compilador.tokens import Token
from ide.compilador.errores import ErrorLexico

__all__ = ["analyze", "Token", "ErrorLexico"]
