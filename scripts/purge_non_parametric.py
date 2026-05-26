import sys
import os
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db_connection
from scripts.seed_static_questions import STATIC_QUESTIONS

load_dotenv()

def get_connection():
    try:
        conn = get_db_connection()
        is_sqlite = False
        print("Conectado con éxito a PostgreSQL (Producción).")
        return conn, is_sqlite
    except Exception as e:
        print(f"Error conectando a PostgreSQL ({e}). Usando SQLite local ('saber11.db').")
        conn = sqlite3.connect('saber11.db')
        conn.row_factory = sqlite3.Row
        is_sqlite = True
        return conn, is_sqlite

def purge_and_clean_db():
    print("Iniciando purga y limpieza de base de datos...")
    
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    # 1. Delete all questions to start from a completely clean state
    print("Eliminando todas las preguntas de la base de datos...")
    cursor.execute("DELETE FROM questions")
    conn.commit()
    conn.close()
    
    # 2. Insert static questions (is_parametric = FALSE)
    print("Insertando las preguntas estáticas de alta calidad...")
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    p = "?" if is_sqlite else "%s"
    inserted_static = 0
    for q in STATIC_QUESTIONS:
        cursor.execute(f'''
            INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, is_parametric, exam_type)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {'0' if is_sqlite else 'FALSE'}, {p})
        ''', (
            q["area"], 
            q["text"], 
            json.dumps(q["options"], ensure_ascii=False), 
            q["correct_answer"], 
            q["explanation"], 
            q["difficulty"],
            "saber_11"
        ))
        inserted_static += 1
        
    conn.commit()
    conn.close()
    
    print(f"* {inserted_static} preguntas estáticas insertadas con éxito.")
    print("=== LIMPIEZA Y RESTAURACIÓN DE BASE DE DATOS COMPLETADA ===")

if __name__ == '__main__':
    purge_and_clean_db()
