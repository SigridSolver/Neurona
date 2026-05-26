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
    
    # 2. Re-seed parametric template questions (which will have is_parametric = TRUE)
    print("Insertando las 12 plantillas de preguntas paramétricas...")
    # To run cross-platform, we manually insert the 12 templates here with appropriate placeholders
    conn, is_sqlite = get_connection()
    cursor = conn.cursor()
    
    p = "?" if is_sqlite else "%s"
    
    # 1. Pisa Tower Question Template
    pisa_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" width="320" height="240">
  <rect width="100%" height="100%" fill="#0f172a"/>
  <line x1="30" y1="200" x2="290" y2="200" stroke="#94a3b8" stroke-width="2.5" />
  <line x1="120" y1="30" x2="120" y2="200" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,4" />
  <rect x="105" y="185" width="15" height="15" fill="none" stroke="#64748b" stroke-width="1.5" />
  <polygon points="120,200 131,40 166,42 155,200" fill="#1e293b" stroke="#38bdf8" stroke-width="3" />
  <line x1="122" y1="170" x2="157" y2="170" stroke="#475569" stroke-width="1.5" />
  <line x1="124" y1="140" x2="159" y2="140" stroke="#475569" stroke-width="1.5" />
  <line x1="126" y1="110" x2="161" y2="110" stroke="#475569" stroke-width="1.5" />
  <line x1="128" y1="80" x2="163" y2="80" stroke="#475569" stroke-width="1.5" />
  <path d="M 120 130 A 70 70 0 0 1 125 130" fill="none" stroke="#3b82f6" stroke-width="2" />
  <text x="110" y="125" fill="#3b82f6" font-family="sans-serif" font-size="12" font-weight="bold">{inclinacion}deg</text>
  <path d="M 175 200 A 20 20 0 0 0 153 182" fill="none" stroke="#f43f5e" stroke-width="2.5" />
  <text x="135" y="185" fill="#f43f5e" font-family="sans-serif" font-size="16" font-weight="bold">?</text>
</svg>"""
    import base64
    pisa_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(pisa_svg.encode('utf-8')).decode('utf-8')
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "Con respecto a la vertical, la torre se ha inclinado {inclinacion}° como se muestra en la gráfica. ¿Cuánto mide el otro ángulo (indicado con el signo de interrogación)?",
        json.dumps(["{inclinacion}°", "{correct}°", "90°", "180°"]),
        "{correct}°",
        "Procesado dinámicamente.",
        "Fácil",
        pisa_graphic_uri
    ))

    # 2. Venn Diagram Question Template
    venn_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 220" width="400" height="220">
  <rect width="100%" height="100%" fill="#0f172a" rx="12"/>
  <rect x="10" y="10" width="380" height="200" fill="none" stroke="#475569" stroke-width="2" rx="8"/>
  <text x="360" y="35" fill="#94a3b8" font-family="sans-serif" font-size="14" font-weight="bold">U</text>
  <circle cx="160" cy="110" r="70" fill="rgba(59, 130, 246, 0.15)" stroke="#3b82f6" stroke-width="2.5"/>
  <circle cx="240" cy="110" r="70" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" stroke-width="2.5"/>
  <text x="120" y="35" fill="#3b82f6" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Fútbol (F)</text>
  <text x="280" y="35" fill="#10b981" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">Baloncesto (B)</text>
  <text x="130" y="115" fill="#f8fafc" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">{futbol_solo}</text>
  <text x="200" y="115" fill="#f8fafc" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">{ambos}</text>
  <text x="270" y="115" fill="#f8fafc" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">{baloncesto_solo}</text>
  <text x="340" y="180" fill="#f8fafc" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">{ninguno}</text>
</svg>"""
    venn_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(venn_svg.encode('utf-8')).decode('utf-8')
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "El siguiente diagrama de Venn representa la distribución de un grupo de estudiantes según sus preferencias deportivas entre Fútbol (F) y Baloncesto (B). Si se selecciona un estudiante al azar dentro del grupo, ¿cuál es la probabilidad de que prefiera únicamente Baloncesto?",
        json.dumps(["{correct_frac}", "d1", "d2", "d3"]),
        "{correct_frac}",
        "Procesado dinámicamente.",
        "Intermedio",
        venn_graphic_uri
    ))

    # 3. Combinations Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "En un colegio se realiza una preselección de estudiantes para participar en las olimpiadas de matemáticas. De un grupo de {n_estudiantes} estudiantes destacados, el entrenador debe elegir a {k_seleccionados} de ellos para conformar el equipo oficial. ¿De cuántas formas diferentes se puede conformar el equipo?",
        json.dumps(["{correct_val}", "d1", "d2", "d3"]),
        "{correct_val}",
        "Procesado dinámicamente.",
        "Intermedio",
        None
    ))

    # 4. Pie Chart Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "La siguiente gráfica circular muestra la distribución porcentual de las asignaturas preferidas por un grupo de estudiantes. ¿Cuántos estudiantes prefieren la asignatura indicada?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Intermedio",
        None
    ))

    # 5. Quadratic Equation Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "Dada la ecuación cuadrática que se muestra a continuación, ¿cuál es la suma de las raíces de esta ecuación?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Intermedio",
        None
    ))

    # 6. Fractions Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "Calcule la suma de las siguientes fracciones y simplifique el resultado.",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Básico",
        None
    ))

    # 7. Median Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "El siguiente conjunto de datos ordenados representa las calificaciones obtenidas por un grupo de estudiantes en un examen. ¿Cuál es la mediana de este conjunto de datos?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Intermedio",
        None
    ))

    # 8. Mode Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "El siguiente conjunto de datos representa los puntajes de un grupo de estudiantes. ¿Cuál es la moda de este conjunto de datos?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Básico",
        None
    ))

    # 9. Exponential Function Question Template
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "Dada la función exponencial $f(x) = {a} \\cdot 2^{x {c_sign} {c_abs}} + {d}$, evalúe $f({x_eval})$.",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Avanzado",
        None
    ))

    # 10. Triangle Area Question Template
    tri_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" width="320" height="240">
  <rect width="100%" height="100%" rx="12" fill="#0f172a"/>
  <polygon points="50,200 270,200 270,60" fill="rgba(56, 189, 248, 0.1)" stroke="#38bdf8" stroke-width="2.5"/>
  <line x1="270" y1="200" x2="270" y2="60" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="5,5"/>
  <text x="160" y="220" fill="#38bdf8" font-family="Inter, sans-serif" font-size="14" font-weight="bold" text-anchor="middle">{base} cm</text>
  <text x="285" y="135" fill="#f43f5e" font-family="Inter, sans-serif" font-size="14" font-weight="bold" text-anchor="start">{altura} cm</text>
  <rect x="258" y="188" width="12" height="12" fill="none" stroke="#64748b" stroke-width="1.5"/>
</svg>"""
    tri_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(tri_svg.encode('utf-8')).decode('utf-8')
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "Halla el área del triángulo rectángulo que tiene una base de {base} cm y una altura de {altura} cm.",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Básico",
        tri_graphic_uri
    ))

    # 11. Bar Chart Question Template
    bar_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 220" width="320" height="220">
  <rect width="100%" height="100%" rx="12" fill="#0f172a"/>
  <text x="160" y="20" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="Inter, sans-serif">Distribución de puntajes</text>
  <line x1="40" y1="30" x2="40" y2="190" stroke="#475569" stroke-width="1.5"/>
  <line x1="40" y1="190" x2="300" y2="190" stroke="#475569" stroke-width="1.5"/>
  <rect x="55" y="{y_bar_1}" width="50" height="{h_bar_1}" rx="4" fill="#38bdf8"/>
  <text x="80" y="{y_txt_1}" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">{frec_1}</text>
  <text x="80" y="205" fill="#94a3b8" font-size="10" text-anchor="middle">10</text>
  <rect x="120" y="{y_bar_2}" width="50" height="{h_bar_2}" rx="4" fill="#f43f5e"/>
  <text x="145" y="{y_txt_2}" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">{frec_2}</text>
  <text x="145" y="205" fill="#94a3b8" font-size="10" text-anchor="middle">20</text>
  <rect x="185" y="{y_bar_3}" width="50" height="{h_bar_3}" rx="4" fill="#10b981"/>
  <text x="210" y="{y_txt_3}" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">{frec_3}</text>
  <text x="210" y="205" fill="#94a3b8" font-size="10" text-anchor="middle">30</text>
  <rect x="250" y="{y_bar_4}" width="50" height="{h_bar_4}" rx="4" fill="#fbbf24"/>
  <text x="275" y="{y_txt_4}" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">{frec_4}</text>
  <text x="275" y="205" fill="#94a3b8" font-size="10" text-anchor="middle">40</text>
</svg>"""
    bar_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(bar_svg.encode('utf-8')).decode('utf-8')
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "La gráfica de barras representa la distribución de puntajes obtenidos por un grupo de estudiantes en un examen de matemáticas. Con base en las frecuencias suministradas, ¿cuál es el promedio (media aritmética) de los puntajes?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Intermedio",
        bar_graphic_uri
    ))

    # 12. Cartesian Plane / Slope Question Template
    slope_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" width="320" height="240">
  <rect width="100%" height="100%" rx="12" fill="#0f172a"/>
  <line x1="50" y1="30" x2="50" y2="210" stroke="#475569" stroke-width="1.5"/>
  <line x1="30" y1="150" x2="290" y2="150" stroke="#475569" stroke-width="1.5"/>
  <text x="55" y="25" fill="#94a3b8" font-size="11" font-family="Inter, sans-serif">y</text>
  <text x="293" y="147" fill="#94a3b8" font-size="11" font-family="Inter, sans-serif">x</text>
  <text x="42" y="163" fill="#94a3b8" font-size="10" font-family="Inter, sans-serif">0</text>
  <line x1="50" y1="150" x2="{x2_svg}" y2="{y2_svg}" stroke="#38bdf8" stroke-width="2.5"/>
  <circle cx="50" cy="150" r="4" fill="#f43f5e"/>
  <circle cx="{x2_svg}" cy="{y2_svg}" r="4" fill="#10b981"/>
  <text x="{x2_lbl_svg}" y="{y2_lbl_svg}" fill="#10b981" font-size="12" font-family="Inter, sans-serif" font-weight="bold">P({a},{b})</text>
</svg>"""
    slope_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(slope_svg.encode('utf-8')).decode('utf-8')
    cursor.execute(f'''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, is_parametric)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {'1' if is_sqlite else 'TRUE'})
    ''', (
        "Matemáticas",
        "La imagen representa una recta en el plano cartesiano que pasa por el origen y por el punto P. ¿Cuál es el valor de la pendiente de esta recta?",
        json.dumps(["d1", "d2", "d3", "d4"]),
        "d1",
        "Procesado dinámicamente.",
        "Intermedio",
        slope_graphic_uri
    ))
    
    print("* Las 12 plantillas paramétricas insertadas con éxito.")
    
    # 3. Insert static questions (is_parametric = FALSE)
    print("Insertando las 10 preguntas estáticas de alta calidad...")
    inserted_static = 0
    for q in STATIC_QUESTIONS:
        cursor.execute(f'''
            INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, is_parametric)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {'0' if is_sqlite else 'FALSE'})
        ''', (
            q["area"], 
            q["text"], 
            json.dumps(q["options"], ensure_ascii=False), 
            q["correct_answer"], 
            q["explanation"], 
            q["difficulty"]
        ))
        inserted_static += 1
        
    conn.commit()
    conn.close()
    
    print(f"* {inserted_static} preguntas estáticas insertadas con éxito.")
    print("=== LIMPIEZA Y RESTAURACIÓN DE BASE DE DATOS COMPLETADA ===")

if __name__ == '__main__':
    purge_and_clean_db()
