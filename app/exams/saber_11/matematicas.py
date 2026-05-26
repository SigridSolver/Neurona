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
    - Deben presentar información suficiente para ser resueltas de forma autónoma.
    - Cada pregunta debe evaluar UNA competencia matemática específica del ICFES:
      * Interpretación y representación
      * Formulación y ejecución
      * Argumentación
    - Todas las preguntas deben estar contextualizadas en situaciones cotidianas o aplicadas (ej. economía familiar, transporte, deportes, ventas, fenómenos sociales, consumo, experimentos, producción, ambiente, datos reales, etc.). Evita ejercicios abstractos sin contexto.
    - Varía el nivel cognitivo entre comprensión, aplicación e inferencia matemática, manteniendo una dificultad intermedia.
    - Debe existir una única respuesta correcta, inequívoca y verificable.
    - Los distractores (opciones incorrectas) deben ser plausibles y representar errores frecuentes de razonamiento o cálculo que cometen los estudiantes. Evita opciones absurdas.
    - Evita preguntas de cálculo mecánico o rutinario sin interpretación o análisis de datos.

    REGLA CRÍTICA DE EVITAR SPOILERS EN GRÁFICOS:
    - **PROHIBIDO revelar la respuesta correcta directamente en el SVG**. 
      * En planos cartesianos/funciones: Si la pregunta pide hallar el valor de 'x' cuando 'y = 15000', NO dibujes un punto marcado con el texto exacto "P(5, 15000)" sobre la recta. En su lugar, rotula puntos de referencia alternativos (como el intercepto en Y "(0, 5000)" o un punto lejano de ejemplo) y dibuja marcas de escala en los ejes para que el estudiante deba deducir e interpretar la ecuación por sí mismo.
      * En diagramas de Venn: Si la pregunta pide calcular la cantidad en una región específica (como "cuántos miembros practican ambos deportes"), la intersección de los círculos en el SVG NO debe mostrar el número final resuelto (ej. "20"). En su lugar, coloca una incógnita como `"?"` o `"x"`. Esto obliga al estudiante a deducir el valor mediante la información del enunciado. El diagrama debe ilustrar la incógnita del problema por resolver, no la solución.

    REGLA CRÍTICA DE DISEÑO SVG Y LEGIBILIDAD (EVITAR TRASLAPES Y TEXTOS CORTADOS):
    - **Fondo y Dimensiones:** Usa siempre un contenedor SVG con viewBox adecuado (ej: `viewBox="0 0 400 250"`) con fondo oscuro (#0f172a) y bordes redondeados (rx="12").
    - **Márgenes de seguridad:** Asegúrate de que todos los elementos gráficos y textos tengan al menos 20px de espacio con respecto a los bordes del SVG para evitar que las etiquetas o números se recorten en la pantalla.
    - **Ejes y Escalas:** En todos los gráficos de barras, histogramas, diagramas de dispersión y planos cartesianos, es OBLIGATORIO dibujar ambos ejes (X e Y) con líneas visibles (stroke="#64748b" o similar). Coloca marcas numéricas indicadoras de escala a lo largo de los ejes y etiquetas de texto legibles indicando qué variable representa cada eje.
    - **Separación de Textos (Evitar Traslapes):** No encimes etiquetas de texto sobre los puntos o las líneas. Usa atributos como `dx` y `dy` en las etiquetas `<text>` para desplazar los textos ligeramente (ej: `dx="10" dy="-10"`) con respecto a los puntos coordenados, líneas o barras correspondientes.
    - **Cuadrículas:** En gráficos cartesianos, dibuja siempre una cuadrícula tenue de fondo (líneas discontinuas delgadas con `stroke="#334155"` y `stroke-dasharray="3,3"`) para facilitar la lectura visual de coordenadas por parte del estudiante.
    - **Contraste de textos:** Todos los textos del SVG deben estar escritos en etiquetas `<text>` con colores contrastantes y visibles sobre fondo oscuro (ej: `fill="#ffffff"`, `fill="#38bdf8"`, `fill="#fbbf24"`, `fill="#10b981"`). Usa fuentes modernas y legibles (`font-family="sans-serif"` o `font-family="Inter, sans-serif"`).

    CATEGORÍAS DE PREGUNTAS Y REGLAS DE GRÁFICOS COMPONENTES:
    Selecciona de manera variada entre las siguientes categorías para las {needed} preguntas:

    CATEGORÍA 1 - GRÁFICA CIRCULAR (TORTA):
    - Contexto: distribución de presupuestos, preferencias, ventas.
    - SVG obligatorio: Círculo dividido en sectores con colores vivos (#38bdf8, #f43f5e, #10b981, #fbbf24). Las etiquetas con los nombres de categorías y porcentajes deben colocarse en una leyenda lateral bien organizada a la derecha (ej. a partir de X=260) o bien espaciadas para evitar que el texto se traslape.

    CATEGORÍA 2 - GRÁFICA DE BARRAS / HISTOGRAMA:
    - Contexto: análisis de frecuencias o estadísticas (ej. porciones de fruta consumidas, libros leídos, calificaciones, producción diaria).
    - SVG obligatorio: Barras verticales de colores. El eje X debe incluir etiquetas de categorías claras y visibles debajo de cada barra (ej: números "1", "2", "3", "4", "5" o marcas equivalentes). El eje Y debe indicar la frecuencia con marcas de escala. La frecuencia numérica de cada barra debe estar escrita en blanco justo encima de cada barra para mayor legibilidad. Asegura suficiente espacio vertical arriba de las barras para que las frecuencias no se corten. **ADVERTENCIA: Sin las etiquetas numéricas/categorías del eje X, la pregunta es imposible de responder; asegúrate de dibujarlas siempre.**

    CATEGORÍA 3 - DIAGRAMA DE VENN:
    - Contexto: problemas de conjuntos y probabilidad.
    - SVG obligatorio: Dibuja un rectángulo de fondo que represente el conjunto universal `U` con su etiqueta de texto en una esquina (ej: "U = 100"). Dibuja dos o tres círculos semitransparentes superpuestos, rotula claramente el nombre de cada conjunto arriba de su respectivo círculo (ej. "Fútbol (F)" y "Natación (N)"). Coloca números legibles dentro de cada sección externa. Si la pregunta busca calcular un dato específico (como la intersección), escribe `"?"` o `"x"` en la sección correspondiente en vez del número resuelto. Coloca visiblemente el número de elementos fuera de los círculos (el complemento) en una esquina interna del rectángulo universal.

    CATEGORÍA 4 - PLANO CARTESIANO / FUNCIONES:
    - Contexto: modelación lineal, costos de envíos, trayectorias.
    - SVG obligatorio: Ejes X y Y perpendiculares con marcas numéricas graduadas y nombres de variables. Dibuja la recta o curva y rotula algunos puntos de apoyo útiles (ej. el intercepto y otro punto de referencia intermedio que obligue al análisis) con sus respectivas coordenadas bien legibles. El punto correspondiente a la respuesta correcta NO debe estar rotulado con su valor numérico en el gráfico.

    CATEGORÍA 5 - GEOMETRÍA (2D Y 3D):
    - Contexto: áreas, perímetros y volúmenes de recipientes u objetos reales (tanques cilíndricos, cajas, terrenos triangulares/rectangulares).
    - SVG obligatorio: Dibuja la figura geométrica en 2D o una proyección en perspectiva 3D estilizada (ej. un cilindro de agua para problemas de volumen). Incluye líneas de cota claras (líneas punteadas con flechas) indicando el radio, diámetro, base o altura y escribe sus medidas numéricas directamente en el gráfico (ej. "r = 2 m", "h = 5 m").

    CATEGORÍA 6 - ECUACIÓN CUADRÁTICA / PARÁBOLA:
    - Contexto: física del movimiento (lanzamientos de objetos) o costos/ingresos parabólicos.
    - SVG obligatorio: Gráfico de la parábola en el plano cartesiano mostrando el vértice y los interceptos con los ejes X/Y para apoyar el análisis de las raíces.

    CATEGORÍA 7 - FRACCIONES / OPERACIONES:
    - Contexto: problemas de partición de recursos, terrenos o presupuestos.
    - SVG obligatorio: Una representación visual de las fracciones involucradas (ej. un rectángulo fraccionado con sectores coloreados, o un diagrama de torta simplificado de partición).

    CATEGORÍA 8 - TABLAS DE DATOS / ESTADÍSTICA:
    - Contexto: promedios, medianas, modas de rendimiento deportivo o encuestas.
    - SVG obligatorio: Una tabla rectangular estilizada con celdas de colores contrastantes y bordes claros, que muestre los datos de forma estructurada para evitar listados de texto simples.

    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Matemáticas"
       - "text": "[El enunciado completo de la pregunta con el contexto y los datos explícitos de la situación]"
       - "options": ["Opción A", "Opción B", "Opción C", "Opción D"]
       - "correct_answer": "[Debe ser exactamente idéntica a una de las opciones]"
       - "explanation": "[justificación pedagógica detallada paso a paso, escrita de forma clara con LaTeX $$fórmulas$$]"
       - "difficulty": "Intermedio"
       - "graphic": "[Código SVG completo conforme a todas las reglas de diseño y legibilidad mencionadas, o null si la categoría de verdad no requiere apoyo visual]"
    """
