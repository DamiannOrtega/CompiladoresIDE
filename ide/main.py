# main.py — Punto de entrada del IDE

import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon

from ide.temas import GestorTemas
from ide.iconos import gestor_ico
from ide.ventana import VentanaPrincipal


def main():
    # Registrar App User Model ID para que Windows muestre el ícono correcto en la barra de tareas
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Compiladores.IDE.1.0")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("IDE Compiladores")
    app.setOrganizationName("Compiladores")

    # Fuente base
    fuente = QFont("Segoe UI", 10)
    app.setFont(fuente)

    # Tema guardado
    gestor = GestorTemas(app)
    gestor.cargar()

    # Icono de aplicación (ventana + barra de tareas)
    _ico_path = os.path.join(os.path.dirname(__file__), "recursos", "icono.ico")
    if os.path.exists(_ico_path):
        ico_app = QIcon(_ico_path)
    else:
        ico_app = gestor_ico.icono("app", gestor.paleta().get("acento", "#007acc"))
    app.setWindowIcon(ico_app)

    # Ventana principal
    ventana = VentanaPrincipal(gestor)
    ventana.setWindowIcon(ico_app)
    ventana.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
