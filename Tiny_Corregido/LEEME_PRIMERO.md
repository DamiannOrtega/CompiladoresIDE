# TINY y TM — versión corregida para GCC y Visual Studio Code

Este proyecto procede de los archivos del compilador TINY y del simulador **TM (Tiny Machine)** que acompañan a *Construcción de compiladores: principios y práctica* de Kenneth C. Louden. Se conservó el funcionamiento didáctico del generador y del simulador. Las correcciones permiten compilar con GCC moderno y ejecutar el ejemplo del factorial.

## 1. Requisitos en Windows

- Instalar **GCC** (por ejemplo, GCC de **MSYS2 UCRT64**, ya utilizado para programación en C/C++ desde VS Code).
- Verificar en la terminal de VS Code: `gcc --version`.
- Descomprimir **toda la carpeta** y abrir `Tiny_Corregido` en Visual Studio Code (`Archivo > Abrir carpeta`).
- Si `gcc` no se encuentra, utilizar la terminal de MSYS2 UCRT64 o agregar la carpeta `C:\msys64\ucrt64\bin` a la variable de entorno PATH, según la instalación de MSYS2. No basta con instalar la extensión C/C++ de VS Code.

## 2. Compilación en Windows

En la terminal **PowerShell** de VS Code, situada en la carpeta `Tiny_Corregido`, ejecutar:

```powershell
.\compilar_windows.bat
```

Se deben crear dos programas, `tiny.exe` y `tm.exe`. Si GCC está instalado en MSYS2 pero no en PATH, abrir la terminal MSYS2 UCRT64, cambiar a la carpeta del proyecto y ejecutar `cmd.exe /c compilar_windows.bat`, o compilar con los comandos GCC que aparecen en el archivo BAT.

## 3. Primera prueba completa, del lenguaje fuente a la ejecución

**Paso A — Generar instrucciones TM.**

```powershell
.\tiny.exe .\ejemplos\factorial.tny
```

`tiny.exe` analiza el archivo TINY, imprime el árbol y la tabla de símbolos, comprueba los tipos y produce `ejemplos\factorial.tm`. Su archivo de salida está comentado para observar el recorrido y la emisión de instrucciones.

**Paso B — Cargar las instrucciones en el simulador.**

```powershell
.\tm.exe .\ejemplos\factorial.tm
```

Dentro del simulador, escribir:

```text
h       (ver comandos)
t       (activar rastreo de instrucciones; opcional)
g       (ejecutar el programa)
5       (valor solicitado por la instrucción IN)
r       (consultar los registros después de HALT)
d 0 2   (consultar x y fact en la memoria)
q       (salir)
```

Para `5`, deberá aparecer `OUT instruction prints: 120`. Para `3`, aparece `6`. Si se introduce `0`, el programa termina sin calcular ni imprimir el factorial.

**Alternativa:** ejecutar `./ejecutar_factorial_windows.bat` en PowerShell (`.\ejecutar_factorial_windows.bat`) para generar el programa y abrir TM en una sola secuencia.

## 4. Qué archivo hace qué

| Archivo | Función |
|---|---|
| `main.c` | Coordina el análisis y la generación. Las opciones `NO_ANALYZE` y `NO_CODE` están ahora desactivadas (`FALSE`). |
| `scan.c` | Reconoce tokens del lenguaje TINY. |
| `parse.c` | Construye el árbol sintáctico. |
| `analyze.c`, `symtab.c` | Construyen la tabla de símbolos, asignan direcciones y revisan tipos. |
| `cgen.c`, `cgen.h` | Recorren el árbol y deciden qué instrucciones TM deben generarse. |
| `code.c`, `code.h` | Las escriben en el archivo `.tm`; permiten reservar, ajustar y restaurar los destinos de saltos. |
| `tm.c` | Carga las instrucciones del archivo `.tm` y las ejecuta sobre registros, memoria de datos e instrucciones. |
| `ejemplos/*.tny` | Programas fuente para prácticas. |
| `ejemplos/*.tm` | Instrucciones generadas para la TM. |

El archivo `.tm` es la **salida del compilador** y la **entrada del simulador**. El simulador **no ejecuta directamente el archivo `.tny`** y tampoco interpreta los cuádruplos ni el código de tres direcciones.

El generador `cgen.c` de Louden recorre directamente el árbol, utiliza `st_lookup()` para recuperar direcciones de variables y llama a funciones como `emitRO`, `emitRM` y `emitRM_Abs` para producir el archivo `.tm`.

## 5. Registros importantes en la TM

| Registro | Alias | Uso |
|---|---|---|
| `reg[0]` | `ac` | Acumulador: resultado principal de expresiones. |
| `reg[1]` | `ac1` | Segundo acumulador: guarda un operando para una operación binaria. |
| `reg[5]` | `gp` | Registro base de las variables globales; `0(5)` es `x` y `1(5)` es `fact` en el factorial. |
| `reg[6]` | `mp` | Registro base de las posiciones temporales. |
| `reg[7]` | `pc` | Contador del programa; referencia los saltos relativos. |

El simulador dispone de dos memorias: `iMem` (instrucciones) y `dMem` (datos). El generador proporciona números concretos de posición para las instrucciones, y desplazamientos `d(s)` para ubicar los operandos.

## 6. Ojo con el orden de las instrucciones en el archivo TM

Al generar un `if`, `cgen.c` puede reservar una instrucción que será completada después con `emitSkip`, `emitBackup`, `emitRM_Abs` y `emitRestore`. Por este motivo, la **instrucción 13 puede estar escrita físicamente después de la 39** en el archivo. Esto **no es un error**: el simulador la carga en la dirección 13 de `iMem` y la ejecuta en el orden indicado por el contador del programa y los saltos.

## 7. Más ejemplos para practicar

- `ejemplos/aritmetica.tny`: expresiones con paréntesis, multiplicación, suma y resta; con entrada 5, imprime 18.
- `ejemplos/condicional.tny`: un `if ... then ... else ... end`; con entrada 2 imprime 1, y con 3 imprime 2.
- `ejemplos/ciclo.tny`: `repeat ... until`; con entrada 3, imprime 0.
- `ejemplos/error_semantico.tny`: demuestra un error de tipos. No debe generarse `.tm`.

Para utilizar otro ejemplo, sustituye el nombre del archivo en los dos comandos del apartado 3.

## 8. Restricciones de este TINY educativo

Esta implementación conserva el subconjunto didáctico del libro: enteros, operaciones `+ - * /`, comparaciones `<` y `=`, sentencias `if`, `repeat`, `read`, `write` y asignaciones. Los identificadores se reconocen como secuencias de letras. No incluye tipos C, funciones, arreglos, ni conversión directa desde cuádruplos a TM.

Los valores numéricos se representan mediante `int` de C; factoriales grandes pueden exceder el rango y provocar desbordamiento. Para la práctica, usar valores de entrada de 1 a 12.

## 9. Correcciones aplicadas al archivo recibido

1. `main.c`: habilitación del análisis semántico y de la generación de código; salida `.tm` en la misma carpeta que el `.tny`; nombres de archivo más largos y salida informativa.
2. `util.c`: declaración explícita `static int indentno` para ajustarse a C moderno.
3. `parse.c`: cambio del nombre de la función interna `exp` a `parseExpression` para evitar la colisión con la función matemática estándar.
4. `scan.c`: reconocimiento de `\r` para archivos CRLF de Windows y corrección del límite del arreglo de lexemas.
5. `tm.c`: sustitución de la función insegura `gets` por lectura limitada con `fgets`; correcciones de lectura al final de archivo y de índices fuera de límites; manejo de rutas más largas.
6. Se agregaron un Makefile compatible con GCC, scripts `.bat` de Windows y esta guía.

**Las modificaciones mantienen las instrucciones TM, el generador del libro y sus reglas de traducción.** Son ajustes de configuración, portabilidad y seguridad para el entorno actual.

## 10. Resultado de pruebas

Se compiló el código corregido con GCC C11 y advertencias estrictas. Se verificó el flujo completo **TINY → análisis → código TM → simulación**, incluyendo factorial 3 y 5, entrada no positiva, operaciones aritméticas, condicionales, repetición y detección de un error semántico.

Nota: las pruebas automáticas se ejecutaron en Linux con GCC; en Windows se han preparado los comandos y scripts, pero no se ha ejecutado un compilador Windows dentro de esta sesión. La versión está escrita en C estándar y pensada para GCC/MinGW/MSYS2.
