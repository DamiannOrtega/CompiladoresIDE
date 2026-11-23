# Ejercicios finales de Compiladores II

Programas de los 12 grupos de `EjericiosFinalesCompisII.pdf`, escritos en el lenguaje del compilador.
Cada grupo tiene 5 ejercicios: ej1 secuencial, ej2 y ej3 selectivos (if), ej4 y ej5 repetitivos (while / do-until).

Probar todos (genera el .tm de cada uno y lo ejecuta en el simulador con los datos de `casos.json`):

```bash
python ejercicios/probar_ejercicios.py
```

En el IDE: abrir el archivo y presionar F9 (Ejecutar TM); los valores se piden en el orden de "Entradas".

## Grupo 1

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dados A, B, C y D enteros, escribirlos en orden inverso. | A, B, C, D (enteros) | `1 2 3 4` → 4 / 3 / 2 / 1 |
| ej2 | selectivo | Dado un entero, imprimir si es positivo=0, negativo=1 o nulo=2. | N (entero) | `5` → Resultado (positivo=0, negativo=1, nulo=2): 0 |
| ej3 | selectivo | Dados tres enteros, determinar si están en orden creciente (1=Sí, 0=No). | A, B, C (enteros) | `1 2 3` → Orden creciente (1=Si, 0=No): 1 |
| ej4 | repetitivo | Calcular el término N de la serie de Fibonacci (los dos primeros son 0 y 1). | N (entero, N >= 1) | `1` → Termino N de Fibonacci: 0 |
| ej5 | repetitivo | Lluvias mensuales de las regiones NORTE, CENTRO y SUR: a) promedio anual del centro, b) mes y registro con menor lluvia en el sur, c) región con mayor lluvia anual. | Para cada mes del 1 al 12: lluvia NORTE, CENTRO, SUR (reales) | `10 1 19 10 2 18 10 3 17 10 4 16 …` → Promedio anual de la región CENTRO: 6.5 / Mes con menor lluvia en la región SUR: 12 / Registro de menor lluvia en la región SUR: 8.0 / Región con mayor lluvia anual: SUR |

## Grupo 2

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dado el ID y 5 calificaciones de un alumno, imprimir su matrícula y su promedio. | ID (entero), 5 calificaciones (reales) | `12345 8 9 10 7 6` → Matrícula: 12345 / Promedio: 8.0 |
| ej2 | selectivo | Temperatura con el grillo: T = N / 4 + 40 (N = sonidos por minuto). | N (entero, sonidos por minuto) | `40` → Temperatura en grados Fahrenheit: 50.0 |
| ej3 | selectivo | Impuesto: los primeros $20 sin impuesto, los siguientes $20 al 30% y el resto al 40% (50% si el costo es mayor a $500). Calcular el precio total. | Costo básico (real) | `15` → Impuesto: 0.0 / Precio total: 15.0 |
| ej4 | repetitivo | Costo de un conjunto de llamadas. Internacional: 3 primeros min $7.59 y $3.03 cada minuto adicional; Nacional: 3 primeros min $1.20 y $0.48 cada minuto adicional; Local: las primeras 50 llamadas gratis, luego $0.60 cada una. | N (número de llamadas); por llamada: tipo (1=Internacional, 2=Nacional, 3=Local) y duración en minutos | `3 1 5 2 2 3 10` → Costo de la llamada: 13.65 / Costo de la llamada: 1.2 / Costo de la llamada: 0.0 / Total a pagar: 14.85 |
| ej5 | repetitivo | Producción de 5 tipos de vino durante N años: a) total de cada tipo, b) total por año, c) año con mayor producción del tipo 2 y sus litros, d) años en que no se produjo el tipo 3. | N (años); por año: año y litros de los tipos 1 a 5 (enteros) | `3 2021 10 20 30 40 50 2022 5 25 0 10 …` → Año: 2021 / Total producido en el año: 150 / Año: 2022 / Total producido en el año: 50 / … |

## Grupo 3

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dada la base y la altura de un rectángulo, calcular su perímetro y su área. | Base, altura (reales) | `3 4.5` → Perímetro: 15.0 / Área: 13.5 |
| ej2 | selectivo | Dados A, B y C enteros diferentes, escribirlos en forma descendente. | A, B, C (enteros diferentes) | `5 9 7` → 9 / 7 / 5 |
| ej3 | selectivo | Dados tres números reales, identificar cuál es el mayor (pueden ser iguales). | A, B, C (reales) | `2.5 7.1 3` → El mayor es: 7.1 |
| ej4 | repetitivo | Leer N y calcular la suma de la serie 1^1 + 2^2 + 3^3 + ... + N^N. | N (entero) | `4` → Suma de la serie: 288 |
| ej5 | repetitivo | Producción mensual de N fábricas: i) total anual de cada fábrica, ii) fábrica que más produjo y su total, iii) claves de las fábricas cuya producción de julio superó $3 000 000. | N (fábricas); por fábrica: clave (entero) y producción de los 12 meses (reales) | `2 101 100000 100000 100000 100000 100000 100000 3500000 100000 100000 100000 …` → Fábrica: 101 / Total anual de producción: 4600000.0 / Producción de julio mayor a $3 000 000, clave: 101 / Fábrica: 202 / … |

## Grupo 4

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Convertir el peso de un dinosaurio de libras a kilogramos y su longitud de pies a metros. | Peso en libras, longitud en pies (reales) | `1000 50` → Peso en kilogramos: 453.6 / Longitud en metros: 15.24 |
| ej2 | selectivo | Dados NUM y V enteros, calcular VAL = 100*V si NUM=1; 100^V si NUM=2; 100/V si NUM=3; 0 en otro caso. | NUM, V (enteros) | `1 5` → VAL = 500 |
| ej3 | selectivo | Pago de un trabajador: sueldo más horas extra (máximo 30) según su categoría (1=$30, 2=$38, 3=$50, 4=$70; categoría mayor a 4 no cobra horas extra). | Sueldo (real), categoría (entero), horas extra (entero) | `5000 2 35` → Pago por horas extra: 1140 / Total a pagar: 6140.0 |
| ej4 | repetitivo | Clasificar las ventas de un vendedor: de $200 o menos, mayores a $200 e inferiores a $400, y de $400 o más. | N (número de ventas) y el importe de cada venta (reales) | `5 150 200 250 399.5 1000` → Ventas de $200 o menos: 2 / Importe de esas ventas: 350.0 / Ventas mayores a $200 e inferiores a $400: 2 / Importe de esas ventas: 649.5 / … |
| ej5 | repetitivo | Estadio con 5 tipos de localidad: leer precios y ventas (CLAVE, CANT hasta -1, -1); imprimir cada venta, boletos vendidos por tipo y la recaudación total. | P1..P5 (reales); luego pares CLAVE, CANT (enteros) terminando con -1, -1 | `100 80 60 40 20 1 2 3 5 1 1 5 …` → Clave: 1 / Cantidad: 2 / Importe total de la venta: 200.0 / Clave: 3 / … |

## Grupo 5

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dados el radio y la altura de un cilindro, calcular Volumen = pi * radio^2 * altura y Área = 2 * pi * radio * altura. | Radio, altura (reales) | `3 10` → Área: 188.4954 / Volumen: 282.7431 |
| ej2 | selectivo | Aplicar al sueldo un aumento del 15% si es inferior a $1000 y del 12% en caso contrario. | Sueldo (real) | `800` → Nuevo sueldo: 920.0 |
| ej3 | selectivo | Determinar si un alumno es aceptado en una facultad menor: Economía (semestre >= 6 y promedio >= 8.8), Computación (semestre > 6 y promedio > 8.5), Administración y Contabilidad (semestre > 5 y promedio > 8.5). | Matrícula (entero), carrera (1=Economía, 2=Computación, 3=Administración, 4=Contabilidad), semestre (entero), promedio (real) | `1001 1 6 8.8` → Matrícula: 1001 / Carrera: 1 / Aceptado=1 |
| ej4 | repetitivo | Dados N números enteros, calcular y mostrar el mayor y el menor. | N y luego los N números enteros | `5 3 -7 12 0 5` → Mayor: 12 / Menor: -7 |
| ej5 | repetitivo | Producción de 5 tipos de vino durante N años: a) total de cada tipo, b) total por año, c) año con mayor producción del tipo 2 y sus litros, d) años en que no se produjo el tipo 3. | N (años); por año: año y litros de los tipos 1 a 5 (enteros) | `3 2021 10 20 30 40 50 2022 5 25 0 10 …` → Año: 2021 / Total producido en el año: 150 / Año: 2022 / Total producido en el año: 50 / … |

## Grupo 6

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Calcular el número de segundos que hay en un número de días. | Días (entero) | `3` → Segundos: 259200 |
| ej2 | selectivo | Escribir aprobado=1 si la calificación es mayor o igual que 8 y reprobado=0 en caso contrario. | Calificación (real) | `8` → aprobado=1 |
| ej3 | selectivo | Costo total de internación de un paciente según el tipo de enfermedad (1=$25, 2=$16, 3=$20, 4=$32 por día), con 10% adicional si tiene entre 14 y 22 años. | Tipo de enfermedad (1-4), días internado, edad (enteros) | `2 10 18` → Costo total del paciente: 176.0 |
| ej4 | repetitivo | Leer N y calcular la serie 1 - 1/2 + 1/3 - 1/4 + ... ± 1/N. | N (entero) | `4` → Resultado de la serie: 0.5833333333 |
| ej5 | repetitivo | Producción mensual de N fábricas: i) total anual de cada fábrica, ii) fábrica que más produjo y su total, iii) claves de las fábricas cuya producción de julio superó $3 000 000. | N (fábricas); por fábrica: clave (entero) y producción de los 12 meses (reales) | `2 101 100000 100000 100000 100000 100000 100000 3500000 100000 100000 100000 …` → Fábrica: 101 / Total anual de producción: 4600000.0 / Producción de julio mayor a $3 000 000, clave: 101 / Fábrica: 202 / … |

## Grupo 7

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dados A y B enteros, escribir el resultado de (A + B)^2 / 3. | A, B (enteros) | `2 4` → (A + B)^2 / 3 = 12.0 |
| ej2 | selectivo | Dado un entero, imprimir si es positivo=0, negativo=1 o nulo=2. | N (entero) | `5` → Resultado (positivo=0, negativo=1, nulo=2): 0 |
| ej3 | selectivo | Dados tres números enteros, imprimirlos en orden creciente. | A, B, C (enteros) | `9 2 5` → 2 / 5 / 9 |
| ej4 | repetitivo | Elección con 4 candidatos: contar los votos de cada uno y su porcentaje; los votos terminan con 0. | Votos (enteros 1 a 4), uno por uno, terminando con 0 | `1 3 1 4 2 2 1 4 1 1 1 2 …` → Votos candidato 1: 8 / Votos candidato 2: 3 / Votos candidato 3: 2 / Votos candidato 4: 3 / … |
| ej5 | repetitivo | Producción mensual de N fábricas: i) total anual de cada fábrica, ii) fábrica que más produjo y su total, iii) claves de las fábricas cuya producción de julio superó $3 000 000. | N (fábricas); por fábrica: clave (entero) y producción de los 12 meses (reales) | `2 101 100000 100000 100000 100000 100000 100000 3500000 100000 100000 100000 …` → Fábrica: 101 / Total anual de producción: 4600000.0 / Producción de julio mayor a $3 000 000, clave: 101 / Fábrica: 202 / … |

## Grupo 8

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dado el costo de un artículo y el dinero entregado por el cliente, calcular el cambio. | Costo, dinero entregado (reales) | `37.5 50` → Cambio a entregar: 12.5 |
| ej2 | selectivo | Dados P y Q enteros, determinar si satisfacen P^3 + Q^4 - 2*P^2 < 680. | P, Q (enteros) | `2 3` → P^3 + Q^4 - 2*P^2 = 81 / Satisfacen la expresión=1 |
| ej3 | selectivo | Descuento según el monto: menor a $500 sin descuento; $500-$1000 5%; hasta $7000 11%; hasta $15000 18%; mayor 25%. | Monto de la compra (real) | `300` → Descuento: 0.0 / Total a pagar: 300.0 |
| ej4 | repetitivo | Dados N números enteros, contar cuántos ceros hay; el fin de datos es -1. | Números enteros, uno por uno, terminando con -1 | `5 0 3 0 0 -1` → Cantidad de ceros: 3 |
| ej5 | repetitivo | Producción de 5 tipos de vino durante N años: a) total de cada tipo, b) total por año, c) año con mayor producción del tipo 2 y sus litros, d) años en que no se produjo el tipo 3. | N (años); por año: año y litros de los tipos 1 a 5 (enteros) | `3 2021 10 20 30 40 50 2022 5 25 0 10 …` → Año: 2021 / Total producido en el año: 150 / Año: 2022 / Total producido en el año: 50 / … |

## Grupo 9

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dados el radio y la altura de un cilindro, calcular Volumen = pi * radio^2 * altura y Área = 2 * pi * radio * altura. | Radio, altura (reales) | `3 10` → Área: 188.4954 / Volumen: 282.7431 |
| ej2 | selectivo | Temperatura con el grillo: T = N / 4 + 40 (N = sonidos por minuto). | N (entero, sonidos por minuto) | `40` → Temperatura en grados Fahrenheit: 50.0 |
| ej3 | selectivo | Impuesto: los primeros $20 sin impuesto, los siguientes $20 al 30% y el resto al 40% (50% si el costo es mayor a $500). Calcular el precio total. | Costo básico (real) | `15` → Impuesto: 0.0 / Precio total: 15.0 |
| ej4 | repetitivo | Leer M y obtener y contar todos los números primos menores a M. | M (entero) | `20` → 2 / 3 / 5 / 7 / … |
| ej5 | repetitivo | Lluvias mensuales de las regiones NORTE, CENTRO y SUR: a) promedio anual del centro, b) mes y registro con menor lluvia en el sur, c) región con mayor lluvia anual. | Para cada mes del 1 al 12: lluvia NORTE, CENTRO, SUR (reales) | `10 1 19 10 2 18 10 3 17 10 4 16 …` → Promedio anual de la región CENTRO: 6.5 / Mes con menor lluvia en la región SUR: 12 / Registro de menor lluvia en la región SUR: 8.0 / Región con mayor lluvia anual: SUR |

## Grupo 10

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dada la base y la altura de un rectángulo, calcular su perímetro y su área. | Base, altura (reales) | `3 4.5` → Perímetro: 15.0 / Área: 13.5 |
| ej2 | selectivo | Aumento de sueldo por categoría (1=15%, 2=10%, 3=8%, 4=7%); imprimir la categoría y el nuevo sueldo. | Categoría (entero), sueldo (real) | `3 10000` → Categoría: 3 / Nuevo sueldo: 10800.0 |
| ej3 | selectivo | Dados tres números reales, identificar cuál es el mayor (pueden ser iguales). | A, B, C (reales) | `2.5 7.1 3` → El mayor es: 7.1 |
| ej4 | repetitivo | Calcular e imprimir los números perfectos menores o iguales que N. | N (entero) | `100` → 6 / 28 / Números perfectos encontrados: 2 |
| ej5 | repetitivo | Estadio con 5 tipos de localidad: leer precios y ventas (CLAVE, CANT hasta -1, -1); imprimir cada venta, boletos vendidos por tipo y la recaudación total. | P1..P5 (reales); luego pares CLAVE, CANT (enteros) terminando con -1, -1 | `100 80 60 40 20 1 2 3 5 1 1 5 …` → Clave: 1 / Cantidad: 2 / Importe total de la venta: 200.0 / Clave: 3 / … |

## Grupo 11

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dado el costo de un artículo y el dinero entregado por el cliente, calcular el cambio. | Costo, dinero entregado (reales) | `37.5 50` → Cambio a entregar: 12.5 |
| ej2 | selectivo | Aumento de sueldo por categoría (1=15%, 2=10%, 3=8%, 4=7%); imprimir la categoría y el nuevo sueldo. | Categoría (entero), sueldo (real) | `3 10000` → Categoría: 3 / Nuevo sueldo: 10800.0 |
| ej3 | selectivo | Costo de una llamada internacional según la clave de zona (12=$2, 15=$2.2, 18=$4.5, 19=$3.5, 23=$6, 25=$6, 29=$5 por minuto). | Clave de zona (entero), minutos (entero) | `18 10` → Costo total de la llamada: 45.0 |
| ej4 | repetitivo | Conjetura de ULAM: leer un entero positivo e imprimir la sucesión hasta llegar a 1. | N (entero positivo) | `26` → 26 / 13 / 40 / 20 / … |
| ej5 | repetitivo | Lluvias mensuales de las regiones NORTE, CENTRO y SUR: a) promedio anual del centro, b) mes y registro con menor lluvia en el sur, c) región con mayor lluvia anual. | Para cada mes del 1 al 12: lluvia NORTE, CENTRO, SUR (reales) | `10 1 19 10 2 18 10 3 17 10 4 16 …` → Promedio anual de la región CENTRO: 6.5 / Mes con menor lluvia en la región SUR: 12 / Registro de menor lluvia en la región SUR: 8.0 / Región con mayor lluvia anual: SUR |

## Grupo 12

| Ej | Tipo | Ejercicio | Entradas (en orden) | Ejemplo: datos → salida |
|---|---|---|---|---|
| ej1 | secuencial | Dados A y B enteros, escribir el resultado de (A + B)^2 / 3. | A, B (enteros) | `2 4` → (A + B)^2 / 3 = 12.0 |
| ej2 | selectivo | Dados P y Q enteros, determinar si satisfacen P^3 + Q^4 - 2*P^2 < 680. | P, Q (enteros) | `2 3` → P^3 + Q^4 - 2*P^2 = 81 / Satisfacen la expresión=1 |
| ej3 | selectivo | Descuento según el monto: menor a $500 sin descuento; $500-$1000 5%; hasta $7000 11%; hasta $15000 18%; mayor 25%. | Monto de la compra (real) | `300` → Descuento: 0.0 / Total a pagar: 300.0 |
| ej4 | repetitivo | Elección con 4 candidatos: contar los votos de cada uno y su porcentaje; los votos terminan con 0. | Votos (enteros 1 a 4), uno por uno, terminando con 0 | `1 3 1 4 2 2 1 4 1 1 1 2 …` → Votos candidato 1: 8 / Votos candidato 2: 3 / Votos candidato 3: 2 / Votos candidato 4: 3 / … |
| ej5 | repetitivo | Estadio con 5 tipos de localidad: leer precios y ventas (CLAVE, CANT hasta -1, -1); imprimir cada venta, boletos vendidos por tipo y la recaudación total. | P1..P5 (reales); luego pares CLAVE, CANT (enteros) terminando con -1, -1 | `100 80 60 40 20 1 2 3 5 1 1 5 …` → Clave: 1 / Cantidad: 2 / Importe total de la venta: 200.0 / Clave: 3 / … |
