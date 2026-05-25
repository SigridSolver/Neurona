import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

def delete_broken_questions():
    print("Conectando a la base de datos para depurar preguntas con instrucciones de imaginación de diagramas...")
    import sqlite3
    try:
        conn = get_db_connection()
        print("Conectado con éxito a PostgreSQL (Producción).")
    except Exception as e:
        print(f"Error conectando a PostgreSQL ({e}). Usando SQLite local ('saber11.db').")
        conn = sqlite3.connect('saber11.db')
        # Allow dict-like access for SQLite if needed (though we only fetch standard rows here)
        conn.row_factory = sqlite3.Row
        
    cursor = conn.cursor()
    
    # Check how many questions match the broken criteria
    # Search for "[IMAGINAR" or "[IMAGEN" or "imaginar diagrama" or similar
    query = """
        SELECT id, area, text FROM questions 
        WHERE text LIKE '%[IMAGINAR%' 
           OR text LIKE '%[IMAGEN%' 
           OR text LIKE '%imaginar diagrama%'
           OR text LIKE '%imaginar imagen%'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No se encontraron preguntas con marcadores visuales rotos '[IMAGINAR DIAGRAMA]'. La base de datos está limpia.")
        conn.close()
        return
        
    print(f"Se encontraron {len(rows)} preguntas rotas:")
    for r in rows:
        print(f"- ID {r['id']} ({r['area']}): {r['text'][:60]}...")
        
    # Delete them
    delete_query = """
        DELETE FROM questions 
        WHERE text LIKE '%[IMAGINAR%' 
           OR text LIKE '%[IMAGEN%' 
           OR text LIKE '%imaginar diagrama%'
           OR text LIKE '%imaginar imagen%'
    """
    cursor.execute(delete_query)
    conn.commit()
    print(f"Éxito: Se eliminaron las {len(rows)} preguntas rotas de la base de datos.")
    conn.close()

if __name__ == '__main__':
    delete_broken_questions()
