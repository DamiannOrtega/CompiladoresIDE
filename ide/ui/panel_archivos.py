# ui/panel_archivos.py — Explorador de archivos

import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QFileSystemModel,
    QMenu, QMessageBox, QInputDialog
)
from PySide6.QtCore import QDir, Qt, Signal, QModelIndex
from PySide6.QtGui import QIcon

from ide.iconos import gestor_ico


# ── Modelo con ícono personalizado para .src ─────────────────────────────────

class _ModeloArchivos(QFileSystemModel):
    """QFileSystemModel que devuelve un ícono propio para archivos .src."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ico_src: QIcon = QIcon()

    def set_ico_src(self, ico: QIcon):
        self._ico_src = ico
        # Notificar cambio visual en todas las filas visibles
        self.dataChanged.emit(
            self.index(self.rootPath()),
            self.index(self.rootPath()),
            [Qt.DecorationRole]
        )

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DecorationRole and index.column() == 0:
            ruta = self.filePath(index)
            if os.path.isfile(ruta) and ruta.lower().endswith(".src"):
                return self._ico_src
        return super().data(index, role)


class PanelArchivos(QWidget):
    """Explorador de archivos del directorio de trabajo."""

    # Emite la ruta del archivo seleccionado con doble clic o menú
    archivo_abierto = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._modelo = _ModeloArchivos()
        self._modelo.setRootPath(QDir.currentPath())
        self._modelo.setNameFilters(["*.src", "*.txt", "*.json", "*.py"])
        self._modelo.setNameFilterDisables(False)
        # Ícono inicial (tema oscuro por defecto)
        self._modelo.set_ico_src(gestor_ico.icono("archivo_src", "#79b8ff"))

        self._vista = QTreeView()
        self._vista.setModel(self._modelo)
        self._vista.setRootIndex(self._modelo.index(QDir.currentPath()))
        self._vista.setColumnHidden(1, True)  # tamaño
        self._vista.setColumnHidden(2, True)  # tipo
        self._vista.setColumnHidden(3, True)  # fecha
        self._vista.setHeaderHidden(True)
        self._vista.doubleClicked.connect(self._al_doble_clic)

        # Menú contextual con clic derecho
        self._vista.setContextMenuPolicy(Qt.CustomContextMenu)
        self._vista.customContextMenuRequested.connect(self._menu_contextual)

        lay.addWidget(self._vista)

    def set_directorio(self, ruta: str):
        self._modelo.setRootPath(ruta)
        self._vista.setRootIndex(self._modelo.index(ruta))

    def set_tema(self, paleta: dict):
        """Actualiza el ícono .src según el color del tema activo."""
        color = paleta.get("acento", "#007acc")
        self._modelo.set_ico_src(gestor_ico.icono("archivo_src", color))

    def _al_doble_clic(self, indice):
        ruta = self._modelo.filePath(indice)
        if os.path.isfile(ruta):
            self.archivo_abierto.emit(ruta)

    # ── Menú contextual ──────────────────────────────────────────────

    def _menu_contextual(self, pos):
        indice = self._vista.indexAt(pos)
        ruta   = self._modelo.filePath(indice) if indice.isValid() else None
        es_archivo = ruta and os.path.isfile(ruta)
        es_dir     = ruta and os.path.isdir(ruta)

        menu = QMenu(self)

        # ── Acciones según el elemento bajo el cursor ──
        if es_archivo:
            act_abrir    = menu.addAction("Abrir")
            menu.addSeparator()
            act_renombrar = menu.addAction("Renombrar")
            act_eliminar  = menu.addAction("Eliminar")
            menu.addSeparator()
        elif es_dir:
            act_renombrar = menu.addAction("Renombrar carpeta")
            act_eliminar  = menu.addAction("Eliminar carpeta")
            menu.addSeparator()
        else:
            act_abrir = act_renombrar = act_eliminar = None

        # Siempre disponibles
        act_nuevo_arch   = menu.addAction("Nuevo archivo...")
        act_nueva_carpeta = menu.addAction("Nueva carpeta...")

        elegida = menu.exec(self._vista.viewport().mapToGlobal(pos))
        if elegida is None:
            return

        # ── Despachar acciones ──
        if es_archivo and elegida == act_abrir:
            self.archivo_abierto.emit(ruta)

        elif (es_archivo or es_dir) and elegida == act_renombrar:
            self._renombrar(ruta)

        elif (es_archivo or es_dir) and elegida == act_eliminar:
            self._eliminar(ruta, es_dir)

        elif elegida == act_nuevo_arch:
            self._nuevo_archivo(ruta if es_dir else (os.path.dirname(ruta) if ruta else None))

        elif elegida == act_nueva_carpeta:
            self._nueva_carpeta(ruta if es_dir else (os.path.dirname(ruta) if ruta else None))

    # ── Operaciones ──────────────────────────────────────────────────

    def _renombrar(self, ruta: str):
        nombre_actual = os.path.basename(ruta)
        nuevo, ok = QInputDialog.getText(
            self, "Renombrar", "Nuevo nombre:", text=nombre_actual
        )
        if ok and nuevo and nuevo != nombre_actual:
            destino = os.path.join(os.path.dirname(ruta), nuevo)
            try:
                os.rename(ruta, destino)
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"No se pudo renombrar:\n{ex}")

    def _eliminar(self, ruta: str, es_dir: bool):
        tipo = "carpeta" if es_dir else "archivo"
        nombre = os.path.basename(ruta)
        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar {tipo} «{nombre}»?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return
        try:
            if es_dir:
                shutil.rmtree(ruta)
            else:
                os.remove(ruta)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{ex}")

    def _nuevo_archivo(self, directorio: str | None):
        base = directorio or self._modelo.rootPath()
        nombre, ok = QInputDialog.getText(
            self, "Nuevo archivo", "Nombre del archivo (ej. programa.src):"
        )
        if ok and nombre:
            ruta = os.path.join(base, nombre)
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write("")
                self.archivo_abierto.emit(ruta)
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"No se pudo crear el archivo:\n{ex}")

    def _nueva_carpeta(self, directorio: str | None):
        base = directorio or self._modelo.rootPath()
        nombre, ok = QInputDialog.getText(
            self, "Nueva carpeta", "Nombre de la carpeta:"
        )
        if ok and nombre:
            ruta = os.path.join(base, nombre)
            try:
                os.makedirs(ruta, exist_ok=True)
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"No se pudo crear la carpeta:\n{ex}")
