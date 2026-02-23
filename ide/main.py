# main.py — Punto de entrada del IDE

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ide.temas import GestorTemas
from ide.iconos import gestor_ico
from ide.ventana import VentanaPrincipal


def main():
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
    ico_app = gestor_ico.icono("app", gestor.paleta().get("acento", "#007acc"))
    app.setWindowIcon(ico_app)

    # Ventana principal
    ventana = VentanaPrincipal(gestor)
    ventana.setWindowIcon(ico_app)
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
