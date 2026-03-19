#!/usr/bin/env python
# runner.py — Ejecutor de línea de comandos del analizador léxico
#
# Uso:
#   python runner.py entrada.txt
#
# Genera:
#   outputs/tokens.json
#   outputs/errores.json

import sys
import json
import os

# Asegurar que la raíz del proyecto esté en el path para importar `ide`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide.compilador.lexico import analyze


def main():
    # ── Validar argumento ─────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print("Uso: python runner.py <archivo_entrada>")
        print("Ejemplo: python runner.py input.txt")
        sys.exit(1)

    ruta_entrada = sys.argv[1]

    # ── Leer el archivo fuente ────────────────────────────────────────────
    try:
        with open(ruta_entrada, "r", encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{ruta_entrada}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        sys.exit(1)

    # ── Analizar ──────────────────────────────────────────────────────────
    tokens, errores = analyze(texto)

    # ── Preparar directorio de salida ─────────────────────────────────────
    directorio_salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(directorio_salida, exist_ok=True)

    ruta_tokens  = os.path.join(directorio_salida, "tokens.json")
    ruta_errores = os.path.join(directorio_salida, "errores.json")

    # ── Escribir tokens.json ──────────────────────────────────────────────
    with open(ruta_tokens, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tokens], f, ensure_ascii=False, indent=2)

    # ── Escribir errores.json ─────────────────────────────────────────────
    with open(ruta_errores, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errores], f, ensure_ascii=False, indent=2)

    # ── Resumen en consola ────────────────────────────────────────────────
    print(f"Análisis léxico completado.")
    print(f"  Tokens encontrados : {len(tokens)}")
    print(f"  Errores encontrados: {len(errores)}")
    print(f"  Salida escrita en  : {directorio_salida}")

    if errores:
        print("\nErrores léxicos:")
        for err in errores:
            print(f"  Línea {err.linea}, Col {err.columna}: {err.error} → '{err.valor}'")


if __name__ == "__main__":
    main()
