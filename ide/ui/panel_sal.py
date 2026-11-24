# ui/panel_sal.py — Pestaña "Salida": consola interactiva de la ejecución TM
#
# Áreas:
#   - Consola: como la terminal de un programa en C++; sólo muestra lo que
#     el programa imprime con cout, lo que el usuario escribe y el mensaje final.
#   - Fila de entrada (sólo visible mientras el programa espera un cin):
#     campo de texto y botón "Enviar".
#   - Registro técnico (oculto por defecto): ruta del .tm, lecturas con su
#     instrucción, estado final, instrucciones ejecutadas y registros.
#
# El panel sólo presenta información y emite señales; la ejecución y la
# validación de los datos las realiza el simulador (maquina_tm).

import html
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QPlainTextEdit, QTextEdit, QSplitter, QLineEdit, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer

from ide.ui.etiqueta import EtiquetaRecortable
from PySide6.QtGui import QFont

# Colores pensados para verse sobre fondos oscuros y claros
_COLOR_TENUE     = "#94a3b8"   # detalles
_COLOR_VALOR     = "#fbbf24"   # lo que el usuario escribe
_COLOR_OK        = "#6ee7b7"   # ejecución finalizada correctamente
_COLOR_ERROR     = "#f48771"   # errores y valores inválidos (igual que "Errores")

_ESPERADO = {
    "int":   "un número entero",
    "float": "un número",
    "bool":  "true o false",
}


_RE_VARIABLE = re.compile(r"\bleer\s+([A-Za-z_]\w*)")


def nombre_variable(comentario: str) -> str:
    """Nombre de la variable leída, tomado del comentario de la instrucción IN ("leer x (int)")."""
    m = _RE_VARIABLE.search(comentario or "")
    return m.group(1) if m else ""


def mensaje_valor_invalido(texto: str, tipo: str) -> str:
    """Aviso breve cuando el simulador rechaza lo que se escribió."""
    return f"Entrada no válida, se esperaba {_ESPERADO.get(tipo, 'otro valor')}."


class PanelSal(QWidget):
    """Consola de ejecución del programa en la TM."""

    enviado = Signal(str)          # el usuario envió un valor
    detener_solicitado = Signal()  # el usuario pidió detener la ejecución

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Barra superior ──
        barra = QFrame()
        blay = QHBoxLayout(barra)
        blay.setContentsMargins(8, 5, 8, 5)
        blay.setSpacing(6)
        titulo = QLabel("Consola de ejecución")
        titulo.setStyleSheet("font-weight: 600;")
        blay.addWidget(titulo)
        titulo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        self._lbl_estado = EtiquetaRecortable("")
        self._lbl_estado.setStyleSheet(f"color: {_COLOR_TENUE};")
        blay.addWidget(self._lbl_estado)
        blay.addStretch()

        css = "padding: 2px 10px; border-radius: 3px;"
        self._btn_detener = QPushButton("Detener")
        self._btn_detener.setStyleSheet(css)
        self._btn_detener.setToolTip("Detiene la ejecución del programa en la TM")
        self._btn_detener.clicked.connect(self.detener_solicitado.emit)
        self._btn_detener.setVisible(False)
        blay.addWidget(self._btn_detener)

        self._btn_reg = QPushButton("Registro técnico")
        self._btn_reg.setStyleSheet(css)
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

        # ── Consola + fila de entrada ──
        consola = QWidget()
        clay = QVBoxLayout(consola)
        clay.setContentsMargins(0, 0, 0, 0)
        clay.setSpacing(0)

        # QTextEdit se desplaza por píxeles (QPlainTextEdit lo hace por líneas y,
        # con escalado de pantalla, la última línea podía quedar cortada).
        self._txt = QTextEdit()
        self._txt.setReadOnly(True)
        self._txt.setAcceptRichText(False)
        self._txt.setFont(mono)
        self._txt.setPlaceholderText("Presiona \"Ejecutar TM\" para ejecutar el programa aquí...")
        self._seguir_final = True
        self._txt.verticalScrollBar().rangeChanged.connect(self._rango_cambiado)
        self._txt.verticalScrollBar().valueChanged.connect(self._valor_cambiado)
        clay.addWidget(self._txt)

        self._fila = QFrame()
        flay = QHBoxLayout(self._fila)
        flay.setContentsMargins(8, 5, 8, 6)
        flay.setSpacing(6)
        self._campo = QLineEdit()
        self._campo.setFont(mono)
        self._campo.setPlaceholderText("Escribe y presiona Enter o Enviar")
        self._campo.returnPressed.connect(self._enviar)
        flay.addWidget(self._campo, 1)
        self._btn_enviar = QPushButton("Enviar")
        self._btn_enviar.setStyleSheet(css)
        self._btn_enviar.clicked.connect(self._enviar)
        flay.addWidget(self._btn_enviar)
        self._fila.setVisible(False)
        clay.addWidget(self._fila)

        # ── Registro técnico ──
        self._reg = QPlainTextEdit()
        self._reg.setReadOnly(True)
        self._reg.setFont(mono)
        self._reg.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._reg.setPlaceholderText("Registro técnico de la ejecución en la TM")
        self._reg.setVisible(False)

        self._split = QSplitter(Qt.Orientation.Vertical)
        self._split.addWidget(consola)
        self._split.addWidget(self._reg)
        self._split.setChildrenCollapsible(False)
        lay.addWidget(self._split)

    # ── API general ───────────────────────────────────────────────────────────

    def cargar(self, texto: str):
        self._txt.setPlainText(texto)

    def limpiar(self):
        self._txt.clear()
        self._reg.clear()
        self.ocultar_entrada()

    # ── API de ejecución ──────────────────────────────────────────────────────
    # La consola se comporta como la terminal de un programa en C++: sólo
    # aparece lo que el programa imprime con cout y lo que el usuario escribe.

    def iniciar_ejecucion(self, programa: str):
        self.limpiar()
        self.set_ejecutando(True)

    def set_ejecutando(self, activo: bool):
        self._btn_detener.setVisible(activo)
        self._lbl_estado.setText("— en ejecución" if activo else "")
        if not activo:
            self.ocultar_entrada()

    def solicitar(self, variable: str = "", tipo: str = ""):
        """El programa se detuvo en un cin: muestra el campo para escribir."""
        self.mostrar_entrada()

    def valor_rechazado(self, mensaje: str, variable: str = "", tipo: str = ""):
        """El simulador rechazó lo escrito: avisa y deja escribir de nuevo."""
        self._linea(mensaje, _COLOR_ERROR)
        self.mostrar_entrada()

    def mostrar_entrada(self, *_):
        self._campo.clear()
        self._campo.setEnabled(True)
        self._btn_enviar.setEnabled(True)
        self._fila.setVisible(True)
        self._lbl_estado.setText("— esperando entrada")
        self._campo.setFocus()
        self._ir_al_final()      # el campo reduce el área de texto: mantener visible la última línea

    def ocultar_entrada(self):
        self._fila.setVisible(False)
        self._campo.clear()
        if self._btn_detener.isVisible():
            self._lbl_estado.setText("— en ejecución")

    def esperando_dato(self) -> bool:
        return self._fila.isVisible()

    def valor_introducido(self, variable: str, valor: str):
        """Eco de lo que el usuario escribió, como en una terminal."""
        self._linea(valor, _COLOR_VALOR)

    def resultado(self, linea: str):
        self._linea(linea)

    def fin_correcto(self):
        self.set_ejecutando(False)
        self._linea("")
        self._linea("Ejecución finalizada correctamente.", _COLOR_OK)

    def fin_con_error(self, mensaje: str):
        self.set_ejecutando(False)
        self._linea("")
        self._linea(mensaje, _COLOR_ERROR)

    def registro(self, linea: str):
        self._reg.appendPlainText(linea)

    # ── Internos ──────────────────────────────────────────────────────────────

    def _enviar(self):
        if not self._fila.isVisible():
            return
        texto = self._campo.text()
        self._campo.setEnabled(False)
        self._btn_enviar.setEnabled(False)
        self.ocultar_entrada()
        self.enviado.emit(texto)

    def _linea(self, texto: str, color: str = ""):
        estilo = "white-space:pre-wrap;" + (f"color:{color};" if color else "")
        self._txt.append(f'<span style="{estilo}">{html.escape(texto)}</span>')
        self._ir_al_final()

    # ── Desplazamiento automático ─────────────────────────────────────────────
    # La consola sigue la última línea, como una terminal. Si el usuario sube
    # con la rueda para leer algo anterior, se respeta su posición hasta que
    # llegue texto nuevo o el programa pida un dato.

    def _ir_al_final(self):
        self._seguir_final = True
        self._bajar()
        # Repetir cuando Qt termine de acomodar el texto (el alto real se
        # calcula después de agregar la línea o de mostrar el campo de entrada)
        QTimer.singleShot(0, self._bajar)

    def _bajar(self):
        barra = self._txt.verticalScrollBar()
        barra.setValue(barra.maximum())

    def _rango_cambiado(self, _minimo: int, maximo: int):
        # Llega texto nuevo o el área se encoge (p. ej. al aparecer el campo)
        if self._seguir_final:
            self._txt.verticalScrollBar().setValue(maximo)

    def _valor_cambiado(self, valor: int):
        self._seguir_final = valor >= self._txt.verticalScrollBar().maximum() - 1

    def _alternar_registro(self):
        visible = not self._reg.isVisible()
        self._reg.setVisible(visible)
        self._btn_reg.setText("Ocultar registro" if visible else "Registro técnico")
        if visible:
            total = max(self._split.height(), 200)
            self._split.setSizes([total * 3 // 5, total * 2 // 5])

    # Texto plano de cada área (usado por pruebas y para copiar)
    def texto_salida(self) -> str:
        return self._txt.toPlainText()

    def texto_registro(self) -> str:
        return self._reg.toPlainText()
