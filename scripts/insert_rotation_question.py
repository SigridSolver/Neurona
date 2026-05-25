import sqlite3
import json
import base64

def insert_question():
    conn = sqlite3.connect('saber11.db')
    cursor = conn.cursor()

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 240" width="700" height="240">
  <style>
    .grid { stroke: rgba(148,163,184,0.15); stroke-width: 1; }
    .axis { stroke: #94a3b8; stroke-width: 2; }
    .label { fill: #94a3b8; font-family: sans-serif; font-size: 10px; font-weight: bold; }
    .title { fill: #cbd5e1; font-family: sans-serif; font-size: 12px; font-weight: bold; text-anchor: middle; }
    .shaded { fill: rgba(6,182,212,0.3); stroke: #06b6d4; stroke-width: 1.5; }
    .white { fill: rgba(255,255,255,0.05); stroke: #ffffff; stroke-width: 1.5; }
    .dot-shaded { fill: #000; }
    .dot-white { fill: #000; stroke: #fff; stroke-width: 0.5; }
  </style>

  <!-- ESTUDIANTE I -->
  <g transform="translate(10, 0)">
    <g class="grid">
      <line x1="20" y1="20" x2="20" y2="200" /><line x1="38" y1="20" x2="38" y2="200" /><line x1="56" y1="20" x2="56" y2="200" /><line x1="74" y1="20" x2="74" y2="200" /><line x1="92" y1="20" x2="92" y2="200" /><line x1="128" y1="20" x2="128" y2="200" /><line x1="146" y1="20" x2="146" y2="200" /><line x1="164" y1="20" x2="164" y2="200" /><line x1="182" y1="20" x2="182" y2="200" /><line x1="200" y1="20" x2="200" y2="200" />
      <line x1="20" y1="20" x2="200" y2="20" /><line x1="20" y1="38" x2="200" y2="38" /><line x1="20" y1="56" x2="200" y2="56" /><line x1="20" y1="74" x2="200" y2="74" /><line x1="20" y1="92" x2="200" y2="92" /><line x1="20" y1="128" x2="200" y2="128" /><line x1="20" y1="146" x2="200" y2="146" /><line x1="20" y1="164" x2="200" y2="164" /><line x1="20" y1="182" x2="200" y2="182" /><line x1="20" y1="200" x2="200" y2="200" />
    </g>
    <line x1="10" y1="110" x2="210" y2="110" class="axis" />
    <line x1="110" y1="10" x2="110" y2="210" class="axis" />
    <text x="212" y="114" class="label">x</text><text x="114" y="14" class="label">y</text>
    <polygon points="74,146 128,146 128,164 74,164" class="shaded" />
    <circle cx="74" cy="146" r="3" class="dot-shaded" /><circle cx="128" cy="146" r="3" class="dot-shaded" /><circle cx="128" cy="164" r="3" class="dot-shaded" /><circle cx="74" cy="164" r="3" class="dot-shaded" />
    <polygon points="56,74 74,74 74,128 56,128" class="white" />
    <circle cx="56" cy="74" r="3" class="dot-white" /><circle cx="74" cy="74" r="3" class="dot-white" /><circle cx="74" cy="128" r="3" class="dot-white" /><circle cx="56" cy="128" r="3" class="dot-white" />
    <text x="110" y="230" class="title">Estudiante I</text>
  </g>

  <!-- ESTUDIANTE II -->
  <g transform="translate(240, 0)">
    <g class="grid">
      <line x1="20" y1="20" x2="20" y2="200" /><line x1="38" y1="20" x2="38" y2="200" /><line x1="56" y1="20" x2="56" y2="200" /><line x1="74" y1="20" x2="74" y2="200" /><line x1="92" y1="20" x2="92" y2="200" /><line x1="128" y1="20" x2="128" y2="200" /><line x1="146" y1="20" x2="146" y2="200" /><line x1="164" y1="20" x2="164" y2="200" /><line x1="182" y1="20" x2="182" y2="200" /><line x1="200" y1="20" x2="200" y2="200" />
      <line x1="20" y1="20" x2="200" y2="20" /><line x1="20" y1="38" x2="200" y2="38" /><line x1="20" y1="56" x2="200" y2="56" /><line x1="20" y1="74" x2="200" y2="74" /><line x1="20" y1="92" x2="200" y2="92" /><line x1="20" y1="128" x2="200" y2="128" /><line x1="20" y1="146" x2="200" y2="146" /><line x1="20" y1="164" x2="200" y2="164" /><line x1="20" y1="182" x2="200" y2="182" /><line x1="20" y1="200" x2="200" y2="200" />
    </g>
    <line x1="10" y1="110" x2="210" y2="110" class="axis" />
    <line x1="110" y1="10" x2="110" y2="210" class="axis" />
    <text x="212" y="114" class="label">x</text><text x="114" y="14" class="label">y</text>
    <polygon points="110,38 110,56 146,128 146,74" class="shaded" />
    <circle cx="110" cy="38" r="3" class="dot-shaded" /><circle cx="110" cy="56" r="3" class="dot-shaded" /><circle cx="146" cy="128" r="3" class="dot-shaded" /><circle cx="146" cy="74" r="3" class="dot-shaded" />
    <polygon points="182,110 164,110 128,146 146,146" class="white" />
    <circle cx="182" cy="110" r="3" class="dot-white" /><circle cx="164" cy="110" r="3" class="dot-white" /><circle cx="128" cy="146" r="3" class="dot-white" /><circle cx="146" cy="146" r="3" class="dot-white" />
    <text x="110" y="230" class="title">Estudiante II</text>
  </g>

  <!-- ESTUDIANTE III -->
  <g transform="translate(470, 0)">
    <g class="grid">
      <line x1="20" y1="20" x2="20" y2="200" /><line x1="38" y1="20" x2="38" y2="200" /><line x1="56" y1="20" x2="56" y2="200" /><line x1="74" y1="20" x2="74" y2="200" /><line x1="92" y1="20" x2="92" y2="200" /><line x1="128" y1="20" x2="128" y2="200" /><line x1="146" y1="20" x2="146" y2="200" /><line x1="164" y1="20" x2="164" y2="200" /><line x1="182" y1="20" x2="182" y2="200" /><line x1="200" y1="20" x2="200" y2="200" />
      <line x1="20" y1="20" x2="200" y2="20" /><line x1="20" y1="38" x2="200" y2="38" /><line x1="20" y1="56" x2="200" y2="56" /><line x1="20" y1="74" x2="200" y2="74" /><line x1="20" y1="92" x2="200" y2="92" /><line x1="20" y1="128" x2="200" y2="128" /><line x1="20" y1="146" x2="200" y2="146" /><line x1="20" y1="164" x2="200" y2="164" /><line x1="20" y1="182" x2="200" y2="182" /><line x1="20" y1="200" x2="200" y2="200" />
    </g>
    <line x1="10" y1="110" x2="210" y2="110" class="axis" />
    <line x1="110" y1="10" x2="110" y2="210" class="axis" />
    <text x="212" y="114" class="label">x</text><text x="114" y="14" class="label">y</text>
    <polygon points="92,92 92,56 74,38 56,56" class="shaded" />
    <circle cx="92" cy="92" r="3" class="dot-shaded" /><circle cx="92" cy="56" r="3" class="dot-shaded" /><circle cx="74" cy="38" r="3" class="dot-shaded" /><circle cx="56" cy="56" r="3" class="dot-shaded" />
    <polygon points="128,92 155,65 155,42 128,42" class="white" />
    <circle cx="128" cy="92" r="3" class="dot-white" /><circle cx="155" cy="65" r="3" class="dot-white" /><circle cx="155" cy="42" r="3" class="dot-white" /><circle cx="128" cy="42" r="3" class="dot-white" />
    <text x="110" y="230" class="title">Estudiante III</text>
  </g>
</svg>"""

    # Encode graphic as Data URI
    graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    text = "Un profesor les asigna a tres estudiantes tres figuras distintas, y a cada uno le pide que rote la figura recibida 90° en el sentido en que giran las manecillas del reloj respecto al origen del sistema de coordenadas. La gráfica muestra las figuras recibidas por cada estudiante (sombreadas) y la figura obtenida (en blanco). ¿Cuáles estudiantes hicieron correctamente el trabajo asignado?"
    
    options = [
        "I y II solamente.",
        "II y III solamente.",
        "I y III solamente.",
        "I, II y III."
    ]
    
    correct_answer = "I y II solamente."
    
    explanation = "La rotación de 90° en sentido horario respecto al origen (0,0) sigue la regla (x, y) -> (y, -x). Evaluando los vértices de cada estudiante: Estudiante I tiene vértices correctos transformados de (-2, -2), (1, -2), (1, -3), (-2, -3) a (-2, 2), (-2, -1), (-3, -1), (-3, 2), coincidiendo con el rectángulo blanco. Estudiante II tiene vértices correctos transformados coincidiendo con el paralelogramo blanco. Estudiante III tiene vértices distorsionados (no rígidos) ya que (-2, 4) debería rotar a (4, 2) pero se dibuja en (2.5, 3.8). Por ende, I y II son correctos."
    
    cursor.execute('''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Matemáticas",
        text,
        json.dumps(options, ensure_ascii=False),
        correct_answer,
        explanation,
        "Intermedio",
        graphic_uri
    ))
    
    conn.commit()
    conn.close()
    print("Pregunta insertada exitosamente en la base de datos.")

if __name__ == '__main__':
    insert_question()
