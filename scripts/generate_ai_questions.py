import sys
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db_connection
from app.areas.registry import AREA_REGISTRY
from app.main import ensure_svg_xmlns

# Load environment variables
load_dotenv()

def generate_bank_questions():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY no encontrada en las variables de entorno.")
        return
        
    genai.configure(api_key=api_key)
    # Using the same model as in main app
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    areas = ["Matemáticas", "Lectura Crítica", "Ciencias Naturales", "Sociales y Ciudadanas", "Inglés"]
    target_count_per_area = 200
    
    print("\n=== INICIANDO GENERACIÓN DE BANCO DE PREGUNTAS ===")
    print("Objetivo: 200 preguntas por área (1000 en total)\n")
    
    for area in areas:
        conn = get_db_connection()
        # Count current questions for this area
        cursor = conn
        row = cursor.execute("SELECT COUNT(*) FROM questions WHERE area = %s", (area,)).fetchone()
        current_count = row[0] if row else 0
        conn.close()
        
        print(f"Área: {area}")
        print(f"  Preguntas actuales en DB: {current_count}")
        
        if current_count >= target_count_per_area:
            print(f"  [OK] El área {area} ya cuenta con {current_count} preguntas (meta: {target_count_per_area}).\n")
            continue
            
        needed = target_count_per_area - current_count
        print(f"  Se necesitan generar: {needed} preguntas.")
        
        # We will generate in batches of 5 to 10 to avoid timeouts and keep token limits safe
        batch_size = 10
        generated_in_area = 0
        
        while needed > 0:
            current_batch = min(batch_size, needed)
            print(f"  -> Generando lote de {current_batch} preguntas...")
            
            handler = AREA_REGISTRY[area]
            prompt = handler.get_generation_prompt(current_batch)
                
            try:
                response = model.generate_content(prompt)
                text_response = response.text.strip()
                # Clean markdown JSON wrapping if present
                text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                
                q_list = json.loads(text_response)
                if isinstance(q_list, dict):
                    q_list = [q_list]
                
                conn = get_db_connection()
                cursor = conn
                inserted_in_batch = 0
                
                for q_data in q_list:
                    # Check duplicate text in DB
                    exists = cursor.execute("SELECT id FROM questions WHERE text = %s", (q_data["text"],)).fetchone()
                    if exists:
                        continue
                        
                    graphic_val = q_data.get("graphic")
                    if graphic_val and "base64," not in graphic_val and "<svg" in graphic_val:
                        try:
                            import base64
                            graphic_val = ensure_svg_xmlns(graphic_val)
                            graphic_val = "data:image/svg+xml;base64," + base64.b64encode(graphic_val.encode('utf-8')).decode('utf-8')
                        except Exception as e:
                            print(f"    Error al codificar SVG generado: {e}")
                            
                    cursor.execute('''
                        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        area,
                        q_data["text"],
                        json.dumps(q_data["options"], ensure_ascii=False),
                        q_data["correct_answer"],
                        q_data["explanation"],
                        q_data.get("difficulty", "Intermedio"),
                        graphic_val
                    ))
                    inserted_in_batch += 1
                    generated_in_area += 1
                    needed -= 1
                    
                conn.commit()
                conn.close()
                
                print(f"    Lote procesado. Se insertaron {inserted_in_batch} nuevas preguntas.")
                
                if inserted_in_batch == 0:
                    print("    [ADVERTENCIA] No se insertó ninguna pregunta del lote. Reintentando...")
                    
            except Exception as e:
                print(f"    Error durante la generación/inserción del lote: {e}")
                print("    Reintentando lote...")
                
        print(f"  [COMPLETADO] Área {area} alcanzó las {target_count_per_area} preguntas.\n")
        
    print("=== BANCO DE PREGUNTAS LISTO Y ACTUALIZADO A 1000 PREGUNTAS ===")

if __name__ == "__main__":
    generate_bank_questions()
