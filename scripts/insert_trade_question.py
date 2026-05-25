import sqlite3
import json
import base64

def insert_question():
    conn = sqlite3.connect('saber11.db')
    cursor = conn.cursor()

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 160" width="360" height="160">
  <style>
    .border { stroke: #475569; stroke-width: 1.5; fill: none; }
    .grid { stroke: #334155; stroke-width: 1; }
    .header-bg { fill: #1e293b; }
    .cell-bg { fill: #0f172a; }
    .text { fill: #f8fafc; font-family: sans-serif; font-size: 11px; text-anchor: middle; }
    .header-text { fill: #38bdf8; font-weight: bold; }
  </style>
  <rect x="0" y="0" width="360" height="160" class="cell-bg" />
  <rect x="0" y="0" width="360" height="32" class="header-bg" />
  <line x1="60" y1="0" x2="60" y2="160" class="grid" />
  <line x1="210" y1="0" x2="210" y2="160" class="grid" />
  <line x1="0" y1="32" x2="360" y2="32" class="grid" />
  <line x1="0" y1="64" x2="360" y2="64" class="grid" />
  <line x1="0" y1="96" x2="360" y2="96" class="grid" />
  <line x1="0" y1="128" x2="360" y2="128" class="grid" />
  <rect x="0" y="0" width="360" height="160" class="border" />
  <text x="30" y="20" class="text header-text">País</text>
  <text x="135" y="20" class="text header-text">Vende a:</text>
  <text x="285" y="20" class="text header-text">Compra de:</text>
  <text x="30" y="52" class="text" font-weight="bold">P</text>
  <text x="135" y="52" class="text" font-style="italic">P, T</text>
  <text x="285" y="52" class="text" font-style="italic">S, V, P, W</text>
  <text x="30" y="84" class="text" font-weight="bold">Q</text>
  <text x="135" y="84" class="text" font-style="italic">U, Q, T, R</text>
  <text x="285" y="84" class="text" font-style="italic">V, Q</text>
  <text x="30" y="116" class="text" font-weight="bold">R</text>
  <text x="135" y="116" class="text" font-style="italic">T, R</text>
  <text x="285" y="116" class="text" font-style="italic">R, V, W, Q</text>
  <text x="30" y="148" class="text" font-weight="bold">S</text>
  <text x="135" y="148" class="text" font-style="italic">P, U, T, S</text>
  <text x="285" y="148" class="text" font-style="italic">S, V</text>
</svg>"""

    graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

    text = "La tabla muestra las relaciones de comercio, venta y compra de productos entre varios países. De acuerdo con la información presentada, ¿cuál es la tabla que muestra las relaciones comerciales del país W?"
    
    options = [
      "Vende productos a: Ninguno | Compra productos de: Ninguno",
      "Vende productos a: Ninguno | Compra productos de: P, R",
      "Vende productos a: P, R | Compra productos de: Ninguno",
      "Vende productos a: R, V, Q | Compra productos de: T, R"
    ]
    
    correct_answer = "Vende productos a: P, R | Compra productos de: Ninguno"
    
    explanation = "Para determinar las relaciones comerciales del país W, analizamos: 1. Ventas de W: Que W venda a otros países significa que esos países le compran a W. Revisando la columna 'Compra productos de:', vemos que P compra de (S, V, P, W) y R compra de (R, V, W, Q). Por tanto, W le vende a P y R. 2. Compras de W: Que W le compre a otros países significa que esos países le venden a W. Revisando la columna 'Vende productos a:', vemos que ningún país incluye a W en su lista de ventas. Por tanto, W compra de 'Ninguno'."
    
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
    print("Pregunta de Relaciones Comerciales insertada exitosamente en la DB local.")

if __name__ == '__main__':
    insert_question()
