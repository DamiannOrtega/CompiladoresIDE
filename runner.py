#!/usr/bin/env python
# runner.py — Ejecutor de línea de comandos del compilador
#
# Uso:
#   python runner.py <archivo>                   → Fase léxica + sintáctica + semántica
#   python runner.py <archivo> --solo-lexico      → Solo fase léxica
#   python runner.py <archivo> --solo-sintactico  → Fase léxica + sintáctica
#
# Salida en outputs/:
#   tokens.json               Tokens reconocidos
#   errores_lexicos.json      Errores léxicos (si los hay)
#   ast.txt                   Árbol sintáctico original en texto ASCII
#   errores_sintacticos.json  Errores sintácticos (si los hay)
#   errores_sintacticos.txt   Errores sintácticos en formato legible
#   ast_anotado.txt           Árbol sintáctico con anotaciones semánticas
#   tabla_simbolos.json       Tabla de símbolos en JSON
#   tabla_simbolos.txt        Tabla de símbolos formateada en texto
#   errores_semanticos.json   Errores semánticos en JSON
#   errores_semanticos.txt    Errores semánticos en formato legible

import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ide.compilador.lexico import analyze
from ide.compilador.sintatico import parse
from ide.compilador.semantico import analyze_semantics, ast_anotado_a_texto


# ── Renderizador ASCII del AST original ───────────────────────────────────────

def _ast_lineas(nodo, prefijo: str = "", es_ultimo: bool = True) -> list:
    """Genera líneas de texto del AST en formato árbol ASCII."""
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


# ── Formateador de Tabla de Símbolos en Texto ─────────────────────────────────

def _tabla_simbolos_a_texto(simbolos, ruta_entrada: str) -> str:
    lineas = [
        f"Tabla de Simbolos",
        f"Archivo fuente: {ruta_entrada}",
        "-" * 88,
        f"{'Nombre':<15} {'Tipo':<8} {'Ambito':<8} {'Dir. Memoria':<14} {'Tam(B)':<8} {'Lin. Decl':<11} {'Referencias':<18}",
        "-" * 88,
    ]
    for s in simbolos:
        dir_str = f"{s.desplazamiento} (0x{s.desplazamiento:04X})"
        refs_str = ", ".join(str(r) for r in s.referencias) if s.referencias else "—"
        lineas.append(
            f"{s.nombre:<15} {s.tipo:<8} {s.ambito:<8} {dir_str:<14} {s.tam_bytes:<8} {s.linea:<11} {refs_str:<18}"
        )
    lineas.append("-" * 88)
    lineas.append(f"Total de identificadores registrados: {len(simbolos)}\n")
    return "\n".join(lineas)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main():
    args            = sys.argv[1:]
    solo_lexico     = "--solo-lexico" in args
    solo_sintactico = "--solo-sintactico" in args
    args            = [a for a in args if not a.startswith("--")]

    if not args:
        print("Uso: python runner.py <archivo_fuente> [--solo-lexico] [--solo-sintactico]")
        print("Ejemplo: python runner.py testSintactico.src")
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

    sep = "=" * 60

    # ── Fase 1: Análisis léxico ───────────────────────────────────────────────
    print(sep)
    print(f"Compilador - Archivo: {ruta_entrada}")
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

    # Guardar AST original como texto ASCII
    ruta_ast = os.path.join(dir_salida, "ast.txt")
    encabezado_ast = (
        f"Arbol Sintactico Abstracto (Original)\n"
        f"Archivo: {ruta_entrada}\n"
        f"{'-' * 40}\n"
    )
    with open(ruta_ast, "w", encoding="utf-8") as f:
        f.write(encabezado_ast)
        f.write(_ast_a_texto(arbol))
        f.write("\n")

    # Guardar errores sintácticos como JSON
    ruta_err_sint = os.path.join(dir_salida, "errores_sintacticos.json")
    with open(ruta_err_sint, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errores_sint], f, ensure_ascii=False, indent=2)

    # Guardar errores sintácticos como TXT
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
            print(f"  (AST parcial generado - recuperacion activa)")
    else:
        print(f"  OK: Programa sintacticamente correcto")

    if solo_sintactico:
        print(f"\nArchivos generados en: {dir_salida}")
        print(f"  {os.path.basename(ruta_tok)}")
        print(f"  {os.path.basename(ruta_err_lex)}")
        print(f"  {os.path.basename(ruta_ast)}")
        print(f"  {os.path.basename(ruta_err_sint)}")
        print(f"  {os.path.basename(ruta_err_txt)}")
        return

    print()

    # ── Fase 3: Análisis semántico ────────────────────────────────────────────
    print(f"Fase 3 - Analisis semantico")

    if errores_sint:
        print("  X Omitido: existen errores sintacticos.")
        print("    Corrija los errores sintacticos antes de ejecutar el analisis semantico.")
        return

    arbol_anotado, tabla, errores_sem = analyze_semantics(arbol)
    simbolos = tabla.obtener_simbolos()

    # Guardar AST Anotado como texto ASCII
    ruta_ast_anot = os.path.join(dir_salida, "ast_anotado.txt")
    encabezado_anot = (
        f"Arbol Sintactico Anotado (Semantico)\n"
        f"Archivo: {ruta_entrada}\n"
        f"{'-' * 40}\n"
    )
    with open(ruta_ast_anot, "w", encoding="utf-8") as f:
        f.write(encabezado_anot)
        f.write(ast_anotado_a_texto(arbol_anotado))
        f.write("\n")

    # Guardar Tabla de Símbolos en JSON
    ruta_sim_json = os.path.join(dir_salida, "tabla_simbolos.json")
    with open(ruta_sim_json, "w", encoding="utf-8") as f:
        json.dump([s.to_dict() for s in simbolos], f, ensure_ascii=False, indent=2)

    # Guardar Tabla de Símbolos en TXT
    ruta_sim_txt = os.path.join(dir_salida, "tabla_simbolos.txt")
    with open(ruta_sim_txt, "w", encoding="utf-8") as f:
        f.write(_tabla_simbolos_a_texto(simbolos, ruta_entrada))

    # Guardar Errores Semánticos en JSON
    ruta_err_sem_json = os.path.join(dir_salida, "errores_semanticos.json")
    with open(ruta_err_sem_json, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errores_sem], f, ensure_ascii=False, indent=2)

    # Guardar Errores Semánticos en TXT
    ruta_err_sem_txt = os.path.join(dir_salida, "errores_semanticos.txt")
    with open(ruta_err_sem_txt, "w", encoding="utf-8") as f:
        f.write("Errores Semanticos Detectados\n")
        f.write(f"Archivo fuente: {ruta_entrada}\n")
        f.write("-" * 52 + "\n")
        if errores_sem:
            f.write(f"Total: {len(errores_sem)} error(es) semantico(s)\n\n")
            for i, e in enumerate(errores_sem, 1):
                f.write(f"[{i}] Linea {e.linea}\n")
                f.write(f"    Tipo    : {e.error}\n")
                if e.valor:
                    f.write(f"    Elemento: '{e.valor}'\n")
                f.write(f"    Mensaje : {e.msg}\n\n")
        else:
            f.write("Sin errores semanticos. Programa semanticamente valido.\n")

    print(f"  Simbolos registrados : {len(simbolos)}")
    print(f"  Errores semanticos   : {len(errores_sem)}")

    if errores_sem:
        for e in errores_sem:
            print(f"  [SEM] L{e.linea}  {e.error}: {e.msg}")
    else:
        print("  OK: Programa semanticamente valido")

    print(f"\nArchivos generados en: {dir_salida}")
    print(f"  {os.path.basename(ruta_tok)}")
    print(f"  {os.path.basename(ruta_err_lex)}")
    print(f"  {os.path.basename(ruta_ast)}")
    print(f"  {os.path.basename(ruta_err_sint)}")
    print(f"  {os.path.basename(ruta_err_txt)}")
    print(f"  {os.path.basename(ruta_ast_anot)}")
    print(f"  {os.path.basename(ruta_sim_json)}")
    print(f"  {os.path.basename(ruta_sim_txt)}")
    print(f"  {os.path.basename(ruta_err_sem_json)}")
    print(f"  {os.path.basename(ruta_err_sem_txt)}")


if __name__ == "__main__":
    main()
