from app.exams.base_area import BaseArea

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
    - NO utilices llaves, corchetes, ni variables de reemplazo de ningún tipo (como texto entre llaves o marcadores de plantilla). Escribe todos los números, nombres, cotas y valores finales de forma directa y explícitamente en el texto del enunciado (por ejemplo: escribe "base de 8 cm" directamente en lugar de usar variables).
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
