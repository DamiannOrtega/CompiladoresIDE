# ejercicios/probar_ejercicios.py — Compila y ejecuta en la TM todos los ejercicios
#
# Uso (desde la raíz del proyecto):
#   python ejercicios/probar_ejercicios.py            → todos los grupos
#   python ejercicios/probar_ejercicios.py grupo4     → sólo un grupo
#
# Para cada ejercicio: análisis léxico, sintáctico y semántico, generación del
# archivo .tm (en outputs/) y ejecución de ESE archivo en el simulador con los
# datos de casos.json; la salida obtenida se compara con la esperada.

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(DIR))

from ide.servicios.compilador import ServicioCompilador   # noqa: E402


def main() -> int:
    filtro = sys.argv[1] if len(sys.argv) > 1 else ""
    with open(os.path.join(DIR, "casos.json"), encoding="utf-8") as f:
        casos = json.load(f)

    def orden(ruta):
        g, e = ruta.split("/")
        return int(g[5:]), int(e[2:-4])

    servicio = ServicioCompilador()
    total = fallos = 0
    for rel in sorted(casos, key=orden):
        if filtro and not rel.startswith(filtro + "/"):
            continue
        ruta = os.path.join(DIR, rel)
        res = servicio.compilar("run", ruta=ruta)
        if res.err:
            fallos += 1
            print(f"FALLA  {rel}: no compiló")
            for e in res.err:
                print(f"         [{e.tipo}] L{e.linea}: {e.msg}")
            continue
        n_instr = sum(1 for l in res.tm.splitlines() if l.strip() and not l.lstrip().startswith("*"))
        for caso in casos[rel]:
            total += 1
            cola = list(caso["entradas"])
            ejec = servicio.ejecutar_tm(res.ruta_tm, lambda s: cola.pop(0) if cola else None)
            ok = ejec.correcto and ejec.salida == caso["salida"] and not cola
            if not ok:
                fallos += 1
                print(f"FALLA  {rel}  entradas={caso['entradas']}")
                print(f"         estado: {ejec.estado} {ejec.mensaje}")
                print(f"         esperado: {caso['salida']}")
                print(f"         obtenido: {ejec.salida}")
            else:
                print(f"ok     {rel:<18} {n_instr:4d} instr TM  entradas={' '.join(caso['entradas'])[:40]}")
    print(f"\n{total - fallos if total >= fallos else 0} de {total} casos correctos; fallas: {fallos}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
