"""
gen_reporte.py — Genera el documento HTML del Reporte de Fase 3 (Analisis Semantico).
Ejecutar con: python docs/gen_reporte.py
El archivo resultante se abre en el navegador y se imprime como PDF con Ctrl+P.
"""
import pathlib

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
:root{--az:#1a2535;--azm:#2c3e6b;--azc:#4a6fa5;--ac:#3b82f6;--acs:#dbeafe;--ve:#16a34a;--vs:#dcfce7;--ro:#dc2626;--rs:#fee2e2;--am:#d97706;--as:#fef3c7;--gc:#f8fafc;--gb:#e2e8f0;--tx:#1e293b;--txs:#64748b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;font-size:10.5pt;line-height:1.6;color:var(--tx);background:#f1f5f9}
.pagina{max-width:900px;margin:0 auto;background:#fff;box-shadow:0 4px 24px rgba(0,0,0,.08)}
/* PORTADA */
.portada{background:linear-gradient(135deg,var(--az),var(--azm) 60%,var(--azc));color:#fff;min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:60px 40px;page-break-after:always}
.portada .badge{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);border-radius:20px;padding:6px 20px;font-size:9pt;letter-spacing:2px;text-transform:uppercase;font-weight:500;margin-bottom:24px}
.portada h1{font-size:32pt;font-weight:700;margin-bottom:12px}
.portada h2{font-size:17pt;font-weight:300;opacity:.85;margin-bottom:40px}
.portada .div{width:80px;height:3px;background:rgba(255,255,255,.5);border-radius:2px;margin:0 auto 40px}
.portada .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:520px;width:100%}
.portada .box{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:12px;padding:16px;text-align:left}
.portada .lbl{font-size:7.5pt;text-transform:uppercase;letter-spacing:1.5px;opacity:.65;margin-bottom:4px;font-weight:500}
.portada .val{font-size:10.5pt;font-weight:600}
/* SECCIONES */
.sec{padding:50px 60px;border-bottom:1px solid var(--gb)}
.sec:last-child{border-bottom:none}
.sh{display:flex;align-items:center;gap:16px;margin-bottom:28px;padding-bottom:16px;border-bottom:2px solid var(--acs)}
.sn{min-width:40px;height:40px;background:linear-gradient(135deg,var(--azm),var(--azc));color:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14pt}
.st{font-size:15pt;font-weight:700;color:var(--az)}
/* TYPO */
h3{font-size:11.5pt;font-weight:600;color:var(--azm);margin:24px 0 10px}
p{margin-bottom:12px}
ul,ol{margin:8px 0 14px 22px}
li{margin-bottom:5px}
/* CODE */
pre{font-family:'Fira Code',monospace;font-size:8.5pt;background:var(--az);color:#e2e8f0;padding:18px 22px;border-radius:10px;overflow-x:auto;line-height:1.7;margin:14px 0;border-left:4px solid var(--ac);white-space:pre-wrap;word-break:break-all}
code{font-family:'Fira Code',monospace;font-size:8.5pt;background:var(--acs);color:var(--azm);padding:2px 6px;border-radius:4px;font-weight:500}
/* TABLAS */
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:9pt}
thead{background:linear-gradient(135deg,var(--az),var(--azm));color:#fff}
thead th{padding:11px 14px;text-align:left;font-weight:600}
tbody tr:nth-child(even){background:var(--gc)}
tbody td{padding:9px 14px;border-bottom:1px solid var(--gb)}
/* ALERTAS */
.al{display:flex;gap:14px;align-items:flex-start;padding:14px 18px;border-radius:10px;margin:16px 0;border-left:4px solid}
.al i{font-size:17pt}
.ali{background:var(--acs);border-color:var(--ac)}
.ale{background:var(--vs);border-color:var(--ve)}
.ala{background:var(--as);border-color:var(--am)}
/* TAGS */
.tag{display:inline-block;padding:2px 10px;border-radius:20px;font-size:8pt;font-weight:600}
.ti{background:#dbeafe;color:#1d4ed8}
.tf{background:#ede9fe;color:#6d28d9}
.tb{background:#dcfce7;color:#166534}
.te{background:#fee2e2;color:#991b1b}
/* AST */
.ast{background:#0f172a;border-radius:10px;padding:20px 24px;margin:14px 0}
.ast pre{background:none;border:none;padding:0;margin:0;color:#94a3b8}
/* ERROR CARDS */
.ec{border:1px solid var(--ro);border-radius:10px;overflow:hidden;margin:12px 0}
.eh{background:var(--ro);color:#fff;padding:8px 16px;font-weight:600;font-size:9.5pt}
.eb{padding:12px 16px;background:var(--rs);font-size:9pt}
/* REGLAS */
.rb{background:var(--gc);border:1px solid var(--gb);border-radius:10px;padding:16px 20px;margin:10px 0;font-size:9pt}
.rn{font-weight:700;color:var(--ac);margin-bottom:6px;font-size:9.5pt}
/* FLUJO */
.flujo{display:flex;align-items:center;flex-wrap:wrap;margin:18px 0;gap:4px}
.fp{background:var(--az);color:#fff;padding:10px 18px;border-radius:8px;font-size:9pt;font-weight:500}
.fa{color:var(--ac);font-size:18pt;padding:0 4px;font-weight:700}
/* ATTR GRID */
.ag{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:14px 0}
.ac-h{border-radius:10px;padding:16px;border:1px solid #93c5fd;background:#eff6ff}
.ac-s{border-radius:10px;padding:16px;border:1px solid #86efac;background:#f0fdf4}
.ac-h h4,.ac-s h4{font-size:10pt;font-weight:700;margin-bottom:10px}
/* TOC */
.toc{background:var(--gc);border:1px solid var(--gb);border-radius:12px;padding:24px 30px}
.ti2{display:flex;align-items:center;padding:7px 0;border-bottom:1px dashed var(--gb);gap:12px;font-size:10pt}
.ti2:last-child{border-bottom:none}
.tn{color:var(--ac);font-weight:700;min-width:24px}
.td{flex:1;border-bottom:2px dotted #cbd5e1;height:1px;margin-top:6px}
.tp{color:var(--txs);font-size:9pt}
/* CAPTURA */
.cap{border:2px dashed #cbd5e1;border-radius:10px;padding:60px 20px;text-align:center;color:#94a3b8;background:var(--gc);margin:12px 0;font-size:11pt}
/* PIE */
.pie{background:var(--az);color:rgba(255,255,255,.5);text-align:center;padding:20px;font-size:8.5pt}
@media print{body{background:#fff}.pagina{box-shadow:none;max-width:100%}.portada{min-height:auto;padding:80px 60px;page-break-after:always}.sec{page-break-inside:avoid}}
"""

HTML_PARTS = [
"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Fase 3 - Analisis Semantico | Compiladores II</title>
<style>""",
CSS,
"""</style>
</head>
<body>
<div class="pagina">

<!-- PORTADA -->
<div class="portada">
  <div class="badge">Compiladores II - 2026</div>
  <h1>Analisis Semantico</h1>
  <h2>Fase 3 - Verificacion de Tipos y Tabla de Simbolos</h2>
  <div class="div"></div>
  <div class="grid">
    <div class="box"><div class="lbl">Proyecto</div><div class="val">IDE de Compiladores</div></div>
    <div class="box"><div class="lbl">Lenguaje</div><div class="val">Mini-lenguaje SRC</div></div>
    <div class="box"><div class="lbl">Tecnologia</div><div class="val">Python 3 / PySide6</div></div>
    <div class="box"><div class="lbl">Fase</div><div class="val">3 de 4 (Semantica)</div></div>
  </div>
</div>

<!-- INDICE -->
<div class="sec">
  <div class="sh"><div class="sn">&#128203;</div><div class="st">Tabla de Contenidos</div></div>
  <div class="toc">
    <div class="ti2"><span class="tn">1</span>Descripcion de la implementacion realizada<div class="td"></div><span class="tp">pag. 3</span></div>
    <div class="ti2"><span class="tn">2</span>Reglas semanticas utilizadas<div class="td"></div><span class="tp">pag. 4</span></div>
    <div class="ti2"><span class="tn">3</span>Atributos sintetizados y heredados<div class="td"></div><span class="tp">pag. 5</span></div>
    <div class="ti2"><span class="tn">4</span>Anotacion del AST<div class="td"></div><span class="tp">pag. 6</span></div>
    <div class="ti2"><span class="tn">5</span>Diseno y funcionamiento de la tabla de simbolos<div class="td"></div><span class="tp">pag. 7</span></div>
    <div class="ti2"><span class="tn">6</span>Reglas para la comprobacion de tipos<div class="td"></div><span class="tp">pag. 8</span></div>
    <div class="ti2"><span class="tn">7</span>Conversiones de tipos consideradas<div class="td"></div><span class="tp">pag. 9</span></div>
    <div class="ti2"><span class="tn">8</span>Errores semanticos implementados<div class="td"></div><span class="tp">pag. 10</span></div>
    <div class="ti2"><span class="tn">9</span>Pruebas realizadas<div class="td"></div><span class="tp">pag. 11</span></div>
    <div class="ti2"><span class="tn">10</span>Capturas de ejecucion<div class="td"></div><span class="tp">pag. 12</span></div>
  </div>
</div>

<!-- 1. DESCRIPCION -->
<div class="sec">
  <div class="sh"><div class="sn">1</div><div class="st">Descripcion de la Implementacion Realizada</div></div>
  <p>La Fase 3 se implemento como modulo independiente en <code>ide/compilador/semantico.py</code>. Recibe el AST de la Fase 2 y produce tres artefactos:</p>
  <ul>
    <li><strong>AST Anotado</strong>: clon del arbol con atributos semanticos en cada nodo.</li>
    <li><strong>Tabla de Simbolos</strong>: identificadores, tipos, offsets de memoria y lineas de uso.</li>
    <li><strong>Lista de Errores Semanticos</strong>: categoria, mensaje, variable y numero de linea.</li>
  </ul>
  <h3>Flujo de Procesamiento</h3>
  <div class="flujo">
    <div class="fp">Codigo Fuente (.src)</div><div class="fa">&rarr;</div>
    <div class="fp">Analisis Lexico</div><div class="fa">&rarr;</div>
    <div class="fp">Analisis Sintactico</div><div class="fa">&rarr;</div>
    <div class="fp">AST Original</div><div class="fa">&rarr;</div>
    <div class="fp">Analisis Semantico</div><div class="fa">&rarr;</div>
    <div class="fp">AST Anotado + Tabla + Errores</div>
  </div>
  <h3>Modulos Creados o Modificados</h3>
  <table>
    <thead><tr><th>Archivo</th><th>Rol</th><th>Descripcion</th></tr></thead>
    <tbody>
      <tr><td><code>ide/compilador/semantico.py</code></td><td>Nuevo</td><td>Motor semantico: AnalizadorSemantico y TablaSimbolos (803 lineas)</td></tr>
      <tr><td><code>ide/compilador/errores.py</code></td><td>Ampliado</td><td>Clase ErrorSemantico y 7 constantes de error semantico</td></tr>
      <tr><td><code>ide/modelos/datos.py</code></td><td>Ampliado</td><td>Campos semanticos en NodoArb (tipo_dato, valor, conversion, atributos) y Sim (desplazamiento, tam_bytes, referencias)</td></tr>
      <tr><td><code>ide/servicios/compilador.py</code></td><td>Ampliado</td><td>Fase semantica integrada en el pipeline del IDE via QThread</td></tr>
      <tr><td><code>ide/ui/panel_sim.py</code></td><td>Ampliado</td><td>Panel visual de tabla de simbolos con columnas de memoria hexadecimal</td></tr>
      <tr><td><code>ide/ui/panel_arb.py</code></td><td>Ampliado</td><td>Pestana &quot;Arbol Anotado&quot; separada de la pestana del AST original</td></tr>
      <tr><td><code>ide/ventana.py</code></td><td>Ampliado</td><td>Boton &quot;Semantico&quot; en barra de herramientas e integracion de resultados</td></tr>
      <tr><td><code>runner.py</code></td><td>Ampliado</td><td>Exportacion de ast_anotado.txt, tabla_simbolos.txt y errores_semanticos.txt</td></tr>
    </tbody>
  </table>
  <div class="al ali"><i>&#128161;</i><div>El analizador trabaja sobre una <strong>copia profunda</strong> del AST original, preservando el arbol sin anotaciones de la Fase 2. Ambas versiones se muestran en pestanas separadas del IDE.</div></div>
</div>

<!-- 2. REGLAS SEMANTICAS -->
<div class="sec">
  <div class="sh"><div class="sn">2</div><div class="st">Reglas Semanticas Utilizadas</div></div>
  <p>El analizador aplica 7 reglas formales durante el recorrido del AST. Cada regla esta asociada a uno o mas tipos de error semantico:</p>
  <div class="rb"><div class="rn">RS-01 &middot; Declaracion Obligatoria</div>Para todo identificador <em>id</em> en expresion, asignacion, cin o cout: <strong>id &isin; TablaSimbolos</strong>. Si no existe &rarr; <code>ERR_VAR_NO_DECLARADA</code>.</div>
  <div class="rb"><div class="rn">RS-02 &middot; Unicidad de Declaracion</div>Para toda declaracion de <em>id</em>: si ya existe en tabla &rarr; <code>ERR_DECL_DUPLICADA</code>. Se conserva el simbolo original registrado primero.</div>
  <div class="rb"><div class="rn">RS-03 &middot; Compatibilidad de Tipos en Asignacion</div>En <em>id := expr</em>: tipo(<em>expr</em>) debe ser compatible con tipo(<em>id</em>). Promocion int&rarr;float permitida. Reduccion float&rarr;int genera <code>ERR_ASIGNACION_INCOMPATIBLE</code>.</div>
  <div class="rb"><div class="rn">RS-04 &middot; Condicion Booleana en Estructuras de Control</div>La condicion de <code>if</code>, <code>while</code> y <code>do-while</code> debe producir tipo <code>bool</code>. Si produce otro tipo &rarr; <code>ERR_CONDICION_NO_BOOL</code>.</div>
  <div class="rb"><div class="rn">RS-05 &middot; Operadores Aritmeticos solo sobre Numericos</div>Los operadores +, -, *, /, ^ requieren int o float. El operador % requiere ambos int. El uso con bool genera <code>ERR_OPERADOR_INDEBIDO</code>.</div>
  <div class="rb"><div class="rn">RS-06 &middot; Operadores Logicos solo sobre Booleanos</div>Los operadores &amp;&amp;, ||, ! requieren operandos estrictamente bool. El uso con int o float genera <code>ERR_OPERADOR_INDEBIDO</code>.</div>
  <div class="rb"><div class="rn">RS-07 &middot; Tipo Resultado de Operadores Relacionales</div>Los operadores &lt;, &lt;=, &gt;, &gt;=, ==, != producen siempre tipo bool, sin importar si los operandos son int o float.</div>
</div>

<!-- 3. ATRIBUTOS -->
<div class="sec">
  <div class="sh"><div class="sn">3</div><div class="st">Atributos Sintetizados y Heredados Implementados</div></div>
  <p>El sistema implementa una gramatica de atributos con dos flujos de informacion:</p>
  <div class="ag">
    <div class="ac-h">
      <h4>&darr; Atributos Heredados (Top-Down)</h4>
      <p>Calculados en el nodo padre y pasados hacia los hijos en pre-orden.</p>
      <table><thead><tr><th>Atributo</th><th>Descripcion</th></tr></thead><tbody>
        <tr><td><code>dtype</code></td><td>Tipo declarado. Heredado desde el nodo Decl: tipo hacia cada Var: id hijo.</td></tr>
      </tbody></table>
      <pre>Decl: int  {dtype: int}
  Var: x {dtype: int, dir: 0}
  Var: y {dtype: int, dir: 4}
  Var: z {dtype: int, dir: 8}</pre>
    </div>
    <div class="ac-s">
      <h4>&uarr; Atributos Sintetizados (Bottom-Up)</h4>
      <p>Calculados desde los hijos y propagados al padre en post-orden.</p>
      <table><thead><tr><th>Atributo</th><th>Descripcion</th></tr></thead><tbody>
        <tr><td><code>tipo</code></td><td>Tipo resultante de la expresion, sintetizado desde hojas hacia raiz.</td></tr>
        <tr><td><code>val</code></td><td>Valor constante evaluado (constant folding) cuando todos los operandos son literales.</td></tr>
        <tr><td><code>dir</code></td><td>Desplazamiento de memoria, extraido de la tabla de simbolos al visitar un identificador.</td></tr>
      </tbody></table>
    </div>
  </div>
  <h3>Atributo <code>conv</code> (marcador de conversion)</h3>
  <p>No es heredado ni sintetizado en sentido estricto. Se anota en el nodo hijo cuando el verificador de tipos detecta una operacion con tipos mixtos que requiere conversion implicita:</p>
  <pre>Op: +  {tipo: float}
  Num: 4   {tipo: int, val: 4, conv: int -&gt; float}  &lt;-- marcado
  Num: 2.5 {tipo: float, val: 2.5}</pre>
</div>

<!-- 4. ANOTACION AST -->
<div class="sec">
  <div class="sh"><div class="sn">4</div><div class="st">Explicacion de la Forma en que se Anoto el AST</div></div>
  <h3>Proceso de Clonacion</h3>
  <p>Antes de iniciar el analisis, <code>clonar_ast()</code> realiza una <strong>copia profunda</strong> del arbol original. Esto garantiza que el AST de la Fase 2 permanezca intacto para visualizacion independiente en el IDE.</p>
  <h3>Campos Semanticos Agregados al Nodo (NodoArb)</h3>
  <table>
    <thead><tr><th>Campo</th><th>Tipo Python</th><th>Descripcion</th></tr></thead>
    <tbody>
      <tr><td><code>tipo_dato</code></td><td><code>str</code></td><td>Tipo semantico del nodo: "int", "float", "bool", "string" o "error"</td></tr>
      <tr><td><code>valor</code></td><td><code>Any</code></td><td>Valor evaluado en tiempo de compilacion (constant folding)</td></tr>
      <tr><td><code>conversion</code></td><td><code>str</code></td><td>Conversion implicita requerida: "int -&gt; float"</td></tr>
      <tr><td><code>atributos</code></td><td><code>dict</code></td><td>Diccionario extensible para dtype, dir y atributos futuros</td></tr>
    </tbody>
  </table>
  <h3>Dispatcher de Nodos: _analizar_nodo()</h3>
  <p>El metodo actua como dispatcher que determina que handler ejecutar segun la etiqueta del nodo:</p>
  <table>
    <thead><tr><th>Tipo de Nodo</th><th>Handler</th><th>Orden de Recorrido</th></tr></thead>
    <tbody>
      <tr><td><code>Decl: tipo</code></td><td><code>_procesar_declaracion()</code></td><td>Pre-orden: hereda dtype a hijos</td></tr>
      <tr><td><code>Asignar: id</code></td><td><code>_procesar_asignacion()</code></td><td>Evalua expresion hija, luego verifica tipo</td></tr>
      <tr><td><code>Si (if)</code></td><td><code>_procesar_if()</code></td><td>Condicion &rarr; then &rarr; else</td></tr>
      <tr><td><code>Mientras (while)</code></td><td><code>_procesar_while()</code></td><td>Condicion &rarr; cuerpo</td></tr>
      <tr><td><code>Hacer (do-while)</code></td><td><code>_procesar_do_while()</code></td><td>Cuerpo &rarr; condicion</td></tr>
      <tr><td><code>Op: operador</code></td><td><code>_evaluar_expresion()</code></td><td>Post-orden: sintetiza tipo y val desde hijos</td></tr>
      <tr><td><code>Id: nombre</code></td><td><code>_evaluar_expresion()</code></td><td>Hoja: consulta tabla de simbolos</td></tr>
      <tr><td><code>Num: valor</code></td><td><code>_evaluar_expresion()</code></td><td>Hoja: tipo determinado por punto decimal</td></tr>
    </tbody>
  </table>
  <h3>Ejemplo real: AST Anotado (testSintactico.src, lineas 3-4)</h3>
  <div class="ast"><pre>Decl: int {dtype: int}   [L3]
+-- Var: x {dtype: int, dir: 0, tipo: int}   [L3]
+-- Var: y {dtype: int, dir: 4, tipo: int}   [L3]
+-- Var: z {dtype: int, dir: 8, tipo: int}   [L3]
Decl: float {dtype: float}   [L4]
+-- Var: a {dtype: float, dir: 12, tipo: float}   [L4]
+-- Var: b {dtype: float, dir: 16, tipo: float}   [L4]
+-- Var: c {dtype: float, dir: 20, tipo: float}   [L4]</pre></div>
</div>

<!-- 5. TABLA DE SIMBOLOS -->
<div class="sec">
  <div class="sh"><div class="sn">5</div><div class="st">Diseno y Funcionamiento de la Tabla de Simbolos</div></div>
  <h3>Estructura de Datos: TablaSimbolos</h3>
  <p>La clase <code>TablaSimbolos</code> encapsula un <code>dict[str, Sim]</code> donde la llave es el nombre del identificador. Cada entrada (<code>Sim</code>) almacena:</p>
  <table>
    <thead><tr><th>Campo</th><th>Tipo</th><th>Descripcion</th></tr></thead>
    <tbody>
      <tr><td><code>nombre</code></td><td>str</td><td>Lexema del identificador</td></tr>
      <tr><td><code>tipo</code></td><td>str</td><td>Tipo de dato declarado</td></tr>
      <tr><td><code>ambito</code></td><td>str</td><td>Ambito de declaracion (siempre "main" en esta fase)</td></tr>
      <tr><td><code>linea</code></td><td>int</td><td>Numero de linea donde fue declarado</td></tr>
      <tr><td><code>desplazamiento</code></td><td>int</td><td>Offset en bytes desde el inicio del ambito</td></tr>
      <tr><td><code>tam_bytes</code></td><td>int</td><td>Tamano del tipo en bytes</td></tr>
      <tr><td><code>referencias</code></td><td>list[int]</td><td>Lista de lineas donde la variable es utilizada</td></tr>
    </tbody>
  </table>
  <h3>Asignacion de Memoria</h3>
  <p>El contador <code>_desplazamiento_actual</code> inicia en 0 y avanza por el tamano del tipo de cada variable registrada:</p>
  <table>
    <thead><tr><th>Tipo</th><th>Tamano</th><th>Justificacion</th></tr></thead>
    <tbody>
      <tr><td><span class="tag ti">int</span></td><td>4 bytes</td><td>Entero de 32 bits (convención estándar)</td></tr>
      <tr><td><span class="tag tf">float</span></td><td>4 bytes</td><td>IEEE 754 de simple precision (32 bits)</td></tr>
      <tr><td><span class="tag tb">bool</span></td><td>1 byte</td><td>Almacenamiento minimo para valor verdadero/falso</td></tr>
    </tbody>
  </table>
  <h3>Tabla de Simbolos Generada &mdash; testSintactico.src</h3>
  <table>
    <thead><tr><th>Nombre</th><th>Tipo</th><th>Ambito</th><th>Dir. Memoria</th><th>Tam(B)</th><th>Lin.Decl.</th><th>Referencias</th></tr></thead>
    <tbody>
      <tr><td><strong>x</strong></td><td><span class="tag ti">int</span></td><td>main</td><td><code>0 (0x0000)</code></td><td>4</td><td>3</td><td>7, 13, 18, 22, 30, 34, 35, 41</td></tr>
      <tr><td><strong>y</strong></td><td><span class="tag ti">int</span></td><td>main</td><td><code>4 (0x0004)</code></td><td>4</td><td>3</td><td>8, 9, 10, 14, 19, 27, 33, 37, 39, 44</td></tr>
      <tr><td><strong>z</strong></td><td><span class="tag ti">int</span></td><td>main</td><td><code>8 (0x0008)</code></td><td>4</td><td>3</td><td>9, 15, 36, 40</td></tr>
      <tr><td><strong>a</strong></td><td><span class="tag tf">float</span></td><td>main</td><td><code>12 (0x000C)</code></td><td>4</td><td>4</td><td>12, 19</td></tr>
      <tr><td><strong>b</strong></td><td><span class="tag tf">float</span></td><td>main</td><td><code>16 (0x0010)</code></td><td>4</td><td>4</td><td>16, 23, 25</td></tr>
      <tr><td><strong>c</strong></td><td><span class="tag tf">float</span></td><td>main</td><td><code>20 (0x0014)</code></td><td>4</td><td>4</td><td>&mdash;</td></tr>
      <tr><td><strong>bandera</strong></td><td><span class="tag tb">bool</span></td><td>main</td><td><code>24 (0x0018)</code></td><td>1</td><td>5</td><td>22</td></tr>
    </tbody>
  </table>
  <div class="al ala"><i>&#128204;</i><div>La variable <strong>c</strong> esta registrada (declarada en L4) pero su lista de referencias esta vacia. Esta informacion es util para advertencias de "variable declarada pero no usada" en fases posteriores.</div></div>
</div>

<!-- 6. COMPROBACION DE TIPOS -->
<div class="sec">
  <div class="sh"><div class="sn">6</div><div class="st">Reglas para la Comprobacion de Tipos</div></div>
  <h3>Operadores Aritmeticos (+, -, *, /, ^, %)</h3>
  <table>
    <thead><tr><th>Operando Izq.</th><th>Operando Der.</th><th>Tipo Resultado</th><th>Accion</th></tr></thead>
    <tbody>
      <tr><td><span class="tag ti">int</span></td><td><span class="tag ti">int</span></td><td><span class="tag ti">int</span></td><td>Operacion directa. Constant folding aplicado.</td></tr>
      <tr><td><span class="tag tf">float</span></td><td><span class="tag tf">float</span></td><td><span class="tag tf">float</span></td><td>Operacion directa. Constant folding aplicado.</td></tr>
      <tr><td><span class="tag ti">int</span></td><td><span class="tag tf">float</span></td><td><span class="tag tf">float</span></td><td>Marca el nodo int con conv: int-&gt;float.</td></tr>
      <tr><td><span class="tag tf">float</span></td><td><span class="tag ti">int</span></td><td><span class="tag tf">float</span></td><td>Marca el nodo int con conv: int-&gt;float.</td></tr>
      <tr><td><span class="tag tb">bool</span></td><td>cualquiera</td><td><span class="tag te">error</span></td><td>ERR_OPERADOR_INDEBIDO generado.</td></tr>
      <tr><td colspan="4"><strong>Operador %:</strong> Requiere ambos operandos int. Cualquier otro tipo genera ERR_OPERADOR_INDEBIDO.</td></tr>
    </tbody>
  </table>
  <h3>Operadores Relacionales (&lt;, &lt;=, &gt;, &gt;=, ==, !=)</h3>
  <table>
    <thead><tr><th>Tipos de Operandos</th><th>Resultado</th><th>Observacion</th></tr></thead>
    <tbody>
      <tr><td><span class="tag ti">int</span> op <span class="tag ti">int</span></td><td><span class="tag tb">bool</span></td><td>Comparacion directa</td></tr>
      <tr><td><span class="tag tf">float</span> op <span class="tag tf">float</span></td><td><span class="tag tb">bool</span></td><td>Comparacion directa</td></tr>
      <tr><td><span class="tag ti">int</span> op <span class="tag tf">float</span></td><td><span class="tag tb">bool</span></td><td>El int se convierte implicitamente a float</td></tr>
      <tr><td><span class="tag tb">bool</span> op <span class="tag tb">bool</span></td><td><span class="tag tb">bool</span></td><td>Solo se permite == y !=</td></tr>
      <tr><td><span class="tag tb">bool</span> op numerico</td><td><span class="tag te">error</span></td><td>ERR_TIPO_INCOMPATIBLE</td></tr>
    </tbody>
  </table>
  <h3>Operadores Logicos (&amp;&amp;, ||, !)</h3>
  <table>
    <thead><tr><th>Tipos de Operandos</th><th>Resultado</th><th>Observacion</th></tr></thead>
    <tbody>
      <tr><td><span class="tag tb">bool</span> op <span class="tag tb">bool</span></td><td><span class="tag tb">bool</span></td><td>Correcto</td></tr>
      <tr><td><span class="tag ti">int</span> op <span class="tag tb">bool</span></td><td><span class="tag te">error</span></td><td>ERR_OPERADOR_INDEBIDO</td></tr>
      <tr><td>no-bool op no-bool</td><td><span class="tag te">error</span></td><td>ERR_OPERADOR_INDEBIDO</td></tr>
    </tbody>
  </table>
  <h3>Asignaciones</h3>
  <table>
    <thead><tr><th>Tipo Variable</th><th>Tipo Expresion</th><th>Resultado</th></tr></thead>
    <tbody>
      <tr><td><span class="tag ti">int</span></td><td><span class="tag ti">int</span></td><td>&#10003; Compatible</td></tr>
      <tr><td><span class="tag tf">float</span></td><td><span class="tag tf">float</span></td><td>&#10003; Compatible</td></tr>
      <tr><td><span class="tag tf">float</span></td><td><span class="tag ti">int</span></td><td>&#10003; Compatible con conv: int-&gt;float</td></tr>
      <tr><td><span class="tag ti">int</span></td><td><span class="tag tf">float</span></td><td>&#10007; ERR_ASIGNACION_INCOMPATIBLE</td></tr>
      <tr><td><span class="tag tb">bool</span></td><td>numerico</td><td>&#10007; ERR_ASIGNACION_INCOMPATIBLE</td></tr>
      <tr><td>numerico</td><td><span class="tag tb">bool</span></td><td>&#10007; ERR_ASIGNACION_INCOMPATIBLE</td></tr>
    </tbody>
  </table>
</div>

<!-- 7. CONVERSIONES -->
<div class="sec">
  <div class="sh"><div class="sn">7</div><div class="st">Conversiones de Tipos Consideradas</div></div>
  <p>Se implementan unicamente conversiones implicitas de <strong>ampliacion</strong> (widening), que no producen perdida de informacion. Las conversiones de reduccion (narrowing) son invalidas.</p>
  <table>
    <thead><tr><th>Tipo Origen</th><th>Tipo Destino</th><th>Clasificacion</th><th>Implementacion</th></tr></thead>
    <tbody>
      <tr><td><span class="tag ti">int</span></td><td><span class="tag tf">float</span></td><td>&#10003; Ampliacion (permitida)</td><td>Se anota <code>conv: int -&gt; float</code> en el nodo origen. El generador de codigo emitira instruccion ITOF.</td></tr>
      <tr><td><span class="tag tf">float</span></td><td><span class="tag ti">int</span></td><td>&#10007; Reduccion (prohibida)</td><td>Genera ERR_ASIGNACION_INCOMPATIBLE. Requiere conversion explicita.</td></tr>
      <tr><td><span class="tag tb">bool</span></td><td>numerico</td><td>&#10007; Invalida</td><td>Incompatibles en todas las operaciones salvo == y != entre booleanos.</td></tr>
    </tbody>
  </table>
  <h3>Ejemplo real: Conversiones en Linea 12 (testSintactico.src)</h3>
  <p>La expresion <code>a = 24.0 + 4 - 1/3*2 + 34 - 1</code> contiene operaciones int/float mixtas. Los nodos enteros se marcan con la anotacion de conversion:</p>
  <div class="ast"><pre>Asignar: a {dir: 12, tipo: float}   [L12]
  +-- Op: - {tipo: float, val: 61.0}   [L12]
      +-- Op: + {tipo: float, val: 62.0}   [L12]
      |   +-- Op: - {tipo: float, val: 28.0}   [L12]
      |   |   +-- Op: + {tipo: float, val: 28.0}   [L12]
      |   |   |   +-- Num: 24.0 {tipo: float, val: 24.0}   [L12]
      |   |   |   +-- Num: 4   {tipo: int, val: 4, conv: int -&gt; float}  &lt;-- CONV
      |   |   +-- Op: * {tipo: int, val: 0, conv: int -&gt; float}          &lt;-- CONV
      |   +-- Num: 34  {tipo: int, val: 34, conv: int -&gt; float}          &lt;-- CONV
      +-- Num: 1   {tipo: int, val: 1, conv: int -&gt; float}               &lt;-- CONV</pre></div>
  <div class="al ale"><i>&#10003;</i><div>Las anotaciones <code>conv</code> indican exactamente que nodos necesitan instruccion de conversion en el futuro generador de codigo, sin necesidad de re-analizar el arbol.</div></div>
</div>

<!-- 8. ERRORES SEMANTICOS -->
<div class="sec">
  <div class="sh"><div class="sn">8</div><div class="st">Errores Semanticos Implementados</div></div>
  <p>Se implementaron <strong>7 categorias de error semantico</strong> en <code>ide/compilador/errores.py</code>. Cada error reporta: categoria, mensaje detallado, identificador o simbolo involucrado y numero de linea.</p>
  <div class="ec"><div class="eh">ERR_VAR_NO_DECLARADA &mdash; Uso de Variable No Declarada</div><div class="eb">Uso de identificador que no existe en la Tabla de Simbolos en expresion, asignacion, cin o cout.<br><strong>Ejemplo:</strong> <code>z = x + noExiste;</code> &rarr; "La variable 'noExiste' no ha sido declarada."</div></div>
  <div class="ec"><div class="eh">ERR_DECL_DUPLICADA &mdash; Declaracion Duplicada</div><div class="eb">Intento de declarar un identificador ya registrado. Se preserva el simbolo original.<br><strong>Ejemplo:</strong> <code>int x; ... int x;</code> &rarr; "La variable 'x' ya fue declarada en la linea N."</div></div>
  <div class="ec"><div class="eh">ERR_TIPO_INCOMPATIBLE &mdash; Incompatibilidad de Tipos</div><div class="eb">Tipos de operandos incompatibles en operacion relacional o aritmetica.<br><strong>Ejemplo:</strong> comparar bool con int usando operador &lt;.</div></div>
  <div class="ec"><div class="eh">ERR_CONVERSION_INVALIDA &mdash; Conversion de Tipos No Valida</div><div class="eb">Asignacion con reduccion de tipo o conversion entre tipos incompatibles.<br><strong>Ejemplo:</strong> <code>int x = 3.14;</code> &rarr; conversion float-&gt;int invalida.</div></div>
  <div class="ec"><div class="eh">ERR_OPERADOR_INDEBIDO &mdash; Uso Indebido de Operadores</div><div class="eb">Operador aplicado a tipos que no lo soportan.<br><strong>Ejemplo real (L22):</strong> <code>if (x &amp;&amp; bandera)</code> &rarr; "Uso indebido de '&amp;&amp;': requiere bool, se obtuvo int y bool."</div></div>
  <div class="ec"><div class="eh">ERR_ASIGNACION_INCOMPATIBLE &mdash; Inconsistencia de Tipos en Asignacion</div><div class="eb">El tipo del lado derecho no puede asignarse al lado izquierdo sin conversion explicita.<br><strong>Ejemplo real (L19):</strong> <code>y = a + 3;</code> &rarr; "No se puede asignar expresion float a variable int."</div></div>
  <div class="ec"><div class="eh">ERR_CONDICION_NO_BOOL &mdash; Tipo No Booleano en Condicion</div><div class="eb">Condicion de if, while o do-while que no produce bool.<br><strong>Ejemplo:</strong> <code>if x then</code> (x es int) &rarr; "Tipo no booleano en condicion de 'if': se requiere bool, se obtuvo int."</div></div>
  <h3>Errores Detectados en testSintactico.src</h3>
  <table>
    <thead><tr><th>#</th><th>Linea</th><th>Categoria</th><th>Variable/Op.</th><th>Descripcion</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>19</td><td><span class="tag te">ERR_ASIGNACION_INCOMPATIBLE</span></td><td><code>y</code></td><td>Se asigna resultado float (a + 3) a variable int y</td></tr>
      <tr><td>2</td><td>22</td><td><span class="tag te">ERR_OPERADOR_INDEBIDO</span></td><td><code>&amp;&amp;</code></td><td>Operando x (tipo int) con &amp;&amp; que requiere bool</td></tr>
    </tbody>
  </table>
</div>

<!-- 9. PRUEBAS -->
<div class="sec">
  <div class="sh"><div class="sn">9</div><div class="st">Explicacion de las Pruebas Realizadas</div></div>
  <h3>Prueba 1: testSintactico.src (programa valido sintacticamente)</h3>
  <p>Programa con 7 variables de 3 tipos, expresiones aritmeticas complejas, estructuras de control anidadas y errores semanticos intencionales en 2 lineas.</p>
  <table>
    <thead><tr><th>Aspecto Verificado</th><th>Lineas</th><th>Resultado Esperado</th><th>OK</th></tr></thead>
    <tbody>
      <tr><td>Declaracion multiple int</td><td>3</td><td>x, y, z con offsets 0, 4, 8</td><td>&#10003;</td></tr>
      <tr><td>Declaracion multiple float</td><td>4</td><td>a, b, c con offsets 12, 16, 20</td><td>&#10003;</td></tr>
      <tr><td>Declaracion bool de 1 byte</td><td>5</td><td>bandera con offset 24</td><td>&#10003;</td></tr>
      <tr><td>Asignaciones y expresiones aritmeticas</td><td>7-16</td><td>Tipos correctos, constant folding</td><td>&#10003;</td></tr>
      <tr><td>Expresion int/float mixta</td><td>12</td><td>4 nodos marcados conv: int-&gt;float</td><td>&#10003;</td></tr>
      <tr><td>Error: float asignado a int</td><td>19</td><td>ERR_ASIGNACION_INCOMPATIBLE</td><td>&#10003;</td></tr>
      <tr><td>Error: operador logico con int</td><td>22</td><td>ERR_OPERADOR_INDEBIDO</td><td>&#10003;</td></tr>
      <tr><td>Estructura do-while con operador %</td><td>32-37</td><td>Cuerpo y condicion analizados correctamente</td><td>&#10003;</td></tr>
      <tr><td>Estructura while con condicion bool</td><td>39-42</td><td>Condicion y == 0 produce bool correctamente</td><td>&#10003;</td></tr>
      <tr><td>Variable declarada pero no usada (c)</td><td>4</td><td>En tabla con lista de referencias vacia</td><td>&#10003;</td></tr>
      <tr><td>Sentencias cin y cout</td><td>35, 40, 41, 44</td><td>Variables verificadas y registradas en referencias</td><td>&#10003;</td></tr>
    </tbody>
  </table>
  <h3>Prueba 2: TestSemantica.txt.txt (con errores sintacticos)</h3>
  <p>Archivo con multiples errores sintacticos intencionales (uso de <code>until</code>, operadores mal escritos). Prueba la robustez ante ASTs parciales.</p>
  <table>
    <thead><tr><th>Comportamiento Verificado</th><th>Resultado</th></tr></thead>
    <tbody>
      <tr><td>El semantico continua ejecutandose con errores sintacticos</td><td>&#10003; Analiza el AST parcial</td></tr>
      <tr><td>Variables declaradas correctamente se registran en la tabla</td><td>&#10003; 6 de 7 variables registradas</td></tr>
      <tr><td>No se generan cascadas de errores falsos</td><td>&#10003; Sin errores espurios</td></tr>
      <tr><td>Errores semanticos en secciones analizables se reportan</td><td>&#10003; Correctamente reportados</td></tr>
    </tbody>
  </table>
  <div class="al ali"><i>&#9432;</i><div>La variable <strong>y</strong> en <code>until y == 5</code> no aparece en referencias porque <code>until</code> no es palabra reservada de la gramatica. El parser no construyo nodos AST para esa seccion. Comportamiento correcto segun teoria de compiladores.</div></div>
</div>

<!-- 10. CAPTURAS -->
<div class="sec">
  <div class="sh"><div class="sn">10</div><div class="st">Capturas de Ejecucion</div></div>
  <div class="al ala"><i>&#128247;</i><div><strong>Instruccion:</strong> Ejecuta <code>py main.py</code>, abre testSintactico.src y presiona el boton "Semantico". Captura con Win+Shift+S y pega las imagenes en cada espacio.</div></div>
  <h3>Captura 1 &mdash; Panel Arbol Anotado</h3>
  <p>Muestra el arbol con atributos {dtype}, {tipo}, {dir}, {val} y {conv} en cada nodo.</p>
  <div class="cap">[ Insertar captura del panel &quot;Arbol Anotado&quot; del IDE ]</div>
  <h3>Captura 2 &mdash; Panel Tabla de Simbolos</h3>
  <p>Muestra las 7 variables con columnas: Nombre, Tipo, Ambito, Direccion de Memoria (decimal y hexadecimal), Tamano en bytes, Linea de declaracion y Lineas de referencia.</p>
  <div class="cap">[ Insertar captura del panel &quot;Tabla de Simbolos&quot; del IDE ]</div>
  <h3>Captura 3 &mdash; Panel Errores Semanticos</h3>
  <p>Muestra los 2 errores detectados: asignacion incompatible en L19 y operador indebido en L22.</p>
  <div class="cap">[ Insertar captura del panel de &quot;Errores Semanticos&quot; del IDE ]</div>
  <h3>Captura 4 &mdash; Archivos de Salida (outputs/)</h3>
  <div class="cap">[ Insertar captura de tabla_simbolos.txt o ast_anotado.txt ]</div>
  <h3>Salidas Textuales Generadas</h3>
  <pre>Errores Semanticos Detectados
Archivo fuente: testSintactico.src
----------------------------------------------------
Total: 2 error(es) semantico(s)

[1] Linea 19
    Tipo    : Inconsistencia de tipos en asignacion
    Elemento: 'y'
    Mensaje : No se puede asignar una expresion float a la variable entera int.

[2] Linea 22
    Tipo    : Uso indebido de operadores
    Elemento: '&amp;&amp;'
    Mensaje : Uso indebido de '&amp;&amp;': requiere bool, se obtuvo int y bool.</pre>
  <pre>Tabla de Simbolos - testSintactico.src
-------------------------------------------------------------------
Nombre    Tipo    Ambito  Dir.Mem       Tam(B)  Lin.Decl  Refs
-------------------------------------------------------------------
x         int     main    0 (0x0000)    4       3         7,13,18,22,30,34,35,41
y         int     main    4 (0x0004)    4       3         8,9,10,14,19,27,33,37,39,44
z         int     main    8 (0x0008)    4       3         9,15,36,40
a         float   main    12 (0x000C)   4       4         12,19
b         float   main    16 (0x0010)   4       4         16,23,25
c         float   main    20 (0x0014)   4       4         ---
bandera   bool    main    24 (0x0018)   1       5         22
-------------------------------------------------------------------
Total: 7 identificadores registrados</pre>
</div>

<div class="pie">Compiladores II &middot; Fase 3 &mdash; Analisis Semantico &nbsp;|&nbsp; IDE de Compiladores &middot; Python / PySide6</div>
</div>
</body>
</html>""",
]

out = pathlib.Path(__file__).parent / "Reporte_Fase3_Semantica.html"
out.write_text("".join(HTML_PARTS), encoding="utf-8")
print(f"OK - {out.name} generado ({out.stat().st_size:,} bytes)")
print(f"Ruta: {out.resolve()}")
print("Abre el archivo en Chrome/Edge y usa Ctrl+P -> Guardar como PDF")
