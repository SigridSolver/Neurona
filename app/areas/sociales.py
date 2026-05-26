from app.areas.base_area import BaseArea

class SocialesArea(BaseArea):
    @property
    def area_name(self) -> str:
        return "Sociales y Ciudadanas"

    def get_generation_prompt(self, needed: int) -> str:
        return f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Sociales y Ciudadanas.
    Genera una lista de {needed} preguntas de selección múltiple originales y diferentes entre sí en contexto, estructura y solución, inéditas y de alta calidad.

    ESTILO ICFES OBLIGATORIO:
    - Las preguntas deben evaluar competencias y razonamiento social y ciudadano, no la memorización de fechas, nombres o datos históricos aislados.
    - Deben presentar información suficiente en el enunciado/contexto para ser resueltas de forma autónoma.
    - Deben usar distractores plausibles y representativos de errores comunes de análisis de perspectivas, sesgos o inferencia.
    - Deben evitar pistas obvias o distractores triviales.
    - Deben asemejarse estrictamente al tono formal, riguroso y analítico de la prueba Saber 11 oficial en Colombia.

    REGLA DE PREGUNTAS CON IMÁGENES / SOPORTE VISUAL:
    - Si la pregunta o el texto de lectura hace referencia directa o indirecta a un elemento visual, soporte gráfico o imagen (por ejemplo, un mapa, una caricatura política, afiches históricos o un gráfico socioeconómico):
      **ES OBLIGATORIO Y MANDATORIO generar un código SVG completo** en el campo `graphic` que represente visualmente dicho elemento. NO devuelvas null en `graphic` si la pregunta menciona una imagen, caricatura o gráfico.
      * El SVG debe ser estético, nítido y de alta calidad, con fondo oscuro (fill="#0f172a") y bordes redondeados (rx="12").
      * Dibuja los elementos del mapa o caricatura de forma creativa usando elementos nativos de SVG (`<rect>`, `<circle>`, `<path>`, `<line>`, `<polygon>`) (por ejemplo, siluetas de países, bocadillos de diálogo, nubes de ruido digital, muros, etc.).
      * REGLA CRÍTICA: Escribe los textos, nombres de lugares, diálogos de la caricatura o etiquetas del gráfico de forma muy clara usando etiquetas `<text>` con suficiente contraste y coordenadas adecuadas para que sean perfectamente legibles (ej. usando fill="white", fill="#38bdf8", fill="#fbbf24" sobre el fondo oscuro).
    - Si la pregunta es 100% textual (no menciona imágenes, ni caricaturas, ni gráficos, ni mapas) y no requiere ningún apoyo visual, pon `graphic`: null.

    REGLAS ESPECÍFICAS DE SOCIALES Y CIUDADANAS:
    - Distribuye equilibradamente las competencias ICFES entre las preguntas generadas:
      * Competencia 1: Pensamiento social (conceptos básicos, constitucionales e históricos de Colombia y el mundo).
      * Competencia 2: Interpretación y análisis de perspectivas (diferenciar opiniones de hechos, multiperspectivismo en dilemas o conflictos).
      * Competencia 3: Pensamiento sistémico y reflexión ciudadana (analizar causas y efectos, mecanismos constitucionales, y deberes/derechos).
    - Incluye análisis de fuentes cuando sea pertinente: extractos de discursos, citas de autores, fragmentos de noticias, mapas, caricaturas políticas o gráficos socioeconómicos.
    - Evita preguntas puramente de memoria factual aislada.

    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Sociales y Ciudadanas"
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
