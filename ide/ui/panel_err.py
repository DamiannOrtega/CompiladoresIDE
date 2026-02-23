# ui/panel_err.py — Panel de errores con navegación al hacer clic

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal
from typing import List
from ide.modelos.datos import Err


class PanelErr(QWidget):
    """Muestra los errores de compilación. Clic en fila → navega al editor."""

    COLS = ["Tipo", "Línea", "Columna", "Mensaje"]

    # Emite el número de línea cuando el usuario hace clic en un error
    ir_a_linea = Signal(int)

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
        self._tabla.setShowGrid(False)

        # Cursor de mano para indicar que las filas son clicables
        self._tabla.setCursor(Qt.PointingHandCursor)

        self._tabla.cellClicked.connect(self._al_clic)
        lay.addWidget(self._tabla)

    def cargar(self, lista: List[Err]):
        self._tabla.setRowCount(0)
        for e in lista:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            items = [
                QTableWidgetItem(e.tipo),
                QTableWidgetItem(str(e.linea)),
                QTableWidgetItem(str(e.col)),
                QTableWidgetItem(e.msg),
            ]
            for it in items:
                it.setForeground(QColor("#f48771"))
            for col, it in enumerate(items):
                self._tabla.setItem(fila, col, it)
        self._tabla.resizeColumnsToContents()

    def limpiar(self):
        self._tabla.setRowCount(0)

    def _al_clic(self, fila: int, _col: int):
        """Emite ir_a_linea con el número de línea del error clicado."""
        item = self._tabla.item(fila, 1)   # columna "Línea"
        if item:
            try:
                self.ir_a_linea.emit(int(item.text()))
            except ValueError:
                pass


# Importación diferida para evitar circular
from PySide6.QtCore import Qt
