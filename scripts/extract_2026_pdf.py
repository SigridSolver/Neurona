import os
import sys
import json
import re
import random
from pathlib import Path
from dotenv import load_dotenv

# Configurar entorno
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

load_dotenv()

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import google.generativeai as genai
except ImportError:
    print("Faltan librerías. Ejecuta: pip install pymupdf pillow google-generativeai")
    sys.exit(1)

# Configurar Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: No se encontró GEMINI_API_KEY en las variables de entorno.")
    sys.exit(1)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Rutas
PDF_DIR = Path(r"D:\Neurona\docs\Cuadernillos Saber 11 2026")
IMAGES_DIR = Path(r"d:\Neurona\app\static\images\2026")
LOG_FILE = Path(r"d:\Neurona\extraccion_fallida_log.txt")

def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    # Crear archivo de log si no existe
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Log de Extracción Fallida - Cuadernillos 2026\n==============================================\n")

def log_error(pdf_name, page_num, reason):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"FALLO: Cuadernillo '{pdf_name}', Página {page_num}. Razón: {reason}\n")

def determine_area(filename):
    filename = filename.lower()
    if "matematicas" in filename: return "Matemáticas"
    elif "lecturacritica" in filename: return "Lectura Crítica"
    elif "socialesyciudadanas" in filename: return "Sociales y Ciudadanas"
    elif "ciencias_naturales" in filename: return "Ciencias Naturales"
    elif "ingles" in filename: return "Inglés"
    return "Área General"

def extract_questions_with_gemini():
    ensure_dirs()
    print(f"Buscando PDFs en: {PDF_DIR}")
    
    if not PDF_DIR.exists():
        print("El directorio de PDFs 2026 no existe.")
        return
        
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No se encontraron PDFs en el directorio.")
        return
        
    conn = get_db_connection()
    cursor = conn
    
    total_extracted = 0
    
    prompt = """
    Eres un analizador pedagógico de alto nivel. Analiza esta página de un examen del ICFES Saber 11.
    Extrae todas las preguntas de opción múltiple (con 4 opciones: A, B, C, D) que encuentres.
    
    Devuelve ÚNICAMENTE un arreglo en formato JSON puro (sin etiquetas markdown, sin bloques ```json, empezando directamente con [) con este esquema exacto para cada pregunta:
    [
      {
        "text": "El enunciado de la pregunta...",
        "options": ["Texto opción A", "Texto opción B", "Texto opción C", "Texto opción D"],
        "correct_answer": "Texto exacto de la opción correcta (si puedes deducirla lógicamente; si no es obvia o no hay hoja de respuestas, elige la que te parezca más coherente para que el sistema funcione)",
        "explanation": "Breve explicación pedagógica de 1 o 2 frases",
        "difficulty": "Intermedio",
        "requiere_imagen": true_o_false
      }
    ]
    
    IMPORTANTE SOBRE 'requiere_imagen': 
    Pon "requiere_imagen": true SI Y SOLO SI la pregunta hace referencia a una gráfica, dibujo, infografía, tabla o texto largo que está en la página y sin el cual es imposible responder la pregunta. Si es solo texto corto autosuficiente, pon false.
    Si no hay preguntas válidas en la página, devuelve un arreglo vacío [].
    """
    
    for pdf_path in pdf_files:
        area = determine_area(pdf_path.name)
        print(f"\n=================================")
        print(f"Procesando {pdf_path.name} ({area})")
        print(f"=================================")
        
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            print(f"Error abriendo PDF {pdf_path.name}: {e}")
            continue
            
        # Opcional: saltar portadas (ej. empezar desde la página 3 si se quiere, pero dejaremos todas por ahora)
        for page_num in range(len(doc)):
            print(f"-> Analizando página {page_num + 1} de {len(doc)}...")
            page = doc[page_num]
            
            # Renderizar página a imagen (alta calidad)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para buena resolución
            image_name = f"{pdf_path.stem}_pag_{page_num+1}.png"
            image_filepath = IMAGES_DIR / image_name
            pix.save(str(image_filepath))
            
            db_image_path = f"/static/images/2026/{image_name}"
            html_image_tag = f'<img src="{db_image_path}" alt="Página de referencia {area}" style="max-width:100%; border-radius:8px; margin: 15px 0; border: 1px solid #334155;">'
            
            # Abrir con Pillow para pasar a Gemini
            try:
                img_pil = Image.open(image_filepath)
                response = model.generate_content([prompt, img_pil])
                
                # Parsear respuesta
                text_response = response.text.strip()
                # Limpiar cualquier residuo de markdown
                text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                
                questions_data = json.loads(text_response)
                
                if not questions_data:
                    # Probablemente una página en blanco o sin preguntas (portada, instrucciones)
                    print("   (Sin preguntas en esta página)")
                    continue
                    
                inserted_in_page = 0
                for q in questions_data:
                    # Asegurar que tenga 4 opciones
                    if len(q.get("options", [])) != 4:
                        continue
                        
                    graphic = html_image_tag if q.get("requiere_imagen", False) else None
                    
                    cursor.execute('''
                        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        area, 
                        q["text"], 
                        json.dumps(q["options"], ensure_ascii=False), 
                        q["correct_answer"], 
                        q["explanation"], 
                        q.get("difficulty", "Intermedio"), 
                        graphic
                    ))
                    inserted_in_page += 1
                    total_extracted += 1
                
                print(f"   [OK] {inserted_in_page} preguntas extraídas correctamente.")
                
            except json.JSONDecodeError:
                print("   [ERROR] Gemini devolvió un formato no válido.")
                log_error(pdf_path.name, page_num + 1, "Gemini devolvió un JSON inválido o texto basura.")
            except Exception as e:
                print(f"   [ERROR] Error con la API de Gemini: {str(e)}")
                log_error(pdf_path.name, page_num + 1, f"Error de API: {str(e)}")
                
    conn.commit()
    conn.close()
    
    print(f"\n¡Extracción Inteligente Finalizada!")
    print(f"Se insertaron {total_extracted} preguntas del cuadernillo 2026 en la base de datos.")
    print(f"Las imágenes de referencia se guardaron en app/static/images/2026/")
    print(f"Cualquier fallo manual fue registrado en: {LOG_FILE}")

if __name__ == "__main__":
    extract_questions_with_gemini()
