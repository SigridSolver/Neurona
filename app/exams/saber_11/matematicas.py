import random
import json
import base64
from math import gcd
from app.exams.base_area import BaseArea

def ensure_svg_xmlns(svg_str):
    if svg_str and '<svg' in svg_str and 'xmlns' not in svg_str:
        svg_str = svg_str.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg_str

class MatematicasArea(BaseArea):
    @property
    def area_name(self) -> str:
        return "Matemáticas"

    def get_generation_prompt(self, needed: int) -> str:
        return f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Matemáticas.
    Genera una lista de {needed} preguntas de selección múltiple originales y diferentes entre sí en contexto, estructura y solución, inéditas, altamente didácticas y visuales.

    ESTILO ICFES OBLIGATORIO:
    - Las preguntas deben evaluar competencias y razonamiento matemático, no la memorización de fórmulas o cálculo mecánico puro.
    - Deben presentar información suficiente para ser resueltas.
    - Cada pregunta debe evaluar UNA competencia matemática específica del ICFES:
      * Interpretación y representación
      * Formulación y ejecución
      * Argumentación
    - Todas las preguntas deben estar contextualizadas en situaciones cotidianas o aplicadas (ej. economía familiar, transporte, deportes, ventas, fenómenos sociales, consumo, experimentos, producción, ambiente, datos reales, etc.). Evita ejercicios abstractos sin contexto.
    - Varía el nivel cognitivo entre comprensión, aplicación e inferencia matemática, manteniendo una dificultad intermedia.
    - Debe existir una única respuesta correcta, inequívoca y verificable.
    - Los distractores (opciones incorrectas) deben ser plausibles y representar errores frecuentes de razonamiento o cálculo que cometen los estudiantes. Evita opciones absurdas.
    - Evita preguntas de cálculo mecánico o rutinario sin interpretación o análisis contextual.

    REGLA CRÍTICA DE DATOS Y GRÁFICOS:
    - NO utilices llaves, corchetes, ni variables de reemplazo de ningún tipo (como texto entre llaves o marcadores de plantilla). Escribe todos los números, nombres, cotas y valores finales de forma directa y explícita en el texto del enunciado (por ejemplo: escribe "base de 8 cm" directamente en lugar de usar variables).
    - Todo gráfico SVG generado DEBE contener las etiquetas de datos, números, valores y nombres de los ejes explícitamente dibujados usando elementos `<text>` legibles y con contraste (ej. blanco o amarillo sobre fondo oscuro).
    - Evita generar gráficos mudos (barras sin números, figuras geométricas sin cotas, o planos sin coordenadas). Dibuja los números en el propio SVG.

    IMPORTANTE: Cada pregunta DEBE ser de una CATEGORÍA DIFERENTE. Selecciona aleatoriamente entre estas categorías:

    CATEGORÍA 1 - GRÁFICA CIRCULAR (TORTA):
    - Contexto: distribución porcentual de datos cotidianos (asignaturas, deportes, preferencias, presupuestos).
    - SVG: Gráfico de pastel con sectores de colores (#38bdf8, #f43f5e, #10b981, #fbbf24), fondo oscuro (#0f172a), porcentajes explícitos dibujados con `<text>` dentro de cada sector, y leyenda lateral legible.
    - Pregunta: calcular la cantidad real a partir de un porcentaje dado o realizar un análisis/interpretación de la distribución.

    CATEGORÍA 2 - GRÁFICA DE BARRAS / HISTOGRAMA:
    - Contexto: distribución de frecuencias (ej. notas, ventas, asistencia).
    - SVG: Barras verticales de colores vibrantes con sus números de frecuencia dibujados en la parte superior de cada barra, ejes X/Y con nombres de variables contextuales y números indicadores de escala dibujados.
    - Pregunta: calcular media aritmética, rango, total, o interpretar relaciones entre las barras.

    CATEGORÍA 3 - DIAGRAMA DE VENN:
    - Contexto: superposición de conjuntos en un escenario real (ej. estudiantes que prefieren deportes o idiomas).
    - SVG: Dos o tres círculos superpuestos con los valores numéricos de cada región dibujados con `<text>` en el centro de sus respectivas áreas, fondo oscuro y etiquetas claras.
    - Pregunta: probabilidad de un evento específico o interpretación de conjuntos.

    CATEGORÍA 4 - PLANO CARTESIANO:
    - Contexto: recta o puntos que representan una situación real (ej. costo de envío según distancia).
    - SVG: Ejes coordenados X/Y marcados con números y una recta trazada con puntos clave claramente rotulados con sus coordenadas (ej. "P(3, 4)").
    - Pregunta: calcular pendiente, intercepto, distancia, o interpretar el significado contextual de la recta.

    CATEGORÍA 5 - GEOMETRÍA (Triángulos, Rectángulos, Círculos):
    - Contexto: cálculo de dimensiones o distribución en espacios (ej. distribución de un terreno, una ventana).
    - SVG: Figura geométrica con cotas, medidas e indicaciones de base y altura escritas de forma muy visible con elementos `<text>` (ej. "8 m" y "5 m") junto a líneas de acotación.
    - Pregunta: calcular área, perímetro, o resolver un problema de optimización simple.

    CATEGORÍA 6 - ECUACIÓN CUADRÁTICA:
    - Enunciado con fórmula LaTeX: $$ax^2 + bx + c = 0$$ que modele una trayectoria, costo o ganancia.
    - Pregunta: suma de raíces, discriminante o soluciones en el contexto planteado.
    - SVG: Puede ser null o un gráfico de la parábola con las raíces y el vértice marcados.

    CATEGORÍA 7 - FRACCIONES:
    - Enunciado con fórmula LaTeX: $$\\frac{{a}}{{b}} + \\frac{{c}}{{d}}$$
    - Pregunta: resultado de la operación simplificado en un contexto aplicado (ej. reparto de recursos).
    - SVG: Puede ser null o un diagrama explicativo de las partes.

    CATEGORÍA 8 - TABLA DE DATOS (Mediana/Moda):
    - Contexto: estudio estadístico de variables discretas.
    - SVG: Una tabla rectangular estilizada con celdas de colores y los datos numéricos ordenados escritos de forma muy clara.
    - Pregunta: calcular mediana o moda e interpretar su significado.

    CATEGORÍA 9 - FUNCIONES EXPONENCIALES:
    - Enunciado: evaluar función $f(x) = a \\cdot 2^{{x+c}} + d$ que represente un modelo de crecimiento.
    - Pregunta: calcular $f(x)$ para un valor dado o interpretar el crecimiento.
    - SVG: Puede ser null o el gráfico de la curva exponencial.

    CATEGORÍA 10 - PROBABILIDAD:
    - Contexto: experimentos de azar, juegos o decisiones cotidianas.
    - Pregunta: calcular probabilidad simple o compuesta.
    - SVG: Diagrama de árbol con porcentajes, tabla de contingencia o gráfico explicativo.

    CATEGORÍA 11 - PROPORCIONALIDAD:
    - Contexto: recetas, escalas de mapas, velocidad, variaciones de producción.
    - Pregunta: razón entre magnitudes, regla de tres o variación proporcional directa o inversa.
    - SVG: Gráfico de proporcionalidad lineal o diagrama explicativo.

    CATEGORÍA 12 - ANÁLISIS ESTADÍSTICO:
    - Contexto: conjuntos de datos reales de encuestas o rendimiento deportivo.
    - Pregunta: interpretar tendencias, comparar dos conjuntos de datos, o seleccionar la conclusión basada en la evidencia estadística.
    - SVG: Gráfico de líneas o comparación de conjuntos.

    REGLAS GENERALES DE SVG:
    1. Si la categoría requiere SVG, INCLUYE el código SVG completo en "graphic". Usa fondo oscuro (fill="#0f172a"), bordes redondeados, colores brillantes (#38bdf8, #f43f5e, #10b981).
    2. Si la categoría no requiere SVG, el campo "graphic" puede ser null pero la explicación DEBE usar LaTeX extenso.
    3. Las explicaciones deben ser paso a paso, claras, pedagógicas y concisas, usando $$fórmulas$$ en LaTeX.
    4. Usa **negritas** (markdown) para resaltar conceptos clave.
    5. CRÍTICO: No incluyas números de pregunta (como "1.", "2.") en el texto de los enunciados.
    6. VARÍA las categorías: no repitas la misma categoría en múltiples preguntas.

    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Matemáticas"
       - "text": "[El enunciado completo con datos reales integrados]"
       - "options": ["Opción A", "Opción B", "Opción C", "Opción D"]
       - "correct_answer": "[Debe ser idéntica a una de las opciones]"
       - "explanation": "[justificación pedagógica, concisa, y clara paso a paso con LaTeX]"
       - "difficulty": "Intermedio"
       - "graphic": "[Código SVG completo o null]"
    """

    def process_question(self, q: dict, seed: int = None) -> dict:
        if not q:
            return q
            
        # Solo procesamos si es una pregunta paramétrica del sistema
        if not q.get("is_parametric", False):
            return q
            
        text = q.get("text", "")
        graphic = q.get("graphic")
        options = q.get("options", [])
        explanation = q.get("explanation", "")
        
        placeholders = [
            "base", "altura", "inclinacion", "frec_1", "frec_2", "frec_3", "frec_4", 
            "futbol_solo", "ambos", "baloncesto_solo", "ninguno", "n_estudiantes", 
            "k_seleccionados", "a", "c_sign", "c_abs", "d", "x_eval", "slope", "x2_svg"
        ]
        
        if text:
            for p in placeholders:
                text = text.replace(f"{{{{{p}}}}}", f"{{{p}}}")
        if graphic and isinstance(graphic, str):
            if graphic.strip().startswith("<svg"):
                graphic = graphic.replace("{{", "{").replace("}}", "}")
                graphic = ensure_svg_xmlns(graphic)
                try:
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(graphic.encode('utf-8')).decode('utf-8')
                except Exception as e:
                    print("Error pre-encoding raw SVG:", e)
            elif "base64," in graphic:
                try:
                    _header, _encoded = graphic.split("base64,", 1)
                    _decoded = base64.b64decode(_encoded).decode("utf-8")
                    _decoded = ensure_svg_xmlns(_decoded)
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(_decoded.encode('utf-8')).decode('utf-8')
                except Exception:
                    if "charset=utf-8" not in graphic:
                        graphic = graphic.replace("data:image/svg+xml;base64,", "data:image/svg+xml;charset=utf-8;base64,")
        if explanation:
            for p in placeholders:
                explanation = explanation.replace(f"{{{{{p}}}}}", f"{{{p}}}")
        if options and isinstance(options, list):
            new_opts = []
            for o in options:
                if isinstance(o, str):
                    for p in placeholders:
                        o = o.replace(f"{{{{{p}}}}}", f"{{{p}}}")
                new_opts.append(o)
            options = new_opts
            
        q = dict(q)
        q["text"] = text
        q["graphic"] = graphic
        q["options"] = options
        q["explanation"] = explanation
        
        local_random = random.Random(seed) if seed is not None else random.Random()
        
        if "{inclinacion}" in text:
            inclinacion = local_random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
            correct_val = 90 - inclinacion
            opts = [
                f"{inclinacion}°",
                f"{90 + inclinacion}°",
                f"{correct_val}°",
                "90°"
            ]
            local_random.shuffle(opts)
            correct_answer = f"{correct_val}°"
            new_text = text.replace("{inclinacion}", str(inclinacion))
            
            explanation_tpl = q.get("explanation", "")
            if "{inclinacion}" in explanation_tpl:
                new_explanation = explanation_tpl.replace("{inclinacion}", str(inclinacion)).replace("{correct}", str(correct_val))
            else:
                new_explanation = f"La línea vertical de referencia es perpendicular al suelo, por lo que forma un ángulo recto de 90°. Como la inclinación de la torre es de {inclinacion}° respecto a la vertical, el ángulo restante para llegar al suelo es 90° - {inclinacion}° = {correct_val}°."
                
            graphic = q.get("graphic")
            if graphic and "base64," in graphic:
                try:
                    header, encoded = graphic.split("base64,", 1)
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    decoded = decoded.replace("{{", "{").replace("}}", "}")
                    decoded = decoded.replace("{inclinacion}", str(inclinacion))
                    decoded = ensure_svg_xmlns(decoded)
                    new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
                except Exception as e:
                    print("Error processing parametric SVG graphic:", e)
                    
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_answer,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        elif "{futbol_solo}" in text or "{baloncesto_solo}" in text:
            futbol_solo = local_random.randint(10, 20)
            ambos = local_random.randint(5, 12)
            baloncesto_solo = local_random.randint(8, 18)
            ninguno = local_random.randint(4, 10)
            total = futbol_solo + ambos + baloncesto_solo + ninguno
            
            num = baloncesto_solo
            den = total
            divisor = gcd(num, den)
            simp_num = num // divisor
            simp_den = den // divisor
            correct_frac = f"{simp_num}/{simp_den}"
            
            d1_num = ambos // gcd(ambos, total)
            d1_den = total // gcd(ambos, total)
            d1 = f"{d1_num}/{d1_den}"
            if d1 == correct_frac: d1 = f"{(ambos+2)//gcd(ambos+2, total)}/{total//gcd(ambos+2, total)}"
            
            b_total = ambos + baloncesto_solo
            d2_num = b_total // gcd(b_total, total)
            d2_den = total // gcd(b_total, total)
            d2 = f"{d2_num}/{d2_den}"
            if d2 == correct_frac: d2 = f"{(b_total-1)//gcd(b_total-1, total)}/{total//gcd(b_total-1, total)}"
            
            b_f_sum = futbol_solo + baloncesto_solo
            d3_num = baloncesto_solo // gcd(baloncesto_solo, b_f_sum)
            d3_den = b_f_sum // gcd(baloncesto_solo, b_f_sum)
            d3 = f"{d3_num}/{d3_den}"
            if d3 == correct_frac: d3 = f"{(baloncesto_solo+1)//gcd(baloncesto_solo+1, b_f_sum)}/{b_f_sum//gcd(baloncesto_solo+1, b_f_sum)}"
            
            opts = [correct_frac, d1, d2, d3]
            unique_opts = []
            for o in opts:
                if o not in unique_opts:
                    unique_opts.append(o)
                    
            while len(unique_opts) < 4:
                random_num = local_random.randint(2, 9)
                random_den = local_random.randint(10, 30)
                g_val = gcd(random_num, random_den)
                opt_str = f"{random_num//g_val}/{random_den//g_val}"
                if opt_str not in unique_opts:
                    unique_opts.append(opt_str)
                    
            local_random.shuffle(unique_opts)
            
            new_text = f"El siguiente diagrama de Venn representa la distribución de un grupo de {total} estudiantes según sus preferencias deportivas entre Fútbol (F) y Baloncesto (B):\n\nSi se selecciona un estudiante al azar dentro del grupo evaluado, ¿cuál es la probabilidad de que este prefiera únicamente Baloncesto?"
            
            new_explanation = f"Para hallar la probabilidad, realizamos el siguiente análisis paso a paso:\n\n1. **Establecer el total del universo:** Sumamos todos los estudiantes distribuidos en el diagrama de Venn:\n$$\\text{{Total}} = {futbol_solo} \\text{{ (F únicamente)}} + {ambos} \\text{{ (Ambos)}} + {baloncesto_solo} \\text{{ (B únicamente)}} + {ninguno} \\text{{ (Ninguno)}} = {total} \\text{{ estudiantes.}}$$\n2. **Identificar los casos favorables:** El problema pide específicamente la probabilidad de que el estudiante prefiera **únicamente** Baloncesto. Esto corresponde a la región exclusiva del círculo B, que equivale a **{baloncesto_solo} estudiantes**.\n3. **Calcular y simplificar la probabilidad:**\n$$P(\\text{{Únicamente Baloncesto}}) = \\frac{{\\text{{Casos Favorables}}}}{{\\text{{Casos Totales}}}} = \\frac{{{baloncesto_solo}}}{{{total}}}$$\nSimplificando la fracción por el MCD ({divisor}) obtenemos la respuesta: **{correct_frac}**."
            
            graphic = q.get("graphic")
            if graphic and "base64," in graphic:
                try:
                    header, encoded = graphic.split("base64,", 1)
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    decoded = decoded.replace("{{", "{").replace("}}", "}")
                    decoded = decoded.replace("{futbol_solo}", str(futbol_solo))
                    decoded = decoded.replace("{ambos}", str(ambos))
                    decoded = decoded.replace("{baloncesto_solo}", str(baloncesto_solo))
                    decoded = decoded.replace("{ninguno}", str(ninguno))
                    decoded = ensure_svg_xmlns(decoded)
                    new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
                except Exception as e:
                    print("Error processing parametric Venn SVG:", e)
                    
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": unique_opts,
                "correct_answer": correct_frac,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        elif "{n_estudiantes}" in text or "{k_seleccionados}" in text:
            comb_options = [
                {"n": 5, "k": 3, "ans": 10, "distractors": [15, 60, 20]},
                {"n": 6, "k": 3, "ans": 20, "distractors": [18, 120, 30]},
                {"n": 7, "k": 3, "ans": 35, "distractors": [21, 210, 42]},
                {"n": 8, "k": 3, "ans": 56, "distractors": [24, 336, 70]},
                {"n": 6, "k": 2, "ans": 15, "distractors": [12, 30, 8]},
                {"n": 7, "k": 2, "ans": 21, "distractors": [14, 42, 18]},
                {"n": 8, "k": 4, "ans": 70, "distractors": [32, 1680, 56]}
            ]
            choice = local_random.choice(comb_options)
            n = choice["n"]
            k = choice["k"]
            correct_val = choice["ans"]
            distractors = choice["distractors"]
            
            opts = [str(correct_val)] + [str(d) for d in distractors]
            local_random.shuffle(opts)
            correct_answer = str(correct_val)
            
            new_text = f"En un colegio se realiza una preselección de estudiantes para participar en las olimpiadas de matemáticas. De un grupo de {n} estudiantes destacados, el entrenador debe elegir a {k} de ellos para conformar el equipo oficial. ¿De cuántas formas diferentes se puede conformar el equipo?"
            
            prod_n_list = [str(n - i) for i in range(k)]
            prod_k_list = [str(k - i) for i in range(k)]
            prod_n_str = " \\times ".join(prod_n_list)
            prod_k_str = " \\times ".join(prod_k_list)
            
            new_explanation = (
                f"Para determinar de cuántas formas se puede conformar el equipo, debemos calcular el número de combinaciones de {n} estudiantes tomados de {k} en {k}, ya que el orden en que se seleccionan los miembros del equipo no importa.\n\n"
                "La fórmula para las combinaciones es:\n\n"
                "$$C_k^n = \\binom{n}{k} = \\frac{n!}{k!(n-k)!}$$\n\n"
                "Reemplazando los valores:\n\n"
                f"$$C_{{{k}}}^{{{n}}} = \\binom{{{n}}}{{{k}}} = \\frac{{{n}!}}{{{k}!({n}-{k})!}} = \\frac{{{prod_n_str}}}{{{prod_k_str}}} = {correct_val}$$\n\n"
                f"Por lo tanto, existen **{correct_val}** formas diferentes de conformar el equipo."
            )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_answer,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": q.get("graphic")
            }
            
        elif "{base}" in text and "{altura}" in text:
            base_val = local_random.choice([4, 6, 8, 10, 12, 14])
            altura_val = local_random.choice([3, 5, 7, 9, 11])
            
            is_triangle = "triángulo" in text.lower()
            if is_triangle:
                correct_val = (base_val * altura_val) / 2
                if correct_val.is_integer():
                    correct_val = int(correct_val)
                correct_str = str(correct_val)
                formula_str = f"\\frac{{base \\times altura}}{{2}} = \\frac{{{base_val} \\times {altura_val}}}{{2}} = {correct_str}"
                distractors = [
                    str(base_val * altura_val),
                    str(base_val + altura_val),
                    str(int((base_val * altura_val) / 2) + 5)
                ]
            else:
                correct_val = base_val * altura_val
                correct_str = str(correct_val)
                formula_str = f"base \\times altura = {base_val} \\times {altura_val} = {correct_str}"
                distractors = [
                    str(int((base_val * altura_val) / 2)),
                    str(base_val + altura_val),
                    str(correct_val + 10)
                ]
                
            opts = [correct_str] + distractors
            opts = list(set(opts))
            while len(opts) < 4:
                opts.append(str(local_random.randint(10, 100)))
            local_random.shuffle(opts)
            
            new_text = text.replace("{base}", str(base_val)).replace("{altura}", str(altura_val))
            
            new_explanation = "El área de la figura geométrica propuesta se calcula utilizando la fórmula estándar del área:\n\n"
            if is_triangle:
                new_explanation += f"$$A = \\frac{{b \\times h}}{{2}}$$\n\nReemplazando la base de {base_val} cm y la altura de {altura_val} cm:\n\n$$A = {formula_str} \\text{{ cm}}^2$$"
            else:
                new_explanation += f"$$A = b \\times h$$\n\nReemplazando la base de {base_val} cm y la altura de {altura_val} cm:\n\n$$A = {formula_str} \\text{{ cm}}^2$$"
                
            graphic = q.get("graphic")
            if graphic and "base64," in graphic:
                try:
                    header, encoded = graphic.split("base64,", 1)
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    decoded = decoded.replace("{{", "{").replace("}}", "}")
                    decoded = decoded.replace("{base}", str(base_val)).replace("{altura}", str(altura_val))
                    decoded = ensure_svg_xmlns(decoded)
                    new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
                except Exception as e:
                    print("Error processing parametric geometry SVG:", e)
                    
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        elif "{x_eval}" in text:
            a = local_random.choice([2, 3, 5])
            b = 2
            c = local_random.choice([-1, 0, 1])
            d = local_random.choice([5, 10, 15, 20])
            x_eval = local_random.choice([1, 2, 3])
            
            exponent = x_eval + c
            correct_val = a * (b ** exponent) + d
            correct_str = str(correct_val)
            
            d1 = (a * b) ** exponent + d
            d2 = a * (b ** x_eval) + c + d
            d3 = correct_val + local_random.choice([10, -5, 25])
            
            opts = [correct_str, str(int(d1)), str(int(d2)), str(int(d3))]
            opts = list(set(opts))
            while len(opts) < 4:
                opts.append(str(local_random.randint(10, 500)))
            local_random.shuffle(opts)
            
            c_sign = "+" if c >= 0 else "-"
            c_abs = abs(c)
            # SAFE REPLACE TO AVOID LATEX CRASH
            new_text = (text
                        .replace("{a}", str(a))
                        .replace("{c_sign}", c_sign)
                        .replace("{c_abs}", str(c_abs))
                        .replace("{d}", str(d))
                        .replace("{x_eval}", str(x_eval)))
            
            new_explanation = (
                f"Para evaluar la función en el punto dado, sustituimos $x = {x_eval}$ en la expresión:\n\n"
                f"$$f({x_eval}) = {a} \\cdot 2^{{{x_eval} {c_sign} {c_abs}}} + {d}$$\n\n"
                "Resolvemos primero la operación en el exponente:\n\n"
                f"$$f({x_eval}) = {a} \\cdot 2^{{{exponent}}} + {d}$$\n\n"
                f"Evaluamos la potencia $2^{{{exponent}}} = {2**exponent}$:\n\n"
                f"$$f({x_eval}) = {a} \\cdot {2**exponent} + {d}$$\n\n"
                f"Multiplicamos por el coeficiente $a = {a}$ y sumamos la constante $d = {d}$:\n\n"
                f"$$f({x_eval}) = {a*2**exponent} + {d} = {correct_val}$$\n\n"
                f"Por lo tanto, la respuesta correcta es **{correct_str}**."
            )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": q.get("graphic")
            }
            
        elif "{frec_1}" in text or "{val_1}" in text:
            val_1, val_2, val_3, val_4 = 10, 20, 30, 40
            frec_1 = local_random.randint(2, 6)
            frec_2 = local_random.randint(3, 8)
            frec_3 = local_random.randint(1, 5)
            frec_4 = local_random.randint(2, 6)
            
            total_n = frec_1 + frec_2 + frec_3 + frec_4
            sum_total = (val_1 * frec_1) + (val_2 * frec_2) + (val_3 * frec_3) + (val_4 * frec_4)
            
            mean_val = round(sum_total / total_n, 2)
            correct_str = f"{mean_val}"
            
            d1 = round((val_1 + val_2 + val_3 + val_4) / 4, 2)
            d2 = round(sum_total / (total_n + 2), 2)
            d3 = round(mean_val + local_random.choice([-1.5, 2.3, -3.2, 1.8]), 2)
            
            opts = [correct_str, f"{d1}", f"{d2}", f"{d3}"]
            opts = list(set(opts))
            while len(opts) < 4:
                opts.append(f"{round(local_random.uniform(15, 35), 2)}")
            local_random.shuffle(opts)
            
            new_text = (
                "La gráfica de barras representa la distribución de puntajes obtenidos por un grupo de estudiantes en un examen de matemáticas.\n\n"
                "Con base en la información suministrada en la gráfica, ¿cuál es el promedio (media aritmética) de los puntajes obtenidos por este grupo de estudiantes?"
            )
            
            new_explanation = (
                "Para hallar la media aritmética (promedio) de datos agrupados en una tabla de frecuencias, utilizamos la fórmula:\n\n"
                "$$\\mu = \\frac{\\sum (x_i \\cdot f_i)}{N}$$\n\n"
                "1. **Calcular la suma de todos los puntajes:**\n"
                f"$$\\sum (x_i \\cdot f_i) = ({val_1} \\cdot {frec_1}) + ({val_2} \\cdot {frec_2}) + ({val_3} \\cdot {frec_3}) + ({val_4} \\cdot {frec_4})$$\n"
                f"$$\\sum (x_i \\cdot f_i) = {val_1*frec_1} + {val_2*frec_2} + {val_3*frec_3} + {val_4*frec_4} = {sum_total}$$\n\n"
                "2. **Calcular el total de estudiantes (N):**\n"
                f"$$N = {frec_1} + {frec_2} + {frec_3} + {frec_4} = {total_n}$$\n\n"
                "3. **Calcular el promedio:**\n"
                f"$$\\mu = \\frac{{{sum_total}}}{{{total_n}}} \\approx {mean_val}$$\n\n"
                f"Por lo tanto, la media aritmética de los puntajes es aproximadamente **{correct_str}**."
            )
            
            graphic = q.get("graphic")
            if graphic and "base64," in graphic:
                try:
                    header, encoded = graphic.split("base64,", 1)
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    decoded = decoded.replace("{{", "{").replace("}}", "}")
                    decoded = (decoded
                               .replace("{frec_1}", str(frec_1))
                               .replace("{frec_2}", str(frec_2))
                               .replace("{frec_3}", str(frec_3))
                               .replace("{frec_4}", str(frec_4)))
                    for i, fr in enumerate([frec_1, frec_2, frec_3, frec_4], 1):
                        h = fr * 20
                        y = 180 - h
                        y_txt = y - 5
                        decoded = (decoded
                                   .replace(f"{{h_bar_{i}}}", str(h))
                                   .replace(f"{{y_bar_{i}}}", str(y))
                                   .replace(f"{{y_txt_{i}}}", str(y_txt)))
                    decoded = ensure_svg_xmlns(decoded)
                    new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
                except Exception as e:
                    print("Error processing parametric statistics SVG:", e)
                    
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        elif "{slope}" in text or "{x2_svg}" in text:
            choices = [
                {"a": 3, "b": 2, "slope_str": "2/3", "distractors": ["3/2", "-2/3", "1/2"]},
                {"a": 4, "b": 3, "slope_str": "3/4", "distractors": ["4/3", "-3/4", "1/3"]},
                {"a": 5, "b": 2, "slope_str": "2/5", "distractors": ["5/2", "-2/5", "1/5"]},
                {"a": 4, "b": 1, "slope_str": "1/4", "distractors": ["4", "-1/4", "1/2"]},
                {"a": 5, "b": 3, "slope_str": "3/5", "distractors": ["5/3", "-3/5", "2/5"]}
            ]
            choice = local_random.choice(choices)
            a = choice["a"]
            b = choice["b"]
            correct_val = choice["slope_str"]
            distractors = choice["distractors"]
            
            opts = [correct_val] + distractors
            local_random.shuffle(opts)
            correct_str = correct_val
            
            x2_svg = 50 + a * 30
            y2_svg = 150 - b * 30
            x2_lbl_svg = x2_svg + 8
            y2_lbl_svg = y2_svg - 8
            
            new_text = (
                "La imagen representa una recta en el plano cartesiano que pasa por el origen $(0,0)$ y por el punto $P$.\n\n"
                "¿Cuál es el valor de la pendiente de esta recta?"
            )
            
            new_explanation = (
                "La pendiente $m$ de una recta que pasa por dos puntos $(x_1, y_1)$ y $(x_2, y_2)$ se calcula mediante la fórmula:\n\n"
                "$$m = \\frac{y_2 - y_1}{x_2 - x_1}$$\n\n"
                f"En este caso, la recta pasa por el origen $(0, 0)$ y por el punto $P({a}, {b})$. "
                f"Sustituyendo las coordenadas correspondientes:\n\n"
                f"$$m = \\frac{{{b} - 0}}{{{a} - 0}} = \\frac{{{b}}}{{{a}}}$$\n\n"
                f"Por lo tanto, la pendiente de la recta es **{correct_str}**."
            )
            
            graphic = q.get("graphic")
            if graphic and "base64," in graphic:
                try:
                    header, encoded = graphic.split("base64,", 1)
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    decoded = decoded.replace("{{", "{").replace("}}", "}")
                    decoded = (decoded
                               .replace("{a}", str(a))
                               .replace("{b}", str(b))
                               .replace("{x2_svg}", str(x2_svg))
                               .replace("{y2_svg}", str(y2_svg))
                               .replace("{x2_lbl_svg}", str(x2_lbl_svg))
                               .replace("{y2_lbl_svg}", str(y2_lbl_svg)))
                    decoded = ensure_svg_xmlns(decoded)
                    new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                    graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
                except Exception as e:
                    print("Error processing parametric coordinate plane SVG:", e)
                    
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        elif "{sector_1}" in text:
            sector_1 = local_random.randint(15, 35)
            sector_2 = local_random.randint(15, 30)
            sector_3 = local_random.randint(10, 25)
            sector_4 = 100 - sector_1 - sector_2 - sector_3
            if sector_4 < 5:
                sector_4 = 10
                sector_3 = 100 - sector_1 - sector_2 - sector_4

            labels = ["Matemáticas", "Español", "Ciencias", "Sociales"]
            values = [sector_1, sector_2, sector_3, sector_4]
            total_students = local_random.choice([80, 100, 120, 150, 200])
            
            ask_idx = local_random.randint(0, 3)
            correct_val = round(values[ask_idx] * total_students / 100)
            correct_str = str(correct_val)
            
            d1 = str(round(values[(ask_idx + 1) % 4] * total_students / 100))
            d2 = str(values[ask_idx])
            d3 = str(correct_val + local_random.choice([5, -3, 8, -7]))
            
            opts = list(set([correct_str, d1, d2, d3]))
            while len(opts) < 4:
                opts.append(str(local_random.randint(10, total_students)))
            local_random.shuffle(opts)
            
            import math
            angles = []
            cumulative = 0
            colors_pie = ["#38bdf8", "#f43f5e", "#10b981", "#fbbf24"]
            svg_paths = ""
            legend_items = ""
            for i, v in enumerate(values):
                start_angle = cumulative * 3.6
                sweep = v * 3.6
                cumulative += v
                
                start_rad = math.radians(start_angle - 90)
                end_rad = math.radians(start_angle + sweep - 90)
                
                cx, cy, r = 120, 120, 95
                x1 = cx + r * math.cos(start_rad)
                y1 = cy + r * math.sin(start_rad)
                x2 = cx + r * math.cos(end_rad)
                y2 = cy + r * math.sin(end_rad)
                
                large_arc = 1 if sweep > 180 else 0
                
                svg_paths += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z" fill="{colors_pie[i]}" stroke="#0f172a" stroke-width="2"/>\n'
                
                mid_rad = math.radians(start_angle + sweep / 2 - 90)
                tx = cx + (r * 0.6) * math.cos(mid_rad)
                ty = cy + (r * 0.6) * math.sin(mid_rad)
                svg_paths += f'<text x="{tx:.1f}" y="{ty:.1f}" fill="white" font-size="12" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{v}%</text>\n'
                
                ly = 15 + i * 22
                legend_items += f'<rect x="260" y="{ly}" width="14" height="14" rx="3" fill="{colors_pie[i]}"/>\n'
                legend_items += f'<text x="280" y="{ly + 12}" fill="#cbd5e1" font-size="11" font-family="Inter, sans-serif">{labels[i]} ({v}%)</text>\n'
            
            pie_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" width="400" height="260">
      <rect width="100%" height="100%" rx="12" fill="#0f172a"/>
      <text x="200" y="252" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Inter, sans-serif">Asignaturas preferidas por los estudiantes</text>
      {svg_paths}
      {legend_items}
    </svg>'''
            
            graphic = "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(pie_svg.encode("utf-8")).decode("utf-8")
            
            new_text = f"La siguiente gráfica circular muestra la distribución porcentual de las asignaturas preferidas por un grupo de {total_students} estudiantes.\n\n¿Cuántos estudiantes prefieren {labels[ask_idx]}?"
            
            new_explanation = (
                f"La gráfica circular muestra que **{labels[ask_idx]}** representa el **{values[ask_idx]}%** del total de estudiantes.\n\n"
                f"Para calcular el número de estudiantes que prefieren esta asignatura, aplicamos la regla de tres:\n\n"
                f"$$\\text{{Estudiantes}} = \\frac{{\\text{{Porcentaje}} \\times \\text{{Total}}}}{{100}} = \\frac{{{values[ask_idx]} \\times {total_students}}}{{100}} = {correct_val}$$\n\n"
                f"Por lo tanto, **{correct_val}** estudiantes prefieren {labels[ask_idx]}."
            )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
        
        elif "{a_cuad}" in text:
            a_c = local_random.choice([1, 2, 3])
            r1 = local_random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5])
            r2 = local_random.choice([-3, -2, -1, 1, 2, 3, 4])
            while r2 == r1:
                r2 = local_random.choice([-3, -2, -1, 1, 2, 3, 4])
            
            b_c = -a_c * (r1 + r2)
            c_c = a_c * r1 * r2
            
            sum_roots = r1 + r2
            correct_str = str(sum_roots)
            
            d1 = str(r1 * r2)
            d2 = str(sum_roots + local_random.choice([1, -1, 2]))
            d3 = str(-sum_roots)
            
            opts = list(set([correct_str, d1, d2, d3]))
            while len(opts) < 4:
                opts.append(str(local_random.randint(-10, 10)))
            local_random.shuffle(opts)
            
            b_sign = "+" if b_c >= 0 else "-"
            c_sign = "+" if c_c >= 0 else "-"
            a_str = "" if a_c == 1 else str(a_c)
            
            new_text = f"Dada la ecuación cuadrática:\n\n$${a_str}x^2 {b_sign} {abs(b_c)}x {c_sign} {abs(c_c)} = 0$$\n\n¿Cuál es la suma de las raíces de esta ecuación?"
            
            new_explanation = (
                f"Para una ecuación cuadrática de la forma $ax^2 + bx + c = 0$, la suma de las raíces está dada por la relación de Vieta:\n\n"
                f"$$x_1 + x_2 = -\\frac{{b}}{{a}}$$\n\n"
                f"En nuestra ecuación, $a = {a_c}$ y $b = {b_c}$. Sustituyendo:\n\n"
                f"$$x_1 + x_2 = -\\frac{{{b_c}}}{{{a_c}}} = {sum_roots}$$\n\n"
                f"Verificación: Las raíces son $x_1 = {r1}$ y $x_2 = {r2}$.\n\n"
                f"$$x_1 + x_2 = {r1} + {'' if r2 < 0 else ''}{r2} = {sum_roots}$$\n\n"
                f"Por lo tanto, la suma de las raíces es **{sum_roots}**."
            )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": q.get("graphic")
            }
        
        elif "{num_1}" in text:
            num_1 = local_random.randint(1, 7)
            den_1 = local_random.choice([2, 3, 4, 5, 6, 8])
            num_2 = local_random.randint(1, 7)
            den_2 = local_random.choice([2, 3, 4, 5, 6, 8])
            while den_2 == den_1:
                den_2 = local_random.choice([2, 3, 4, 5, 6, 8])
            
            op = local_random.choice(["suma", "resta"])
            
            result_num = num_1 * den_2 + num_2 * den_1 if op == "suma" else num_1 * den_2 - num_2 * den_1
            result_den = den_1 * den_2
            
            g = gcd(abs(result_num), result_den)
            simp_num = result_num // g
            simp_den = result_den // g
            
            if simp_den < 0:
                simp_num = -simp_num
                simp_den = -simp_den
            
            correct_str = f"{simp_num}/{simp_den}"
            
            d1_n = simp_num + local_random.choice([1, -1, 2])
            d1 = f"{d1_n}/{simp_den}"
            d2 = f"{num_1 + num_2}/{den_1 + den_2}"
            d3_n = simp_num * 2
            d3_d = simp_den
            d3_g = gcd(abs(d3_n), abs(d3_d))
            d3 = f"{d3_n // d3_g}/{d3_d // d3_g}"
            
            opts = list(set([correct_str, d1, d2, d3]))
            while len(opts) < 4:
                rn = local_random.randint(1, 15)
                rd = local_random.randint(2, 12)
                rg = gcd(rn, rd)
                opts.append(f"{rn // rg}/{rd // rg}")
                opts = list(set(opts))
            local_random.shuffle(opts)
            
            op_symbol = "+" if op == "suma" else "-"
            op_word = "la suma" if op == "suma" else "la resta"
            
            new_text = f"Calcule {op_word} de las siguientes fracciones:\n\n$$\\frac{{{num_1}}}{{{den_1}}} {op_symbol} \\frac{{{num_2}}}{{{den_2}}}$$"
            
            cross_1 = num_1 * den_2
            cross_2 = num_2 * den_1
            
            new_explanation = (
                f"Para {op_word} de fracciones con diferente denominador, primero hallamos el denominador común:\n\n"
                f"$$\\frac{{{num_1}}}{{{den_1}}} {op_symbol} \\frac{{{num_2}}}{{{den_2}}} = \\frac{{{num_1} \\times {den_2}}}{{{den_1} \\times {den_2}}} {op_symbol} \\frac{{{num_2} \\times {den_1}}}{{{den_2} \\times {den_1}}}$$\n\n"
                f"$$= \\frac{{{cross_1}}}{{{result_den}}} {op_symbol} \\frac{{{cross_2}}}{{{result_den}}} = \\frac{{{cross_1} {op_symbol} {cross_2}}}{{{result_den}}} = \\frac{{{result_num}}}{{{result_den}}}$$\n\n"
                f"Simplificando por el MCD ({g}):\n\n"
                f"$$= \\frac{{{simp_num}}}{{{simp_den}}}$$\n\n"
                f"La respuesta correcta es **{correct_str}**."
            )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": q.get("graphic")
            }
        
        elif "{dato_1}" in text:
            n_data = local_random.choice([7, 9, 11])
            data_set = sorted([local_random.randint(2, 30) for _ in range(n_data)])
            
            ask_type = local_random.choice(["mediana", "moda"])
            
            if ask_type == "moda":
                mode_val = local_random.choice(data_set)
                extra_copies = local_random.randint(1, 2)
                for _ in range(extra_copies):
                    data_set.append(mode_val)
                data_set.sort()
                
                from collections import Counter
                freq = Counter(data_set)
                mode_val = freq.most_common(1)[0][0]
                correct_str = str(mode_val)
            else:
                mid = len(data_set) // 2
                median_val = data_set[mid]
                correct_str = str(median_val)
            
            d1 = str(data_set[0])
            d2 = str(data_set[-1])
            d3 = str(round(sum(data_set) / len(data_set), 1))
            
            opts = list(set([correct_str, d1, d2, d3]))
            while len(opts) < 4:
                opts.append(str(local_random.choice(data_set) + local_random.choice([1, -1, 2])))
                opts = list(set(opts))
            local_random.shuffle(opts)
            
            data_str = ", ".join(str(d) for d in data_set)
            
            cols = len(data_set)
            cell_w = max(35, 320 // cols)
            table_w = cell_w * cols + 20
            svg_table = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {table_w} 90" width="{table_w}" height="90">
      <rect width="100%" height="100%" rx="10" fill="#0f172a"/>
      <text x="{table_w // 2}" y="18" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="Inter, sans-serif">Conjunto de datos ordenados</text>'''
            
            for i, d in enumerate(data_set):
                x = 10 + i * cell_w
                svg_table += f'\n  <rect x="{x}" y="28" width="{cell_w - 2}" height="24" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1"/>'
                svg_table += f'\n  <text x="{x + cell_w // 2}" y="45" fill="#38bdf8" font-size="13" font-weight="bold" text-anchor="middle" font-family="Inter, sans-serif">{d}</text>'
                svg_table += f'\n  <text x="{x + cell_w // 2}" y="74" fill="#64748b" font-size="9" text-anchor="middle" font-family="Inter, sans-serif">x{chr(8321 + i) if i < 9 else "₊"}</text>'
            
            svg_table += '\n</svg>'
            
            graphic = "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(svg_table.encode("utf-8")).decode("utf-8")
            
            if ask_type == "mediana":
                new_text = f"El siguiente conjunto de datos ordenados representa las calificaciones obtenidas por un grupo de {len(data_set)} estudiantes en un examen.\n\n¿Cuál es la **mediana** de este conjunto de datos?"
                mid = len(data_set) // 2
                new_explanation = (
                    f"La **mediana** es el valor central de un conjunto de datos ordenados.\n\n"
                    f"El conjunto tiene **{len(data_set)}** datos (impar), por lo tanto la mediana es el dato en la posición:\n\n"
                    f"$$\\text{{Posición}} = \\frac{{n+1}}{{2}} = \\frac{{{len(data_set)}+1}}{{2}} = {(len(data_set) + 1) // 2}$$\n\n"
                    f"Los datos ordenados son: ${data_str}$\n\n"
                    f"El valor en la posición {(len(data_set) + 1) // 2} es **{data_set[mid]}**.\n\n"
                    f"Por lo tanto, la mediana es **{correct_str}**."
                )
            else:
                from collections import Counter
                freq = Counter(data_set)
                mode_val = freq.most_common(1)[0][0]
                mode_count = freq[mode_val]
                new_text = f"El siguiente conjunto de datos representa las calificaciones obtenidas por un grupo de {len(data_set)} estudiantes.\n\n¿Cuál es la **moda** de este conjunto de datos?"
                new_explanation = (
                    f"La **moda** es el dato que más se repite en un conjunto de datos.\n\n"
                    f"Los datos son: ${data_str}$\n\n"
                    f"Analizando las frecuencias, el valor **{mode_val}** aparece **{mode_count} veces**, siendo el dato con mayor frecuencia.\n\n"
                    f"Por lo tanto, la moda es **{correct_str}**."
                )
            
            return {
                "id": q["id"],
                "area": q["area"],
                "text": new_text,
                "options": opts,
                "correct_answer": correct_str,
                "explanation": new_explanation,
                "difficulty": q["difficulty"],
                "graphic": graphic
            }
            
        return q
