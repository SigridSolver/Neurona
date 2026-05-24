import psycopg2
import psycopg2.extras
import re
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "saber11.db"

def clean_question_text(text):
    # Remove: "respuestas, pídele ayuda a tu docente. 20 N.º de preguntas: 2Matemáticas - Cuadernillo 1 Saber 11.º "
    text = re.sub(
        r'^respuestas,\s*pídele\s*ayuda\s*a\s*tu\s*docente\.\s*\d*\s*N\.º\s*de\s*preguntas:\s*\d+\s*[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\d\.ºº,-]*Saber\s*11\.?º?\s*',
        '', text, flags=re.IGNORECASE
    )
    
    # Remove: "2. 3. Ciencias Naturales - Cuadernillo 1..." at start
    text = re.sub(
        r'^\d+\.\s*\d+\.\s*[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\d\.ºº,-]*Cuadernillo\s*\d+\s*Saber\s*11\.?º?\s*\d*\s*',
        '', text, flags=re.IGNORECASE
    )
    
    # Remove: "Sociales y Ciudadanas - Cuadernillo 1 Saber 11.º 5"
    text = re.sub(
        r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\d\.ºº,-]*Cuadernillo\s*\d+\s*Saber\s*11\.?º?\s*\d*\s*',
        '', text, flags=re.IGNORECASE
    )
    
    # Strip space, digits, dots, dashes, degrees, bullets, and replacement characters at the beginning
    text = re.sub(
        r'^[\s\dº°*·\.\-\ufffd]+',
        '', text
    )
    
    # Strip any leading Roman numerals followed by space (e.g. "II I VIV ")
    text = re.sub(r'^[IVXLC\s\.-]+(%s=\s[A-ZÁÉÍÓÚÑa-z¿¡"“])', '', text)
    
    # Trim and clean double spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_option_text(opt):
    # Strip common header names or table headers appended at the end of the text
    opt = re.sub(
        r'\s*(%s:Número de|Nutrientes|Corriente|Tiburón|Piscina de niñ.*|Figura \d+|Altitud.*|Fuerza del río|Célula inicial.*|Duplicación.*|Reactivos.*|Productos.*)$',
        '', opt, flags=re.IGNORECASE
    )
    
    # Remove trailing Roman numerals attached to numbers (like "25III" -> "25", but NOT "I y II solamente"!)
    opt = re.sub(r'^(\d+)[IVXLC]+$', r'\1', opt)
    
    # Remove trailing dots or replacement characters
    opt = re.sub(r'[\s\ufffd]+$', '', opt)
    
    return opt.strip()

def run_cleanup():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    questions = cursor.execute("SELECT id, text, options, correct_answer FROM questions").fetchall()
    
    updated_count = 0
    for q_id, text, options_json, correct_answer in questions:
        # Skip questions we already manually updated to be pristine (IDs 110, 111)
        if q_id in [110, 111]:
            continue
            
        cleaned_text = clean_question_text(text)
        
        try:
            options = json.loads(options_json)
            cleaned_options = [clean_option_text(o) for o in options]
            
            # Find corresponding correct answer in the cleaned list
            cleaned_correct = clean_option_text(correct_answer)
            # If the old correct answer matches one of the options, use the cleaned version
            if cleaned_correct not in cleaned_options:
                # Try finding by index
                try:
                    idx = options.index(correct_answer)
                    cleaned_correct = cleaned_options[idx]
                except ValueError:
                    # Keep it as is or fallback
                    pass
        except Exception as e:
            print(f"Error parsing options for ID {q_id}: {e}")
            continue
            
        # Update row if changes made
        if cleaned_text != text or cleaned_options != options or cleaned_correct != correct_answer:
            cursor.execute(
                "UPDATE questions SET text = %s, options = %s, correct_answer = %s WHERE id = %s",
                (cleaned_text, json.dumps(cleaned_options, ensure_ascii=False), cleaned_correct, q_id)
            )
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f"Cleanup finished. Updated {updated_count} questions.")

if __name__ == "__main__":
    run_cleanup()
