# ui/panel_sal.py — Panel de salida de ejecución
#
# Dos áreas:
#   - Salida del programa: inicio de la ejecución, datos introducidos,
#     resultados y mensaje final, sin detalles internos.
#   - Registro técnico (oculto por defecto): ruta del .tm, direcciones de las
#     lecturas, estado final del simulador, instrucciones ejecutadas y
#     registros, para comprobar la ejecución cuando se necesite.

import html

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QPlainTextEdit, QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

_COLOR_DATO  = "#94a3b8"   # gris: datos introducidos
_COLOR_OK    = "#6ee7b7"   # verde: fin correcto
_COLOR_ERROR = "#f48771"   # rojo: error (mismo tono que el panel de errores)
_SEPARADOR   = "─" * 44


class PanelSal(QWidget):
    """Muestra la salida de ejecución del programa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        barra = QFrame()
        blay = QHBoxLayout(barra)
        blay.setContentsMargins(8, 5, 8, 5)
        blay.setSpacing(6)
        titulo = QLabel("Salida del programa")
        titulo.setStyleSheet("font-weight: 600;")
        blay.addWidget(titulo)
        blay.addStretch()
        self._btn_reg = QPushButton("Mostrar registro técnico")
        self._btn_reg.setStyleSheet("padding: 2px 10px; border-radius: 3px;")
        self._btn_reg.setToolTip("Detalles internos de la ejecución en la TM (ruta, lecturas, estado, registros)")
        self._btn_reg.clicked.connect(self._alternar_registro)
        blay.addWidget(self._btn_reg)
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
        self._txt.setPlaceholderText("La salida de ejecución aparecerá aquí...")

        self._reg = QPlainTextEdit()
        self._reg.setReadOnly(True)
        self._reg.setFont(mono)
        self._reg.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._reg.setPlaceholderText("Registro técnico de la ejecución en la TM")
        self._reg.setVisible(False)

        self._split = QSplitter(Qt.Orientation.Vertical)
        self._split.addWidget(self._txt)
        self._split.addWidget(self._reg)
        self._split.setChildrenCollapsible(False)
        lay.addWidget(self._split)

    # ── API general (compatible con versiones anteriores) ─────────────────────

    def cargar(self, texto: str):
        self._txt.setPlainText(texto)

    def limpiar(self):
        self._txt.clear()
        self._reg.clear()

    # ── API de ejecución ──────────────────────────────────────────────────────

    def iniciar_ejecucion(self, programa: str):
        self.limpiar()
        self._linea(f"Ejecución iniciada: {programa}")
        self._linea(_SEPARADOR, _COLOR_DATO)

    def dato_introducido(self, variable: str, valor: str):
        self._linea(f"  > {variable} = {valor}" if variable else f"  > {valor}", _COLOR_DATO)

    def resultado(self, linea: str):
        self._linea(linea)

    def fin_correcto(self):
        self._linea(_SEPARADOR, _COLOR_DATO)
        self._linea("Ejecución finalizada correctamente.", _COLOR_OK)

    def fin_con_error(self, mensaje: str):
        self._linea(_SEPARADOR, _COLOR_DATO)
        self._linea(mensaje, _COLOR_ERROR)

    def registro(self, linea: str):
        self._reg.appendPlainText(linea)

    # ── Internos ──────────────────────────────────────────────────────────────

    def _linea(self, texto: str, color: str = ""):
        estilo = "white-space:pre-wrap;" + (f"color:{color};" if color else "")
        self._txt.appendHtml(f'<span style="{estilo}">{html.escape(texto)}</span>')

    def _alternar_registro(self):
        visible = not self._reg.isVisible()
        self._reg.setVisible(visible)
        self._btn_reg.setText("Ocultar registro técnico" if visible else "Mostrar registro técnico")
        if visible:
            total = max(self._split.height(), 200)
            self._split.setSizes([total * 3 // 5, total * 2 // 5])

    # Texto plano de cada área (usado por pruebas y para copiar)
    def texto_salida(self) -> str:
        return self._txt.toPlainText()

    def texto_registro(self) -> str:
        return self._reg.toPlainText()
