# ui/panel_archivos.py — Explorador de archivos

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel
from PySide6.QtCore import QDir, Signal


class PanelArchivos(QWidget):
    """Explorador de archivos del directorio de trabajo."""

    # Emite la ruta del archivo seleccionado con doble clic
    archivo_abierto = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._modelo = QFileSystemModel()
        self._modelo.setRootPath(QDir.currentPath())
        self._modelo.setNameFilters(["*.src", "*.txt", "*.json", "*.py"])
        self._modelo.setNameFilterDisables(False)

        self._vista = QTreeView()
        self._vista.setModel(self._modelo)
        self._vista.setRootIndex(self._modelo.index(QDir.currentPath()))
        self._vista.setColumnHidden(1, True)  # tamaño
        self._vista.setColumnHidden(2, True)  # tipo
        self._vista.setColumnHidden(3, True)  # fecha
        self._vista.setHeaderHidden(True)
        self._vista.doubleClicked.connect(self._al_doble_clic)
        lay.addWidget(self._vista)

    def set_directorio(self, ruta: str):
        self._modelo.setRootPath(ruta)
        self._vista.setRootIndex(self._modelo.index(ruta))

    def _al_doble_clic(self, indice):
        ruta = self._modelo.filePath(indice)
        if os.path.isfile(ruta):
            self.archivo_abierto.emit(ruta)
