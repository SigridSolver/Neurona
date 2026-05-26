import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection
import sqlite3

def purge_all_booklet_questions():
    print("Conectando a la base de datos para eliminar todas las preguntas de cuadernillos...")
    try:
        conn = get_db_connection()
        print("Conectado con éxito a PostgreSQL (Producción).")
    except Exception as e:
        print(f"Error conectando a PostgreSQL ({e}). Usando SQLite local ('saber11.db').")
        conn = sqlite3.connect('saber11.db')
        conn.row_factory = sqlite3.Row
        
    cursor = conn.cursor()
    
    # Select questions that are NOT parametric and NOT recortes
    # Parametric: text contains '{' (indicating placeholder variables)
    # Recortes: graphic contains 'recortes' or starts with 'data:image' (indicating base64 upload)
    select_query = """
        SELECT id, area, text FROM questions 
        WHERE NOT (
            text LIKE '%{%}' 
            OR (graphic IS NOT NULL AND (graphic LIKE 'data:image%' OR graphic LIKE '%recortes%'))
        )
    """
    
    # We execute this search to report what is being deleted
    cursor.execute(select_query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No se encontraron preguntas de cuadernillos estáticos. ¡La base de datos está limpia!")
        conn.close()
        return
        
    print(f"Se encontraron {len(rows)} preguntas de cuadernillos estáticos para eliminar:")
    for r in rows[:15]:
        row_id = r[0] if isinstance(r, tuple) else r['id']
        row_area = r[1] if isinstance(r, tuple) else r['area']
        row_text = r[2] if isinstance(r, tuple) else r['text']
        print(f"- ID {row_id} ({row_area}): {row_text[:80]}...")
        
    if len(rows) > 15:
        print(f"... y {len(rows) - 15} preguntas más.")
        
    # Delete them
    delete_query = """
        DELETE FROM questions 
        WHERE NOT (
            text LIKE '%{%}' 
            OR (graphic IS NOT NULL AND (graphic LIKE 'data:image%' OR graphic LIKE '%recortes%'))
        )
    """
    cursor.execute(delete_query)
    conn.commit()
    print(f"Éxito: Se eliminaron las {len(rows)} preguntas estáticas de cuadernillo de la base de datos.")
    conn.close()

if __name__ == '__main__':
    purge_all_booklet_questions()
