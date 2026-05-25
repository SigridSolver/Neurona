import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection
import os

import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Load environment
load_dotenv()

DB_PATH = Path(__file__).parent.parent / "saber11.db"


# Prototipo de preguntas pre-diseñadas por IA como base si no hay API Key disponible
AI_MOCK_GENERATED_QUESTIONS = [
    {
        "area": "Ciencias Naturales",
        "text": "Un grupo de investigación estudia la degradación de un polímero usando hongos del género Pestalotiopsis. Si observan que en ausencia de oxígeno el polímero se degrada un 80% más lento, ¿cuál es la conclusión correcta sobre el metabolismo del hongo?",
        "options": [
            "El hongo realiza respiración principalmente aerobia para degradar el polímero de forma eficiente.",
            "El hongo es anaerobio estricto y el oxígeno actúa como un inhibidor de sus enzimas.",
            "La degradación del polímero no depende de la temperatura ni de la concentración de oxígeno.",
            "El hongo degrada el polímero mediante procesos fermentativos anaerobios únicamente."
        ],
        "correct_answer": "El hongo realiza respiración principalmente aerobia para degradar el polímero de forma eficiente.",
        "explanation": "El oxígeno actúa como aceptor final de electrones en la respiración aerobia, permitiendo una mayor producción de energía (ATP). Si la degradación disminuye significativamente en ausencia de oxígeno, significa que el metabolismo del hongo es principalmente aerobio o se ve altamente favorecido por la presencia de oxígeno.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Sociales y Ciudadanas",
        "text": "En una región del país, un proyecto de minería a gran escala es aprobado por el Gobierno Nacional sin consultar a la comunidad indígena local que habita el territorio. Según la Constitución de 1991, ¿qué mecanismo constitucional protege directamente el derecho de esta comunidad?",
        "options": [
            "La Consulta Previa y la Acción de Tutela",
            "El Referendo Derogatorio de la licencia ambiental",
            "La Acción Popular para la protección del suelo",
            "La Consulta Popular convocada por el alcalde municipal"
        ],
        "correct_answer": "La Consulta Previa y la Acción de Tutela",
        "explanation": "La Consulta Previa es un derecho fundamental de los grupos étnicos para decidir sobre proyectos que afecten sus territorios. Al no realizarse, se vulnera el debido proceso y la diversidad étnica, lo cual hace procedente la Acción de Tutela para suspender el proyecto y exigir la consulta.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Lectura Crítica",
        "text": "Considere la siguiente afirmación: 'Si bien la ciencia nos proporciona herramientas poderosas para manipular el entorno físico, carece por completo de la capacidad para resolver dilemas morales o definir qué es lo moralmente correcto'. La intención principal del autor al formular esta frase es:",
        "options": [
            "Delimitar el alcance epistemológico de la ciencia frente a la ética.",
            "Desacreditar los avances científicos recientes.",
            "Demostrar que la ética debe subordinarse al método científico.",
            "Promover la investigación ética en laboratorios científicos."
        ],
        "correct_answer": "Delimitar el alcance epistemológico de la ciencia frente a la ética.",
        "explanation": "Al señalar que la ciencia aporta herramientas materiales pero carece de facultad para decidir sobre dilemas morales, el autor establece una frontera o límite entre el conocimiento científico (hechos) y el juicio de valor ético (moral).",
        "difficulty": "Intermedio"
    }
]

def generate_questions_with_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n[INFO IA] No se detectó 'GEMINI_API_KEY' en el archivo .env o variables del sistema.")
        print("[INFO IA] Habilitando prototipo simulador de IA para cargar las preguntas inteligentes de muestra...")
        questions = AI_MOCK_GENERATED_QUESTIONS
    else:
        print("\n[INFO IA] GEMINI_API_KEY detectada. Iniciando Generación de Preguntas Inteligentes con Gemini...")
        genai.configure(api_key=api_key)
        
        conn = get_db_connection()
        cursor = conn
        
        # Get a sample of chunks from knowledge base to use as context
        chunks = cursor.execute("SELECT area, content FROM knowledge_base ORDER BY RANDOM() LIMIT 3").fetchall()
        conn.close()
        
        if not chunks:
            print("No se encontraron textos en 'knowledge_base'. Por favor ejecuta scripts/ingest.py primero.")
            return
            
        questions = []
        for chunk in chunks:
            area = chunk["area"]
            context = chunk["content"]
            
            prompt = f"""
            Eres un experto pedagogo diseñando preguntas para el examen oficial ICFES Saber 11 en Colombia.
            Basándote en el siguiente fragmento de lectura de la materia {area}, genera 1 pregunta de opción múltiple con 4 opciones.
            
            Contexto del cuadernillo:
            \"\"\"{context}\"\"\"
            
            REGLAS IMPORTANTES:
            1. La pregunta debe evaluar competencias específicas de {area} (e.g. uso comprensivo, explicación, indagación, lectura crítica).
            2. El formato de salida DEBE ser estrictamente un objeto JSON en español, sin envolverlo en bloques markdown (sin ```json) y con las siguientes llaves:
               - "area": "{area}"
               - "text": "[Escribe el enunciado de la pregunta aquí]"
               - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
               - "correct_answer": "[Debe coincidir exactamente con una de las opciones]"
               - "explanation": "[Explicación pedagógica de por qué es la correcta y por qué las otras no]"
               - "difficulty": "[Básico, Intermedio o Avanzado]"
            """
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                # Parse JSON clean
                text_response = response.text.strip()
                # Remove possible markdown tags
                text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                
                question_data = json.loads(text_response)
                questions.append(question_data)
                print(f"Pregunta generada con éxito para el área: {area}")
            except Exception as e:
                print(f"Error al generar pregunta para {area}: {e}")
                
        if not questions:
            print("No se pudieron generar preguntas con la API de Gemini. Usando prototipo de respaldo.")
            questions = AI_MOCK_GENERATED_QUESTIONS

    # Insert into database
    conn = get_db_connection()
    cursor = conn
    inserted_count = 0
    for q in questions:
        exists = cursor.execute("SELECT id FROM questions WHERE text = %s", (q["text"],)).fetchone()
        if not exists:
            cursor.execute('''
                INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (q["area"], q["text"], json.dumps(q["options"], ensure_ascii=False), q["correct_answer"], q["explanation"], q["difficulty"]))
            inserted_count += 1
            
    conn.commit()
    conn.close()
    print(f"Generación Inteligente completada. Se insertaron {inserted_count} preguntas de IA en la base de datos.")

if __name__ == "__main__":
    generate_questions_with_gemini()
