from app.exams.base_area import BaseArea

class InglesArea(BaseArea):
    @property
    def area_name(self) -> str:
        return "Inglés"

    def get_generation_prompt(self, needed: int) -> str:
        return f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Inglés.
    Genera una lista de {needed} preguntas de selección múltiple originales y diferentes entre sí en contexto, estructura y solución, inéditas y de alta calidad.

    ESTILO ICFES OBLIGATORIO:
    - Las preguntas deben evaluar la competencia lingüística y comunicativa según el Marco Común Europeo (MCER) desde nivel A1 hasta B1.
    - Deben presentar información suficiente en el enunciado/contexto para ser resueltas de forma autónoma.
    - Deben usar distractores plausibles y representativos de errores gramaticales o de vocabulario comunes en los estudiantes.
    - Deben evitar pistas obvias o distractores triviales.
    - Deben asemejarse estrictamente al tono formal, riguroso y pedagógico de la prueba Saber 11 oficial en Colombia.

    REGLAS ESPECÍFICAS DE INGLÉS:
    - Varía la tipología de preguntas entre:
      * Parte 1/2: Notices, advertisements or short messages (avisos cotidianos en inglés).
      * Parte 3/4: Vocabulary in context / Functional language (completar diálogos o seleccionar palabras adecuadas).
      * Parte 5/6: Reading comprehension (textos medianos y preguntas de comprensión factual e inferencial).
      * Parte 7: Grammar in context (completar textos con estructuras verbales adecuadas, nivel A2/B1).
    - REGLA CRÍTICA: El texto (enunciado) y las opciones de respuesta DEBEN estar completamente en inglés. La explicación ("explanation") puede estar en español para facilitar la retroalimentación pedagógica.
    - Inspírate en las tipologías de Saber 11 Inglés, sin necesidad de seguir el orden exacto del examen oficial.

    REGLA DE IMÁGENES / SOPORTE VISUAL:
    - Si la pregunta hace referencia a un aviso publicitario (Notice) o anuncio gráfico, puedes dibujar dicho aviso en un código SVG estético en el campo `graphic`.
      * El SVG debe tener fondo oscuro (fill="#0f172a") y bordes redondeados.
      * Escribe el aviso de forma muy clara usando etiquetas `<text>` con fill="white" u otros colores visibles.
    - Si la pregunta es puramente textual y no requiere apoyo visual, pon `graphic`: null.

    El formato de salida DEBE ser estrictamente una lista JSON, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
       - "area": "Inglés"
       - "text": "[El texto/aviso/diálogo de base en inglés y la pregunta correspondiente]"
       - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
       - "correct_answer": "[Debe ser idéntica a una de las opciones en inglés]"
       - "explanation": "[Justificación detallada de por qué es la clave correcta en español]"
       - "difficulty": "Intermedio"
       - "graphic": "[Código SVG completo o null]"
    
    - REGLA CRÍTICA DE FORMATO:
    * Devuelve EXCLUSIVAMENTE una lista JSON válida.
    * No agregues texto antes ni después del JSON.
    * No uses bloques markdown.
    * Todas las comillas deben ser dobles.
    * El JSON debe ser parseable por json.loads().
    """
