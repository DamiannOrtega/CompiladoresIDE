# iconos.py — Gestor de iconos SVG embebidos y coloreados por tema
#
# Los SVGs usan el marcador FILL para ser reemplazado en tiempo de ejecución
# con el color del tema activo. No se necesitan archivos externos.

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QByteArray


# ── SVGs embebidos (16×16 viewBox) ───────────────────────────────────────────
# FILL se reemplaza con el color real al cargar.

_SVGS: dict[str, str] = {

    # Archivo — hoja con esquina doblada
    "nuevo": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="FILL" d="M4 1h6l4 4v10H4V1zm6 0v4h4"/>
  <path fill="none" stroke="FILL" stroke-width="1" d="M4 1h6l4 4v10H4z"/>
  <path fill="none" stroke="FILL" stroke-width="1" d="M10 1v4h4"/>
</svg>""",

    # Abrir — carpeta abierta
    "abrir": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <path fill="none" stroke="FILL" stroke-width="1.2"
    d="M1 4h4l2 2h7v8H1V4z"/>
  <path fill="none" stroke="FILL" stroke-width="1.2"
    d="M1 8h13"/>
</svg>""",

    # Guardar — disquete
    "guardar": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <rect fill="none" stroke="FILL" stroke-width="1.2" x="2" y="1" width="12" height="14" rx="1"/>
  <rect fill="FILL" x="5" y="1" width="6" height="5"/>
  <rect fill="none" stroke="FILL" stroke-width="1" x="4" y="9" width="8" height="5"/>
</svg>""",

    # Léxico — lupa con L
    "lexico": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <circle fill="none" stroke="FILL" stroke-width="1.4" cx="6.5" cy="6.5" r="4.5"/>
  <line stroke="FILL" stroke-width="1.8" stroke-linecap="round" x1="10" y1="10" x2="14" y2="14"/>
  <text x="4" y="9" font-size="5" fill="FILL" font-family="monospace" font-weight="bold">L</text>
</svg>""",

    # Sintáctico — árbol
    "sintactico": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <circle fill="FILL" cx="8" cy="2.5" r="1.5"/>
  <circle fill="FILL" cx="4" cy="8" r="1.5"/>
  <circle fill="FILL" cx="12" cy="8" r="1.5"/>
  <circle fill="FILL" cx="4" cy="13.5" r="1.5"/>
  <circle fill="FILL" cx="12" cy="13.5" r="1.5"/>
  <line stroke="FILL" stroke-width="1" x1="8" y1="4" x2="4" y2="6.5"/>
  <line stroke="FILL" stroke-width="1" x1="8" y1="4" x2="12" y2="6.5"/>
  <line stroke="FILL" stroke-width="1" x1="4" y1="9.5" x2="4" y2="12"/>
  <line stroke="FILL" stroke-width="1" x1="12" y1="9.5" x2="12" y2="12"/>
</svg>""",

    # Semántico — check con símbolo
    "semantico": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <circle fill="none" stroke="FILL" stroke-width="1.3" cx="8" cy="8" r="6.5"/>
  <polyline fill="none" stroke="FILL" stroke-width="1.8" stroke-linecap="round"
    points="5,8.5 7,10.5 11,6"/>
</svg>""",

    # IR — código con flecha
    "ir": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <line stroke="FILL" stroke-width="1.3" stroke-linecap="round" x1="2" y1="4" x2="9" y2="4"/>
  <line stroke="FILL" stroke-width="1.3" stroke-linecap="round" x1="2" y1="7" x2="7" y2="7"/>
  <line stroke="FILL" stroke-width="1.3" stroke-linecap="round" x1="2" y1="10" x2="9" y2="10"/>
  <line stroke="FILL" stroke-width="1.3" stroke-linecap="round" x1="2" y1="13" x2="6" y2="13"/>
  <polyline fill="none" stroke="FILL" stroke-width="1.5" stroke-linecap="round"
    points="11,5 14,8 11,11"/>
  <line stroke="FILL" stroke-width="1.5" stroke-linecap="round" x1="14" y1="8" x2="9" y2="8"/>
</svg>""",

    # Ejecutar — triángulo play
    "ejecutar": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <polygon fill="FILL" points="4,2 14,8 4,14"/>
</svg>""",

    # Compilar todo — doble play
    "compilar_todo": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <polygon fill="FILL" points="1,2 8,8 1,14"/>
  <polygon fill="FILL" points="8,2 15,8 8,14"/>
</svg>""",

    # Icono de aplicación — llaves de código con acento
    "app": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect fill="#1e1e1e" width="64" height="64" rx="8"/>
  <text x="8" y="44" font-size="42" fill="FILL"
    font-family="Consolas,monospace" font-weight="bold">&lt;/&gt;</text>
</svg>""",
}


# ── GestorIconos ──────────────────────────────────────────────────────────────

class GestorIconos:
    """Carga y coloriza iconos SVG según el tema activo."""

    def __init__(self):
        self._cache: dict[tuple, QIcon] = {}

    def icono(self, nombre: str, color: str = "#cccccc") -> QIcon:
        """Devuelve un QIcon del SVG indicado, coloreado con `color`."""
        clave = (nombre, color)
        if clave in self._cache:
            return self._cache[clave]

        svg_raw = _SVGS.get(nombre, "")
        if not svg_raw:
            return QIcon()

        svg_col = svg_raw.replace("FILL", color)
        datos = QByteArray(svg_col.encode("utf-8"))
        px = QPixmap()
        px.loadFromData(datos, "SVG")
        ico = QIcon(px)
        self._cache[clave] = ico
        return ico

    def set_tema(self, paleta: dict) -> dict[str, QIcon]:
        """
        Genera el dict completo de iconos para el tema dado.
        paleta debe tener claves 'txt' y 'acento'.
        """
        self._cache.clear()
        txt    = paleta.get("txt",    "#cccccc")
        acento = paleta.get("acento", "#007acc")

        return {
            "nuevo":          self.icono("nuevo",          txt),
            "abrir":          self.icono("abrir",          txt),
            "guardar":        self.icono("guardar",        txt),
            "lexico":         self.icono("lexico",         acento),
            "sintactico":     self.icono("sintactico",     acento),
            "semantico":      self.icono("semantico",      acento),
            "ir":             self.icono("ir",             acento),
            "ejecutar":       self.icono("ejecutar",       acento),
            "compilar_todo":  self.icono("compilar_todo",  acento),
            "app":            self.icono("app",            acento),
        }


# Instancia global — importada por ventana.py y main.py
gestor_ico = GestorIconos()
