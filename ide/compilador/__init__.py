# compilador/__init__.py
# Expone las funciones principales del compilador.

from ide.compilador.lexico import analyze
from ide.compilador.sintatico import parse
from ide.compilador.tokens import Token
from ide.compilador.errores import ErrorLexico, ErrorSintactico

__all__ = ["analyze", "parse", "Token", "ErrorLexico", "ErrorSintactico"]
