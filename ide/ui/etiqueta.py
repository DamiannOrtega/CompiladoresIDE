# ui/etiqueta.py — Etiqueta que se recorta con "…" cuando falta espacio
#
# Se usa en las barras de los paneles para que un título largo no obligue al
# panel a ser más ancho: se muestra completo si cabe y, si no, termina en "…"
# (el texto completo queda en el tooltip).

from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QSize


class EtiquetaRecortable(QLabel):
    def __init__(self, texto: str = "", parent=None):
        super().__init__(parent)
        self._completo = ""
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setText(texto)

    def setText(self, texto: str):
        self._completo = texto or ""
        self.setToolTip(self._completo)
        self.updateGeometry()
        self._actualizar()

    def text(self) -> str:
        return self._completo

    def sizeHint(self) -> QSize:
        alto = super().sizeHint().height()
        return QSize(self.fontMetrics().horizontalAdvance(self._completo) + 6, alto)

    def minimumSizeHint(self) -> QSize:
        alto = super().minimumSizeHint().height()
        return QSize(min(40, self.sizeHint().width()), alto)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._actualizar()

    def _actualizar(self):
        visible = self.fontMetrics().elidedText(self._completo, Qt.TextElideMode.ElideRight,
                                                max(self.width() - 2, 0))
        QLabel.setText(self, visible)
