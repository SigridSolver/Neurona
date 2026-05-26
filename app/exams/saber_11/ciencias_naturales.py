from app.exams.base_area import BaseArea

class CienciasNaturalesArea(BaseArea):
    @property
    def area_name(self) -> str:
        return "Ciencias Naturales"

    def get_generation_prompt(self, needed: int) -> str:
        return f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Ciencias Naturales (Física, Química, Biología y Ciencia, Tecnología y Sociedad).
    Genera una lista de {needed} preguntas de selección múltiple originales y diferentes entre sí en contexto, estructura y solución, inéditas y de alta calidad.

    ESTILO ICFES OBLIGATORIO:
    - Las preguntas deben evaluar competencias y razonamiento científico, no la memorización de fórmulas, nomenclatura o datos abstractos.
    - Deben presentar información suficiente en el enunciado/contexto para ser resueltas de forma autónoma.
    - Deben usar distractores plausibles y representativos de errores comunes de análisis, cálculo o inferencia.
    - Deben evitar pistas obvias o distractores triviales.
    - Deben asemejarse estrictamente al tono formal, riguroso y analítico de la prueba Saber 11 oficial en Colombia.

    REGLA DE PREGUNTAS CON IMÁGENES / SOPORTE VISUAL:
    - Si la pregunta o el texto de lectura hace referencia directa o indirecta a un elemento visual, soporte gráfico o imagen (por ejemplo, un diagrama de laboratorio, circuito eléctrico, célula, ciclo ecológico, tabla de resultados, gráfica de dispersión, etc.):
      **ES OBLIGATORIO Y MANDATORIO generar un código SVG completo** en el campo `graphic` que represente visualmente dicho elemento. NO devuelvas null en `graphic` si la pregunta menciona una imagen, gráfica o diagrama.
      * El SVG debe ser estético, nítido y de alta calidad, con fondo oscuro (fill="#0f172a") y bordes redondeados (rx="12").
      * Dibuja los elementos del diagrama de forma creativa usando elementos nativos de SVG (`<rect>`, `<circle>`, `<path>`, `<line>`, `<polygon>`) (por ejemplo, tubos de ensayo, células, resistencias, nubes, flechas de ciclo, etc.).
      * REGLA CRÍTICA: Escribe los textos, nombres de ejes, diálogos o etiquetas del diagrama de forma muy clara usando etiquetas `<text>` con suficiente contraste y coordenadas adecuadas para que sean perfectamente legibles (ej. usando fill="white", fill="#38bdf8", fill="#fbbf24" sobre el fondo oscuro).
    - Si la pregunta es 100% textual (no menciona imágenes, ni gráficas, ni diagramas) y no requiere ningún apoyo visual, pon `graphic`: null.

    REGLAS ESPECÍFICAS DE CIENCIAS NATURALES:
    - Distribuye equilibradamente las competencias ICFES entre las preguntas generadas:
      * Competencia 1: Uso comprensivo del conocimiento científico.
      * Competencia 2: Explicación de fenómenos.
      * Competencia 3: Indagación e interpretación de evidencia.
    - Incluye tablas de datos, resultados experimentales descritos, gráficos, diagramas de flujo de procesos o escenarios de investigación/laboratorio cuando sea pertinente.
    - Evita preguntas puramente de memoria factual aislada.

    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Ciencias Naturales"
       - "text": "[El texto/contexto de base y el enunciado de la pregunta, integrados limpiamente]"
       - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
       - "correct_answer": "[Debe ser idéntica a una de las opciones]"
       - "explanation": "[justificación pedagógica y concisa de la opción correcta y descarte de las incorrectas]"
       - "difficulty": "Intermedio"
       - "graphic": "[Código SVG completo o null]"
    
    - REGLA CRÍTICA DE FORMATO:
    * Devuelve EXCLUSIVAMENTE una lista JSON válida.
    * No agregues texto antes ni después del JSON.
    * No uses bloques markdown.
    * Todas las comillas deben ser dobles.
    * El JSON debe ser parseable por json.loads().
    """
