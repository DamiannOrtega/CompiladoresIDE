# ui/panel_tm.py — Panel "Código TM" (instrucciones de la Tiny Machine)
#
# Muestra el archivo .tm generado para el programa actual:
#   - Vista de tabla: Dirección | Instrucción | Operandos | Comentario
#   - Vista de archivo: el texto exacto del .tm que se ejecuta
# La tabla se construye leyendo el texto con el mismo analizador que usa el
# simulador (tm_formato.parsear_programa), así lo que se ve es lo que se ejecuta.
# Muestra sólo instrucciones TM; no es código intermedio de tres direcciones (.ci).

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QPlainTextEdit, QStackedWidget, QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from ide.compilador.tm_formato import (
    parsear_programa, lista_ordenada, ErrorFormatoTM, EXTENSIONES,
)

_COLOR_SALTO = "#818cf8"
_COLOR_ES    = "#6ee7b7"
_COLOR_EXT   = "#fbbf24"


class PanelTm(QWidget):
    """Visualización del código TM generado y botón para ejecutarlo."""

    COLS = ["Dirección", "Instrucción", "Operandos", "Comentario"]

    ejecutar_solicitado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ruta = ""
        self._construir_ui()

    def _construir_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        barra = QFrame()
        blay = QHBoxLayout(barra)
        blay.setContentsMargins(8, 5, 8, 5)
        blay.setSpacing(6)

        titulo = QLabel("Código TM")
        titulo.setToolTip("Instrucciones para la máquina objetivo TM (Tiny Machine)")
        titulo.setStyleSheet("font-weight: 600;")
        blay.addWidget(titulo)

        self._lbl_info = QLabel("Sin código generado")
        self._lbl_info.setStyleSheet("color: #94a3b8;")
        blay.addWidget(self._lbl_info)
        blay.addStretch()

        css = "padding: 2px 10px; border-radius: 3px;"
        self._btn_vista = QPushButton("Ver archivo .tm")
        self._btn_vista.setStyleSheet(css)
        self._btn_vista.setToolTip("Alterna entre la tabla de instrucciones y el texto del archivo .tm")
        self._btn_vista.clicked.connect(self._alternar_vista)
        blay.addWidget(self._btn_vista)

        self._btn_ejec = QPushButton("Ejecutar TM")
        self._btn_ejec.setStyleSheet(css)
        self._btn_ejec.setToolTip(
            "Recompila el programa actual, regenera el .tm y lo ejecuta en el simulador (F9)")
        self._btn_ejec.clicked.connect(self.ejecutar_solicitado.emit)
        blay.addWidget(self._btn_ejec)

        lay.addWidget(barra)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)

        self._tabla = QTableWidget(0, len(self.COLS))
        self._tabla.setHorizontalHeaderLabels(self.COLS)
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setShowGrid(False)
        self._tabla.setFont(mono)

        self._texto = QPlainTextEdit()
        self._texto.setReadOnly(True)
        self._texto.setFont(mono)
        self._texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._texto.setPlaceholderText("El código TM aparecerá aquí...")

        self._pila = QStackedWidget()
        self._pila.addWidget(self._tabla)
        self._pila.addWidget(self._texto)
        lay.addWidget(self._pila)

    def _alternar_vista(self):
        if self._pila.currentWidget() is self._tabla:
            self._pila.setCurrentWidget(self._texto)
            self._btn_vista.setText("Ver tabla")
        else:
            self._pila.setCurrentWidget(self._tabla)
            self._btn_vista.setText("Ver archivo .tm")

    def cargar(self, texto: str, ruta: str = ""):
        self._ruta = ruta
        self._texto.setPlainText(texto)
        self._tabla.setRowCount(0)
        try:
            instrucciones, cadenas = parsear_programa(texto)
        except ErrorFormatoTM as ex:
            self._lbl_info.setText(f"Archivo .tm inválido: {ex}")
            return

        for ins in lista_ordenada(instrucciones):
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            comentario = ins.comentario
            if ins.op == "OUTS" and ins.a in cadenas:
                comentario = f"{comentario}  {cadenas[ins.a]!r}"
            items = [
                QTableWidgetItem(str(ins.direccion)),
                QTableWidgetItem(ins.op),
                QTableWidgetItem(ins.operandos()),
                QTableWidgetItem(comentario),
            ]
            items[0].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            color = None
            if ins.op.startswith("J") or (ins.op == "LDA" and ins.r == 7):
                color = _COLOR_SALTO
            elif ins.op in ("IN", "OUT"):
                color = _COLOR_ES
            elif ins.op in EXTENSIONES:
                color = _COLOR_EXT
            if color:
                items[1].setForeground(QColor(color))
            for col, it in enumerate(items):
                self._tabla.setItem(fila, col, it)

        nombre = os.path.basename(ruta) if ruta else "(sin archivo)"
        self._lbl_info.setText(f"{nombre} — {len(instrucciones)} instrucciones")
        self._lbl_info.setToolTip(ruta)

    def limpiar(self):
        self._ruta = ""
        self._tabla.setRowCount(0)
        self._texto.clear()
        self._lbl_info.setText("Sin código generado")
        self._lbl_info.setToolTip("")
