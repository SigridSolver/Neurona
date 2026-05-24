import sqlite3
import json
from pathlib import Path

# Paths
DB_PATH = Path(__file__).parent.parent / "saber11.db"

def update_questions():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SVG definition for Question 1: Pentagon with houses I to V
    svg_q1 = """<svg viewBox="0 0 200 200" width="100%" style="max-width: 280px; margin: 1.5rem auto; display: block;">
  <!-- Connections -->
  <line x1="58.9" y1="156.6" x2="33.5" y2="78.4" stroke="#3b82f6" stroke-width="2.5" />
  <line x1="33.5" y1="78.4" x2="100" y2="30" stroke="#3b82f6" stroke-width="2.5" />
  <line x1="100" y1="30" x2="166.5" y2="78.4" stroke="#3b82f6" stroke-width="2.5" />
  <line x1="166.5" y1="78.4" x2="141.1" y2="156.6" stroke="#3b82f6" stroke-width="2.5" />
  <line x1="141.1" y1="156.6" x2="58.9" y2="156.6" stroke="#3b82f6" stroke-width="2.5" />
  
  <!-- Circle Vertices -->
  <!-- I -->
  <circle cx="58.9" cy="156.6" r="18" fill="#0f172a" stroke="#06b6d4" stroke-width="2" />
  <text x="58.9" y="162" font-family="'Outfit', sans-serif" font-size="14" fill="#f8fafc" text-anchor="middle" font-weight="bold">I</text>
  
  <!-- II -->
  <circle cx="33.5" cy="78.4" r="18" fill="#0f172a" stroke="#06b6d4" stroke-width="2" />
  <text x="33.5" y="83.8" font-family="'Outfit', sans-serif" font-size="14" fill="#f8fafc" text-anchor="middle" font-weight="bold">II</text>
  
  <!-- III -->
  <circle cx="100" cy="30" r="18" fill="#0f172a" stroke="#06b6d4" stroke-width="2" />
  <text x="100" y="35.4" font-family="'Outfit', sans-serif" font-size="14" fill="#f8fafc" text-anchor="middle" font-weight="bold">III</text>
  
  <!-- IV -->
  <circle cx="166.5" cy="78.4" r="18" fill="#0f172a" stroke="#06b6d4" stroke-width="2" />
  <text x="166.5" y="83.8" font-family="'Outfit', sans-serif" font-size="14" fill="#f8fafc" text-anchor="middle" font-weight="bold">IV</text>
  
  <!-- V -->
  <circle cx="141.1" cy="156.6" r="18" fill="#0f172a" stroke="#06b6d4" stroke-width="2" />
  <text x="141.1" y="162" font-family="'Outfit', sans-serif" font-size="14" fill="#f8fafc" text-anchor="middle" font-weight="bold">V</text>
</svg>"""

    # Grid generator helper to reuse code for Question 2
    def generate_grid_svg(shaded_points, white_points):
        return f"""<svg viewBox="0 0 220 220" width="100%" height="100%" style="background: rgba(15, 23, 42, 0.4); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); padding: 5px;">
  <!-- Grid Lines -->
  <path d="M 20 20 L 200 20 M 20 38 L 200 38 M 20 56 L 200 56 M 20 74 L 200 74 M 20 92 L 200 92 M 20 128 L 200 128 M 20 146 L 200 146 M 20 164 L 200 164 M 20 182 L 200 182 M 20 200 L 200 200" stroke="rgba(148, 163, 184, 0.12)" stroke-width="1" />
  <path d="M 20 20 L 20 200 M 38 20 L 38 200 M 56 20 L 56 200 M 74 20 L 74 200 M 92 20 L 92 200 M 128 20 L 128 200 M 146 20 L 146 200 M 164 20 L 164 200 M 182 20 L 182 200 M 200 20 L 200 200" stroke="rgba(148, 163, 184, 0.12)" stroke-width="1" />
  
  <!-- Main Axes -->
  <line x1="110" y1="10" x2="110" y2="210" stroke="#94a3b8" stroke-width="1.5" />
  <line x1="10" y1="110" x2="210" y2="110" stroke="#94a3b8" stroke-width="1.5" />
  
  <!-- Axis Arrows -->
  <polygon points="110,5 106,12 114,12" fill="#94a3b8" />
  <polygon points="215,110 208,106 208,114" fill="#94a3b8" />
  
  <!-- Axis Labels -->
  <text x="215" y="105" font-size="10" fill="#94a3b8" font-family="'Outfit', sans-serif" font-weight="bold">x</text>
  <text x="115" y="15" font-size="10" fill="#94a3b8" font-family="'Outfit', sans-serif" font-weight="bold">y</text>
  
  <!-- Tick numbers -->
  <text x="20" y="122" font-size="8" fill="#64748b" text-anchor="middle" font-family="sans-serif">-5</text>
  <text x="200" y="122" font-size="8" fill="#64748b" text-anchor="middle" font-family="sans-serif">5</text>
  <text x="102" y="23" font-size="8" fill="#64748b" text-anchor="end" font-family="sans-serif">5</text>
  <text x="102" y="203" font-size="8" fill="#64748b" text-anchor="end" font-family="sans-serif">-5</text>
  
  <!-- Shaded original shape -->
  <polygon points="{shaded_points}" fill="rgba(34, 211, 238, 0.4)" stroke="#06b6d4" stroke-width="2" />
  
  <!-- Rotated white shape -->
  <polygon points="{white_points}" fill="rgba(255, 255, 255, 0.85)" stroke="#ffffff" stroke-width="2" />
</svg>"""

    svg_grid_i = generate_grid_svg("74,146 128,146 128,164 74,164", "56,74 74,74 74,128 56,128")
    svg_grid_ii = generate_grid_svg("110,38 146,74 146,92 110,56", "164,110 182,110 146,146 128,146")
    svg_grid_iii = generate_grid_svg("56,56 74,38 92,56 92,92", "128,92 155,65 155,38 128,38")

    svg_q2 = f"""<div style="display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin: 1.5rem 0; width: 100%;">
  <div style="flex: 1; min-width: 180px; max-width: 220px; text-align: center; margin-bottom: 1rem;">
    {svg_grid_i}
    <div style="font-weight: bold; font-family: 'Outfit', sans-serif; font-size: 0.9rem; margin-top: 0.5rem; color: var(--text-main);">Estudiante I</div>
  </div>
  <div style="flex: 1; min-width: 180px; max-width: 220px; text-align: center; margin-bottom: 1rem;">
    {svg_grid_ii}
    <div style="font-weight: bold; font-family: 'Outfit', sans-serif; font-size: 0.9rem; margin-top: 0.5rem; color: var(--text-main);">Estudiante II</div>
  </div>
  <div style="flex: 1; min-width: 180px; max-width: 220px; text-align: center; margin-bottom: 1rem;">
    {svg_grid_iii}
    <div style="font-weight: bold; font-family: 'Outfit', sans-serif; font-size: 0.9rem; margin-top: 0.5rem; color: var(--text-main);">Estudiante III</div>
  </div>
</div>"""

    # Clean text and update Question 1 (ID 110)
    q1_text = (
        "Un pequeño conjunto cerrado tiene cinco casas formando un pentágono como se ve en la figura. "
        "Las casas están representadas por círculos.\n\n"
        "En el conjunto viven los señores Gómez, Hernández, López, Pérez y Vélez. Todas las casas del conjunto "
        "tienen una cantidad diferente de pisos. El señor Pérez lamenta que su casa sea considerada, según la ley, "
        "un edificio por tener cinco pisos, aunque también se alegra de tener la casa más alta del conjunto y no "
        "estar \"a la sombra de los demás\". ¿Cuál es el total de pisos construidos en el conjunto?"
    )
    q1_options = ["9", "15", "20", "25"]
    q1_correct = "15"
    q1_explanation = (
        "Dado que hay cinco casas en total, cada una con un número diferente de pisos, y la más alta tiene 5 pisos "
        "(la del señor Pérez), las alturas de las cinco casas deben ser necesariamente números enteros del 1 al 5 "
        "(1, 2, 3, 4 y 5). Sumando el número de pisos de todas las casas obtenemos: 1 + 2 + 3 + 4 + 5 = 15 pisos en total."
    )

    # Clean text and update Question 2 (ID 111)
    q2_text = (
        "Un profesor les asigna a tres estudiantes tres figuras distintas, y a cada uno le pide que rote "
        "la figura recibida 90° en el sentido en que giran las manecillas del reloj respecto al origen del sistema "
        "de coordenadas. La gráfica muestra las figuras recibidas por cada estudiante (sombreadas) y la figura "
        "obtenida (en blanco).\n\n"
        "¿Cuáles estudiantes hicieron correctamente el trabajo asignado?"
    )
    q2_options = ["I y II solamente.", "II y III solamente.", "I y III solamente.", "I, II y III."]
    q2_correct = "I y II solamente."
    q2_explanation = (
        "Para verificar la rotación de 90° en sentido horario respecto al origen (0,0), aplicamos la regla de "
        "transformación (x, y) -> (y, -x):\n\n"
        "- **Estudiante I:** Su rectángulo original tiene vértices en (-2,-2), (1,-2), (1,-3) y (-2,-3). "
        "Al rotarlos 90° en sentido horario, los nuevos vértices quedan en (-2,2), (-2,-1), (-3,-1) y (-3,2). "
        "Esto coincide exactamente con el rectángulo en blanco dibujado. **Hizo el trabajo correctamente.**\n"
        "- **Estudiante II:** Su paralelogramo original tiene vértices en (0,4), (2,2), (2,1) y (0,3). "
        "Al rotar 90° horario, los nuevos y correspondientes vértices son (4,0), (2,-2), (1,-2) y (3,0). "
        "Esto coincide exactamente con la figura en blanco representada. **Hizo el trabajo correctamente.**\n"
        "- **Estudiante III:** Al rotar sus vértices, la figura obtenida en blanco no corresponde con una rotación "
        "de 90° horario de la figura sombreada (las proporciones y la posición no coinciden). **Hizo el trabajo de forma incorrecta.**\n\n"
        "Por lo tanto, los estudiantes I y II realizaron la rotación de manera correcta."
    )

    print("Updating Question 1 (ID 110)...")
    cursor.execute(
        "UPDATE questions SET text = ?, options = ?, correct_answer = ?, explanation = ?, graphic = ? WHERE id = 110",
        (q1_text, json.dumps(q1_options, ensure_ascii=False), q1_correct, q1_explanation, svg_q1)
    )

    print("Updating Question 2 (ID 111)...")
    cursor.execute(
        "UPDATE questions SET text = ?, options = ?, correct_answer = ?, explanation = ?, graphic = ? WHERE id = 111",
        (q2_text, json.dumps(q2_options, ensure_ascii=False), q2_correct, q2_explanation, svg_q2)
    )

    conn.commit()
    conn.close()
    print("Database update completed successfully!")

if __name__ == "__main__":
    update_questions()
