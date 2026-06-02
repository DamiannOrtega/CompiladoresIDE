#!/usr/bin/env python
# runner.py — Ejecutor de línea de comandos del compilador
#
# Uso:
#   python runner.py <archivo>              → Fase léxica + sintáctica
#   python runner.py <archivo> --solo-lexico → Solo fase léxica
#
# Salida en outputs/:
#   tokens.json               Tokens reconocidos
#   errores_lexicos.json      Errores léxicos (si los hay)
#   ast.txt                   Árbol sintáctico en texto ASCII (si sin errores léxicos)
#   errores_sintacticos.json  Errores sintácticos (si los hay)

import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide.compilador.lexico import analyze
from ide.compilador.sintatico import parse


# ── Renderizador ASCII del AST ────────────────────────────────────────────────

def _ast_lineas(nodo, prefijo: str = "", es_ultimo: bool = True) -> list:
    """
    Genera lineas de texto del AST en formato arbol ASCII:
      Programa: main
      +-- Decl: int x   [L4]
      +-- Asignar: y    [L8]
      |   +-- Num: 5   [L8]
      +-- Si (if)       [L10]
    """
    conector  = "+-- "
    sufijo    = f"   [L{nodo.linea}]" if getattr(nodo, "linea", 0) else ""
    lineas    = [prefijo + conector + nodo.etiqueta + sufijo]
    extension = "    " if es_ultimo else "|   "
    for i, hijo in enumerate(nodo.hijos):
        lineas.extend(_ast_lineas(hijo, prefijo + extension, i == len(nodo.hijos) - 1))
    return lineas


def _ast_a_texto(raiz) -> str:
    if raiz is None:
        return "(árbol vacío)"
    sufijo = f"   [L{raiz.linea}]" if getattr(raiz, "linea", 0) else ""
    lineas = [raiz.etiqueta + sufijo]
    for i, hijo in enumerate(raiz.hijos):
        lineas.extend(_ast_lineas(hijo, "", i == len(raiz.hijos) - 1))
    return "\n".join(lineas)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main():
    args       = sys.argv[1:]
    solo_lexico = "--solo-lexico" in args
    args       = [a for a in args if not a.startswith("--")]

    if not args:
        print("Uso: python runner.py <archivo_fuente> [--solo-lexico]")
        print("Ejemplo: python runner.py docs/pruebas/valido1.src")
        sys.exit(1)

    ruta_entrada = args[0]

    try:
        with open(ruta_entrada, "r", encoding="utf-8") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró '{ruta_entrada}'")
        sys.exit(1)
    except Exception as ex:
        print(f"Error al leer el archivo: {ex}")
        sys.exit(1)

    dir_salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(dir_salida, exist_ok=True)

    sep = "-" * 56

    # ── Fase 1: Analisis lexico ───────────────────────────────────────────────
    print(sep)
    print(f"Archivo fuente : {ruta_entrada}")
    print(sep)

    tokens, errores_lex = analyze(texto)

    # Guardar tokens
    ruta_tok = os.path.join(dir_salida, "tokens.json")
    with open(ruta_tok, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tokens], f, ensure_ascii=False, indent=2)

    # Guardar errores léxicos
    ruta_err_lex = os.path.join(dir_salida, "errores_lexicos.json")
    with open(ruta_err_lex, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errores_lex], f, ensure_ascii=False, indent=2)

    print(f"Fase 1 - Analisis lexico")
    print(f"  Tokens encontrados  : {len(tokens)}")
    print(f"  Errores lexicos     : {len(errores_lex)}")
    if errores_lex:
        for e in errores_lex:
            print(f"  [LEX] L{e.linea}:C{e.columna}  {e.error}: '{e.valor}'")

    if solo_lexico:
        print(f"\nArchivos generados en: {dir_salida}")
        print(f"  {os.path.basename(ruta_tok)}")
        print(f"  {os.path.basename(ruta_err_lex)}")
        return

    print()

    # ── Fase 2: Análisis sintáctico ───────────────────────────────────────────
    print(f"Fase 2 - Analisis sintactico")

    if errores_lex:
        print("  X Omitido: existen errores lexicos.")
        print("    Corrija los errores lexicos antes de ejecutar el analisis sintactico.")
        print(f"\nArchivos generados en: {dir_salida}")
        return

    arbol, errores_sint = parse(tokens)

    # ── Guardar AST como texto ASCII ──────────────────────────────────────────
    ruta_ast = os.path.join(dir_salida, "ast.txt")
    encabezado = (
        f"Arbol Sintactico Abstracto\n"
        f"Archivo: {ruta_entrada}\n"
        f"{'-' * 40}\n"
    )
    with open(ruta_ast, "w", encoding="utf-8") as f:
        f.write(encabezado)
        f.write(_ast_a_texto(arbol))
        f.write("\n")

    # ── Guardar errores sintácticos como JSON ─────────────────────────────────
    ruta_err_sint = os.path.join(dir_salida, "errores_sintacticos.json")
    with open(ruta_err_sint, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errores_sint], f, ensure_ascii=False, indent=2)

    # ── Guardar errores sintácticos como TXT (legible) ───────────────────────
    ruta_err_txt = os.path.join(dir_salida, "errores_sintacticos.txt")
    with open(ruta_err_txt, "w", encoding="utf-8") as f:
        f.write("Errores Sintacticos Detectados\n")
        f.write(f"Archivo fuente: {ruta_entrada}\n")
        f.write("-" * 48 + "\n")
        if errores_sint:
            f.write(f"Total: {len(errores_sint)} error(es)\n\n")
            for i, e in enumerate(errores_sint, 1):
                f.write(f"[{i}] Linea {e.linea}, Columna {e.columna}\n")
                f.write(f"    Tipo    : {e.error}\n")
                f.write(f"    Token   : '{e.valor}'\n")
                f.write(f"    Mensaje : {e.msg}\n\n")
        else:
            f.write("Sin errores sintacticos. Programa correcto.\n")

    print(f"  Errores sintacticos : {len(errores_sint)}")

    if errores_sint:
        for e in errores_sint:
            print(f"  [SIN] L{e.linea}:C{e.columna}  {e.msg}")
        if arbol:
            print(f"  (AST parcial generado - recuperacion de errores activa)")
    else:
        print(f"  OK: Programa sintacticamente correcto")

    print(f"\nArchivos generados en: {dir_salida}")
    print(f"  {os.path.basename(ruta_tok)}")
    print(f"  {os.path.basename(ruta_err_lex)}")
    print(f"  {os.path.basename(ruta_ast)}")
    print(f"  {os.path.basename(ruta_err_sint)}")
    print(f"  {os.path.basename(ruta_err_txt)}")


if __name__ == "__main__":
    main()
