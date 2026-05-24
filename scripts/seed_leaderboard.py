import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

from pathlib import Path
from passlib.context import CryptContext

# Paths
DB_PATH = Path(__file__).parent.parent / "saber11.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_leaderboard():
    conn = get_db_connection()
    cursor = conn

    dummy_users = [
        # (name, email, password, math, reading, science, social, english)
        ("Carlos Gómez", "carlos.gomez@gmail.com", "saber11secure", 92, 85, 90, 88, 95),
        ("Sofía Miranda", "sofia.miranda@gmail.com", "saber11secure", 80, 85, 78, 82, 88),
        ("Mateo Salazar", "mateo.salazar@gmail.com", "saber11secure", 72, 75, 70, 78, 75),
        ("Valeria Rojas", "valeria.rojas@gmail.com", "saber11secure", 55, 60, 58, 62, 65)
    ]

    for name, email, password, math, reading, science, social, english in dummy_users:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            hashed_pwd = pwd_context.hash(password)
            cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hashed_pwd))
            user_id = cursor.fetchone()[0] if cursor.description else None
            
            # Insert diagnostic result
            cursor.execute('''
                INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_science, score_social, score_english)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, math, reading, science, social, english))
            print(f"Seeded dummy user: {name} ({email}) with diagnostic scores.")
        else:
            print(f"User {name} already exists.")

    conn.commit()
    conn.close()
    print("Leaderboard seeding complete!")

if __name__ == "__main__":
    seed_leaderboard()
