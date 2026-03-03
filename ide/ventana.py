# ventana.py — Ventana principal del IDE (QMainWindow)

import os
import ctypes
import ctypes.wintypes
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTabWidget, QWidget,
    QLabel, QFileDialog, QMessageBox, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QActionGroup, QKeySequence

from ide.ui.editor import EditorCodigo
from ide.ui.panel_tok import PanelTok
from ide.ui.panel_err import PanelErr
from ide.ui.panel_sim import PanelSim
from ide.ui.panel_arb import PanelArb
from ide.ui.panel_ir import PanelIr
from ide.ui.panel_sal import PanelSal
from ide.ui.panel_archivos import PanelArchivos
from ide.servicios.compilador import ServicioCompilador
from ide.iconos import gestor_ico


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
        self._p_arb  = PanelArb()
        self._p_ir   = PanelIr()
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
        self._acc_ir      = self._accion("Generar Código IR",   "F8",  m_comp)
        m_comp.addSeparator()
        self._acc_ejec    = self._accion("Ejecutar",            "F9",  m_comp)
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
        acc_izq.setText("&Explorador / Símbolos")
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
            (self._acc_ir,     "IR"),
            (self._acc_ejec,   "Ejecutar"),
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
        # ── Izquierda: Explorador + Tabla de símbolos ──
        tabs_izq = QTabWidget()
        tabs_izq.addTab(self._p_arch, "Explorador")
        tabs_izq.addTab(self._p_sim,  "Símbolos")

        self._dock_izq = QDockWidget("Explorador", self)
        self._dock_izq.setWidget(tabs_izq)
        self._dock_izq.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock_izq)

        # ── Derecha: Árbol sintáctico + Semántico ──
        self._p_semant_info = QLabel(
            "El análisis semántico\naparecerá aquí.",
            alignment=Qt.AlignCenter
        )
        self._p_semant_info.setObjectName("semant_placeholder")

        tabs_der = QTabWidget()
        tabs_der.addTab(self._p_arb,         "Árbol Sintáctico")
        tabs_der.addTab(self._p_semant_info, "Semántico")

        self._dock_der = QDockWidget("Análisis", self)
        self._dock_der.setWidget(tabs_der)
        self._dock_der.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock_der)

        # ── Abajo: Tokens, IR, Errores, Salida ──
        self._tabs_abj = QTabWidget()
        self._tabs_abj.addTab(self._p_tok, "Tokens")
        self._tabs_abj.addTab(self._p_ir,  "Código Intermedio")
        self._tabs_abj.addTab(self._p_err, "Errores")
        self._tabs_abj.addTab(self._p_sal, "Salida")

        self._dock_abj = QDockWidget("Resultados", self)
        self._dock_abj.setWidget(self._tabs_abj)
        self._dock_abj.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._dock_abj)

        # Tamaños iniciales
        self.resizeDocks([self._dock_izq], [220], Qt.Horizontal)
        self.resizeDocks([self._dock_der], [260], Qt.Horizontal)
        self.resizeDocks([self._dock_abj], [200], Qt.Vertical)

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
        self._acc_ir.triggered.connect(lambda: self._compilar("ir"))
        self._acc_ejec.triggered.connect(lambda: self._compilar("run"))
        self._acc_todo.triggered.connect(lambda: self._compilar("run"))

        # Pestañas del editor
        self._tabs_editor.tabCloseRequested.connect(self._cerrar_tab)
        self._tabs_editor.currentChanged.connect(self._tab_cambiado)

        # Explorador
        self._p_arch.archivo_abierto.connect(self._abrir_ruta)

        # Panel de errores → navegar al editor
        self._p_err.ir_a_linea.connect(self._ir_a_linea_activa)
        self._p_err.ir_a_linea.connect(
            lambda n: self._tabs_abj.setCurrentWidget(self._p_err)
        )

    def _ir_a_linea_activa(self, n: int):
        if self._editor:
            self._editor.ir_a_linea(n)

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
            self._p_arch.set_directorio(os.path.dirname(ruta))
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

    # ── Compilación ───────────────────────────────────────────────────

    def _compilar(self, fase: str):
        self._set_estado(f"Compilando ({fase})...")
        self._limpiar_paneles()

        res = self._servicio.compilar(fase, self._ruta_arch or "")

        # Poblar paneles según la fase
        if res.tok:
            self._p_tok.cargar(res.tok)
        if res.err:
            self._p_err.cargar(res.err)
            self._tabs_abj.setCurrentWidget(self._p_err)
        if res.sim:
            self._p_sim.cargar(res.sim)
        if res.arb:
            self._p_arb.cargar(res.arb)
        if res.ir:
            self._p_ir.cargar(res.ir)
        if res.sal:
            self._p_sal.cargar(res.sal)

        # Cambiar al tab más relevante
        if fase == "lexical":
            self._tabs_abj.setCurrentWidget(self._p_tok)
        elif fase in ("syntax", "semantic"):
            self._tabs_abj.setCurrentWidget(self._p_tok)
        elif fase == "ir":
            self._tabs_abj.setCurrentWidget(self._p_ir)
        elif fase == "run":
            self._tabs_abj.setCurrentWidget(self._p_sal)

        n_err = len(res.err)
        if n_err:
            self._set_estado(f"Compilación completada con {n_err} error(es)")
        else:
            self._set_estado("Compilación exitosa ✓")

    def _limpiar_paneles(self):
        self._p_tok.limpiar()
        self._p_err.limpiar()
        self._p_sim.limpiar()
        self._p_arb.limpiar()
        self._p_ir.limpiar()
        self._p_sal.limpiar()

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
            evento.accept()
        elif clicked == btn_salir:
            evento.accept()
        else:
            evento.ignore()
