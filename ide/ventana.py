# ventana.py — Ventana principal del IDE (QMainWindow)

import os
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


class VentanaPrincipal(QMainWindow):
    """Ventana principal del IDE de compiladores."""

    TITULO = "IDE Compiladores"

    def __init__(self, gestor=None):
        super().__init__()
        self._ruta_arch = None
        self._modificado = False
        self._servicio = ServicioCompilador()
        self._gestor = gestor
        self._iconos = {}   # dict nombre→QIcon, actualizado al cambiar tema

        self._construir_ui()
        self._aplicar_iconos()          # iconos iniciales
        self._conectar_senales()
        self._nuevo_archivo()

    # ── Construcción de la UI ─────────────────────────────────────────

    def _construir_ui(self):
        self.setWindowTitle(self.TITULO)
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # Editor central
        self._editor = EditorCodigo()
        self.setCentralWidget(self._editor)

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
        """Agrega el menú Ver → Tema con las opciones de tema disponibles."""
        m_ver = self._mb.addMenu("&Ver")
        m_tema = m_ver.addMenu("Tema")

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
            # Actualizar iconos y resaltado del editor con el nuevo tema
            self._aplicar_iconos()
            paleta = self._gestor.paleta(nombre)
            self._editor.set_tema(nombre, paleta)
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

        dock_izq = QDockWidget("Explorador", self)
        dock_izq.setWidget(tabs_izq)
        dock_izq.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_izq)

        # ── Derecha: Árbol sintáctico + Semántico ──
        # Placeholder para análisis semántico (se expandirá en fases futuras)
        self._p_semant_info = QLabel(
            "El análisis semántico\naparecerá aquí.",
            alignment=Qt.AlignCenter
        )
        # objectName controlado por QSS del tema (sin hardcode de color)
        self._p_semant_info.setObjectName("semant_placeholder")

        tabs_der = QTabWidget()
        tabs_der.addTab(self._p_arb,         "Árbol Sintáctico")
        tabs_der.addTab(self._p_semant_info, "Semántico")

        dock_der = QDockWidget("Análisis", self)
        dock_der.setWidget(tabs_der)
        dock_der.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_der)

        # ── Abajo: Tokens, IR, Errores, Salida ──
        self._tabs_abj = QTabWidget()
        self._tabs_abj.addTab(self._p_tok, "Tokens")
        self._tabs_abj.addTab(self._p_ir,  "Código IR")
        self._tabs_abj.addTab(self._p_err, "Errores")
        self._tabs_abj.addTab(self._p_sal, "Salida")

        dock_abj = QDockWidget("Resultados", self)
        dock_abj.setWidget(self._tabs_abj)
        dock_abj.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_abj)


        # Tamaños iniciales
        self.resizeDocks([dock_izq], [220], Qt.Horizontal)
        self.resizeDocks([dock_der], [260], Qt.Horizontal)
        self.resizeDocks([dock_abj], [200], Qt.Vertical)

    # ── Conexión de señales ───────────────────────────────────────────

    def _conectar_senales(self):
        # Archivo
        self._acc_nuevo.triggered.connect(self._nuevo_archivo)
        self._acc_abrir.triggered.connect(self._abrir_archivo)
        self._acc_guardar.triggered.connect(self._guardar)
        self._acc_guar_as.triggered.connect(self._guardar_como)
        self._acc_salir.triggered.connect(self.close)

        # Compilar
        self._acc_lexico.triggered.connect(lambda: self._compilar("lexical"))
        self._acc_sintac.triggered.connect(lambda: self._compilar("syntax"))
        self._acc_semant.triggered.connect(lambda: self._compilar("semantic"))
        self._acc_ir.triggered.connect(lambda: self._compilar("ir"))
        self._acc_ejec.triggered.connect(lambda: self._compilar("run"))
        self._acc_todo.triggered.connect(lambda: self._compilar("run"))

        # Editor
        self._editor.cursor_movido.connect(self._actualizar_posicion)
        self._editor.textChanged.connect(self._al_modificar)

        # Explorador
        self._p_arch.archivo_abierto.connect(self._abrir_ruta)

        # Panel de errores → navegar al editor
        self._p_err.ir_a_linea.connect(self._editor.ir_a_linea)
        self._p_err.ir_a_linea.connect(
            lambda n: self._tabs_abj.setCurrentWidget(self._p_err)
        )

    def actualizar_check_tema(self, nombre: str):
        """Marca el tema activo en el menú Ver → Tema."""
        for n, acc in self._acc_temas.items():
            acc.setChecked(n == nombre)

    # ── Acciones de archivo ───────────────────────────────────────────

    def _nuevo_archivo(self):
        if not self._confirmar_descarte():
            return
        self._editor.clear()
        self._ruta_arch = None
        self._modificado = False
        self._limpiar_paneles()
        self._actualizar_titulo()
        self._set_estado("Nuevo archivo")

    def _abrir_archivo(self):
        if not self._confirmar_descarte():
            return
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "",
            "Archivos fuente (*.src *.txt);;Todos los archivos (*)"
        )
        if ruta:
            self._abrir_ruta(ruta)

    def _abrir_ruta(self, ruta: str):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self._editor.setPlainText(f.read())
            self._ruta_arch = ruta
            self._modificado = False
            self._actualizar_titulo()
            self._set_estado(f"Abierto: {os.path.basename(ruta)}")
            # Actualizar explorador al directorio del archivo
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
        if not self._modificado:
            self._modificado = True
            self._actualizar_titulo()

    def _actualizar_titulo(self):
        nombre = os.path.basename(self._ruta_arch) if self._ruta_arch else "Sin título"
        mod = " •" if self._modificado else ""
        self.setWindowTitle(f"{nombre}{mod} — {self.TITULO}")
        self._lbl_arch.setText(nombre)

    def _set_estado(self, msg: str):
        self._lbl_estado.setText(msg)

    # ── Cierre ────────────────────────────────────────────────────────

    def closeEvent(self, evento):
        if self._confirmar_descarte():
            evento.accept()
        else:
            evento.ignore()
