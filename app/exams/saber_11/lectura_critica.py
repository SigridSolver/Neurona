from app.exams.base_area import BaseArea

class LecturaCriticaArea(BaseArea):
    @property
    def area_name(self) -> str:
        return "Lectura Crítica"

    def get_generation_prompt(self, needed: int) -> str:
        return f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Lectura Crítica.
    Genera una lista de {needed} preguntas de selección múltiple originales y diferentes entre sí en contexto, estructura y solución, inéditas y de alta calidad.

    ESTILO ICFES OBLIGATORIO:
    - Las preguntas deben evaluar competencias y razonamiento crítico, no la memorización de datos o conceptos.
    - Deben presentar información suficiente en el enunciado/contexto para ser resueltas de forma autónoma.
    - Deben usar distractores plausibles y representativos de errores comunes de análisis o inferencia.
    - Deben evitar pistas obvias o distractores triviales.
    - Deben asemejarse estrictamente al tono formal, riguroso y analítico de la prueba Saber 11 oficial en Colombia.

    REGLA DE PREGUNTAS CON IMÁGENES / SOPORTE VISUAL:
    - Si la pregunta o el texto de lectura hace referencia directa o indirecta a un elemento visual, soporte gráfico o imagen (por ejemplo, una caricatura, afiche, cómic, publicidad o infografía):
      **ES OBLIGATORIO Y MANDATORIO generar un código SVG completo** en el campo `graphic` que represente visualmente dicho elemento. NO devuelvas null en `graphic` si la pregunta menciona una imagen, caricatura o gráfico.
      * El SVG debe ser estético, nítido y de alta calidad, con fondo oscuro (fill="#0f172a") y bordes redondeados (rx="12").
      * Dibuja los elementos de la caricatura o diagrama de forma creativa usando elementos nativos de SVG (`<rect>`, `<circle>`, `<path>`, `<line>`, `<polygon>`) (por ejemplo, dibuja siluetas de personas, bocadillos de diálogo, nubes, pantallas, libros, etc.).
      * REGLA CRÍTICA: Escribe los textos, diálogos de la caricatura o etiquetas de los diagramas de forma muy clara usando etiquetas `<text>` con suficiente contraste y coordenadas adecuadas para que sean perfectamente legibles (ej. usando fill="white", fill="#38bdf8", fill="#fbbf24" sobre el fondo oscuro).
    - Si la pregunta es 100% textual (no menciona caricaturas, ni imágenes, ni gráficos) y no requiere ningún apoyo visual, pon `graphic`: null.

    REGLAS ESPECÍFICAS DE LECTURA CRÍTICA:
    - Distribuye equilibradamente las competencias ICFES entre las preguntas generadas:
      * Competencia 1: Identificar y entender los contenidos locales que conforman un texto.
      * Competencia 2: Comprender cómo se articulan las partes de un texto para darle un sentido global.
      * Competencia 3: Reflexionar a partir de un texto y evaluar su contenido y su forma.
    - Usa variedad de tipologías textuales: literario (cuento, novela, poesía), argumentativo (ensayo, editorial, columna), divulgativo o científico, periodístico, filosófico, o discontinuo (caricatura, afiche, tabla, infografía).
    - Varía la longitud y complejidad del texto propuesto (desde fragmentos cortos a medianos/largos).
    - Evita preguntas puramente definicionales o de memoria.

    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Lectura Crítica"
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
