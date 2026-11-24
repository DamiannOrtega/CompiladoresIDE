# ventana.py — Ventana principal del IDE (QMainWindow)

import os
import ctypes
import threading
import ctypes.wintypes
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTabWidget, QTabBar, QWidget,
    QLabel, QFileDialog, QMessageBox, QToolBar, QStatusBar, QApplication, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize, QPoint, QMimeData, QObject, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QDrag, QPixmap, QPainter

from ide.ui.editor import EditorCodigo
from ide.ui.panel_tok import PanelTok
from ide.ui.panel_err import PanelErr
from ide.ui.panel_sim import PanelSim
from ide.ui.panel_arb import PanelArb
from ide.ui.panel_sal import PanelSal
from ide.ui.panel_tm import PanelTm
from ide.ui.panel_ir import PanelIr
from ide.ui.panel_sal import nombre_variable, mensaje_valor_invalido
from ide.ui.panel_archivos import PanelArchivos
from ide.modelos.datos import Err
from ide.compilador.tm_formato import ErrorFormatoTM
from ide.servicios.compilador import ServicioCompilador
from ide.iconos import gestor_ico


# ── Worker de compilación en hilo de fondo ─────────────────────────────────────────

class _WorkerCompilacion(QObject):
    """
    Ejecuta self._servicio.compilar() en un hilo separado.
    Emite 'terminado(fase, res)' cuando termina.
    La señal incluye la fase para poder conectarse a un método real
    (no a un lambda), lo que permite que Qt use AutoConnection y
    asegure que el callback se ejecute en el hilo principal.
    """
    terminado = Signal(str, object)   # fase, ResultadoCompilacion

    def __init__(self, servicio, fase: str, ruta: str, texto: str):
        super().__init__()
        self._servicio = servicio
        self._fase     = fase
        self._ruta     = ruta
        self._texto    = texto

    def ejecutar(self):
        try:
            res = self._servicio.compilar(self._fase, self._ruta, self._texto)
        except Exception as ex:
            from ide.modelos.datos import ResultadoCompilacion, Err
            res = ResultadoCompilacion(fase=self._fase)
            res.err = [Err(tipo="error interno", linea=0, col=0,
                          msg=f"Error inesperado en el compilador: {ex}")]
        self.terminado.emit(self._fase, res)


# ── Worker de ejecución TM en hilo de fondo ──────────────────────────────────

class _WorkerEjecucion(QObject):
    """
    Ejecuta el simulador TM en un hilo separado.

    Cuando el programa llega a una instrucción IN, el simulador llama a
    _leer(); ese método emite 'entrada_requerida' hacia la interfaz y espera
    (threading.Event) a que el usuario envíe el valor desde la consola. Durante
    la espera la máquina queda en pausa con registros, memoria y pc intactos, y
    continúa desde la misma instrucción al recibir el dato. La validación la
    realiza el simulador; si rechaza el valor vuelve a llamar a _leer().

    Todas las señales llevan el id de la ejecución para que la interfaz ignore
    mensajes de una ejecución anterior ya cancelada.
    """
    salida            = Signal(int, str)      # id, línea impresa por el programa
    entrada_requerida = Signal(int, object)   # id, SolicitudEntrada
    terminado         = Signal(int, object)   # id, ResultadoEjecucion | Exception

    def __init__(self, id_ejec: int, servicio, ruta_tm: str):
        super().__init__()
        self._id = id_ejec
        self._servicio = servicio
        self._ruta = ruta_tm
        self._respuesta = None
        self._hay_respuesta = threading.Event()
        self._cancelar = threading.Event()

    def ejecutar(self):
        try:
            res = self._servicio.ejecutar_tm(self._ruta, self._leer, self._escribir,
                                             interrumpir=self._cancelar)
        except Exception as ex:          # archivo no encontrado / .tm inválido
            res = ex
        self.terminado.emit(self._id, res)

    def _escribir(self, linea: str):
        self.salida.emit(self._id, linea)

    def _leer(self, solicitud):
        if self._cancelar.is_set():
            return None
        self._hay_respuesta.clear()
        self.entrada_requerida.emit(self._id, solicitud)
        self._hay_respuesta.wait()          # pausa hasta que el usuario envía el dato
        if self._cancelar.is_set():
            return None
        return self._respuesta

    # Llamados desde el hilo de la interfaz
    def responder(self, texto: str):
        self._respuesta = texto
        self._hay_respuesta.set()

    def cancelar(self):
        self._cancelar.set()
        self._hay_respuesta.set()


# ── Tab widget con pestañas arrastrables (tear-off) ──────────────────────────

class TabsArrastrables(QTabWidget):
    """
    QTabWidget que permite arrastrar una pestaña fuera de la barra
    para convertirla en un QDockWidget flotante.
    Al cerrar el dock flotante, el panel vuelve a esta barra.
    """

    # Umbral de píxeles que hay que mover para iniciar un tear-off
    _UMBRAL_DRAG = 30

    def __init__(self, ventana_principal: 'VentanaPrincipal', parent=None):
        super().__init__(parent)
        self._win = ventana_principal
        self._drag_inicio: QPoint | None = None
        self._drag_tab_idx: int = -1
        # dock flotante activo por nombre de pestaña → QDockWidget
        self._docks_flotantes: dict[str, QDockWidget] = {}

        tb = self.tabBar()
        tb.setMouseTracking(True)
        tb.installEventFilter(self)

    # ── Event filter en la TabBar ──────────────────────────────────────

    def eventFilter(self, obj, evento):
        from PySide6.QtCore import QEvent
        if obj is not self.tabBar():
            return super().eventFilter(obj, evento)

        t = evento.type()
        if t == QEvent.MouseButtonPress:
            if evento.button() == Qt.LeftButton:
                idx = self.tabBar().tabAt(evento.position().toPoint())
                if idx >= 0:
                    self._drag_inicio = evento.globalPosition().toPoint()
                    self._drag_tab_idx = idx

        elif t == QEvent.MouseMove:
            if self._drag_inicio is not None and evento.buttons() == Qt.LeftButton:
                delta = (evento.globalPosition().toPoint() - self._drag_inicio).manhattanLength()
                if delta >= self._UMBRAL_DRAG:
                    self._iniciar_tear_off(self._drag_tab_idx)
                    self._drag_inicio = None
                    self._drag_tab_idx = -1

        elif t == QEvent.MouseButtonRelease:
            self._drag_inicio = None
            self._drag_tab_idx = -1

        return super().eventFilter(obj, evento)

    # ── Tear-off: sacar la pestaña como dock flotante ──────────────────

    _ORDEN = ["Tokens", "Código intermedio", "Código TM", "Errores", "Salida"]

    def _iniciar_tear_off(self, idx: int):
        if idx < 0 or idx >= self.count():
            return
        titulo = self.tabText(idx)
        # Evitar dobles docks del mismo panel
        if titulo in self._docks_flotantes:
            return

        widget = self.widget(idx)
        if widget is None:
            return

        # Quitar la pestaña del tab bar
        self.removeTab(idx)

        # Crear dock flotante
        dock = QDockWidget(titulo, self._win)
        dock.setWidget(widget)
        dock.setAllowedAreas(Qt.NoDockWidgetArea)   # sólo flotante, nunca re-acopla
        from PySide6.QtGui import QCursor
        cursor_pos = QCursor.pos()
        dock.move(cursor_pos.x() - 50, cursor_pos.y() - 20)
        dock.resize(600, 300)
        self._win.addDockWidget(Qt.BottomDockWidgetArea, dock)
        dock.setFloating(True)
        dock.show()

        self._docks_flotantes[titulo] = dock

        # Cerrar con el botón X → devolver al tab bar
        dock.closeEvent = lambda ev, t=titulo, w=widget, d=dock: \
            self._devolver_panel(ev, t, w, d)

    def _devolver_panel(self, evento, titulo: str, widget: QWidget, dock: QDockWidget):
        """Devuelve el panel al tab bar en su posición original."""
        evento.accept()
        # Desvincular el widget del dock ANTES de destruirlo
        dock.setWidget(None)
        self._win.removeDockWidget(dock)
        self._docks_flotantes.pop(titulo, None)

        # Calcular posición de reinserción según el orden original
        pos = self._ORDEN.index(titulo) if titulo in self._ORDEN else self.count()
        insert_at = 0
        for nombre in self._ORDEN[:pos]:
            for i in range(self.count()):
                if self.tabText(i) == nombre:
                    insert_at = i + 1
                    break
        self.insertTab(insert_at, widget, titulo)
        self.setCurrentIndex(insert_at)



# ── Utilidad: colorear barra de título (Windows 10/11) ────────────────────────

def _aplicar_color_titlebar(hwnd: int, color_hex: str, es_oscuro: bool):
    """Aplica el color de fondo a la barra de título nativa de Windows.

    Usa dos atributos DWM:
      - DWMWA_USE_IMMERSIVE_DARK_MODE (20): activa texto blanco en Win10+
      - DWMWA_CAPTION_COLOR (35): color exacto de la barra (Win11 22000+)
    Si la llamada falla en algún sistema, se ignora silenciosamente.
    """
    try:
        dwm = ctypes.windll.dwmapi

        # Modo oscuro/claro del texto de la barra (Win10 1809+)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark = ctypes.c_int(1 if es_oscuro else 0)
        dwm.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark), ctypes.sizeof(dark)
        )

        # Color exacto de fondo de la barra de título (Win11 build 22000+)
        DWMWA_CAPTION_COLOR = 35
        # COLORREF = 0x00BBGGRR
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)
        colorref = ctypes.c_uint(r | (g << 8) | (b << 16))
        dwm.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR,
            ctypes.byref(colorref), ctypes.sizeof(colorref)
        )
    except Exception:
        pass  # No disponible en Linux/macOS o builds antiguos de Windows


class VentanaPrincipal(QMainWindow):
    """Ventana principal del IDE de compiladores."""

    TITULO = "IDE Compiladores"

    def __init__(self, gestor=None):
        super().__init__()
        self._servicio = ServicioCompilador()
        self._gestor = gestor
        self._iconos = {}   # dict nombre→QIcon, actualizado al cambiar tema

        self._construir_ui()
        self._aplicar_iconos()
        self._conectar_senales()
        self.setWindowTitle(self.TITULO)
        self._set_estado("Sin archivos abiertos")
        self._aplicar_titlebar()

    # ── Acceso al editor / estado de la pestaña activa ────────────────

    @property
    def _editor(self):
        """Editor de la pestaña actualmente visible."""
        return self._tabs_editor.currentWidget()

    @property
    def _ruta_arch(self):
        w = self._editor
        return getattr(w, "_ruta_arch", None) if w else None

    @_ruta_arch.setter
    def _ruta_arch(self, v):
        w = self._editor
        if w is not None:
            w._ruta_arch = v

    @property
    def _modificado(self):
        w = self._editor
        return getattr(w, "_modificado", False) if w else False

    @_modificado.setter
    def _modificado(self, v):
        w = self._editor
        if w is not None:
            w._modificado = v

    # ── Construcción de la UI ─────────────────────────────────────────

    def _construir_ui(self):
        self.setWindowTitle(self.TITULO)
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # ── Tab widget central ──
        self._tabs_editor = QTabWidget()
        self._tabs_editor.setTabsClosable(True)
        self._tabs_editor.setMovable(True)
        self._tabs_editor.setDocumentMode(True)
        self.setCentralWidget(self._tabs_editor)

        # Paneles
        self._p_tok  = PanelTok()
        self._p_err  = PanelErr()
        self._p_sim  = PanelSim()
        self._p_arb  = PanelArb(titulo="Árbol Sintáctico (Original)")
        self._p_arb_semant = PanelArb(titulo="Árbol Anotado (Semántico)")
        self._p_ir   = PanelIr()
        self._p_tm   = PanelTm()
        self._p_sal  = PanelSal()
        self._p_arch = PanelArchivos()

        self._crear_barra_menu()
        self._crear_barra_herramientas()
        self._crear_barra_estado()
        self._crear_docks()
        self._crear_menu_ver()

    # ── Menú ──────────────────────────────────────────────────────────

    def _crear_barra_menu(self):
        mb = self.menuBar()

        # ── Archivo ──
        m_arch = mb.addMenu("&Archivo")

        self._acc_nuevo   = self._accion("Nuevo",        "Ctrl+N", m_arch)
        self._acc_abrir   = self._accion("Abrir...",     "Ctrl+O", m_arch)
        m_arch.addSeparator()
        self._acc_guardar = self._accion("Guardar",      "Ctrl+S", m_arch)
        self._acc_guar_as = self._accion("Guardar como...", "Ctrl+Shift+S", m_arch)
        self._acc_cerrar  = self._accion("Cerrar",       "Ctrl+W", m_arch)
        m_arch.addSeparator()
        self._acc_salir   = self._accion("Salir",        "Ctrl+Q", m_arch)

        # ── Compilar ──
        m_comp = mb.addMenu("&Compilar")

        self._acc_lexico  = self._accion("Análisis Léxico",     "F5",  m_comp)
        self._acc_sintac  = self._accion("Análisis Sintáctico", "F6",  m_comp)
        self._acc_semant  = self._accion("Análisis Semántico",  "F7",  m_comp)
        self._acc_ir      = self._accion("Generar Código (intermedio y TM)", "F8", m_comp)
        m_comp.addSeparator()
        self._acc_ejec    = self._accion("Ejecutar TM",         "F9",  m_comp)
        m_comp.addSeparator()
        self._acc_todo    = self._accion("Compilar Todo",       "F10", m_comp)

        # Ver se crea después en _crear_menu_ver() para poder acceder al gestor
        self._mb = mb

    def _accion(self, texto: str, atajo: str, menu) -> QAction:
        acc = QAction(texto, self)
        acc.setShortcut(QKeySequence(atajo))
        menu.addAction(acc)
        return acc

    def _aplicar_iconos(self):
        """Carga/recarga iconos según el tema activo y los asigna a acciones."""
        paleta = self._gestor.paleta() if self._gestor else {}
        self._iconos = gestor_ico.set_tema(paleta)

        self._acc_nuevo.setIcon(self._iconos.get("nuevo",   {}))
        self._acc_abrir.setIcon(self._iconos.get("abrir",   {}))
        self._acc_guardar.setIcon(self._iconos.get("guardar", {}))
        self._acc_lexico.setIcon(self._iconos.get("lexico",  {}))
        self._acc_sintac.setIcon(self._iconos.get("sintactico", {}))
        self._acc_semant.setIcon(self._iconos.get("semantico",  {}))
        self._acc_ir.setIcon(self._iconos.get("ir",          {}))
        self._acc_ejec.setIcon(self._iconos.get("ejecutar",  {}))
        self._acc_todo.setIcon(self._iconos.get("compilar_todo", {}))

    # ── Menú Ver (temas) ──────────────────────────────────────────────

    def _crear_menu_ver(self):
        """Agrega el menú Ver con submenús de Paneles y Tema."""
        m_ver = self._mb.addMenu("&Ver")

        # ── Paneles ──
        m_paneles = m_ver.addMenu("&Paneles")

        # Explorador (izquierda)
        acc_izq = self._dock_izq.toggleViewAction()
        acc_izq.setText("&Explorador")
        acc_izq.setShortcut(QKeySequence("Alt+1"))
        m_paneles.addAction(acc_izq)

        # Análisis (derecha)
        acc_der = self._dock_der.toggleViewAction()
        acc_der.setText("&Análisis")
        acc_der.setShortcut(QKeySequence("Alt+2"))
        m_paneles.addAction(acc_der)

        # Resultados (abajo)
        acc_abj = self._dock_abj.toggleViewAction()
        acc_abj.setText("&Resultados")
        acc_abj.setShortcut(QKeySequence("Alt+3"))
        m_paneles.addAction(acc_abj)

        m_paneles.addSeparator()
        self._acc_restablecer = self._accion("Restablecer distribución", "Alt+0", m_paneles)
        self._acc_restablecer.triggered.connect(self._restablecer_paneles)

        # Botones en la barra de herramientas (a la derecha) para mostrar u
        # ocultar cada panel; son las mismas acciones del menú Ver > Paneles.
        espacio = QWidget()
        espacio.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        espacio.setStyleSheet("background: transparent; border: none;")
        self._tb.addWidget(espacio)
        for acc, tip in (
            (acc_izq, "Mostrar u ocultar el Explorador de archivos (Alt+1)"),
            (acc_der, "Mostrar u ocultar el panel de Análisis: árboles y tabla de símbolos (Alt+2)"),
            (acc_abj, "Mostrar u ocultar los Resultados: tokens, código, errores y salida (Alt+3)"),
        ):
            acc.setToolTip(tip)
            self._tb.addAction(acc)

        # Recordar qué paneles cerró el usuario para no reabrirlos al compilar
        self._ocultos = {}
        for dock in (self._dock_izq, self._dock_der, self._dock_abj):
            dock.visibilityChanged.connect(
                lambda visible, d=dock: self._dock_visibilidad(d, visible))

        m_ver.addSeparator()

        # ── Zoom del editor ──
        m_zoom = m_ver.addMenu("&Zoom Editor")
        self._acc_zoom_in    = self._accion("Acercar (+)",    "Ctrl+=", m_zoom)
        self._acc_zoom_out   = self._accion("Alejar (-)",     "Ctrl+-", m_zoom)
        self._acc_zoom_reset = self._accion("Tamaño normal",  "Ctrl+0", m_zoom)

        m_ver.addSeparator()

        # ── Tema ──
        m_tema = m_ver.addMenu("&Tema")

        self._grp_temas = QActionGroup(self)
        self._grp_temas.setExclusive(True)
        self._acc_temas = {}

        nombres = self._gestor.nombres if self._gestor else ["Oscuro"]
        actual  = self._gestor.actual  if self._gestor else "Oscuro"

        for nombre in nombres:
            acc = QAction(nombre, self)
            acc.setCheckable(True)
            acc.setChecked(nombre == actual)
            acc.setData(nombre)
            self._grp_temas.addAction(acc)
            m_tema.addAction(acc)
            self._acc_temas[nombre] = acc

        self._grp_temas.triggered.connect(self._cambiar_tema)

    def _cambiar_tema(self, acc: QAction):
        nombre = acc.data()
        if self._gestor:
            self._gestor.aplicar(nombre)
            self._gestor.guardar()
            # Actualizar iconos y resaltado de TODOS los editores abiertos
            self._aplicar_iconos()
            paleta = self._gestor.paleta(nombre)
            for i in range(self._tabs_editor.count()):
                self._tabs_editor.widget(i).set_tema(nombre, paleta)
            self._p_arch.set_tema(paleta)   # ícono .src del explorador
            self._aplicar_titlebar()
            self._set_estado(f"Tema: {nombre}")

    # ── Barra de herramientas ─────────────────────────────────────────

    def _crear_barra_herramientas(self):
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        self._tb = tb

        # Acciones de archivo
        tb.addAction(self._acc_nuevo)
        tb.addAction(self._acc_abrir)
        tb.addAction(self._acc_guardar)
        tb.addSeparator()

        # Fases de compilación
        fases = [
            (self._acc_lexico, "Léxico"),
            (self._acc_sintac, "Sintáctico"),
            (self._acc_semant, "Semántico"),
            (self._acc_ir,     "Generar código"),
            (self._acc_ejec,   "Ejecutar TM"),
        ]
        for acc, etiq in fases:
            acc.setText(etiq)
            tb.addAction(acc)

        tb.addSeparator()
        self._acc_todo.setText("Compilar Todo")
        tb.addAction(self._acc_todo)

    # ── Barra de estado ───────────────────────────────────────────────

    def _crear_barra_estado(self):
        sb = self.statusBar()

        self._lbl_pos    = QLabel("Ln 1, Col 1")
        self._lbl_estado = QLabel("Listo")
        self._lbl_arch   = QLabel("")

        sb.addWidget(self._lbl_arch)
        sb.addPermanentWidget(self._lbl_estado)
        sb.addPermanentWidget(self._lbl_pos)

    # ── Docks ─────────────────────────────────────────────────────────

    def _crear_docks(self):
        # ── Izquierda: Explorador ──
        self._tabs_izq = QTabWidget()
        self._tabs_izq.addTab(self._p_arch, "Explorador")

        self._dock_izq = QDockWidget("Explorador", self)
        self._dock_izq.setWidget(self._tabs_izq)
        self._dock_izq.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_izq)

        # ── Derecha: Árbol sintáctico + Árbol Anotado + Tabla de Símbolos ──
        self._tabs_der = QTabWidget()
        self._tabs_der.addTab(self._p_arb,        "Árbol Sintáctico")
        self._tabs_der.addTab(self._p_arb_semant, "Árbol Anotado")
        self._tabs_der.addTab(self._p_sim,        "Tabla de Símbolos")

        self._dock_der = QDockWidget("Análisis", self)
        self._dock_der.setWidget(self._tabs_der)
        self._dock_der.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_der)

        # ── Abajo: Tokens, IR, Errores, Salida ──
        self._tabs_abj = TabsArrastrables(self)
        self._tabs_abj.addTab(self._p_tok, "Tokens")
        self._tabs_abj.addTab(self._p_ir,  "Código intermedio")
        self._tabs_abj.addTab(self._p_tm,  "Código TM")
        self._tabs_abj.addTab(self._p_err, "Errores")
        self._tabs_abj.addTab(self._p_sal, "Salida")

        self._dock_abj = QDockWidget("Resultados", self)
        self._dock_abj.setWidget(self._tabs_abj)
        self._dock_abj.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._dock_abj)

        # Tamaños iniciales (se ajustan al tamaño real de la ventana al mostrarse)
        self._tamanos_iniciales()

    # ── Distribución de paneles ───────────────────────────────────────

    def _tamanos_iniciales(self):
        """Reparte el espacio dando prioridad al editor de código."""
        ancho, alto = max(self.width(), 900), max(self.height(), 600)
        izq = int(min(max(ancho * 0.15, 170), 260))
        der = int(min(max(ancho * 0.25, 280), 420))
        abj = int(min(max(alto * 0.30, 180), 300))
        self.resizeDocks([self._dock_izq, self._dock_der], [izq, der], Qt.Horizontal)
        self.resizeDocks([self._dock_abj], [abj], Qt.Vertical)

    def showEvent(self, evento):
        super().showEvent(evento)
        if not getattr(self, "_distribucion_lista", False):
            self._distribucion_lista = True
            # Esperar a que se aplique el maximizado antes de repartir el espacio
            QTimer.singleShot(0, self._tamanos_iniciales)

    def _restablecer_paneles(self):
        """Muestra y reacomoda todos los paneles en su posición original."""
        for dock, area in ((self._dock_izq, Qt.LeftDockWidgetArea),
                           (self._dock_der, Qt.RightDockWidgetArea),
                           (self._dock_abj, Qt.BottomDockWidgetArea)):
            dock.setFloating(False)
            self.addDockWidget(area, dock)
            dock.setVisible(True)
        self._ocultos.clear()
        self._tamanos_iniciales()
        self._set_estado("Distribución de paneles restablecida")

    def _dock_visibilidad(self, dock, visible: bool):
        # isHidden() distingue un cierre del usuario de una ventana minimizada
        if visible:
            self._ocultos[dock] = False
        elif dock.isHidden() and not self.isMinimized():
            self._ocultos[dock] = True

    def _mostrar_dock(self, dock, forzar: bool = False):
        """Muestra un panel, salvo que el usuario lo haya ocultado (o si se fuerza)."""
        if forzar or not self._ocultos.get(dock, False):
            dock.setVisible(True)
            dock.raise_()

    # ── Conexión de señales ───────────────────────────────────────────

    def _conectar_senales(self):
        # Archivo
        self._acc_nuevo.triggered.connect(self._nuevo_archivo)
        self._acc_abrir.triggered.connect(self._abrir_archivo)
        self._acc_guardar.triggered.connect(self._guardar)
        self._acc_guar_as.triggered.connect(self._guardar_como)
        self._acc_cerrar.triggered.connect(lambda: self._cerrar_tab(self._tabs_editor.currentIndex()))
        self._acc_salir.triggered.connect(self.close)

        # Compilar
        self._acc_lexico.triggered.connect(lambda: self._compilar("lexical"))
        self._acc_sintac.triggered.connect(lambda: self._compilar("syntax"))
        self._acc_semant.triggered.connect(lambda: self._compilar("semantic"))
        self._acc_ir.triggered.connect(lambda: self._compilar("tm"))
        self._p_tm.ejecutar_solicitado.connect(lambda: self._compilar("run"))

        # Consola de ejecución (pestaña Salida)
        self._p_sal.enviado.connect(self._ejec_enviar)
        self._p_sal.detener_solicitado.connect(self._ejec_detener)
        self._acc_ejec.triggered.connect(lambda: self._compilar("run"))
        self._acc_todo.triggered.connect(lambda: self._compilar("run"))

        # Zoom editor
        self._acc_zoom_in.triggered.connect(self._zoom_in_editor)
        self._acc_zoom_out.triggered.connect(self._zoom_out_editor)
        self._acc_zoom_reset.triggered.connect(self._zoom_reset_editor)

        # Pestañas del editor
        self._tabs_editor.tabCloseRequested.connect(self._cerrar_tab)
        self._tabs_editor.currentChanged.connect(self._tab_cambiado)

        # Explorador
        self._p_arch.archivo_abierto.connect(self._abrir_ruta)

        # Panel de errores → navegar al editor
        self._p_err.ir_a_linea.connect(self._ir_a_linea_activa)
        self._p_err.ir_a_linea.connect(
            lambda n: self._mostrar_panel(self._p_err)
        )

    def _ir_a_linea_activa(self, n: int):
        if self._editor:
            self._editor.ir_a_linea(n)

    # ── Zoom del editor ────────────────────────────────────────────────

    def _zoom_in_editor(self):
        if self._editor:
            self._editor.zoom_in()

    def _zoom_out_editor(self):
        if self._editor:
            self._editor.zoom_out()

    def _zoom_reset_editor(self):
        if self._editor:
            self._editor.zoom_reset()

    def _mostrar_panel(self, panel: QWidget):
        """Cambia la pestaña activa al panel dado, sólo si no está flotando."""
        # indexOf devuelve -1 cuando el widget no está en el tab bar
        if self._tabs_abj.indexOf(panel) >= 0:
            self._tabs_abj.setCurrentWidget(panel)
            self._mostrar_dock(self._dock_abj)

    def actualizar_check_tema(self, nombre: str):
        """Marca el tema activo en el menú Ver → Tema."""
        for n, acc in self._acc_temas.items():
            acc.setChecked(n == nombre)

    # ── Gestión de pestañas ───────────────────────────────────────────

    def _crear_tab(self, titulo: str = "Sin título") -> EditorCodigo:
        """Crea un nuevo EditorCodigo, lo agrega como pestaña y lo devuelve."""
        editor = EditorCodigo()
        editor._ruta_arch = None
        editor._modificado = False
        idx = self._tabs_editor.addTab(editor, titulo)
        self._tabs_editor.setCurrentIndex(idx)
        # Señales propias de este editor
        editor.cursor_movido.connect(self._actualizar_posicion)
        editor.textChanged.connect(self._al_modificar)
        # Aplicar el tema activo al nuevo editor
        if self._gestor:
            nombre = self._gestor.actual
            paleta = self._gestor.paleta(nombre)
            editor.set_tema(nombre, paleta)
        return editor

    def _tab_titulo(self, editor: EditorCodigo) -> str:
        """Devuelve el título adecuado para la pestaña del editor dado."""
        nombre = os.path.basename(editor._ruta_arch) if editor._ruta_arch else "Sin título"
        return nombre + (" •" if editor._modificado else "")

    def _tab_cambiado(self, idx: int):
        """Actualiza título de ventana y barra de estado al cambiar de pestaña."""
        self._actualizar_titulo()
        editor = self._tabs_editor.widget(idx)
        if editor and editor._ruta_arch:
            self._set_estado(editor._ruta_arch)
        else:
            self._set_estado("Nuevo archivo")

    def _cerrar_tab(self, idx: int):
        """Solicita confirmación si hay cambios, luego cierra la pestaña."""
        editor = self._tabs_editor.widget(idx)
        if editor and editor._modificado:
            self._tabs_editor.setCurrentIndex(idx)
            titulo = self._tabs_editor.tabText(idx).rstrip(" •")
            msg = QMessageBox(self)
            msg.setWindowTitle("Cambios sin guardar")
            msg.setText(f"¿Qué deseas hacer con «{titulo}»?")
            msg.setIcon(QMessageBox.Question)
            btn_guardar = msg.addButton("Guardar", QMessageBox.AcceptRole)
            btn_salir   = msg.addButton("Cerrar",  QMessageBox.DestructiveRole)
            btn_cancel  = msg.addButton("Cancelar", QMessageBox.RejectRole)
            msg.setDefaultButton(btn_guardar)
            self._colorear_dialogo(msg)
            msg.exec()
            self._aplicar_titlebar()   # restaurar color tras cerrar el diálogo
            clicked = msg.clickedButton()
            if clicked == btn_guardar:
                self._tabs_editor.setCurrentIndex(idx)
                self._guardar()
            elif clicked == btn_cancel:
                return

        self._tabs_editor.removeTab(idx)

        # Si ya no quedan pestañas, limpiar título y estado
        if self._tabs_editor.count() == 0:
            self.setWindowTitle(self.TITULO)
            self._lbl_arch.setText("")
            self._set_estado("Sin archivos abiertos")

    # ── Acciones de archivo ───────────────────────────────────────────

    def _nuevo_archivo(self):
        """Crea una pestaña nueva con un editor en blanco."""
        self._crear_tab("Sin título")
        self._actualizar_titulo()
        self._set_estado("Nuevo archivo")

    def _abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "",
            "Archivos fuente (*.src *.txt);;Todos los archivos (*)"
        )
        if ruta:
            self._abrir_ruta(ruta)

    def _abrir_ruta(self, ruta: str):
        # Si el archivo ya está abierto en otra pestaña, sólo cambiar a ella
        for i in range(self._tabs_editor.count()):
            ed = self._tabs_editor.widget(i)
            if getattr(ed, "_ruta_arch", None) == ruta:
                self._tabs_editor.setCurrentIndex(i)
                return
        # Abrir en pestaña nueva
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            editor = self._crear_tab(os.path.basename(ruta))
            editor.setPlainText(contenido)
            editor._ruta_arch = ruta
            editor._modificado = False
            self._actualizar_titulo()
            self._set_estado(f"Abierto: {os.path.basename(ruta)}")
            self._p_arch.seleccionar_archivo(ruta)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{ex}")

    def _guardar(self):
        if self._ruta_arch:
            self._escribir_archivo(self._ruta_arch)
        else:
            self._guardar_como()

    def _guardar_como(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar como", "",
            "Archivos fuente (*.src);;Archivos de texto (*.txt);;Todos (*)"
        )
        if ruta:
            self._escribir_archivo(ruta)
            self._ruta_arch = ruta
            self._actualizar_titulo()

    def _escribir_archivo(self, ruta: str):
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
            self._modificado = False
            self._actualizar_titulo()
            self._set_estado(f"Guardado: {os.path.basename(ruta)}")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{ex}")

    def _confirmar_descarte(self) -> bool:
        if not self._modificado:
            return True
        resp = QMessageBox.question(
            self, "Cambios sin guardar",
            "¿Descartar los cambios actuales?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if resp == QMessageBox.Save:
            self._guardar()
            return True
        return resp == QMessageBox.Discard

    # ── Compilación (en hilo de fondo) ─────────────────────────────────

    def _compilar(self, fase: str):
        """Lanza la compilación en un QThread para no bloquear la UI."""
        if not self._editor:
            return

        # Evitar doble compilación simultánea (bandera simple, sin isRunning())
        if getattr(self, "_compilando", False):
            return
        self._compilando = True

        # Una nueva compilación termina la ejecución TM que siguiera en curso
        self._detener_ejecucion(esperar=True)

        self._set_estado(f"Compilando ({fase})...")
        self._limpiar_paneles()
        self._acc_lexico.setEnabled(False)
        self._acc_sintac.setEnabled(False)
        self._acc_semant.setEnabled(False)

        texto = self._editor.toPlainText()
        ruta  = self._ruta_arch or ""

        # Reutilizar o crear hilo (NO usar deleteLater para evitar referencia inválida)
        self._hilo_compilacion  = QThread(self)
        self._worker_compilacion = _WorkerCompilacion(self._servicio, fase, ruta, texto)
        self._worker_compilacion.moveToThread(self._hilo_compilacion)

        # Conectar al método real (no lambda) → Qt usa AutoConnection → queued entre hilos
        self._hilo_compilacion.started.connect(self._worker_compilacion.ejecutar)
        self._worker_compilacion.terminado.connect(self._compilacion_terminada)
        self._worker_compilacion.terminado.connect(self._hilo_compilacion.quit)
        self._hilo_compilacion.finished.connect(self._worker_compilacion.deleteLater)

        self._hilo_compilacion.start()

    def _compilacion_terminada(self, fase: str, res):
        """
        Slot ejecutado en el hilo PRINCIPAL gracias a AutoConnection.
        Actualiza la UI con el resultado de la compilación.
        """
        self._compilando = False
        self._acc_lexico.setEnabled(True)
        self._acc_sintac.setEnabled(True)
        self._acc_semant.setEnabled(True)

        # Separar errores por tipo para mostrar solo los correspondientes a cada fase
        errores_sint = [e for e in res.err if getattr(e, "tipo", "") == "sintáctico"]
        errores_sem  = [e for e in res.err if getattr(e, "tipo", "") == "semántico"]

        # Determinar qué errores mostrar en el panel de errores según la fase
        if fase == "lexical":
            errores_panel = res.err  # errores léxicos (todos)
        elif fase == "syntax":
            errores_panel = errores_sint
        elif fase == "semantic":
            errores_panel = errores_sem
        elif fase in ("tm", "run"):
            # Para generar/ejecutar TM se muestran todos los errores que lo impiden
            errores_panel = res.err
        else:
            errores_panel = res.err

        if res.tok:
            self._p_tok.cargar(res.tok)
        if errores_panel:
            self._p_err.cargar(errores_panel)
            self._mostrar_panel(self._p_err)
        if res.sim:
            self._p_sim.cargar(res.sim)
        if res.arb:
            self._p_arb.cargar(res.arb, errores_sint)
        if getattr(res, "arb_anotado", None):
            self._p_arb_semant.cargar(res.arb_anotado, errores_sem)
        if res.ir:
            self._p_ir.cargar(res.ir, res.ruta_ci)
        if res.tm:
            self._p_tm.cargar(res.tm, res.ruta_tm)
        if res.sal:
            self._p_sal.cargar(res.sal)

        if fase == "lexical":
            self._mostrar_panel(self._p_tok)
        elif fase == "syntax":
            self._mostrar_panel(self._p_tok)
            if res.arb is not None:
                self._mostrar_dock(self._dock_der)
                self._tabs_der.setCurrentWidget(self._p_arb)
        elif fase in ("semantic", "tm", "run"):
            if getattr(res, "arb_anotado", None) is not None:
                self._mostrar_dock(self._dock_der)
                self._tabs_der.setCurrentWidget(self._p_arb_semant)
            elif res.arb is not None:
                self._mostrar_dock(self._dock_der)
                self._tabs_der.setCurrentWidget(self._p_arb)

            # Mostrar tabla de símbolos en el panel de análisis (derecha)
            if res.sim:
                self._mostrar_dock(self._dock_der)
                self._tabs_der.setCurrentWidget(self._p_sim)

            if errores_panel:
                self._mostrar_panel(self._p_err)
            elif res.tm:
                self._mostrar_panel(self._p_tm)
            elif res.sal:
                self._mostrar_panel(self._p_sal)
            else:
                self._mostrar_panel(self._p_tok)

        n_err = len(errores_panel)
        n_err_total = len(res.err)
        if n_err:
            self._set_estado(f"Compilación completada con {n_err} error(es)")
        else:
            self._set_estado("Compilación exitosa")

        # Marcar en el editor solo los errores de la fase actual
        if self._editor and errores_panel:
            self._editor.marcar_errores([e for e in errores_panel if getattr(e, "linea", 0) > 0])
        elif self._editor:
            self._editor.limpiar_errores()

        if fase in ("tm", "run") and not errores_panel and res.ruta_tm:
            self._set_estado(f"Código intermedio y código TM generados: "
                             f"{os.path.basename(res.ruta_ci)}, {os.path.basename(res.ruta_tm)}")
            if fase == "run":
                self._ejecutar_tm(res.ruta_tm)

    # ── Ejecución en el simulador TM ───────────────────────────────────

    @staticmethod
    def _mensaje_ejecucion(res) -> str:
        """Mensaje comprensible para el usuario según el resultado del simulador."""
        if res.estado == "CANCELADO":
            # Sólo ocurre con "Detener", una nueva compilación o al cerrar el IDE
            return "Ejecución detenida por el usuario."
        if res.estado == "LIMITE":
            return ("La ejecución se detuvo: el programa superó el número máximo de "
                    "instrucciones permitidas (posible ciclo infinito).")
        if "División entre cero" in res.mensaje:
            return "La ejecución se detuvo: división entre cero."
        if "memoria" in res.mensaje:
            return "La ejecución se detuvo: acceso inválido a memoria."
        return "La ejecución se detuvo por un error."

    def _ejecutando(self) -> bool:
        return getattr(self, "_worker_ejec", None) is not None

    def _ejecutar_tm(self, ruta_tm: str):
        """
        Ejecuta en el simulador el mismo archivo .tm que se muestra en el
        panel "Código TM", en un hilo aparte. La pestaña "Salida" funciona como
        consola: cada instrucción IN pausa la máquina y muestra un campo para
        introducir el dato; las salidas aparecen conforme se producen.
        """
        self._detener_ejecucion(esperar=True)

        sal = self._p_sal
        programa = (os.path.basename(self._ruta_arch) if self._ruta_arch
                    else "programa sin guardar")
        self._id_ejec = getattr(self, "_id_ejec", 0) + 1
        self._solicitud_actual = None
        self._ultimo_valor = ""

        sal.iniciar_ejecucion(programa)
        sal.registro(f"Archivo .tm cargado en el simulador: {ruta_tm}")
        # La consola es necesaria para escribir los datos: se muestra siempre
        self._mostrar_dock(self._dock_abj, forzar=True)
        self._mostrar_panel(sal)
        self._set_estado("Ejecutando TM...")

        self._hilo_ejec = QThread(self)
        self._worker_ejec = _WorkerEjecucion(self._id_ejec, self._servicio, ruta_tm)
        self._worker_ejec.moveToThread(self._hilo_ejec)
        self._hilo_ejec.started.connect(self._worker_ejec.ejecutar)
        self._worker_ejec.salida.connect(self._ejec_salida)
        self._worker_ejec.entrada_requerida.connect(self._ejec_entrada)
        self._worker_ejec.terminado.connect(self._ejec_terminada)
        self._worker_ejec.terminado.connect(self._hilo_ejec.quit)
        self._hilo_ejec.finished.connect(self._worker_ejec.deleteLater)
        self._hilo_ejec.start()

    def _detener_ejecucion(self, esperar: bool = False):
        """Cancela la ejecución en curso (si la hay)."""
        worker = getattr(self, "_worker_ejec", None)
        if worker is None:
            return
        worker.cancelar()
        if esperar:
            hilo = self._hilo_ejec
            self._worker_ejec = None          # sus señales posteriores se ignoran
            self._id_ejec = getattr(self, "_id_ejec", 0) + 1
            hilo.quit()
            hilo.wait(5000)
            self._p_sal.set_ejecutando(False)

    # Slots de la ejecución (hilo principal)

    def _ejec_salida(self, id_ejec: int, linea: str):
        if id_ejec == self._id_ejec:
            self._p_sal.resultado(linea)

    def _ejec_entrada(self, id_ejec: int, sol):
        if id_ejec != self._id_ejec:
            return
        sal = self._p_sal
        variable = nombre_variable(sol.comentario)
        if sol.error_previo and self._solicitud_actual is not None:
            sal.registro(f"  rechazado por el simulador: {sol.error_previo}")
            sal.valor_rechazado(mensaje_valor_invalido(self._ultimo_valor, sol.tipo),
                                variable, sol.tipo)
        else:
            sal.registro(f"IN  [instrucción {sol.direccion}] {sol.comentario}: esperando valor")
            sal.solicitar(variable, sol.tipo)
        self._solicitud_actual = sol
        self._mostrar_dock(self._dock_abj, forzar=True)
        self._mostrar_panel(sal)
        self._set_estado("Esperando entrada...")

    def _ejec_enviar(self, texto: str):
        worker = getattr(self, "_worker_ejec", None)
        sol = self._solicitud_actual
        if worker is None or sol is None:
            return
        variable = nombre_variable(sol.comentario)
        self._ultimo_valor = texto
        self._p_sal.valor_introducido(variable, texto.strip())
        self._p_sal.registro(f"IN  [instrucción {sol.direccion}] {sol.comentario} <- {texto.strip()}")
        self._set_estado("Ejecutando TM...")
        worker.responder(texto)

    def _ejec_detener(self):
        if self._ejecutando():
            self._p_sal.registro("Detención solicitada por el usuario")
            self._detener_ejecucion(esperar=False)

    def _ejec_terminada(self, id_ejec: int, res):
        if id_ejec != self._id_ejec:
            return
        self._worker_ejec = None
        self._solicitud_actual = None
        sal = self._p_sal

        if isinstance(res, Exception):
            sal.fin_con_error("No se pudo cargar el código TM para ejecutarlo.")
            sal.registro(f"Error al cargar el archivo .tm: {res}")
            self._p_err.cargar([Err(tipo="ejecución", linea=0, col=0, msg=str(res))])
            self._set_estado("Error al cargar el código TM")
            return

        sal.registro(f"Estado final: {res.estado} — {res.mensaje}")
        sal.registro(f"Instrucciones ejecutadas: {res.pasos}")
        if res.instruccion is not None and not res.correcto:
            sal.registro(f"Instrucción donde se detuvo: "
                         f"{res.instruccion.direccion}: {res.instruccion.op} "
                         f"{res.instruccion.operandos()}")
        sal.registro(f"pc final: {res.pc}")
        sal.registro("Registros: " + "  ".join(f"r{i}={v}" for i, v in enumerate(res.registros)))

        if res.correcto:
            sal.fin_correcto()
            self._set_estado("Ejecución TM finalizada correctamente")
        else:
            mensaje = self._mensaje_ejecucion(res)
            sal.fin_con_error(mensaje)
            if res.estado != "CANCELADO":
                self._p_err.cargar([Err(tipo="ejecución", linea=0, col=0,
                                        msg=f"{mensaje} Detalle: {res.mensaje}.")])
            self._set_estado(mensaje)

    def _limpiar_paneles(self):
        self._p_tok.limpiar()
        self._p_err.limpiar()
        self._p_sim.limpiar()
        self._p_arb.limpiar()
        self._p_arb_semant.limpiar()
        self._p_ir.limpiar()
        self._p_tm.limpiar()
        self._p_sal.limpiar()
        # Quitar subrayados de error del editor activo
        if self._editor:
            self._editor.limpiar_errores()

    # ── Helpers ───────────────────────────────────────────────────────

    def _actualizar_posicion(self, linea: int, col: int):
        self._lbl_pos.setText(f"Ln {linea}, Col {col}")

    def _al_modificar(self):
        editor = self._editor
        if editor and not editor._modificado:
            editor._modificado = True
            self._actualizar_titulo()

    def _actualizar_titulo(self):
        editor = self._editor
        if editor:
            nombre = os.path.basename(editor._ruta_arch) if editor._ruta_arch else "Sin título"
            mod = " •" if editor._modificado else ""
            self.setWindowTitle(f"{nombre}{mod} — {self.TITULO}")
            self._lbl_arch.setText(nombre)
            # Actualizar el texto de la pestaña activa
            idx = self._tabs_editor.currentIndex()
            if idx >= 0:
                self._tabs_editor.setTabText(idx, nombre + mod)
        else:
            self.setWindowTitle(self.TITULO)
            self._lbl_arch.setText("")

    def _set_estado(self, msg: str):
        self._lbl_estado.setText(msg)

    def _aplicar_titlebar(self):
        """Colorea la barra de título nativa según el tema activo."""
        if not self._gestor:
            return
        paleta = self._gestor.paleta()
        color_bg = paleta.get("bg3", "#2d2d2d")
        # El texto de la barra es oscuro si el fondo es claro (luminancia > 0.5)
        r, g, b = int(color_bg[1:3], 16), int(color_bg[3:5], 16), int(color_bg[5:7], 16)
        luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        es_oscuro = luminancia < 0.5
        hwnd = int(self.winId())
        _aplicar_color_titlebar(hwnd, color_bg, es_oscuro)

    def _colorear_dialogo(self, dlg):
        """Aplica el color de barra de título del tema activo a un diálogo (ej. QMessageBox)."""
        if not self._gestor:
            return
        paleta = self._gestor.paleta()
        color_bg = paleta.get("bg3", "#2d2d2d")
        r, g, b = int(color_bg[1:3], 16), int(color_bg[3:5], 16), int(color_bg[5:7], 16)
        luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        es_oscuro = luminancia < 0.5
        _aplicar_color_titlebar(int(dlg.winId()), color_bg, es_oscuro)

    # ── Cierre ────────────────────────────────────────────────────────

    def closeEvent(self, evento):
        """Pide confirmar el cierre si hay pestañas con cambios sin guardar."""
        pestanas_modificadas = [
            (i, self._tabs_editor.widget(i))
            for i in range(self._tabs_editor.count())
            if getattr(self._tabs_editor.widget(i), "_modificado", False)
        ]
        if not pestanas_modificadas:
            self._detener_ejecucion(esperar=True)
            evento.accept()
            return

        nombres = "\n".join(
            f"  • {self._tabs_editor.tabText(i).rstrip(' •')}"
            for i, _ in pestanas_modificadas
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("Cambios sin guardar")
        msg.setText(f"Hay archivos con cambios sin guardar:\n{nombres}\n\n¿Qué deseas hacer?")
        msg.setIcon(QMessageBox.Question)
        btn_guardar = msg.addButton("Guardar", QMessageBox.AcceptRole)
        btn_salir   = msg.addButton("Salir",   QMessageBox.DestructiveRole)
        btn_cancel  = msg.addButton("Cancelar", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_guardar)
        self._colorear_dialogo(msg)
        msg.exec()
        self._aplicar_titlebar()   # restaurar color tras cerrar el diálogo
        clicked = msg.clickedButton()
        if clicked == btn_guardar:
            for _, ed in pestanas_modificadas:
                if ed._modificado:
                    self._tabs_editor.setCurrentWidget(ed)
                    self._guardar()
            self._detener_ejecucion(esperar=True)
            evento.accept()
        elif clicked == btn_salir:
            self._detener_ejecucion(esperar=True)
            evento.accept()
        else:
            evento.ignore()
