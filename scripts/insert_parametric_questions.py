import sqlite3
import json
import base64

def insert_questions():
    conn = sqlite3.connect('saber11.db')
    cursor = conn.cursor()

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
  <text x="110" y="125" fill="#3b82f6" font-family="sans-serif" font-size="12" font-weight="bold">{inclinacion}°</text>
  <path d="M 175 200 A 20 20 0 0 0 153 182" fill="none" stroke="#f43f5e" stroke-width="2.5" />
  <text x="135" y="185" fill="#f43f5e" font-family="sans-serif" font-size="16" font-weight="bold">?</text>
</svg>"""

    pisa_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(pisa_svg.encode('utf-8')).decode('utf-8')
    pisa_text = "Con respecto a la vertical, la torre se ha inclinado {inclinacion}° como se muestra en la gráfica. ¿Cuánto mide el otro ángulo (indicado con el signo de interrogación)?"
    pisa_explanation = "La línea vertical de referencia es perpendicular al suelo, por lo que forma un ángulo recto de 90°. Como la inclinación de la torre es de {inclinacion}° respecto a la vertical, el ángulo interno correspondiente entre la torre y la superficie disminuye en la misma cantidad: 90° - {inclinacion}° = {correct}°."

    cursor.execute('''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Matemáticas",
        pisa_text,
        json.dumps(["{inclinacion}°", "{correct}°", "90°", "180°"]), # Placeholders
        "{correct}°",
        pisa_explanation,
        "Fácil",
        pisa_graphic_uri
    ))

    # 2. Venn Diagram Question Template
    venn_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 220" width="400" height="220" style="background:#0f172a; border-radius:12px; padding:10px; max-width: 450px; border: 1px solid rgba(255, 255, 255, 0.1);">
  <rect width="100%" height="100%" fill="#0f172a"/>
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
    venn_text = "El siguiente diagrama de Venn representa la distribución de un grupo de estudiantes según sus preferencias deportivas entre Fútbol (F) y Baloncesto (B). Si se selecciona un estudiante al azar dentro del grupo, ¿cuál es la probabilidad de que prefiera únicamente Baloncesto?"
    venn_explanation = "Para hallar la probabilidad, sumamos los estudiantes del diagrama: {futbol_solo} (F) + {ambos} (F y B) + {baloncesto_solo} (B) + {ninguno} = {total} en total. Los que prefieren únicamente Baloncesto son {baloncesto_solo}, por lo que la probabilidad es {baloncesto_solo}/{total}, que simplificada equivale a {correct_frac}."

    cursor.execute('''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Matemáticas",
        venn_text,
        json.dumps(["{correct_frac}", "d1", "d2", "d3"]), # Placeholders
        "{correct_frac}",
        venn_explanation,
        "Intermedio",
        venn_graphic_uri
    ))

    conn.commit()
    conn.close()
    print("Preguntas paramétricas insertadas con éxito en la base de datos local.")

if __name__ == '__main__':
    insert_questions()
