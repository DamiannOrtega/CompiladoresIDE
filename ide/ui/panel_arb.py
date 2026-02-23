# ui/panel_arb.py — Panel del árbol sintáctico

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt
from ide.modelos.datos import NodoArb


class PanelArb(QWidget):
    """Muestra el árbol sintáctico en un QTreeWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._arbol = QTreeWidget()
        self._arbol.setHeaderLabel("Árbol Sintáctico")
        self._arbol.setAlternatingRowColors(True)
        lay.addWidget(self._arbol)

    def cargar(self, raiz: NodoArb):
        self._arbol.clear()
        if raiz is None:
            return
        item_raiz = QTreeWidgetItem([raiz.etiqueta])
        self._arbol.addTopLevelItem(item_raiz)
        self._agregar_hijos(item_raiz, raiz)
        self._arbol.expandAll()

    def _agregar_hijos(self, item_padre: QTreeWidgetItem, nodo: NodoArb):
        for hijo in nodo.hijos:
            item_hijo = QTreeWidgetItem([hijo.etiqueta])
            item_padre.addChild(item_hijo)
            self._agregar_hijos(item_hijo, hijo)

    def limpiar(self):
        self._arbol.clear()
