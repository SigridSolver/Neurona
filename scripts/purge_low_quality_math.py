import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection
import sqlite3

def purge_low_quality_math():
    print("Conectando a la base de datos para depurar preguntas de Matemáticas de baja calidad...")
    try:
        conn = get_db_connection()
        print("Conectado con éxito a PostgreSQL (Producción).")
    except Exception as e:
        print(f"Error conectando a PostgreSQL ({e}). Usando SQLite local ('saber11.db').")
        conn = sqlite3.connect('saber11.db')
        conn.row_factory = sqlite3.Row
        
    cursor = conn.cursor()
    
    # Query mathematical questions without graphic and without LaTeX formulas
    query = """
        SELECT id, text FROM questions 
        WHERE area = 'Matemáticas'
          AND graphic IS NULL
          AND text NOT LIKE '%$$%'
          AND text NOT LIKE '%$%'
          AND text NOT LIKE '%{n_estudiantes}%'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("No se encontraron preguntas de Matemáticas planas sin fórmulas ni gráficos. ¡El banco está limpio!")
        conn.close()
        return
        
    print(f"Se encontraron {len(rows)} preguntas de Matemáticas planas (sin gráficos ni LaTeX):")
    for r in rows:
        print(f"- ID {r[0] if isinstance(r, tuple) else r['id']}: {r[1][:80]}...")
        
    # Delete them
    delete_query = """
        DELETE FROM questions 
        WHERE area = 'Matemáticas'
          AND graphic IS NULL
          AND text NOT LIKE '%$$%'
          AND text NOT LIKE '%$%'
          AND text NOT LIKE '%{n_estudiantes}%'
    """
    cursor.execute(delete_query)
    conn.commit()
    print(f"Éxito: Se eliminaron las {len(rows)} preguntas planas de Matemáticas de la base de datos.")
    conn.close()

if __name__ == '__main__':
    purge_low_quality_math()
