# ui/editor.py — Editor de código con numeración de líneas y resaltado de sintaxis

import re
from typing import List
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtCore import Qt, QRect, QSize, Signal, QTimer
from PySide6.QtGui import (
    QColor, QPainter, QTextFormat, QFont,
    QSyntaxHighlighter, QTextCharFormat, QTextCursor, QKeySequence
)
from PySide6.QtWidgets import QApplication
from ide.modelos.datos import Err


# ── Colores de resaltado por tema ─────────────────────────────────────────────
# Cada tema define su paleta de resaltado.
# Se actualiza llamando a _Resaltador.set_colores(dict).

_COLORES_OSCURO = {
    "kw":      "#569cd6",   # palabras clave
    "tipo":    "#4ec9b0",   # tipos de dato
    "num":     "#b5cea8",   # números
    "str":     "#ce9178",   # cadenas
    "com":     "#6a9955",   # comentarios
    "delim":   "#ffd700",   # delimitadores { } ( ) ;
    "op":      "#d4d4d4",   # operadores = + - * /
}

_COLORES_CLARO = {
    "kw":      "#0000ff",
    "tipo":    "#267f99",
    "num":     "#098658",
    "str":     "#a31515",
    "com":     "#008000",
    "delim":   "#795e26",
    "op":      "#000000",
}

_COLORES_AZUL = {
    "kw":      "#79b8ff",
    "tipo":    "#56d364",
    "num":     "#f0e68c",
    "str":     "#f97583",
    "com":     "#6a737d",
    "delim":   "#e3b341",
    "op":      "#c9d1d9",
}

_COLORES_CONTRASTE = {
    "kw":      "#0056B3",   # azul cobalto            — keywords (class, import, return…)
    "tipo":    "#AF00DB",   # rosa fuerte / magenta   — tipos y clases
    "num":     "#0000FF",   # azul puro               — literales numéricos
    "str":     "#D47000",   # naranja oscuro          — cadenas de texto
    "com":     "#008000",   # verde bosque            — comentarios
    "delim":   "#0070C1",   # azul eléctrico          — funciones y métodos
    "op":      "#000000",   # negro                   — variables, propiedades y operadores
}

COLORES_TEMA: dict[str, dict] = {
    "Oscuro":          _COLORES_OSCURO,
    "Claro":           _COLORES_CLARO,
    "Azul":            _COLORES_AZUL,
    "Alto Contraste":  _COLORES_CONTRASTE,
}


class _Resaltador(QSyntaxHighlighter):
    """Resaltado de sintaxis configurable por tema."""

    _KEYWORDS = [
        "int", "float", "double", "char", "bool", "void", "string",
        "if", "else", "while", "for", "do", "return", "break", "continue",
        "switch", "case", "default",
        "main", "print", "println", "input", "true", "false", "null",
        "and", "or", "not",
        "cin", "cout", "end",
    ]
    _TIPOS = ["int", "float", "double", "char", "bool", "void", "string"]

    def __init__(self, doc):
        super().__init__(doc)
        self._cols = _COLORES_OSCURO
        self._construir_reglas()

    def set_colores(self, cols: dict):
        self._cols = cols
        self._construir_reglas()
        self.rehighlight()

    def _fmt(self, clave: str, negrita: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(self._cols.get(clave, "#d4d4d4")))
        if negrita:
            f.setFontWeight(QFont.Bold)
        return f

    def _construir_reglas(self):
        self._reglas = []

        # Cadenas entre comillas dobles
        self._reglas.append((r'"[^"\\]*(?:\\.[^"\\]*)*"', self._fmt("str")))

        # Cadenas entre comillas simples
        self._reglas.append((r"'[^'\\]*(?:\\.[^'\\]*)*'", self._fmt("str")))

        # Tipos (antes que keywords para no solapar)
        for t in self._TIPOS:
            self._reglas.append((rf"\b{t}\b", self._fmt("tipo", True)))

        # Keywords
        kw_no_tipo = [k for k in self._KEYWORDS if k not in self._TIPOS]
        for kw in kw_no_tipo:
            self._reglas.append((rf"\b{kw}\b", self._fmt("kw", True)))

        # Números (enteros y decimales)
        self._reglas.append((r"\b\d+(\.\d+)?\b", self._fmt("num")))

        # Delimitadores
        self._reglas.append((r"[{}()\[\];,]", self._fmt("delim")))

        # Operadores
        self._reglas.append((r"[+\-*/=<>!&|^~%]", self._fmt("op")))

        # Formato de comentario — guardado para aplicar AL FINAL (máxima prioridad)
        self._fmt_com = self._fmt("com")

    def highlightBlock(self, texto: str):
        # ── Paso 1: todas las reglas normales (keywords, ops, delimitadores…)
        for patron, fmt in self._reglas:
            for m in re.finditer(patron, texto):
                self.setFormat(m.start(), m.end() - m.start(), fmt)

        # ── Paso 2: comentarios de UNA LÍNEA (//) — se aplican DESPUÉS
        # para que sobreescriban cualquier color anterior en ese tramo.
        for m in re.finditer(r"//[^\n]*", texto):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt_com)


        # ── Paso 3: comentarios de bloque /* */ (multilínea) — máxima prioridad
        # Estado 0 = normal, estado 1 = dentro de comentario de bloque
        self.setCurrentBlockState(0)

        if self.previousBlockState() == 1:
            inicio_com  = 0
            buscar_desde = 0   # ya estamos DENTRO del comentario: buscar */ desde el inicio
        else:
            inicio_com = texto.find("/*")
            if inicio_com == -1:
                return
            buscar_desde = inicio_com + 2  # saltar los dos chars del abridor

        while inicio_com >= 0:
            fin_com = texto.find("*/", buscar_desde)
            if fin_com == -1:
                # No cierra en esta línea → marcamos estado 1
                self.setCurrentBlockState(1)
                self.setFormat(inicio_com, len(texto) - inicio_com, self._fmt_com)
                break
            else:
                # Cierra en esta misma línea
                self.setFormat(inicio_com, fin_com + 2 - inicio_com, self._fmt_com)
                # Buscar siguiente apertura /* tras el cierre
                inicio_com   = texto.find("/*", fin_com + 2)
                buscar_desde = inicio_com + 2 if inicio_com >= 0 else -1



# ── Margen de números de línea ────────────────────────────────────────────────

class _NumLineas(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._ed = editor

    def sizeHint(self):
        return QSize(self._ed.ancho_margen(), 0)

    def paintEvent(self, evento):
        self._ed.pintar_margen(evento)


# ── Editor principal ──────────────────────────────────────────────────────────

class EditorCodigo(QPlainTextEdit):
    """Editor principal con números de línea, resaltado y navegación."""

    # Emite (linea, columna) cuando cambia el cursor
    cursor_movido = Signal(int, int)

    _TAM_FUENTE_DEF = 12   # tamaño de fuente por defecto (pt)
    _TAM_FUENTE_MIN = 6
    _TAM_FUENTE_MAX = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self._margen = _NumLineas(self)
        self._resaltador = _Resaltador(self.document())
        self._color_margen_bg = QColor("#252526")
        self._color_margen_txt = QColor("#858585")
        self._color_linea_act  = QColor("#2a2d2e")
        self._sels_error: list = []   # ExtraSelections de subrayado de error
        self._tam_fuente = self._TAM_FUENTE_DEF

        self.blockCountChanged.connect(self._actualizar_ancho_margen)
        self.updateRequest.connect(self._actualizar_margen)
        self.cursorPositionChanged.connect(self._emitir_posicion)
        self.textChanged.connect(self.limpiar_errores)  # limpiar al editar

        self._actualizar_ancho_margen(0)
        self._resaltar_linea_actual()

        self.setTabStopDistance(28)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    # ── Tema ──────────────────────────────────────────────────────────

    def set_tema(self, nombre_tema: str, paleta: dict):
        """Actualiza colores del editor y resaltado según el tema."""
        self._color_margen_bg  = QColor(paleta.get("bg2",  "#252526"))
        self._color_margen_txt = QColor(paleta.get("txt2", "#858585"))
        self._color_linea_act  = QColor(paleta.get("hover", "#2a2d2e"))
        cols = COLORES_TEMA.get(nombre_tema, _COLORES_OSCURO)
        self._resaltador.set_colores(cols)
        self._resaltar_linea_actual()
        self._margen.update()

    # ── Margen de números de línea ────────────────────────────────────

    def ancho_margen(self) -> int:
        digitos = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digitos

    def _actualizar_ancho_margen(self, _):
        self.setViewportMargins(self.ancho_margen(), 0, 0, 0)

    def _actualizar_margen(self, rect, dy):
        if dy:
            self._margen.scroll(0, dy)
        else:
            self._margen.update(0, rect.y(), self._margen.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._actualizar_ancho_margen(0)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        cr = self.contentsRect()
        self._margen.setGeometry(
            QRect(cr.left(), cr.top(), self.ancho_margen(), cr.height())
        )

    def pintar_margen(self, evento):
        painter = QPainter(self._margen)
        painter.fillRect(evento.rect(), self._color_margen_bg)

        bloque = self.firstVisibleBlock()
        num = bloque.blockNumber()
        top = int(self.blockBoundingGeometry(bloque)
                  .translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(bloque).height())

        cur_num = self.textCursor().blockNumber()

        while bloque.isValid() and top <= evento.rect().bottom():
            if bloque.isVisible() and bottom >= evento.rect().top():
                # Línea activa más brillante
                if num == cur_num:
                    painter.setPen(QColor("#c6c6c6"))
                else:
                    painter.setPen(self._color_margen_txt)
                painter.drawText(
                    0, top, self._margen.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignRight, str(num + 1)
                )
            bloque = bloque.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(bloque).height())
            num += 1

    # ── Subrayado ondulado de errores léxicos ────────────────────────

    def marcar_errores(self, errores: List[Err]):
        """
        Dibuja un subrayado ondulado rojo bajo cada error léxico.

        Parámetros
        ----------
        errores : List[Err]
            Lista de errores con .linea, .col y .msg  (msg contiene el lexema
            entre comillas simples como   "Número mal formado: '32.'").
        """
        doc = self.document()
        self._sels_error = []

        # Formato: subrayado ondulado rojo
        fmt_err = QTextCharFormat()
        fmt_err.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        fmt_err.setUnderlineColor(QColor("#f14c4c"))

        for e in errores:
            # Extraer el lexema del mensaje  (viene como  "…: 'lexema'")
            lexema = ""
            if "'" in e.msg:
                partes = e.msg.split("'")
                if len(partes) >= 2:
                    lexema = partes[1]   # texto entre las primeras comillas simples
            longitud = max(len(lexema), 1)   # al menos 1 carácter

            # Localizar el bloque (línea) — linea está en base 1
            bloque = doc.findBlockByLineNumber(e.linea - 1)
            if not bloque.isValid():
                continue

            # Posición absoluta = inicio del bloque + (col - 1)
            pos_inicio = bloque.position() + max(e.col - 1, 0)
            pos_fin    = pos_inicio + longitud

            cur = QTextCursor(doc)
            cur.setPosition(pos_inicio)
            cur.setPosition(pos_fin, QTextCursor.KeepAnchor)

            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            sel.format  = fmt_err
            self._sels_error.append(sel)

        self._aplicar_extra_selections()

    def limpiar_errores(self):
        """Quita todos los subrayados de error del editor."""
        if self._sels_error:
            self._sels_error = []
            self._aplicar_extra_selections()

    def _aplicar_extra_selections(self):
        """Combina la selección de línea activa con los subrayados de error."""
        extras = list(self._sels_error)   # primero errores (debajo)
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(self._color_linea_act)
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extras.append(sel)            # línea activa encima
        self.setExtraSelections(extras)

    # ── Resaltado de línea actual ─────────────────────────────────────

    def _resaltar_linea_actual(self):
        self._aplicar_extra_selections()

    # ── Posición del cursor ───────────────────────────────────────────

    def _emitir_posicion(self):
        cur = self.textCursor()
        linea = cur.blockNumber() + 1
        col = cur.columnNumber() + 1
        self.cursor_movido.emit(linea, col)
        self._resaltar_linea_actual()
        self._margen.update()

    # ── Zoom de fuente ────────────────────────────────────────────────

    def _aplicar_zoom(self, nuevo_tam: int):
        """Aplica el tamaño de fuente dado y reajusta el margen."""
        nuevo_tam = max(self._TAM_FUENTE_MIN, min(self._TAM_FUENTE_MAX, nuevo_tam))
        if nuevo_tam == self._tam_fuente:
            return
        self._tam_fuente = nuevo_tam
        fuente = self.font()
        fuente.setPointSize(nuevo_tam)
        self.setFont(fuente)
        self._actualizar_ancho_margen(0)
        self._margen.update()

    def zoom_in(self):
        self._aplicar_zoom(self._tam_fuente + 1)

    def zoom_out(self):
        self._aplicar_zoom(self._tam_fuente - 1)

    def zoom_reset(self):
        self._aplicar_zoom(self._TAM_FUENTE_DEF)

    def keyPressEvent(self, evento):
        """Intercepta Ctrl++, Ctrl+- y Ctrl+0 para el zoom."""
        mod = evento.modifiers()
        key = evento.key()
        if mod == Qt.ControlModifier:
            if key in (Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()
                return
            if key == Qt.Key_Minus:
                self.zoom_out()
                return
            if key == Qt.Key_0:
                self.zoom_reset()
                return
        super().keyPressEvent(evento)

    def wheelEvent(self, evento):
        """Ctrl+Rueda del ratón → zoom."""
        if evento.modifiers() == Qt.ControlModifier:
            delta = evento.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            evento.accept()
            return
        super().wheelEvent(evento)

    # ── Navegación a línea ────────────────────────────────────────────

    def ir_a_linea(self, num_linea: int):
        """Mueve el cursor a la línea indicada y la resalta brevemente."""
        bloque = self.document().findBlockByLineNumber(num_linea - 1)
        if not bloque.isValid():
            return

        cur = self.textCursor()
        cur.setPosition(bloque.position())
        cur.select(QTextCursor.LineUnderCursor)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

        # Flash: resaltar la línea con color de acento brevemente
        self._flash_linea(cur)

    def _flash_linea(self, cur: QTextCursor):
        """Resalta la línea seleccionada brevemente (400ms)."""
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#264f78"))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = cur
        # Mantener los subrayados de error durante el flash
        self.setExtraSelections(self._sels_error + [sel])
        QTimer.singleShot(400, self._resaltar_linea_actual)
