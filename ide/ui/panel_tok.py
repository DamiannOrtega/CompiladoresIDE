# ui/panel_tok.py — Panel de tokens léxicos

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from typing import List
from ide.modelos.datos import Tok


class PanelTok(QWidget):
    """Muestra la lista de tokens en una tabla."""

    COLS = ["Lexema", "Tipo", "Línea", "Columna"]

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._tabla = QTableWidget(0, len(self.COLS))
        self._tabla.setHorizontalHeaderLabels(self.COLS)
        self._tabla.horizontalHeader().setStretchLastSection(True)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabla.setAlternatingRowColors(True)
        lay.addWidget(self._tabla)

    def cargar(self, lista: List[Tok]):
        self._tabla.setRowCount(0)
        for t in lista:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, QTableWidgetItem(t.lexema))
            self._tabla.setItem(fila, 1, QTableWidgetItem(t.tipo))
            self._tabla.setItem(fila, 2, QTableWidgetItem(str(t.linea)))
            self._tabla.setItem(fila, 3, QTableWidgetItem(str(t.col)))
        self._tabla.resizeColumnsToContents()

    def limpiar(self):
        self._tabla.setRowCount(0)
