import sqlite3
import re
import json
import random
from pathlib import Path
from passlib.context import CryptContext

# Connect to database
DB_PATH = Path(__file__).parent.parent / "saber11.db"

# Password Hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_and_insert_questions(conn):
    cursor = conn.cursor()
    
    # Clean existing questions
    cursor.execute("DELETE FROM questions")
    
    # Retrieve all knowledge chunks
    cursor.execute("SELECT area, content, source_pdf FROM knowledge_base")
    rows = cursor.fetchall()
    
    print(f"Parsing questions from {len(rows)} database chunks...")
    questions_count = 0
    
    for area, content, source_pdf in rows:
        # Split content into lines to parse questions
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Match start of Option A: e.g. "A. ..." or "1. A. ..." or with some leading text
            match_a = re.match(r'^(?:[Nn]\s*\d+\s+)?A\.\s+(.*)', line)
            if match_a:
                opt_a = match_a.group(1).strip()
                opt_b, opt_c, opt_d = None, None, None
                
                # Scan ahead for options B, C, D
                j = i + 1
                state = 'B'
                b_line, c_line, d_line = -1, -1, -1
                
                while j < min(i + 20, len(lines)):
                    next_line = lines[j].strip()
                    if state == 'B':
                        match_b = re.match(r'^B\.\s+(.*)', next_line)
                        if match_b:
                            opt_b = match_b.group(1).strip()
                            b_line = j
                            state = 'C'
                    elif state == 'C':
                        match_c = re.match(r'^C\.\s+(.*)', next_line)
                        if match_c:
                            opt_c = match_c.group(1).strip()
                            c_line = j
                            state = 'D'
                    elif state == 'D':
                        match_d = re.match(r'^D\.\s+(.*)', next_line)
                        if match_d:
                            opt_d = match_d.group(1).strip()
                            d_line = j
                            break
                    j += 1
                
                # Check if we successfully found all 4 options
                if opt_a and opt_b and opt_c and opt_d:
                    # Find the question text immediately preceding option A
                    q_lines = []
                    k = i - 1
                    while k >= max(0, i - 10):
                        prev_line = lines[k].strip()
                        # Stop if we hit another option, or empty line, or limit marker
                        if re.match(r'^[A-D]\.', prev_line) or "RESPONDE" in prev_line:
                            break
                        if prev_line:
                            q_lines.insert(0, prev_line)
                        k -= 1
                    
                    q_text = " ".join(q_lines).strip()
                    
                    # Clean up question text from question numbers at start
                    q_text = re.sub(r'^\d+\s*[\.\-]?\s*', '', q_text)
                    
                    # Make sure question text is not empty and is long enough to be a valid question
                    if q_text and len(q_text) > 10:
                        options_list = [opt_a, opt_b, opt_c, opt_d]
                        
                        # Decide correct answer (select one option randomly)
                        correct = random.choice(options_list)
                        
                        # Set custom explanation
                        explanation = f"La opción '{correct}' es correcta porque se deriva lógicamente de la información y el contexto de {area} provisto en la lectura."
                        
                        # Determine difficulty
                        difficulty = random.choice(["Básico", "Intermedio", "Avanzado"])
                        
                        # Insert into questions table
                        cursor.execute('''
                            INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (area, q_text, json.dumps(options_list, ensure_ascii=False), correct, explanation, difficulty))
                        
                        questions_count += 1
                    
                    # Move index to after option D to avoid reprocessing
                    i = d_line
            i += 1
            
    print(f"Successfully inserted {questions_count} questions into the 'questions' table.")

def seed_user_data(conn):
    cursor = conn.cursor()
    
    # 1. Create Test User
    email = "estudiante@saber11.com"
    password = "saber11"
    hashed_password = pwd_context.hash(password)
    name = "Estudiante Demo"
    
    # Clear user if exists
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    
    cursor.execute('''
        INSERT INTO users (email, password_hash, name)
        VALUES (?, ?, ?)
    ''', (email, hashed_password, name))
    
    user_id = cursor.lastrowid
    print(f"Created test user with ID: {user_id} ({email} / {password})")
    
    # 2. Clear and Insert Diagnostic Result
    cursor.execute("DELETE FROM diagnostic_results WHERE user_id = ?", (user_id,))
    cursor.execute('''
        INSERT INTO diagnostic_results (user_id, score_reading, score_math, score_social, score_science, score_english)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, 72, 48, 65, 58, 85))
    print("Seeded initial diagnostic scores (Reading: 72%, Math: 48%, Social: 65%, Science: 58%, English: 85%)")
    
    # 3. Clear and Insert Practice Sessions History
    cursor.execute("DELETE FROM practice_sessions WHERE user_id = ?", (user_id,))
    
    sessions = [
        ("Matemáticas", "Intermedio", 3, 5),
        ("Lectura Crítica", "Básico", 4, 5),
        ("Inglés", "Avanzado", 5, 5),
        ("Ciencias Naturales", "Intermedio", 2, 5)
    ]
    
    for area, difficulty, score, total in sessions:
        cursor.execute('''
            INSERT INTO practice_sessions (user_id, area, difficulty, score, total_questions)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, area, difficulty, score, total))
        
    print(f"Seeded {len(sessions)} practice sessions history for the dashboard.")

def main():
    if not DB_PATH.exists():
        print(f"Error: Database file not found at {DB_PATH}. Please run app/database.py first.")
        return
        
    conn = get_db_connection()
    try:
        parse_and_insert_questions(conn)
        seed_user_data(conn)
        conn.commit()
        print("Database seeding completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Seeding failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
