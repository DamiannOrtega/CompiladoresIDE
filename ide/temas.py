# temas.py — Sistema de temas visuales del IDE
#
# Arquitectura:
#   - Cada tema define un dict de colores (paleta).
#   - _generar_hoja(p) produce el QSS completo a partir de esa paleta.
#   - GestorTemas.aplicar() llama setStyleSheet + unpolish/polish para
#     forzar el repintado de TODOS los widgets sin excepción.

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPalette, QColor


# ── Paletas de colores ────────────────────────────────────────────────────────
# Cada clave es un token semántico usado en _generar_hoja().

_PALETAS: dict[str, dict] = {
    "Oscuro": {
        "bg":          "#1e1e1e",   # fondo principal
        "bg2":         "#252526",   # fondo paneles / filas alternas
        "bg3":         "#2d2d2d",   # fondo barras / cabeceras
        "borde":       "#3c3c3c",   # separadores
        "txt":         "#d4d4d4",   # texto principal
        "txt2":        "#888888",   # texto secundario / tabs inactivos
        "acento":      "#007acc",   # color de acento (statusbar, tab activo)
        "acento_txt":  "#ffffff",   # texto sobre acento
        "sel":         "#094771",   # fondo selección
        "sel_txt":     "#ffffff",
        "hover":       "#2a2d2e",   # hover en items
        "hover_btn":   "#3c3c3c",   # hover en botones
        "pressed":     "#094771",   # pressed en botones
        "editor_bg":   "#1e1e1e",
        "editor_txt":  "#d4d4d4",
        "editor_sel":  "#264f78",
        "scroll":      "#424242",
        "scroll_hov":  "#686868",
        "grid":        "#2d2d2d",
    },
    "Claro": {
        "bg":          "#f5f5f5",
        "bg2":         "#eeeeee",
        "bg3":         "#e0e0e0",
        "borde":       "#cccccc",
        "txt":         "#1e1e1e",
        "txt2":        "#666666",
        "acento":      "#0078d4",
        "acento_txt":  "#ffffff",
        "sel":         "#cce4f7",
        "sel_txt":     "#000000",
        "hover":       "#e8f4fd",
        "hover_btn":   "#d0d0d0",
        "pressed":     "#b0d0f0",
        "editor_bg":   "#ffffff",
        "editor_txt":  "#1e1e1e",
        "editor_sel":  "#add6ff",
        "scroll":      "#c0c0c0",
        "scroll_hov":  "#999999",
        "grid":        "#e0e0e0",
    },
    "Azul": {
        "bg":          "#0d1117",
        "bg2":         "#161b22",
        "bg3":         "#161b22",
        "borde":       "#30363d",
        "txt":         "#c9d1d9",
        "txt2":        "#6e7681",
        "acento":      "#00b4d8",
        "acento_txt":  "#000000",
        "sel":         "#1f4068",
        "sel_txt":     "#ffffff",
        "hover":       "#1c2128",
        "hover_btn":   "#21262d",
        "pressed":     "#1f4068",
        "editor_bg":   "#0d1117",
        "editor_txt":  "#c9d1d9",
        "editor_sel":  "#1f4068",
        "scroll":      "#30363d",
        "scroll_hov":  "#8b949e",
        "grid":        "#21262d",
    },
    "Alto Contraste": {
        "bg":          "#000000",
        "bg2":         "#111111",
        "bg3":         "#000000",
        "borde":       "#ffff00",
        "txt":         "#ffffff",
        "txt2":        "#cccccc",
        "acento":      "#ffff00",
        "acento_txt":  "#000000",
        "sel":         "#ffff00",
        "sel_txt":     "#000000",
        "hover":       "#222222",
        "hover_btn":   "#333300",
        "pressed":     "#666600",
        "editor_bg":   "#000000",
        "editor_txt":  "#ffffff",
        "editor_sel":  "#ffff00",
        "scroll":      "#ffff00",
        "scroll_hov":  "#cccc00",
        "grid":        "#333333",
    },
}

TEMA_POR_DEFECTO = "Oscuro"


# ── Generador de hoja de estilo ───────────────────────────────────────────────

def _generar_hoja(p: dict) -> str:
    """Genera el QSS completo a partir de una paleta de colores."""
    borde_ac = "2px" if p["acento"] == "#ffff00" else "1px"
    return f"""
/* ── Base ── */
QMainWindow, QDialog, QWidget {{
    background-color: {p['bg']};
    color: {p['txt']};
}}

/* ── Menú ── */
QMenuBar {{
    background-color: {p['bg3']};
    color: {p['txt']};
    border-bottom: {borde_ac} solid {p['borde']};
    padding: 2px 0;
    font-size: 13px;
}}
QMenuBar::item {{
    padding: 4px 10px;
    background: transparent;
    color: {p['txt']};
}}
QMenuBar::item:selected {{
    background-color: {p['hover_btn']};
    color: {p['txt']};
}}
QMenu {{
    background-color: {p['bg2']};
    color: {p['txt']};
    border: {borde_ac} solid {p['borde']};
    padding: 4px 0;
}}
QMenu::item {{
    padding: 5px 24px 5px 16px;
    color: {p['txt']};
}}
QMenu::item:selected {{
    background-color: {p['sel']};
    color: {p['sel_txt']};
}}
QMenu::separator {{
    height: 1px;
    background: {p['borde']};
    margin: 3px 0;
}}

/* ── Barra de herramientas ── */
QToolBar {{
    background-color: {p['bg3']};
    border-bottom: {borde_ac} solid {p['borde']};
    spacing: 2px;
    padding: 2px 4px;
}}
QToolBar::separator {{
    width: 1px;
    background: {p['borde']};
    margin: 4px 2px;
}}
QToolButton {{
    background: transparent;
    color: {p['txt']};
    border: none;
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 12px;
}}
QToolButton:hover {{
    background-color: {p['hover_btn']};
    color: {p['txt']};
}}
QToolButton:pressed {{
    background-color: {p['pressed']};
    color: {p['sel_txt']};
}}

/* ── Barra de estado ── */
QStatusBar {{
    background-color: {p['acento']};
    color: {p['acento_txt']};
    font-size: 12px;
    padding: 0 8px;
}}
QStatusBar::item {{
    border: none;
}}
QStatusBar QLabel {{
    background-color: transparent;
    color: {p['acento_txt']};
    padding: 0 8px;
}}

/* ── Docks ── */
QDockWidget {{
    color: {p['txt']};
    font-size: 12px;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: {p['bg3']};
    color: {p['txt']};
    padding: 4px 8px;
    border-bottom: {borde_ac} solid {p['borde']};
    text-align: left;
}}
QDockWidget::close-button,
QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: none;
    background-color: {p['bg']};
}}
QTabBar {{
    background-color: {p['bg3']};
}}
QTabBar::tab {{
    background-color: {p['bg3']};
    color: {p['txt2']};
    padding: 6px 14px;
    border: none;
    border-right: 1px solid {p['bg']};
    font-size: 12px;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    background-color: {p['bg']};
    color: {p['txt']};
    border-top: 2px solid {p['acento']};
}}
QTabBar::tab:hover:!selected {{
    background-color: {p['hover']};
    color: {p['txt']};
}}

/* ── Editor ── */
QPlainTextEdit {{
    background-color: {p['editor_bg']};
    color: {p['editor_txt']};
    border: none;
    font-family: Consolas, "Courier New", monospace;
    font-size: 14px;
    selection-background-color: {p['editor_sel']};
    selection-color: {p['sel_txt']};
}}

/* ── Tablas ── */
QTableWidget {{
    background-color: {p['bg']};
    color: {p['txt']};
    gridline-color: {p['grid']};
    border: none;
    font-size: 12px;
    selection-background-color: {p['sel']};
    selection-color: {p['sel_txt']};
    alternate-background-color: {p['bg2']};
}}
QTableWidget::item {{
    padding: 3px 6px;
    border: none;
    color: {p['txt']};
}}
QHeaderView::section {{
    background-color: {p['bg3']};
    color: {p['txt2']};
    padding: 4px 6px;
    border: none;
    border-right: 1px solid {p['borde']};
    border-bottom: 1px solid {p['borde']};
    font-size: 11px;
    font-weight: bold;
}}

/* ── Árbol ── */
QTreeView, QTreeWidget {{
    background-color: {p['bg']};
    color: {p['txt']};
    border: none;
    font-size: 12px;
    selection-background-color: {p['sel']};
    selection-color: {p['sel_txt']};
    alternate-background-color: {p['bg2']};
    show-decoration-selected: 1;
}}
QTreeView::item, QTreeWidget::item {{
    padding: 2px 4px;
    border: none;
    color: {p['txt']};
}}
QTreeView::item:hover, QTreeWidget::item:hover {{
    background-color: {p['hover']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {p['bg']};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['scroll']};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {p['scroll_hov']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {p['bg']};
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {p['scroll']};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {p['scroll_hov']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Splitter ── */
QSplitter::handle {{
    background-color: {p['borde']};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* ── Placeholder semántico ── */
QLabel#semant_placeholder {{
    color: {p['txt2']};
    font-size: 13px;
    background-color: {p['bg']};
}}
"""


# ── Registro de temas ─────────────────────────────────────────────────────────

TEMAS: dict[str, str] = {
    nombre: _generar_hoja(paleta)
    for nombre, paleta in _PALETAS.items()
}


# ── Gestor de temas ───────────────────────────────────────────────────────────

class GestorTemas:
    """Aplica y persiste el tema visual de la aplicación."""

    _CLAVE = "tema/nombre"

    def __init__(self, app: QApplication):
        self._app = app
        self._actual = TEMA_POR_DEFECTO
        self._cfg = QSettings("Compiladores", "IDE")

    @property
    def actual(self) -> str:
        return self._actual

    @property
    def nombres(self) -> list[str]:
        return list(_PALETAS.keys())

    def paleta(self, nombre: str = None) -> dict:
        """Devuelve el dict de colores del tema indicado (o el actual)."""
        return _PALETAS.get(nombre or self._actual, _PALETAS[TEMA_POR_DEFECTO])

    def aplicar(self, nombre: str):
        """Cambia el tema en tiempo de ejecución y fuerza repintado total."""
        if nombre not in TEMAS:
            return
        self._actual = nombre

        # 1. Aplicar hoja de estilo a la aplicación
        self._app.setStyleSheet(TEMAS[nombre])

        # 2. Forzar repintado de TODOS los widgets top-level
        #    unpolish → polish → update garantiza que Qt recalcule estilos
        for w in self._app.topLevelWidgets():
            self._refrescar(w)

    def _refrescar(self, widget: QWidget):
        """Aplica unpolish/polish recursivamente para forzar repintado."""
        estilo = self._app.style()
        estilo.unpolish(widget)
        estilo.polish(widget)
        widget.update()
        for hijo in widget.findChildren(QWidget):
            estilo.unpolish(hijo)
            estilo.polish(hijo)
            hijo.update()

    def guardar(self):
        """Persiste el tema actual en QSettings."""
        self._cfg.setValue(self._CLAVE, self._actual)

    def cargar(self):
        """Restaura el último tema guardado (o el predeterminado)."""
        nombre = self._cfg.value(self._CLAVE, TEMA_POR_DEFECTO)
        self.aplicar(nombre)
