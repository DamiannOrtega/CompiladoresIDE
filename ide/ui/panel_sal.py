# ui/panel_sal.py — Panel de salida de ejecución

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PySide6.QtGui import QColor


class PanelSal(QWidget):
    """Muestra la salida de ejecución del programa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._txt = QPlainTextEdit()
        self._txt.setReadOnly(True)
        self._txt.setPlaceholderText("La salida de ejecución aparecerá aquí...")
        lay.addWidget(self._txt)

    def cargar(self, texto: str):
        self._txt.setPlainText(texto)

    def limpiar(self):
        self._txt.clear()
