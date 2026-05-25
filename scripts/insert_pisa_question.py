import sqlite3
import json
import base64

def insert_question():
    conn = sqlite3.connect('saber11.db')
    cursor = conn.cursor()

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240" width="320" height="240">
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
  <text x="110" y="125" fill="#3b82f6" font-family="sans-serif" font-size="12" font-weight="bold">4°</text>
  <path d="M 175 200 A 20 20 0 0 0 153 182" fill="none" stroke="#f43f5e" stroke-width="2.5" />
  <text x="135" y="185" fill="#f43f5e" font-family="sans-serif" font-size="16" font-weight="bold">?</text>
</svg>"""

    graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    text = "Con respecto a la vertical, la torre se ha inclinado 4° como se muestra en la gráfica. ¿Cuánto mide el otro ángulo (indicado con el signo de interrogación)?"
    
    options = [
      "4°",
      "14°",
      "86°",
      "90°"
    ]
    
    correct_answer = "86°"
    
    explanation = "La línea vertical de referencia es perpendicular al suelo, por lo que forma un ángulo recto de 90° con la horizontal. Como la inclinación de la torre es de 4° respecto a la vertical, el ángulo interno correspondiente entre la torre y la superficie disminuye en la misma cantidad. Así, calculamos: 90° - 4° = 86°."
    
    cursor.execute('''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Matemáticas",
        text,
        json.dumps(options, ensure_ascii=False),
        correct_answer,
        explanation,
        "Fácil",
        graphic_uri
    ))
    
    conn.commit()
    conn.close()
    print("Pregunta de la Torre de Pisa insertada exitosamente en la DB local.")

if __name__ == '__main__':
    insert_question()
