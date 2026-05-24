import psycopg2
import psycopg2.extras
from typing import Dict, Any
from pathlib import Path

DATABASE_URL = str(Path(__file__).resolve().parent.parent / "saber11.db")

class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()
        
    def cursor(self):
        return self.conn.cursor()

def get_db_connection():
    import os
    url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.DictCursor)
    
    return PostgresConnWrapper(conn)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            streak INTEGER DEFAULT 0,
            last_active_date TEXT,
            bio TEXT DEFAULT '',
            avatar_color TEXT DEFAULT '#3b82f6',
            badges TEXT DEFAULT '[]'
        )
    ''')
    
    # Migración de columnas de racha y perfil si no existen en la base de datos previa
    for column, col_type in [("streak", "INTEGER DEFAULT 0"), ("last_active_date", "TEXT"), ("bio", "TEXT DEFAULT ''"), ("avatar_color", "TEXT DEFAULT '#3b82f6'"), ("badges", "TEXT DEFAULT '[]'")]:
        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} {col_type}")
    
    # Diagnostic Results Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnostic_results (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            score_reading INTEGER DEFAULT 0,
            score_math INTEGER DEFAULT 0,
            score_social INTEGER DEFAULT 0,
            score_science INTEGER DEFAULT 0,
            score_english INTEGER DEFAULT 0,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Knowledge Base Table (Extracted text from PDFs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id SERIAL PRIMARY KEY,
            area TEXT NOT NULL,
            content TEXT NOT NULL,
            source_pdf TEXT NOT NULL
        )
    ''')
    
    # Generated Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            area TEXT NOT NULL,
            text TEXT NOT NULL,
            options TEXT NOT NULL, -- JSON string
            correct_answer TEXT NOT NULL,
            explanation TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            graphic TEXT DEFAULT NULL
        )
    ''')
    
    # Migración de columna graphic en la tabla questions si no existe
    cursor.execute("ALTER TABLE questions ADD COLUMN IF NOT EXISTS graphic TEXT DEFAULT NULL")
    
    # Practice Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            area TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Posts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            area TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Comments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Post Likes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_likes (
            post_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY(post_id, user_id),
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()

    # --- SEEDING MOCK USERS AND COMMUNITY ---
    # Add mock users if they don't exist
    from datetime import date
    today_str = date.today().isoformat()
    
    mock_users = [
        ("carlos@saber11.edu.co", "google_sso_oauth_user", "Carlos Gómez", 5, today_str, "¡Estudiando duro para Ingeniería! 🚀", "#10b981", '["Racha de 5 días", "Matemáticas Pro"]'),
        ("sofia@saber11.edu.co", "google_sso_oauth_user", "Sofía Rodríguez", 3, today_str, "Amo la lectura y los debates de sociales. 📚", "#ec4899", '["Lectura Veloz", "Racha de 3 días"]'),
        ("mateo@saber11.edu.co", "google_sso_oauth_user", "Mateo Ramos", 7, today_str, "Apuntando a medicina. Las ciencias son lo mío. 🧪", "#f59e0b", '["Científico Junior", "Racha de 7 días"]'),
        ("valeria@saber11.edu.co", "google_sso_oauth_user", "Valeria Ortiz", 10, today_str, "Practicando inglés y sociales todos los días. 🌎", "#8b5cf6", '["Bilingüe", "Racha de 10 días"]'),
        ("tutor_david@saber11.edu.co", "tutor_secret_password_hash", "Tutor David AI", 99, today_str, "Tutor Inteligente de David Saber 11. Moderador y guía de aprendizaje. 🤖", "#3b82f6", '["Tutor Oficial", "AI de Oro"]')
    ]

    for email, pwd_hash, name, streak, last_active, bio, color, badges in mock_users:
        user_row = cursor.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
        if not user_row:
            cursor.execute('''
                INSERT INTO users (email, password_hash, name, streak, last_active_date, bio, avatar_color, badges)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (email, pwd_hash, name, streak, last_active, bio, color, badges))
            user_id = cursor.lastrowid
            
            # Add diagnostic results for leaderboard
            if email == "carlos@saber11.edu.co":
                cursor.execute("INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english) VALUES (%s, 85, 65, 60, 75, 55)", (user_id,))
            elif email == "sofia@saber11.edu.co":
                cursor.execute("INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english) VALUES (%s, 60, 88, 85, 65, 70)", (user_id,))
            elif email == "mateo@saber11.edu.co":
                cursor.execute("INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english) VALUES (%s, 75, 70, 68, 90, 65)", (user_id,))
            elif email == "valeria@saber11.edu.co":
                cursor.execute("INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english) VALUES (%s, 70, 78, 80, 72, 88)", (user_id,))
            elif email == "tutor_david@saber11.edu.co":
                cursor.execute("INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english) VALUES (%s, 95, 95, 95, 95, 95)", (user_id,))
                
    conn.commit()

    # Seed mock posts if none exist
    post_count = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    if post_count == 0:
        valeria_id = cursor.execute("SELECT id FROM users WHERE email = 'valeria@saber11.edu.co'").fetchone()[0]
        carlos_id = cursor.execute("SELECT id FROM users WHERE email = 'carlos@saber11.edu.co'").fetchone()[0]
        sofia_id = cursor.execute("SELECT id FROM users WHERE email = 'sofia@saber11.edu.co'").fetchone()[0]
        mateo_id = cursor.execute("SELECT id FROM users WHERE email = 'mateo@saber11.edu.co'").fetchone()[0]
        tutor_id = cursor.execute("SELECT id FROM users WHERE email = 'tutor_david@saber11.edu.co'").fetchone()[0]

        # Post 1
        cursor.execute('''
            INSERT INTO posts (user_id, content, area, likes)
            VALUES (%s, 'Hola a todos! ¿Alguien tiene algún truco para recordar las diferencias entre los tipos de células en Ciencias Naturales?', 'Ciencias Naturales', 4)
        ''', (valeria_id,))
        p1_id = cursor.lastrowid
        
        # Comments on Post 1
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (%s, %s, 'Valeria, yo suelo hacer analogías con una fábrica: la mitocondria es la central de energía y el núcleo es la oficina de administración. ¡Me sirve muchísimo! 🧪')
        ''', (p1_id, mateo_id))
        
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (%s, %s, '¡Excelente analogía, Mateo! Recuerden también que en las pruebas Saber 11 suelen preguntar mucho sobre la respiración celular (en la mitocondria) y la fotosíntesis (en el cloroplasto) como procesos complementarios. ¡Sigan así! 🤖')
        ''', (p1_id, tutor_id))

        # Post 2
        cursor.execute('''
            INSERT INTO posts (user_id, content, area, likes)
            VALUES (%s, '¡Qué buen duelo acabo de tener con Sofía en Matemáticas! Esas preguntas de probabilidad estaban bien picantes. ⚡', 'Matemáticas', 2)
        ''', (carlos_id,))
        p2_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (%s, %s, '¡Jajaja estuvo súper cerrado! Para la próxima te gano en el último segundo. ¡Prepárate! 🏎️💨')
        ''', (p2_id, sofia_id))

        # Post 3
        cursor.execute('''
            INSERT INTO posts (user_id, content, area, likes)
            VALUES (%s, 'Recomiendo mucho leer noticias de actualidad para la sección de Sociales y Ciudadanas. Ayuda a entender mejor los mecanismos de participación ciudadana y la estructura del Estado.', 'Sociales y Ciudadanas', 5)
        ''', (sofia_id,))
        p3_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (%s, %s, '¡Totalmente de acuerdo, Sofía! Especialmente repasar qué es la tutela, el plebiscito y las funciones del Congreso. Siempre sale al menos una pregunta de eso. 👍')
        ''', (p3_id, carlos_id))

        # Insert some initial likes in post_likes
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (p1_id, carlos_id))
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (p1_id, sofia_id))
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (p1_id, mateo_id))
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (p2_id, mateo_id))
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (p3_id, valeria_id))

        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
