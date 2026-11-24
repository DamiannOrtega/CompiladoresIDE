# Fase final: generación de código TM y ejecución

Del árbol semántico validado a instrucciones de la Tiny Machine (TM) y su
ejecución en un simulador escrito en Python.

## Flujo

```
fuente → léxico → sintáctico → árbol → semántico ─┬─ (errores) → no se genera .tm
                                                   └─ sin errores → generador_tm → outputs/<programa>.tm
                                                                    → panel "Código TM"
                                                                    → maquina_tm ejecuta ESE archivo
```

- Si hay errores léxicos, sintácticos, semánticos o de generación, no se
  produce `.tm` y se borra cualquier `.tm` anterior con ese nombre.
- El panel "Código TM" muestra el texto leído del disco, y el simulador
  carga ese mismo archivo: lo que se ve es lo que se ejecuta.
- El `.ci` (código intermedio de tres direcciones) es una extensión didáctica
  opcional del PDF y no está implementado; por eso la interfaz no tiene una
  pestaña para él. El simulador nunca recibe código intermedio, sólo el `.tm`.

## Archivos

| Archivo | Responsabilidad |
|---|---|
| `ide/compilador/tm_formato.py` | Conjunto de instrucciones, registros, formato de línea, escritura y lectura del `.tm`. Lo comparten el generador y el simulador |
| `ide/compilador/generador_tm.py` | `EmisorTM` (como `code.c`: numeración, comentarios, reserva y ajuste de saltos) y `GeneradorTM` (como `cgen.c`: recorrido del `NodoArb`) |
| `ide/compilador/maquina_tm.py` | Simulador (como `tm.c`). Uso por consola: `python -m ide.compilador.maquina_tm archivo.tm [--traza]` |
| `ide/servicios/compilador.py` | Fases `tm` y `run`: generan y escriben el `.tm`; `ejecutar_tm()` lo ejecuta |
| `ide/ui/panel_tm.py` | Pestaña "Código TM": tabla Dirección/Instrucción/Operandos/Comentario y vista del archivo |
| `ide/ventana.py` | F8 "Generar Código TM", F9 "Ejecutar TM". `_WorkerEjecucion` corre el simulador en un hilo: en cada IN la máquina queda en pausa (registros, memoria y pc intactos) hasta que el usuario envía el dato desde la consola |
| `ide/ui/panel_sal.py` | Pestaña "Salida": consola interactiva (solicitudes de datos, valores introducidos, resultados, errores), campo "Enviar" que aparece sólo cuando el programa pide un dato, botón "Detener" y un "Registro técnico" desplegable |
| `runner.py` | La CLI genera el `.tm`; con `--ejecutar` también lo ejecuta |
| `pruebas_tm/` | Programas de prueba y `test_tm.py` (`python -m unittest pruebas_tm.test_tm -v`) |

## Registros y memoria

| Registro | Uso |
|---|---|
| 0 `ac` | acumulador / resultado de expresiones |
| 1 `ac1` | operando izquierdo de operaciones binarias |
| 2, 3, 4 | auxiliares (`%`, `^`, conversión int→float) |
| 5 `gp` | base de variables: la variable *i* de la tabla de símbolos está en `i(5)` |
| 6 `mp` | base de temporales: tope de la memoria, crece hacia abajo (`0(6)`, `-1(6)`...) |
| 7 `pc` | contador de programa; todos los saltos son relativos a `pc` |

La tabla de símbolos guarda desplazamientos en **bytes** (int/float = 4,
bool = 1). La TM direcciona por palabra, por eso el generador asigna
`dMem[gp + i]` según el orden de la tabla. El encabezado de cada `.tm` muestra
ese mapa.

## Traducción de nodos

| Nodo del árbol | Instrucciones TM |
|---|---|
| `Num:` / `Bool:` | `LDC 0,valor(0)` (true=1, false=0) |
| `Id: x` | `LD 0,dir(5)` |
| `Op:` binario | izq → `ST 0,t(6)`; der → `LD 1,t(6)`; operación |
| `+ - * /` | `ADD` / `SUB` / `MUL` / `DIV` |
| `%` | `DIV 2,1,0` · `MUL 2,2,0` · `SUB 0,1,2` |
| `^` | ciclo con contador en r3 y `MUL`; exponente negativo → `1 / resultado` |
| `< <= > >= == !=` | `SUB` + `JLT/JLE/JGT/JGE/JEQ/JNE` → ac = 0 o 1 |
| `&&` / `\|\|` / `!` | `MUL` / `ADD` normalizado / `1 - ac` |
| conversión `int -> float` | `LDC 2,1.0(0)` · `MUL 0,0,2` |
| `Decl` con valor inicial, `Asignar` | expresión → `ST 0,dir(5)` |
| `x++` / `x--` | `LD` · `LDA 0,±1(0)` · `ST` |
| `Leer (cin)` | `IN 0,0,tipo` · `ST 0,dir(5)` |
| `Escribir (cout)` | `OUT` (número), `OUTS` (texto), `OUTN` (número seguido de texto) |
| `Si (if)` | cond · `JEQ` → else/fin (reservado) · then · `LDA 7` → fin (reservado) · else |
| `Mientras (while)` | inicio: cond · `JEQ` → fin (reservado) · cuerpo · `LDA 7` → inicio |
| `Hacer (do-until)` | inicio: cuerpo · cond · `JEQ` → inicio (repite mientras sea falsa) |

Saltos: `EmisorTM.reservar()` deja un hueco en la dirección actual (como
`emitSkip(1)`). `EmisorTM.completar(hueco, op, r, destino)` escribe la
instrucción con `d = destino - (hueco + 1)` cuando ya se conoce el destino
(como `emitBackup` + `emitRM_Abs` + `emitRestore`).

## Extensiones respecto a la TM original (tm.c / tm.exe)

| Extensión | Motivo | Compatibilidad con tm.exe |
|---|---|---|
| Valores reales en registros y memoria; `LDC r,2.5(0)` | el lenguaje tiene `float` | tm.exe no puede leer constantes reales |
| `DIV` con dos enteros trunca hacia cero (igual que C); con algún real divide normalmente | mantener `int` idéntico a la TM | igual en programas enteros |
| `OUTS r,k(s)`: imprime la cadena *k* de la tabla `*.STR` | `cout << "texto"` | no existe en tm.exe |
| `OUTN r,s,t`: imprime sin terminar la línea | `cout << expr << "texto"` | no existe en tm.exe |
| `IN r,s,t` con t = 0 int, 1 float, 2 bool | validar la entrada según el tipo de la variable | tm.exe ignora s y t: compatible |
| Tabla de cadenas en líneas `*.STR k "texto"` | que el texto viaje dentro del `.tm` | tm.exe las ignora como comentarios |
| Memorias de 4096 posiciones (tm.c: 1024) | programas más grandes | igual si el programa ocupa < 1024 |

Los programas que sólo usan enteros y no imprimen texto generan un `.tm` que
corre sin cambios en `Tiny_Corregido/tm.exe`. La prueba
`test_compatibilidad_con_tm_exe` lo verifica.

## Limitaciones conocidas

- `^` requiere exponente de tipo `int` (o un `int` promovido a `float`); un
  exponente `float` literal o variable produce un error de generación.
- `&&` y `||` evalúan ambos operandos (sin cortocircuito). No hay efectos
  laterales en expresiones, así que el resultado es el mismo.
- `%` y `/` con negativos siguen la semántica de C (truncar hacia cero). El
  plegado de constantes del análisis semántico usa la de Python (`//`, `%`),
  así que la anotación `val:` del árbol puede diferir para negativos; el
  código TM no usa esos valores.
- El lenguaje no tiene menos unario (`-5`); se escribe `0 - 5`.
- `a ++ b` / `a -- b` como operadores binarios pasan el análisis semántico sin
  tipo; el generador los reporta como error de generación.
- La generación de `.ci` no está implementada (en el PDF es opcional).
