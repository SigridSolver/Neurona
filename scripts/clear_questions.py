import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

def clear_questions():
    print("Conectando a la base de datos para limpiar las preguntas...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions")
    conn.commit()
    conn.close()
    print("¡Base de datos de preguntas limpiada con éxito!")

if __name__ == "__main__":
    clear_questions()
