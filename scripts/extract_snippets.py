import os
import sys
import json
import time
import shutil
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: La librería google-generativeai no está instalada. Ejecuta: pip install google-generativeai")
    sys.exit(1)

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: No se encontró GEMINI_API_KEY en las variables de entorno.")
    sys.exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite')

# Rutas
RECORTES_DIR = Path(r"D:\Neurona\docs\recortes")
IMAGES_STATIC_DIR = Path(r"D:\Neurona\app\static\images\recortes")

# Crear directorios si no existen
os.makedirs(RECORTES_DIR, exist_ok=True)
os.makedirs(IMAGES_STATIC_DIR, exist_ok=True)

PROMPT_RECORTES = """
Eres un experto extrayendo preguntas de opción múltiple del ICFES (Saber 11) a partir de recortes de pantalla.
En la imagen que te adjunto hay UNA pregunta de opción múltiple con sus 4 opciones de respuesta (A, B, C, D).

Por favor, analiza la imagen y devuelve estrictamente un objeto JSON con la siguiente estructura exacta:
{
  "text": "Aquí el enunciado de la pregunta. Si hay un contexto grande antes de la pregunta, inclúyelo aquí.",
  "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
  "correct_answer": "Escribe aquí textualmente la opción que consideres correcta",
  "explanation": "Explica brevemente paso a paso por qué esa es la respuesta correcta.",
  "difficulty": "Intermedio"
}

REGLAS:
- No inventes información. Copia el texto y las opciones exactamente como están en la imagen.
- NO uses formato markdown (como ```json) en tu respuesta, devuelve ÚNICAMENTE el código JSON puro para poder parsearlo directamente.
- Si no logras leer las opciones o la pregunta con claridad, devuelve un JSON vacío: {}
"""

def process_snippets():
    print("===============================================")
    print("Iniciando extracción semiautomática de Recortes")
    print("===============================================")

    # Obtener todas las imágenes en la carpeta de recortes
    image_files = [f for f in RECORTES_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg']]

    if not image_files:
        print(f"No se encontraron imágenes en: {RECORTES_DIR}")
        print("Usa la herramienta Recortes (Win + Shift + S) para guardar tus preguntas aquí.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted_count = 0

    for img_path in image_files:
        print(f"\n-> Procesando recorte: {img_path.name}")
        
        # Intentar deducir el área a partir del nombre del archivo (ej. matematicas_1.png -> Matemáticas)
        area = "Área General"
        name_lower = img_path.name.lower()
        if "matematica" in name_lower or "mate" in name_lower:
            area = "Matemáticas"
        elif "lectura" in name_lower or "critica" in name_lower:
            area = "Lectura Crítica"
        elif "sociales" in name_lower or "ciudadanas" in name_lower:
            area = "Sociales y Ciudadanas"
        elif "ciencias" in name_lower or "naturales" in name_lower:
            area = "Ciencias Naturales"
        elif "ingle" in name_lower or "english" in name_lower:
            area = "Inglés"

        try:
            # Abrir la imagen
            img_pil = Image.open(img_path)
            
            # Consultar a Gemini
            response = model.generate_content([PROMPT_RECORTES, img_pil])
            
            # Limpiar la respuesta (por si acaso Gemini manda ```json ... ```)
            text_response = response.text.strip()
            if text_response.startswith('```json'):
                text_response = text_response[7:]
            if text_response.startswith('```'):
                text_response = text_response[3:]
            if text_response.endswith('```'):
                text_response = text_response[:-3]
            
            data = json.loads(text_response.strip())
            
            if not data or "text" not in data:
                print(f"   [AVISO] No se pudo extraer la pregunta de {img_path.name}. Saltando...")
                continue
                
            # Mover/Copiar la imagen a static
            # Para evitar sobreescribir, usamos un timestamp
            safe_filename = f"recorte_{int(time.time())}_{img_path.name}"
            dest_path = IMAGES_STATIC_DIR / safe_filename
            shutil.copy2(img_path, dest_path)
            
            graphic_url = f"/static/images/recortes/{safe_filename}"
            
            # Guardar en BD
            cursor.execute('''
                INSERT INTO questions (area, text, graphic, options, correct_answer, explanation, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                area,
                data["text"],
                graphic_url,
                json.dumps(data["options"], ensure_ascii=False),
                data["correct_answer"],
                data["explanation"],
                data.get("difficulty", "Intermedio")
            ))
            
            inserted_count += 1
            print(f"   [OK] Pregunta extraída y guardada exitosamente en {area}.")
            
            # Pequeña pausa para evitar límites de RPM
            time.sleep(3)

        except json.JSONDecodeError:
             print(f"   [ERROR] Gemini no devolvió un JSON válido para {img_path.name}")
        except Exception as e:
            print(f"   [ERROR] Error procesando {img_path.name}: {str(e)}")

    conn.commit()
    conn.close()
    
    print("\n===============================================")
    print(f"¡Proceso Terminado! Se inyectaron {inserted_count} recortes a la base de datos.")
    print("===============================================")

if __name__ == "__main__":
    process_snippets()
