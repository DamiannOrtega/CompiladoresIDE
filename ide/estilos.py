# estilos.py — Re-exporta desde temas.py para compatibilidad
# El tema activo lo gestiona GestorTemas en temas.py.

from ide.temas import TEMAS, TEMA_POR_DEFECTO, GestorTemas

# Hoja de estilo por defecto (Oscuro) — usada si se importa directamente
HOJA = TEMAS[TEMA_POR_DEFECTO]
