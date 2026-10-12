# Reporte de Fase 3: Análisis Semántico

## 1. Descripción de la implementación realizada
La fase de análisis semántico se implementó como un módulo independiente (`ide/compilador/semantico.py`) que procesa el Árbol Sintáctico Abstracto (AST) generado por el analizador sintáctico. El objetivo principal fue verificar que las sentencias del código fuente tengan significado válido y respeten las reglas del lenguaje, así como recolectar información necesaria para la futura generación de código. 

La integración en el IDE incluyó:
- Modificación de la estructura `NodoArb` para admitir anotaciones semánticas.
- Ampliación de la estructura `Sim` para almacenar direcciones de memoria (offsets) y listas de referencias (líneas de uso).
- Creación de paneles visuales para mostrar la Tabla de Símbolos detallada, el AST Anotado y los Errores Semánticos.

## 2. Reglas semánticas utilizadas
El analizador aplica las siguientes reglas fundamentales durante el recorrido del AST:
- **Declaración obligatoria:** Toda variable debe ser declarada antes de su uso.
- **Unicidad de identificadores:** Una variable no puede declararse más de una vez en el mismo ámbito.
- **Tipado en sentencias de control:** Las condiciones de sentencias como `if`, `while` y `do-while` deben evaluar estrictamente a un tipo booleano.
- **Tipado de operaciones lógicas:** Los operadores `and`, `or`, `not` exigen operandos booleanos.
- **Asignaciones válidas:** El tipo de la expresión a la derecha de una asignación debe ser compatible o convertible al tipo de la variable a la izquierda.
- **Estructura del programa:** Todo programa válido debe contener una función `main`.

## 3. Atributos sintetizados y heredados implementados
La anotación del AST se basa en el paso de atributos entre nodos:

*   **Atributos Heredados (Top-Down):**
    *   `dtype` (Data Type): Utilizado en las declaraciones (`int`, `float`, `bool`). Se hereda desde el nodo raíz de la declaración (ej. `Decl: int`) hacia los nodos hijos (las variables individuales declaradas en esa línea).
*   **Atributos Sintetizados (Bottom-Up):**
    *   `tipo` (Type): El tipo resultante de una expresión o el tipo de una variable. Se calcula a partir de los hijos hacia los padres (ej. sumar dos `int` sintetiza un tipo `int`).
    *   `val` (Value): En expresiones constantes, el valor evaluado se sintetiza hacia arriba para optimización.
    *   `dir` (Dirección): El desplazamiento en memoria (offset) asignado a la variable, sintetizado desde la tabla de símbolos hacia los nodos identificadores.

## 4. Explicación de la forma en que se anotó el AST
Se implementó un patrón de recorrido mediante el patrón Visitor modificado, que realiza pasadas combinadas (pre-orden y post-orden según el nodo). 
Las anotaciones se inyectan dinámicamente en los nodos del árbol (`NodoArb.anotaciones`), apareciendo en la visualización entre llaves `{...}`. 

- **Declaraciones:** Se extrae el tipo y se hereda a los identificadores, guardando `{dtype: tipo}` y `{dir: offset}`.
- **Expresiones:** Se evalúan en post-orden (hijos primero). El tipo resultante se anota en el nodo operador como `{tipo: resultado}`. Si se requiere una conversión de tipos (ej. `int -> float`), se anota `{conv: int -> float}` en el hijo correspondiente.
- **Asignaciones:** Se anota la variable destino con su `{dir, tipo}` y se comprueba la compatibilidad con el hijo derecho.

## 5. Diseño y funcionamiento de la tabla de símbolos
La Tabla de Símbolos (`TablaSimbolos`) se estructuró como un diccionario en memoria (`dict[str, Sim]`). 
*   **Llave:** El nombre del identificador (ej. `"x"`).
*   **Valor:** Objeto `Sim` que almacena: Nombre, Tipo de dato, Línea de declaración, Desplazamiento de memoria (`dir` o `offset`), y una lista de líneas de referencia donde la variable es utilizada.

**Funcionamiento de Memoria (Offsets):**
Se mantiene un contador global de desplazamiento (`_offset_actual`). Cada vez que se registra una variable exitosamente, se le asigna el desplazamiento actual y el contador se incrementa según el tamaño del tipo de dato:
- `int` = 4 bytes
- `float` = 4 bytes
- `bool` = 1 byte (o 4 bytes si se alinea a palabra).

## 6. Reglas utilizadas para la comprobación de tipos
Para validar las operaciones (nodos `Op`), el analizador semántico aplica reglas estrictas:
- **Aritméticas (`+`, `-`, `*`, `/`):** Se permiten `int` y `float`. Si ambos son `int`, el resultado es `int`. Si al menos uno es `float`, el resultado es `float`.
- **Relacionales (`<`, `<=`, `>`, `>=`, `==`, `!=`):** Se permiten `int` y `float` comparados entre sí. El resultado siempre es `bool`.
- **Lógicas (`and`, `or`, `not`):** Requieren operandos estrictamente `bool`. Resultado `bool`.

## 7. Conversiones de tipos consideradas
El sistema soporta coerciones implícitas (widening conversions) en operaciones mixtas y asignaciones:
- **Promoción de Int a Float:** Cuando una operación aritmética involucra un `int` y un `float`, el operando `int` es marcado con el atributo `{conv: int -> float}` para indicar que el generador de código deberá insertar una instrucción de conversión.
- En asignaciones, si el lado izquierdo es `float` y el derecho es `int`, se inyecta la anotación de conversión en la expresión derecha.
- **No permitidas:** No se permiten conversiones implícitas de `float` a `int` (narrowing), ni conversiones que involucren tipos `bool`.

## 8. Errores semánticos implementados
Se definieron clases de error específicas (`ErrorSemantico`) reportadas con línea, columna y mensaje explicativo:
1.  `VARIABLE_NO_DECLARADA`: Uso de una variable que no existe en la tabla de símbolos.
2.  `VARIABLE_REDECLARADA`: Intento de declarar una variable con un nombre que ya fue registrado.
3.  `TIPO_INCOMPATIBLE`: Operaciones o asignaciones entre tipos que no pueden mezclarse (ej. `int` con `bool`).
4.  `CONDICION_NO_BOOLEANA`: Expresión en sentencias `if` o `while` que no devuelve `bool`.
5.  `FALTA_MAIN`: Estructura principal del programa no encontrada.

## 9. Explicación de las pruebas realizadas
Se ejecutaron pruebas integrales utilizando archivos `.src` desde la interfaz IDE, diseñadas para estresar al analizador:
- **`testSintactico.src`:** Archivo válido que permitió comprobar el correcto cálculo de offsets acumulativos (0, 4, 8, 12, etc.), síntesis de atributos en expresiones matemáticas complejas y la resolución de conversiones implícitas de tipos en nodos específicos.
- **Pruebas de errores (`TestSemantica.txt.txt`):** Se comprobó la robustez del analizador asegurando que, aún en presencia de errores sintácticos, el motor semántico puede recuperar el AST parcial, construir la tabla de símbolos con lo disponible y reportar errores semánticos reales sin detenerse abruptamente.

## 10. Capturas de ejecución

*(Por favor, inserta aquí las siguientes capturas para completar tu reporte PDF)*

1.  **Captura del Panel "Árbol Anotado":** Mostrando el árbol con llaves `{tipo, val, dir, conv}`.
2.  **Captura de la "Tabla de Símbolos":** Demostrando las columnas de nombre, tipo, offset (dirección en memoria) y las líneas de uso de cada variable.
3.  **Captura del Panel "Errores Semánticos":** Mostrando el reporte de errores detectados y la ubicación de los mismos.
