# ui/panel_sim.py — Panel de tabla de símbolos

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from typing import List
from ide.modelos.datos import Sim


class PanelSim(QWidget):
    """Muestra la tabla de símbolos."""

    COLS = ["Nombre", "Tipo", "Ámbito", "Línea"]

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

    def cargar(self, lista: List[Sim]):
        self._tabla.setRowCount(0)
        for s in lista:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, QTableWidgetItem(s.nombre))
            self._tabla.setItem(fila, 1, QTableWidgetItem(s.tipo))
            self._tabla.setItem(fila, 2, QTableWidgetItem(s.ambito))
            self._tabla.setItem(fila, 3, QTableWidgetItem(str(s.linea)))
        self._tabla.resizeColumnsToContents()

    def limpiar(self):
        self._tabla.setRowCount(0)
