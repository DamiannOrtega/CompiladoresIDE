# ui/panel_arb.py — Panel del árbol sintáctico abstracto (AST)
#
# Diseño: tabla de 3 columnas (Nodo | Categoría | Línea)
# Sin iconos emoji. Colores sutiles por categoría.
# Colapsable, expandible automáticamente, abre en ventana independiente.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QFrame,
    QMainWindow, QHeaderView, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ide.modelos.datos import NodoArb


# ── Mapas de metadatos por tipo de nodo ──────────────────────────────────────

_CATEGORIAS: dict[str, str] = {
    "prog":   "Programa",
    "decl":   "Declaración",
    "stmt":   "Sentencia",
    "bloque": "Bloque",
    "expr":   "Expresión",
    "":       "—",
}

# Colores que funcionan sobre fondos oscuros y claros
_COLORES: dict[str, str] = {
    "prog":   "#93c5fd",   # azul suave
    "decl":   "#6ee7b7",   # verde menta
    "stmt":   "#818cf8",   # índigo
    "bloque": "#c4b5fd",   # violeta claro
    "expr":   "#fde68a",   # ámbar suave
    "":       "#94a3b8",   # gris slate
}


# ── Ventana independiente ─────────────────────────────────────────────────────

class _VentanaArbol(QMainWindow):
    """Ventana flotante para ver el árbol a pantalla completa."""

    def __init__(self, raiz: NodoArb, errores=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Árbol Sintáctico — Vista completa")
        self.resize(1100, 750)
        panel = PanelArb(_standalone=True)
        panel.cargar(raiz, errores or [])
        self.setCentralWidget(panel)


# ── Panel principal ───────────────────────────────────────────────────────────

class PanelArb(QWidget):
    """
    Panel del árbol sintáctico abstracto.

    Características:
    - 3 columnas: Nodo | Categoría | Línea
    - Expansión automática al cargar
    - Botones Expandir todo / Colapsar todo
    - Botón "Abrir en ventana" para pantalla completa
    - Colores por categoría (sin emoji)
    """

    def __init__(self, parent=None, _standalone: bool = False):
        super().__init__(parent)
        self._raiz_actual: NodoArb | None = None
        self._errores_actual: list = []          # lista de Err con errores sintácticos
        self._ventana_ext: _VentanaArbol | None = None
        self._standalone = _standalone
        self._construir_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _construir_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Barra de herramientas ─────────────────────────────────────────
        barra = QFrame()
        barra.setFrameShape(QFrame.Shape.NoFrame)
        blay = QHBoxLayout(barra)
        blay.setContentsMargins(8, 5, 8, 5)
        blay.setSpacing(6)

        titulo = QLabel("Árbol Sintáctico Abstracto")
        titulo.setStyleSheet("font-weight: 600;")
        blay.addWidget(titulo)
        blay.addStretch()

        _btn_css = "padding: 2px 10px; border-radius: 3px;"

        self._btn_exp = QPushButton("Expandir todo")
        self._btn_exp.setStyleSheet(_btn_css)
        self._btn_exp.setToolTip("Expandir todos los nodos del árbol")
        self._btn_exp.clicked.connect(self._expandir_todo)
        blay.addWidget(self._btn_exp)

        self._btn_col = QPushButton("Colapsar todo")
        self._btn_col.setStyleSheet(_btn_css)
        self._btn_col.setToolTip("Colapsar todos los nodos del árbol")
        self._btn_col.clicked.connect(self._colapsar_todo)
        blay.addWidget(self._btn_col)

        if not self._standalone:
            self._btn_win = QPushButton("Abrir en ventana")
            self._btn_win.setStyleSheet(_btn_css)
            self._btn_win.setToolTip(
                "Abre el árbol en una ventana independiente para visualización a pantalla completa"
            )
            self._btn_win.clicked.connect(self._abrir_en_ventana)
            blay.addWidget(self._btn_win)

            self._btn_export = QPushButton("Exportar AST...")
            self._btn_export.setStyleSheet(_btn_css)
            self._btn_export.setToolTip("Guarda el árbol sintáctico como archivo de texto (.txt)")
            self._btn_export.clicked.connect(self._exportar_ast)
            blay.addWidget(self._btn_export)

        lay.addWidget(barra)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        # ── Árbol de 3 columnas ───────────────────────────────────────────
        self._arbol = QTreeWidget()
        self._arbol.setColumnCount(3)
        self._arbol.setHeaderLabels(["Nodo", "Categoría", "Línea"])
        self._arbol.setAlternatingRowColors(True)
        self._arbol.setAnimated(True)
        self._arbol.setIndentation(20)
        self._arbol.setUniformRowHeights(True)
        self._arbol.setRootIsDecorated(True)

        # Dimensionamiento de columnas
        hdr = self._arbol.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._arbol.setColumnWidth(2, 52)

        lay.addWidget(self._arbol)

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def cargar(self, raiz: NodoArb, errores=None):
        """Carga el AST y lo muestra completamente expandido.
        
        errores: lista opcional de objetos Err con los errores sintácticos
                 detectados durante el análisis (se usará al exportar).
        """
        self._raiz_actual   = raiz
        self._errores_actual = list(errores) if errores else []
        self._arbol.clear()
        if raiz is None:
            return

        item_raiz = self._crear_item(raiz)
        self._arbol.addTopLevelItem(item_raiz)
        self._poblar(item_raiz, raiz)
        self._arbol.expandAll()     # expansión automática requerida
        self._arbol.scrollToTop()

    def limpiar(self):
        self._raiz_actual    = None
        self._errores_actual = []
        self._arbol.clear()

    # ── Construcción del árbol ────────────────────────────────────────────────

    def _crear_item(self, nodo: NodoArb) -> QTreeWidgetItem:
        tipo  = getattr(nodo, "tipo_nodo", "")
        linea = getattr(nodo, "linea",     0)
        categ = _CATEGORIAS.get(tipo, "—")
        color = QColor(_COLORES.get(tipo, _COLORES[""]))

        item = QTreeWidgetItem([
            nodo.etiqueta,
            categ,
            str(linea) if linea else "",
        ])
        item.setForeground(0, color)
        item.setForeground(1, color)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if linea:
            item.setToolTip(0, f"Línea {linea}")

        return item

    def _poblar(self, item_padre: QTreeWidgetItem, nodo: NodoArb):
        for hijo in nodo.hijos:
            item_hijo = self._crear_item(hijo)
            item_padre.addChild(item_hijo)
            self._poblar(item_hijo, hijo)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _expandir_todo(self):
        self._arbol.expandAll()

    def _colapsar_todo(self):
        self._arbol.collapseAll()
        if self._arbol.topLevelItemCount() > 0:
            self._arbol.topLevelItem(0).setExpanded(True)

    def _abrir_en_ventana(self):
        """Abre el árbol en ventana independiente (para pantalla completa)."""
        if self._raiz_actual is None:
            return

        # Reutilizar la ventana si ya está abierta
        if self._ventana_ext is not None:
            try:
                if self._ventana_ext.isVisible():
                    self._ventana_ext.raise_()
                    self._ventana_ext.activateWindow()
                    return
            except RuntimeError:
                pass   # fue destruida

        self._ventana_ext = _VentanaArbol(self._raiz_actual, self._errores_actual)
        self._ventana_ext.destroyed.connect(
            lambda: setattr(self, "_ventana_ext", None)
        )
        self._ventana_ext.show()
        self._ventana_ext.raise_()

    def _exportar_ast(self):
        """Guarda el AST como .txt y, si hay errores, también un _errores_sintacticos.txt."""
        if self._raiz_actual is None:
            QMessageBox.information(self, "Exportar AST",
                "No hay árbol generado. Ejecuta el análisis sintáctico primero.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar Árbol Sintáctico",
            "ast.txt",
            "Archivo de texto (*.txt);;Todos los archivos (*)"
        )
        if not ruta:
            return

        # ── Generar texto del AST ───────────────────────────────────────
        def _lineas(nodo, prefijo="", es_ultimo=True):
            conector = "└── " if es_ultimo else "├── "
            sufijo   = f"   [L{nodo.linea}]" if getattr(nodo, "linea", 0) else ""
            res = [prefijo + conector + nodo.etiqueta + sufijo]
            ext = "    " if es_ultimo else "│   "
            for i, h in enumerate(nodo.hijos):
                res.extend(_lineas(h, prefijo + ext, i == len(nodo.hijos) - 1))
            return res

        raiz = self._raiz_actual
        sufijo_raiz = f"   [L{raiz.linea}]" if getattr(raiz, "linea", 0) else ""
        lineas_ast = [raiz.etiqueta + sufijo_raiz]
        for i, h in enumerate(raiz.hijos):
            lineas_ast.extend(_lineas(h, "", i == len(raiz.hijos) - 1))

        try:
            # ── Guardar AST ─────────────────────────────────────────
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("Árbol Sintáctico Abstracto\n")
                if self._errores_actual:
                    f.write(f"(AST parcial — {len(self._errores_actual)} error(es) sintáctico(s) detectado(s))\n")
                f.write("─" * 40 + "\n")
                f.write("\n".join(lineas_ast))
                f.write("\n")

            archivos_guardados = [ruta]

            # ── Guardar errores sintácticos si los hay ───────────────────
            if self._errores_actual:
                import os
                base   = os.path.splitext(ruta)[0]
                ruta_e = base + "_errores_sintacticos.txt"
                with open(ruta_e, "w", encoding="utf-8") as f:
                    f.write("Errores Sintácticos Detectados\n")
                    f.write(f"Total: {len(self._errores_actual)} error(es)\n")
                    f.write("─" * 48 + "\n\n")
                    for i, e in enumerate(self._errores_actual, 1):
                        linea = getattr(e, "linea", getattr(e, "linea", "?"))
                        col   = getattr(e, "col",   getattr(e, "columna", "?"))
                        msg   = getattr(e, "msg",   str(e))
                        tipo  = getattr(e, "tipo",  "sintáctico")
                        f.write(f"[{i}] Línea {linea}, Columna {col}\n")
                        f.write(f"    Tipo    : {tipo}\n")
                        f.write(f"    Mensaje : {msg}\n\n")
                archivos_guardados.append(ruta_e)

            # ── Mensaje de éxito ──────────────────────────────────────
            detalle = "\n".join(f"  • {a}" for a in archivos_guardados)
            QMessageBox.information(self, "Exportar AST",
                f"Archivos guardados:\n{detalle}")

        except Exception as ex:
            QMessageBox.critical(self, "Error al exportar",
                f"No se pudo guardar el archivo:\n{ex}")

