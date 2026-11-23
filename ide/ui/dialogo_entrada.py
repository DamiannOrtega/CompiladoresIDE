# ui/dialogo_entrada.py — Ventana "Entrada de datos" para las lecturas (cin)
#
# Se muestra cuando el programa en ejecución necesita un valor. Presenta el
# nombre de la variable y el tipo esperado en lenguaje comprensible, y valida
# el valor ANTES de cerrarse usando la misma regla que aplica el simulador
# (maquina_tm), de modo que el usuario puede corregir sin perder el dato.

import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt

from ide.compilador.maquina_tm import _leer_valor
from ide.compilador.tm_formato import TIPO_IN

DESCRIPCION_TIPO = {
    "int":   "Número entero (por ejemplo: 25 o -3)",
    "float": "Número real (por ejemplo: 3.5 o 10)",
    "bool":  "Valor lógico: true o false (también 1 o 0)",
}

_AYUDA_ERROR = {
    "int":   "no es un número entero. Escribe un número sin decimales, por ejemplo 25.",
    "float": "no es un número válido. Usa punto decimal, por ejemplo 3.5.",
    "bool":  "no es un valor lógico. Escribe true o false (o 1 o 0).",
}

_RE_VARIABLE = re.compile(r"\bleer\s+([A-Za-z_]\w*)")


def nombre_variable(comentario: str) -> str:
    """Obtiene el nombre de la variable del comentario de la lectura ("leer x (int)")."""
    m = _RE_VARIABLE.search(comentario or "")
    return m.group(1) if m else ""


def mensaje_valor_invalido(texto: str, tipo: str) -> str:
    valor = texto.strip()
    if not valor:
        return "Escribe un valor antes de aceptar."
    return f"El valor «{valor}» {_AYUDA_ERROR.get(tipo, 'no es válido.')}"


class DialogoEntrada(QDialog):
    """Pide al usuario el valor de una variable durante la ejecución."""

    def __init__(self, variable: str, tipo: str, error_previo: str = "", parent=None):
        super().__init__(parent)
        self._tipo = tipo
        self.setWindowTitle("Entrada de datos")
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(10)

        msg = QLabel("El programa necesita un valor para continuar.")
        msg.setStyleSheet("font-weight: 600;")
        lay.addWidget(msg)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(6)
        lbl_var = QLabel(variable or "(sin nombre)")
        lbl_var.setStyleSheet("font-family: Consolas, monospace; font-weight: 600;")
        form.addRow("Variable:", lbl_var)
        form.addRow("Tipo esperado:", QLabel(DESCRIPCION_TIPO.get(tipo, tipo)))
        self._campo = QLineEdit()
        self._campo.setPlaceholderText("Escribe el valor y presiona Enter")
        form.addRow("Valor:", self._campo)
        lay.addLayout(form)

        self._lbl_error = QLabel(error_previo)
        self._lbl_error.setWordWrap(True)
        self._lbl_error.setStyleSheet("color: #f48771;")
        self._lbl_error.setVisible(bool(error_previo))
        lay.addWidget(self._lbl_error)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Aceptar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self._aceptar)
        botones.rejected.connect(self.reject)
        lay.addWidget(botones)

        self._campo.textEdited.connect(lambda _: self._lbl_error.setVisible(False))
        self._campo.setFocus()

    def valor(self) -> str:
        return self._campo.text().strip()

    def _aceptar(self):
        texto = self._campo.text()
        try:
            _leer_valor(texto, TIPO_IN.get(self._tipo, 0))
        except ValueError:
            self._lbl_error.setText(mensaje_valor_invalido(texto, self._tipo))
            self._lbl_error.setVisible(True)
            self._campo.selectAll()
            self._campo.setFocus()
            return
        self.accept()
