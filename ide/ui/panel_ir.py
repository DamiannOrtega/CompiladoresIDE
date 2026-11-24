# ui/panel_ir.py — Pestaña "Código intermedio" (tres direcciones, archivo .ci)
#
# Muestra el código intermedio de tres direcciones generado desde el árbol
# anotado: temporales (t1, t2, ...), etiquetas (L1, L2, ...), read/write y
# saltos if_false/goto. Es una salida paralela al código TM: el simulador no
# ejecuta este código, sólo el archivo .tm de la pestaña "Código TM".

import os
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPlainTextEdit,
)
from PySide6.QtGui import QFont

from ide.ui.etiqueta import EtiquetaRecortable


class PanelIr(QWidget):
    """Muestra el código intermedio de tres direcciones (.ci)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        barra = QFrame()
        blay = QHBoxLayout(barra)
        blay.setContentsMargins(8, 5, 8, 5)
        blay.setSpacing(6)
        titulo = EtiquetaRecortable("Código intermedio de tres direcciones")
        titulo.setStyleSheet("font-weight: 600;")
        blay.addWidget(titulo)
        self._lbl_info = EtiquetaRecortable("Sin código generado")
        self._lbl_info.setStyleSheet("color: #94a3b8;")
        blay.addWidget(self._lbl_info)
        blay.addStretch()
        lay.addWidget(barra)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self._txt = QPlainTextEdit()
        self._txt.setReadOnly(True)
        self._txt.setFont(mono)
        self._txt.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._txt.setPlaceholderText(
            "El código intermedio (t1 = a + b, if_false t2 goto L1, ...) aparecerá aquí "
            "al generar el código (F8) o al ejecutar (F9)."
        )
        lay.addWidget(self._txt)

    def cargar(self, texto: str, ruta: str = ""):
        self._txt.setPlainText(texto)
        instrucciones = sum(1 for l in texto.splitlines() if re.match(r"\s*\d+:", l))
        etiquetas = sum(1 for l in texto.splitlines() if l.startswith("L") and l.rstrip().endswith(":"))
        nombre = os.path.basename(ruta) if ruta else ""
        info = f"{instrucciones} instrucciones, {etiquetas} etiquetas"
        self._lbl_info.setText(f"{nombre} — {info}" if nombre else info)
        self._lbl_info.setToolTip(ruta)

    def limpiar(self):
        self._txt.clear()
        self._lbl_info.setText("Sin código generado")
        self._lbl_info.setToolTip("")
