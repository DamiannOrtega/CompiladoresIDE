# ui/editor.py — Editor de código con numeración de líneas y resaltado de sintaxis

import re
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtCore import Qt, QRect, QSize, Signal, QTimer
from PySide6.QtGui import (
    QColor, QPainter, QTextFormat, QFont,
    QSyntaxHighlighter, QTextCharFormat, QTextCursor
)


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
    "kw":      "#c45000",   # naranja oscuro (palabras clave)
    "tipo":    "#0070a8",   # azul petróleo (tipos)
    "num":     "#2e7d32",   # verde oscuro (números)
    "str":     "#b71c1c",   # rojo ladrillo (cadenas)
    "com":     "#8d6e63",   # marrón (comentarios)
    "delim":   "#ea6b00",   # naranja acento (delimitadores)
    "op":      "#1a0d00",   # texto principal (operadores)
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
        "main", "print", "println", "input", "true", "false", "null",
        "and", "or", "not",
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

        # Comentarios de línea (máxima prioridad visual)
        self._reglas.append((r"//[^\n]*", self._fmt("com")))

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

    def highlightBlock(self, texto: str):
        for patron, fmt in self._reglas:
            for m in re.finditer(patron, texto):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._margen = _NumLineas(self)
        self._resaltador = _Resaltador(self.document())
        self._color_margen_bg = QColor("#252526")
        self._color_margen_txt = QColor("#858585")
        self._color_linea_act  = QColor("#2a2d2e")

        self.blockCountChanged.connect(self._actualizar_ancho_margen)
        self.updateRequest.connect(self._actualizar_margen)
        self.cursorPositionChanged.connect(self._emitir_posicion)

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

    # ── Resaltado de línea actual ─────────────────────────────────────

    def _resaltar_linea_actual(self):
        extras = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(self._color_linea_act)
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extras.append(sel)
        self.setExtraSelections(extras)

    # ── Posición del cursor ───────────────────────────────────────────

    def _emitir_posicion(self):
        cur = self.textCursor()
        linea = cur.blockNumber() + 1
        col = cur.columnNumber() + 1
        self.cursor_movido.emit(linea, col)
        self._resaltar_linea_actual()
        self._margen.update()

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
        self.setExtraSelections([sel])
        QTimer.singleShot(400, self._resaltar_linea_actual)
