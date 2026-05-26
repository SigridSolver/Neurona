# Copyright (c) 2026 David Saber 11
# Todos los derechos reservados.
# Licenciado bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from passlib.context import CryptContext
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import random
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
import base64
import io
from PIL import Image

# Validation patterns
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
NAME_REGEX = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]{3,50}$'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&.+-])[A-Za-z\d@$!%*?&.+-]{8,}$'

FORBIDDEN_NAMES = {
    "admin", "administrator", "administrador", "root", "moderador", "moderator",
    "david", "tutor", "soporte", "support", "test", "demo", "estudiante_test", "prueba"
}

VULGAR_WORDS = {
    "puto", "puta", "mierda", "pendejo", "pendeja", "maricon", "cabron", "cabrona", "hp", "hijueputa", "gonorrea", "culon", "culona"
}



def format_points_compact(pts: int) -> str:
    if pts is None:
        return "0"
    if pts >= 1000000:
        return f"{pts / 1000000:.1f}M".replace(".0", "")
    if pts >= 1000:
        return f"{pts / 1000:.1f}k".replace(".0", "")
    return str(pts)

def process_parametric_question(q, seed=None):
    if not q:
        return q
        
    text = q.get("text", "")
    graphic = q.get("graphic")
    options = q.get("options", [])
    explanation = q.get("explanation", "")
    
    placeholders = [
        "base", "altura", "inclinacion", "frec_1", "frec_2", "frec_3", "frec_4", 
        "futbol_solo", "ambos", "baloncesto_solo", "ninguno", "n_estudiantes", 
        "k_seleccionados", "a", "c_sign", "c_abs", "d", "x_eval", "slope", "x2_svg"
    ]
    if text:
        for p in placeholders:
            text = text.replace(f"{{{{{p}}}}}", f"{{{p}}}")
    if graphic and isinstance(graphic, str):
        if graphic.strip().startswith("<svg"):
            graphic = graphic.replace("{{", "{").replace("}}", "}")
            try:
                import base64 as b64mod
                graphic = "data:image/svg+xml;charset=utf-8;base64," + b64mod.b64encode(graphic.encode('utf-8')).decode('utf-8')
            except Exception as e:
                print("Error pre-encoding raw SVG:", e)
        elif "base64," in graphic and "charset=utf-8" not in graphic:
            graphic = graphic.replace("data:image/svg+xml;base64,", "data:image/svg+xml;charset=utf-8;base64,")
    if explanation:
        for p in placeholders:
            explanation = explanation.replace(f"{{{{{p}}}}}", f"{{{p}}}")
    if options and isinstance(options, list):
        new_opts = []
        for o in options:
            if isinstance(o, str):
                for p in placeholders:
                    o = o.replace(f"{{{{{p}}}}}", f"{{{p}}}")
            new_opts.append(o)
        options = new_opts
        
    q = dict(q)
    q["text"] = text
    q["graphic"] = graphic
    q["options"] = options
    q["explanation"] = explanation
    
    import random
    import base64
    from math import gcd
    
    local_random = random.Random(seed) if seed is not None else random.Random()
    
    if "{inclinacion}" in text:
        inclinacion = local_random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
        correct_val = 90 - inclinacion
        opts = [
            f"{inclinacion}°",
            f"{90 + inclinacion}°",
            f"{correct_val}°",
            "90°"
        ]
        local_random.shuffle(opts)
        correct_answer = f"{correct_val}°"
        new_text = text.format(inclinacion=inclinacion)
        
        explanation_tpl = q.get("explanation", "")
        if "{inclinacion}" in explanation_tpl:
            new_explanation = explanation_tpl.format(inclinacion=inclinacion, correct=correct_val)
        else:
            new_explanation = f"La línea vertical de referencia es perpendicular al suelo, por lo que forma un ángulo recto de 90°. Como la inclinación de la torre es de {inclinacion}° respecto a la vertical, el ángulo restante para llegar al suelo es 90° - {inclinacion}° = {correct_val}°."
            
        graphic = q.get("graphic")
        if graphic and "base64," in graphic:
            try:
                header, encoded = graphic.split("base64,", 1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                decoded = decoded.replace("{{", "{").replace("}}", "}")
                if "{inclinacion}" in decoded:
                    decoded = decoded.replace("{inclinacion}", str(inclinacion))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
            except Exception as e:
                print("Error processing parametric SVG graphic:", e)
                
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_answer,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    elif "{futbol_solo}" in text or "{baloncesto_solo}" in text or "diagrama de Venn" in text:
        futbol_solo = local_random.randint(10, 20)
        ambos = local_random.randint(5, 12)
        baloncesto_solo = local_random.randint(8, 18)
        ninguno = local_random.randint(4, 10)
        total = futbol_solo + ambos + baloncesto_solo + ninguno
        
        num = baloncesto_solo
        den = total
        divisor = gcd(num, den)
        simp_num = num // divisor
        simp_den = den // divisor
        correct_frac = f"{simp_num}/{simp_den}"
        
        d1_num = ambos // gcd(ambos, total)
        d1_den = total // gcd(ambos, total)
        d1 = f"{d1_num}/{d1_den}"
        if d1 == correct_frac: d1 = f"{(ambos+2)//gcd(ambos+2, total)}/{total//gcd(ambos+2, total)}"
        
        b_total = ambos + baloncesto_solo
        d2_num = b_total // gcd(b_total, total)
        d2_den = total // gcd(b_total, total)
        d2 = f"{d2_num}/{d2_den}"
        if d2 == correct_frac: d2 = f"{(b_total-1)//gcd(b_total-1, total)}/{total//gcd(b_total-1, total)}"
        
        b_f_sum = futbol_solo + baloncesto_solo
        d3_num = baloncesto_solo // gcd(baloncesto_solo, b_f_sum)
        d3_den = b_f_sum // gcd(baloncesto_solo, b_f_sum)
        d3 = f"{d3_num}/{d3_den}"
        if d3 == correct_frac: d3 = f"{(baloncesto_solo+1)//gcd(baloncesto_solo+1, b_f_sum)}/{b_f_sum//gcd(baloncesto_solo+1, b_f_sum)}"
        
        opts = [correct_frac, d1, d2, d3]
        unique_opts = []
        for o in opts:
            if o not in unique_opts:
                unique_opts.append(o)
                
        while len(unique_opts) < 4:
            random_num = local_random.randint(2, 9)
            random_den = local_random.randint(10, 30)
            g_val = gcd(random_num, random_den)
            opt_str = f"{random_num//g_val}/{random_den//g_val}"
            if opt_str not in unique_opts:
                unique_opts.append(opt_str)
                
        local_random.shuffle(unique_opts)
        
        new_text = f"El siguiente diagrama de Venn representa la distribución de un grupo de {total} estudiantes según sus preferencias deportivas entre Fútbol (F) y Baloncesto (B):\n\nSi se selecciona un estudiante al azar dentro del grupo evaluado, ¿cuál es la probabilidad de que este prefiera únicamente Baloncesto?"
        
        new_explanation = f"Para hallar la probabilidad, realizamos el siguiente análisis paso a paso:\n\n1. **Establecer el total del universo:** Sumamos todos los estudiantes distribuidos en el diagrama de Venn:\n$$\\text{{Total}} = {futbol_solo} \\text{{ (F únicamente)}} + {ambos} \\text{{ (Ambos)}} + {baloncesto_solo} \\text{{ (B únicamente)}} + {ninguno} \\text{{ (Ninguno)}} = {total} \\text{{ estudiantes.}}$$\n2. **Identificar los casos favorables:** El problema pide específicamente la probabilidad de que el estudiante prefiera **únicamente** Baloncesto. Esto corresponde a la región exclusiva del círculo B, que equivale a **{baloncesto_solo} estudiantes**.\n3. **Calcular y simplificar la probabilidad:**\n$$P(\\text{{Únicamente Baloncesto}}) = \\frac{{\\text{{Casos Favorables}}}}{{\\text{{Casos Totales}}}} = \\frac{{{baloncesto_solo}}}{{{total}}}$$\nSimplificando la fracción por el MCD ({divisor}) obtenemos la respuesta: **{correct_frac}**."
        
        graphic = q.get("graphic")
        if graphic and "base64," in graphic:
            try:
                header, encoded = graphic.split("base64,", 1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                decoded = decoded.replace("{{", "{").replace("}}", "}")
                decoded = decoded.replace("{futbol_solo}", str(futbol_solo))
                decoded = decoded.replace("{ambos}", str(ambos))
                decoded = decoded.replace("{baloncesto_solo}", str(baloncesto_solo))
                decoded = decoded.replace("{ninguno}", str(ninguno))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
            except Exception as e:
                print("Error processing parametric Venn SVG:", e)
                
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": unique_opts,
            "correct_answer": correct_frac,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    elif "{n_estudiantes}" in text or "preselección de estudiantes" in text or "{k_seleccionados}" in text:
        comb_options = [
            {"n": 5, "k": 3, "ans": 10, "distractors": [15, 60, 20]},
            {"n": 6, "k": 3, "ans": 20, "distractors": [18, 120, 30]},
            {"n": 7, "k": 3, "ans": 35, "distractors": [21, 210, 42]},
            {"n": 8, "k": 3, "ans": 56, "distractors": [24, 336, 70]},
            {"n": 6, "k": 2, "ans": 15, "distractors": [12, 30, 8]},
            {"n": 7, "k": 2, "ans": 21, "distractors": [14, 42, 18]},
            {"n": 8, "k": 4, "ans": 70, "distractors": [32, 1680, 56]}
        ]
        choice = local_random.choice(comb_options)
        n = choice["n"]
        k = choice["k"]
        correct_val = choice["ans"]
        distractors = choice["distractors"]
        
        opts = [str(correct_val)] + [str(d) for d in distractors]
        local_random.shuffle(opts)
        correct_answer = str(correct_val)
        
        new_text = "En un colegio se realiza una preselección de estudiantes para participar en las olimpiadas de matemáticas. De un grupo de {n_estudiantes} estudiantes destacados, el entrenador debe elegir a {k_seleccionados} de ellos para conformar el equipo oficial. ¿De cuántas formas diferentes se puede conformar el equipo?".format(n_estudiantes=n, k_seleccionados=k)
        
        prod_n_list = [str(n - i) for i in range(k)]
        prod_k_list = [str(k - i) for i in range(k)]
        prod_n_str = " \\times ".join(prod_n_list)
        prod_k_str = " \\times ".join(prod_k_list)
        
        new_explanation = (
            f"Para determinar de cuántas formas se puede conformar el equipo, debemos calcular el número de combinaciones de {n} estudiantes tomados de {k} en {k}, ya que el orden en que se seleccionan los miembros del equipo no importa.\n\n"
            "La fórmula para las combinaciones es:\n\n"
            "$$C_k^n = \\binom{n}{k} = \\frac{n!}{k!(n-k)!}$$\n\n"
            "Reemplazando los valores:\n\n"
            f"$$C_{{{k}}}^{{{n}}} = \\binom{{{n}}}{{{k}}} = \\frac{{{n}!}}{{{k}!({n}-{k})!}} = \\frac{{{prod_n_str}}}{{{prod_k_str}}} = {correct_val}$$\n\n"
            f"Por lo tanto, existen **{correct_val}** formas diferentes de conformar el equipo."
        )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_answer,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": q.get("graphic")
        }
        
    elif "{base}" in text and "{altura}" in text:
        base_val = local_random.choice([4, 6, 8, 10, 12, 14])
        altura_val = local_random.choice([3, 5, 7, 9, 11])
        
        is_triangle = "triángulo" in text.lower()
        if is_triangle:
            correct_val = (base_val * altura_val) / 2
            if correct_val.is_integer():
                correct_val = int(correct_val)
            correct_str = str(correct_val)
            formula_str = f"\\frac{{base \\times altura}}{{2}} = \\frac{{{base_val} \\times {altura_val}}}{{2}} = {correct_str}"
            distractors = [
                str(base_val * altura_val),
                str(base_val + altura_val),
                str(int((base_val * altura_val) / 2) + 5)
            ]
        else:
            correct_val = base_val * altura_val
            correct_str = str(correct_val)
            formula_str = f"base \\times altura = {base_val} \\times {altura_val} = {correct_str}"
            distractors = [
                str(int((base_val * altura_val) / 2)),
                str(base_val + altura_val),
                str(correct_val + 10)
            ]
            
        opts = [correct_str] + distractors
        opts = list(set(opts))
        while len(opts) < 4:
            opts.append(str(local_random.randint(10, 100)))
        local_random.shuffle(opts)
        
        new_text = text.format(base=base_val, altura=altura_val)
        
        new_explanation = "El área de la figura geométrica propuesta se calcula utilizando la fórmula estándar del área:\n\n"
        if is_triangle:
            new_explanation += f"$$A = \\frac{{b \\times h}}{{2}}$$\n\nReemplazando la base de {base_val} cm y la altura de {altura_val} cm:\n\n$$A = {formula_str} \\text{{ cm}}^2$$"
        else:
            new_explanation += f"$$A = b \\times h$$\n\nReemplazando la base de {base_val} cm y la altura de {altura_val} cm:\n\n$$A = {formula_str} \\text{{ cm}}^2$$"
            
        graphic = q.get("graphic")
        if graphic and "base64," in graphic:
            try:
                header, encoded = graphic.split("base64,", 1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                decoded = decoded.replace("{{", "{").replace("}}", "}")
                decoded = decoded.replace("{base}", str(base_val)).replace("{altura}", str(altura_val))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
            except Exception as e:
                print("Error processing parametric geometry SVG:", e)
                
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    elif "{x_eval}" in text:
        a = local_random.choice([2, 3, 5])
        b = 2
        c = local_random.choice([-1, 0, 1])
        d = local_random.choice([5, 10, 15, 20])
        x_eval = local_random.choice([1, 2, 3])
        
        exponent = x_eval + c
        correct_val = a * (b ** exponent) + d
        correct_str = str(correct_val)
        
        d1 = (a * b) ** exponent + d
        d2 = a * (b ** x_eval) + c + d
        d3 = correct_val + local_random.choice([10, -5, 25])
        
        opts = [correct_str, str(int(d1)), str(int(d2)), str(int(d3))]
        opts = list(set(opts))
        while len(opts) < 4:
            opts.append(str(local_random.randint(10, 500)))
        local_random.shuffle(opts)
        
        c_sign = "+" if c >= 0 else "-"
        c_abs = abs(c)
        new_text = text.format(
            a=a,
            c_sign=c_sign,
            c_abs=c_abs,
            d=d,
            x_eval=x_eval
        )
        
        new_explanation = (
            f"Para evaluar la función en el punto dado, sustituimos $x = {x_eval}$ en la expresión:\n\n"
            f"$$f({x_eval}) = {a} \\cdot 2^{{{x_eval} {c_sign} {c_abs}}} + {d}$$\n\n"
            "Resolvemos primero la operación en el exponente:\n\n"
            f"$$f({x_eval}) = {a} \\cdot 2^{{{exponent}}} + {d}$$\n\n"
            f"Evaluamos la potencia $2^{{{exponent}}} = {2**exponent}$:\n\n"
            f"$$f({x_eval}) = {a} \\cdot {2**exponent} + {d}$$\n\n"
            f"Multiplicamos por el coeficiente $a = {a}$ y sumamos la constante $d = {d}$:\n\n"
            f"$$f({x_eval}) = {a*2**exponent} + {d} = {correct_val}$$\n\n"
            f"Por lo tanto, la respuesta correcta es **{correct_str}**."
        )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": q.get("graphic")
        }
        
    elif "{frec_1}" in text or "frecuencias" in text.lower() or "gráfica de barras" in text.lower() or "grafica de barras" in text.lower() or "{val_1}" in text:
        val_1, val_2, val_3, val_4 = 10, 20, 30, 40
        frec_1 = local_random.randint(2, 6)
        frec_2 = local_random.randint(3, 8)
        frec_3 = local_random.randint(1, 5)
        frec_4 = local_random.randint(2, 6)
        
        total_n = frec_1 + frec_2 + frec_3 + frec_4
        sum_total = (val_1 * frec_1) + (val_2 * frec_2) + (val_3 * frec_3) + (val_4 * frec_4)
        
        mean_val = round(sum_total / total_n, 2)
        correct_str = f"{mean_val}"
        
        d1 = round((val_1 + val_2 + val_3 + val_4) / 4, 2)
        d2 = round(sum_total / (total_n + 2), 2)
        d3 = round(mean_val + local_random.choice([-1.5, 2.3, -3.2, 1.8]), 2)
        
        opts = [correct_str, f"{d1}", f"{d2}", f"{d3}"]
        opts = list(set(opts))
        while len(opts) < 4:
            opts.append(f"{round(local_random.uniform(15, 35), 2)}")
        local_random.shuffle(opts)
        
        new_text = (
            "La gráfica de barras representa la distribución de puntajes obtenidos por un grupo de estudiantes en un examen de matemáticas.\n\n"
            "Con base en la información suministrada en la gráfica, ¿cuál es el promedio (media aritmética) de los puntajes obtenidos por este grupo de estudiantes?"
        )
        
        new_explanation = (
            "Para hallar la media aritmética (promedio) de datos agrupados en una tabla de frecuencias, utilizamos la fórmula:\n\n"
            "$$\\mu = \\frac{\\sum (x_i \\cdot f_i)}{N}$$\n\n"
            "1. **Calcular la suma de todos los puntajes:**\n"
            f"$$\\sum (x_i \\cdot f_i) = ({val_1} \\cdot {frec_1}) + ({val_2} \\cdot {frec_2}) + ({val_3} \\cdot {frec_3}) + ({val_4} \\cdot {frec_4})$$\n"
            f"$$\\sum (x_i \\cdot f_i) = {val_1*frec_1} + {val_2*frec_2} + {val_3*frec_3} + {val_4*frec_4} = {sum_total}$$\n\n"
            "2. **Calcular el total de estudiantes (N):**\n"
            f"$$N = {frec_1} + {frec_2} + {frec_3} + {frec_4} = {total_n}$$\n\n"
            "3. **Calcular el promedio:**\n"
            f"$$\\mu = \\frac{{{sum_total}}}{{{total_n}}} \\approx {mean_val}$$\n\n"
            f"Por lo tanto, la media aritmética de los puntajes es aproximadamente **{correct_str}**."
        )
        
        graphic = q.get("graphic")
        if graphic and "base64," in graphic:
            try:
                header, encoded = graphic.split("base64,", 1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                decoded = decoded.replace("{{", "{").replace("}}", "}")
                decoded = (decoded
                           .replace("{frec_1}", str(frec_1))
                           .replace("{frec_2}", str(frec_2))
                           .replace("{frec_3}", str(frec_3))
                           .replace("{frec_4}", str(frec_4)))
                for i, fr in enumerate([frec_1, frec_2, frec_3, frec_4], 1):
                    h = fr * 20
                    y = 180 - h
                    y_txt = y - 5
                    decoded = (decoded
                               .replace(f"{{h_bar_{i}}}", str(h))
                               .replace(f"{{y_bar_{i}}}", str(y))
                               .replace(f"{{y_txt_{i}}}", str(y_txt)))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
            except Exception as e:
                print("Error processing parametric statistics SVG:", e)
                
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    elif "{slope}" in text or "plano cartesiano" in text.lower() or "{x2_svg}" in text:
        choices = [
            {"a": 3, "b": 2, "slope_str": "2/3", "distractors": ["3/2", "-2/3", "1/2"]},
            {"a": 4, "b": 3, "slope_str": "3/4", "distractors": ["4/3", "-3/4", "1/3"]},
            {"a": 5, "b": 2, "slope_str": "2/5", "distractors": ["5/2", "-2/5", "1/5"]},
            {"a": 4, "b": 1, "slope_str": "1/4", "distractors": ["4", "-1/4", "1/2"]},
            {"a": 5, "b": 3, "slope_str": "3/5", "distractors": ["5/3", "-3/5", "2/5"]}
        ]
        choice = local_random.choice(choices)
        a = choice["a"]
        b = choice["b"]
        correct_val = choice["slope_str"]
        distractors = choice["distractors"]
        
        opts = [correct_val] + distractors
        local_random.shuffle(opts)
        correct_str = correct_val
        
        x2_svg = 50 + a * 30
        y2_svg = 150 - b * 30
        x2_lbl_svg = x2_svg + 8
        y2_lbl_svg = y2_svg - 8
        
        new_text = (
            "La imagen representa una recta en el plano cartesiano que pasa por el origen $(0,0)$ y por el punto $P$.\n\n"
            "¿Cuál es el valor de la pendiente de esta recta?"
        )
        
        new_explanation = (
            "La pendiente $m$ de una recta que pasa por dos puntos $(x_1, y_1)$ y $(x_2, y_2)$ se calcula mediante la fórmula:\n\n"
            "$$m = \\frac{y_2 - y_1}{x_2 - x_1}$$\n\n"
            f"En este caso, la recta pasa por el origen $(0, 0)$ y por el punto $P({a}, {b})$. "
            f"Sustituyendo las coordenadas correspondientes:\n\n"
            f"$$m = \\frac{{{b} - 0}}{{{a} - 0}} = \\frac{{{b}}}{{{a}}}$$\n\n"
            f"Por lo tanto, la pendiente de la recta es **{correct_str}**."
        )
        
        graphic = q.get("graphic")
        if graphic and "base64," in graphic:
            try:
                header, encoded = graphic.split("base64,", 1)
                decoded = base64.b64decode(encoded).decode("utf-8")
                decoded = decoded.replace("{{", "{").replace("}}", "}")
                decoded = (decoded
                           .replace("{a}", str(a))
                           .replace("{b}", str(b))
                           .replace("{x2_svg}", str(x2_svg))
                           .replace("{y2_svg}", str(y2_svg))
                           .replace("{x2_lbl_svg}", str(x2_lbl_svg))
                           .replace("{y2_lbl_svg}", str(y2_lbl_svg)))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = "data:image/svg+xml;charset=utf-8;base64," + new_encoded
            except Exception as e:
                print("Error processing parametric coordinate plane SVG:", e)
                
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    elif "{sector_1}" in text or "gráfica circular" in text.lower() or "gráfica de torta" in text.lower():
        # PIE CHART / CIRCULAR GRAPH QUESTION
        sector_1 = local_random.randint(15, 35)
        sector_2 = local_random.randint(15, 30)
        sector_3 = local_random.randint(10, 25)
        sector_4 = 100 - sector_1 - sector_2 - sector_3
        if sector_4 < 5:
            sector_4 = 10
            sector_3 = 100 - sector_1 - sector_2 - sector_4

        labels = ["Matemáticas", "Español", "Ciencias", "Sociales"]
        values = [sector_1, sector_2, sector_3, sector_4]
        total_students = local_random.choice([80, 100, 120, 150, 200])
        
        ask_idx = local_random.randint(0, 3)
        correct_val = round(values[ask_idx] * total_students / 100)
        correct_str = str(correct_val)
        
        d1 = str(round(values[(ask_idx + 1) % 4] * total_students / 100))
        d2 = str(values[ask_idx])
        d3 = str(correct_val + local_random.choice([5, -3, 8, -7]))
        
        opts = list(set([correct_str, d1, d2, d3]))
        while len(opts) < 4:
            opts.append(str(local_random.randint(10, total_students)))
        local_random.shuffle(opts)
        
        import math
        angles = []
        cumulative = 0
        colors_pie = ["#38bdf8", "#f43f5e", "#10b981", "#fbbf24"]
        svg_paths = ""
        legend_items = ""
        for i, v in enumerate(values):
            start_angle = cumulative * 3.6
            sweep = v * 3.6
            cumulative += v
            
            start_rad = math.radians(start_angle - 90)
            end_rad = math.radians(start_angle + sweep - 90)
            
            cx, cy, r = 120, 120, 95
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)
            
            large_arc = 1 if sweep > 180 else 0
            
            svg_paths += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large_arc},1 {x2:.1f},{y2:.1f} Z" fill="{colors_pie[i]}" stroke="#0f172a" stroke-width="2"/>\n'
            
            mid_rad = math.radians(start_angle + sweep / 2 - 90)
            tx = cx + (r * 0.6) * math.cos(mid_rad)
            ty = cy + (r * 0.6) * math.sin(mid_rad)
            svg_paths += f'<text x="{tx:.1f}" y="{ty:.1f}" fill="white" font-size="12" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{v}%</text>\n'
            
            ly = 15 + i * 22
            legend_items += f'<rect x="260" y="{ly}" width="14" height="14" rx="3" fill="{colors_pie[i]}"/>\n'
            legend_items += f'<text x="280" y="{ly + 12}" fill="#cbd5e1" font-size="11" font-family="Inter, sans-serif">{labels[i]} ({v}%)</text>\n'
        
        pie_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" width="400" height="260">
  <rect width="100%" height="100%" rx="12" fill="#0f172a"/>
  <text x="200" y="252" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="Inter, sans-serif">Asignaturas preferidas por los estudiantes</text>
  {svg_paths}
  {legend_items}
</svg>'''
        
        import base64 as b64mod
        graphic = "data:image/svg+xml;charset=utf-8;base64," + b64mod.b64encode(pie_svg.encode("utf-8")).decode("utf-8")
        
        new_text = f"La siguiente gráfica circular muestra la distribución porcentual de las asignaturas preferidas por un grupo de {total_students} estudiantes.\n\n¿Cuántos estudiantes prefieren {labels[ask_idx]}?"
        
        new_explanation = (
            f"La gráfica circular muestra que **{labels[ask_idx]}** representa el **{values[ask_idx]}%** del total de estudiantes.\n\n"
            f"Para calcular el número de estudiantes que prefieren esta asignatura, aplicamos la regla de tres:\n\n"
            f"$$\\text{{Estudiantes}} = \\frac{{\\text{{Porcentaje}} \\times \\text{{Total}}}}{{100}} = \\frac{{{values[ask_idx]} \\times {total_students}}}{{100}} = {correct_val}$$\n\n"
            f"Por lo tanto, **{correct_val}** estudiantes prefieren {labels[ask_idx]}."
        )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
    
    elif "{a_cuad}" in text or "ecuación cuadrática" in text.lower() or "ecuación de segundo grado" in text.lower():
        # QUADRATIC EQUATION QUESTION
        a_c = local_random.choice([1, 2, 3])
        r1 = local_random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5])
        r2 = local_random.choice([-3, -2, -1, 1, 2, 3, 4])
        while r2 == r1:
            r2 = local_random.choice([-3, -2, -1, 1, 2, 3, 4])
        
        b_c = -a_c * (r1 + r2)
        c_c = a_c * r1 * r2
        discriminant = b_c**2 - 4*a_c*c_c
        
        sum_roots = r1 + r2
        correct_str = str(sum_roots)
        
        d1 = str(r1 * r2)
        d2 = str(sum_roots + local_random.choice([1, -1, 2]))
        d3 = str(-sum_roots)
        
        opts = list(set([correct_str, d1, d2, d3]))
        while len(opts) < 4:
            opts.append(str(local_random.randint(-10, 10)))
        local_random.shuffle(opts)
        
        b_sign = "+" if b_c >= 0 else "-"
        c_sign = "+" if c_c >= 0 else "-"
        a_str = "" if a_c == 1 else str(a_c)
        
        new_text = f"Dada la ecuación cuadrática:\n\n$${a_str}x^2 {b_sign} {abs(b_c)}x {c_sign} {abs(c_c)} = 0$$\n\n¿Cuál es la suma de las raíces de esta ecuación?"
        
        new_explanation = (
            f"Para una ecuación cuadrática de la forma $ax^2 + bx + c = 0$, la suma de las raíces está dada por la relación de Vieta:\n\n"
            f"$$x_1 + x_2 = -\\frac{{b}}{{a}}$$\n\n"
            f"En nuestra ecuación, $a = {a_c}$ y $b = {b_c}$. Sustituyendo:\n\n"
            f"$$x_1 + x_2 = -\\frac{{{b_c}}}{{{a_c}}} = {sum_roots}$$\n\n"
            f"Verificación: Las raíces son $x_1 = {r1}$ y $x_2 = {r2}$.\n\n"
            f"$$x_1 + x_2 = {r1} + {'' if r2 < 0 else ''}{r2} = {sum_roots}$$\n\n"
            f"Por lo tanto, la suma de las raíces es **{sum_roots}**."
        )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": q.get("graphic")
        }
    
    elif "{num_1}" in text or "fracción" in text.lower() or "fracciones" in text.lower():
        # FRACTIONS QUESTION
        num_1 = local_random.randint(1, 7)
        den_1 = local_random.choice([2, 3, 4, 5, 6, 8])
        num_2 = local_random.randint(1, 7)
        den_2 = local_random.choice([2, 3, 4, 5, 6, 8])
        while den_2 == den_1:
            den_2 = local_random.choice([2, 3, 4, 5, 6, 8])
        
        op = local_random.choice(["suma", "resta"])
        
        result_num = num_1 * den_2 + num_2 * den_1 if op == "suma" else num_1 * den_2 - num_2 * den_1
        result_den = den_1 * den_2
        
        g = gcd(abs(result_num), result_den)
        simp_num = result_num // g
        simp_den = result_den // g
        
        if simp_den < 0:
            simp_num = -simp_num
            simp_den = -simp_den
        
        correct_str = f"{simp_num}/{simp_den}"
        
        d1_n = simp_num + local_random.choice([1, -1, 2])
        d1 = f"{d1_n}/{simp_den}"
        d2 = f"{num_1 + num_2}/{den_1 + den_2}"
        d3_n = simp_num * 2
        d3_d = simp_den
        d3_g = gcd(abs(d3_n), abs(d3_d))
        d3 = f"{d3_n // d3_g}/{d3_d // d3_g}"
        
        opts = list(set([correct_str, d1, d2, d3]))
        while len(opts) < 4:
            rn = local_random.randint(1, 15)
            rd = local_random.randint(2, 12)
            rg = gcd(rn, rd)
            opts.append(f"{rn // rg}/{rd // rg}")
            opts = list(set(opts))
        local_random.shuffle(opts)
        
        op_symbol = "+" if op == "suma" else "-"
        op_word = "la suma" if op == "suma" else "la resta"
        
        new_text = f"Calcule {op_word} de las siguientes fracciones:\n\n$$\\frac{{{num_1}}}{{{den_1}}} {op_symbol} \\frac{{{num_2}}}{{{den_2}}}$$"
        
        cross_1 = num_1 * den_2
        cross_2 = num_2 * den_1
        
        new_explanation = (
            f"Para {op_word} de fracciones con diferente denominador, primero hallamos el denominador común:\n\n"
            f"$$\\frac{{{num_1}}}{{{den_1}}} {op_symbol} \\frac{{{num_2}}}{{{den_2}}} = \\frac{{{num_1} \\times {den_2}}}{{{den_1} \\times {den_2}}} {op_symbol} \\frac{{{num_2} \\times {den_1}}}{{{den_2} \\times {den_1}}}$$\n\n"
            f"$$= \\frac{{{cross_1}}}{{{result_den}}} {op_symbol} \\frac{{{cross_2}}}{{{result_den}}} = \\frac{{{cross_1} {op_symbol} {cross_2}}}{{{result_den}}} = \\frac{{{result_num}}}{{{result_den}}}$$\n\n"
            f"Simplificando por el MCD ({g}):\n\n"
            f"$$= \\frac{{{simp_num}}}{{{simp_den}}}$$\n\n"
            f"La respuesta correcta es **{correct_str}**."
        )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": q.get("graphic")
        }
    
    elif "{dato_1}" in text or "mediana" in text.lower() or "moda de" in text.lower():
        # STATISTICAL DATA TABLE - MEDIAN/MODE QUESTION
        n_data = local_random.choice([7, 9, 11])
        data_set = sorted([local_random.randint(2, 30) for _ in range(n_data)])
        
        ask_type = local_random.choice(["mediana", "moda"])
        
        if ask_type == "moda":
            mode_val = local_random.choice(data_set)
            extra_copies = local_random.randint(1, 2)
            for _ in range(extra_copies):
                data_set.append(mode_val)
            data_set.sort()
            
            from collections import Counter
            freq = Counter(data_set)
            mode_val = freq.most_common(1)[0][0]
            correct_str = str(mode_val)
        else:
            mid = len(data_set) // 2
            median_val = data_set[mid]
            correct_str = str(median_val)
        
        d1 = str(data_set[0])
        d2 = str(data_set[-1])
        d3 = str(round(sum(data_set) / len(data_set), 1))
        
        opts = list(set([correct_str, d1, d2, d3]))
        while len(opts) < 4:
            opts.append(str(local_random.choice(data_set) + local_random.choice([1, -1, 2])))
            opts = list(set(opts))
        local_random.shuffle(opts)
        
        data_str = ", ".join(str(d) for d in data_set)
        
        # Build an SVG table for the data
        cols = len(data_set)
        cell_w = max(35, 320 // cols)
        table_w = cell_w * cols + 20
        svg_table = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {table_w} 90" width="{table_w}" height="90">
  <rect width="100%" height="100%" rx="10" fill="#0f172a"/>
  <text x="{table_w // 2}" y="18" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="Inter, sans-serif">Conjunto de datos ordenados</text>'''
        
        for i, d in enumerate(data_set):
            x = 10 + i * cell_w
            svg_table += f'\n  <rect x="{x}" y="28" width="{cell_w - 2}" height="24" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1"/>'
            svg_table += f'\n  <text x="{x + cell_w // 2}" y="45" fill="#38bdf8" font-size="13" font-weight="bold" text-anchor="middle" font-family="Inter, sans-serif">{d}</text>'
            svg_table += f'\n  <text x="{x + cell_w // 2}" y="74" fill="#64748b" font-size="9" text-anchor="middle" font-family="Inter, sans-serif">x{chr(8321 + i) if i < 9 else "₊"}</text>'
        
        svg_table += '\n</svg>'
        
        import base64 as b64mod
        graphic = "data:image/svg+xml;base64," + b64mod.b64encode(svg_table.encode("utf-8")).decode("utf-8")
        
        if ask_type == "mediana":
            new_text = f"El siguiente conjunto de datos ordenados representa las calificaciones obtenidas por un grupo de {len(data_set)} estudiantes en un examen.\n\n¿Cuál es la **mediana** de este conjunto de datos?"
            mid = len(data_set) // 2
            new_explanation = (
                f"La **mediana** es el valor central de un conjunto de datos ordenados.\n\n"
                f"El conjunto tiene **{len(data_set)}** datos (impar), por lo tanto la mediana es el dato en la posición:\n\n"
                f"$$\\text{{Posición}} = \\frac{{n+1}}{{2}} = \\frac{{{len(data_set)}+1}}{{2}} = {(len(data_set) + 1) // 2}$$\n\n"
                f"Los datos ordenados son: ${data_str}$\n\n"
                f"El valor en la posición {(len(data_set) + 1) // 2} es **{data_set[mid]}**.\n\n"
                f"Por lo tanto, la mediana es **{correct_str}**."
            )
        else:
            from collections import Counter
            freq = Counter(data_set)
            mode_count = freq[mode_val]
            new_text = f"El siguiente conjunto de datos representa las calificaciones obtenidas por un grupo de {len(data_set)} estudiantes.\n\n¿Cuál es la **moda** de este conjunto de datos?"
            new_explanation = (
                f"La **moda** es el dato que más se repite en un conjunto de datos.\n\n"
                f"Los datos son: ${data_str}$\n\n"
                f"Analizando las frecuencias, el valor **{mode_val}** aparece **{mode_count} veces**, siendo el dato con mayor frecuencia.\n\n"
                f"Por lo tanto, la moda es **{correct_str}**."
            )
        
        return {
            "id": q["id"],
            "area": q["area"],
            "text": new_text,
            "options": opts,
            "correct_answer": correct_str,
            "explanation": new_explanation,
            "difficulty": q["difficulty"],
            "graphic": graphic
        }
        
    return q

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize App
app = FastAPI(title="David Saber 11")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "tu_clave_super_secreta_aqui"))

@app.on_event("startup")
def on_startup():
    from app.database import init_db
    try:
        init_db()
        print("Database auto-migrated on startup!")
    except Exception as e:
        print("Error auto-migrating database on startup:", e)

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("DB_PATH", BASE_DIR.parent / "saber11.db")

# Mount Static and Templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB Helper
class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()
        
    def cursor(self):
        return self.conn.cursor()

def get_db():
    import os
    url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.DictCursor)
    
    return PostgresConnWrapper(conn)

# Mock Authentication (For MVP, using simple cookie sessions)
# In production, use JWT or proper session management.
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    if user:
        from datetime import datetime
        try:
            conn.execute("UPDATE users SET last_seen = %s WHERE id = %s", (datetime.now(), user_id))
            conn.commit()
        except Exception as e:
            print("Error updating last_seen:", e)
    conn.close()
    return user

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="landing.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
    conn.close()
    
    if not user or not pwd_context.verify(password, user["password_hash"]):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Credenciales inválidas"})
    
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    request.session["user_id"] = user["id"]
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    guest_cookie = request.cookies.get("guest_diagnostic")
    guest_mode = guest_cookie is not None
    return templates.TemplateResponse(request=request, name="register.html", context={"guest_mode": guest_mode})

@app.post("/register")
async def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    name_clean = name.strip()
    email_clean = email.strip()
    
    # 1. Validar nombre (solo letras y espacios, largo 3 a 50)
    if not re.match(NAME_REGEX, name_clean):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El nombre debe tener entre 3 y 50 caracteres y contener solo letras."})
        
    # 2. Validar nombres prohibidos y palabras vulgares
    words = name_clean.lower().split()
    if any(w in FORBIDDEN_NAMES or w in VULGAR_WORDS for w in words):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El nombre contiene términos no permitidos o palabras reservadas."})
        
    # 3. Validar email
    if not re.match(EMAIL_REGEX, email_clean):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Por favor ingrese un correo electrónico válido."})
        
    # 4. Validar contraseña
    if not re.match(PASSWORD_REGEX, password):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "La contraseña debe tener mínimo 8 caracteres, al menos una letra mayúscula, una minúscula, un número y un carácter especial."})

    # 5. Check if user already exists
    conn = get_db()
    existing_user = conn.execute("SELECT id FROM users WHERE email = %s", (email_clean,)).fetchone()
    if existing_user:
        conn.close()
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El correo ya está registrado."})

    hashed_pwd = pwd_context.hash(password)
    try:
        cursor = conn.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id", (name_clean, email_clean, hashed_pwd))
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        # Save guest diagnostic results if they exist in cookies
        guest_cookie = request.cookies.get("guest_diagnostic")
        response = RedirectResponse(url="/dashboard", status_code=303)
        if guest_cookie:
            try:
                scores = json.loads(guest_cookie)
                math_avg = (scores["math1"] + scores["math2"]) // 2
                reading_avg = (scores["reading1"] + scores["reading2"]) // 2
                social_avg = (scores["social1"] + scores["social2"]) // 2
                science_avg = (scores["science1"] + scores["science2"]) // 2
                english_avg = (scores["english1"] + scores["english2"]) // 2
                
                s_math = map_diagnostic_score(math_avg)
                s_reading = map_diagnostic_score(reading_avg)
                s_social = map_diagnostic_score(social_avg)
                s_science = map_diagnostic_score(science_avg)
                s_english = map_diagnostic_score(english_avg)
                
                cursor.execute('''
                    INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, s_math, s_reading, s_social, s_science, s_english))
                conn.commit()
                response.delete_cookie("guest_diagnostic")
            except Exception:
                pass
                
        conn.close()
        request.session["user_id"] = user_id
        return response
    except psycopg2.IntegrityError:
        conn.close()
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El correo ya está registrado."})



@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    request.session.clear()
    return response

def map_diagnostic_score(value: int) -> int:
    if value == 100:
        return random.randint(70, 90)
    else:
        return random.randint(30, 48)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    
    # --- STREAK (RACHA DIARIA) UPDATE ---
    from datetime import date, timedelta
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    user_id = user["id"]
    streak = user["streak"] if user["streak"] is not None else 0
    last_active = user["last_active_date"]
    
    if last_active is None:
        streak = 1
        conn.execute("UPDATE users SET streak = %s, last_active_date = %s WHERE id = %s", (streak, today_str, user_id))
        conn.commit()
    elif last_active == yesterday_str:
        streak += 1
        conn.execute("UPDATE users SET streak = %s, last_active_date = %s WHERE id = %s", (streak, today_str, user_id))
        conn.commit()
    elif last_active != today_str:
        streak = 1
        conn.execute("UPDATE users SET streak = %s, last_active_date = %s WHERE id = %s", (streak, today_str, user_id))
        conn.commit()
        
    # Get updated user record
    user = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    # ------------------------------------
    
    diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
    
    proficiency = {}
    global_score = None
    
    if diagnostic:
        proficiency = {
            "Matemáticas": diagnostic["score_math"],
            "Lectura Crítica": diagnostic["score_reading"],
            "Ciencias Naturales": diagnostic["score_science"],
            "Sociales y Ciudadanas": diagnostic["score_social"],
            "Inglés": diagnostic["score_english"]
        }
        
        # Calculate dynamic proficiency based on practice sessions
        for area in proficiency.keys():
            practice_stats = conn.execute('''
                SELECT SUM(score) as correct, SUM(total_questions) as total 
                FROM practice_sessions 
                WHERE user_id = %s AND area = %s
            ''', (user["id"], area)).fetchone()
            
            if practice_stats and practice_stats["total"] and practice_stats["total"] > 0:
                avg_pct = (practice_stats["correct"] / practice_stats["total"]) * 100
                proficiency[area] = round(proficiency[area] * 0.6 + avg_pct * 0.4)
                
        # Saber 11 weighted global score formula
        weighted_sum = (
            proficiency["Matemáticas"] * 3 +
            proficiency["Lectura Crítica"] * 3 +
            proficiency["Ciencias Naturales"] * 3 +
            proficiency["Sociales y Ciudadanas"] * 3 +
            proficiency["Inglés"] * 1
        )
        global_score = round((weighted_sum / 13) * 5)
        
    practice_history = conn.execute("SELECT * FROM practice_sessions WHERE user_id = %s ORDER BY date DESC LIMIT 5", (user["id"],)).fetchall()
    
    # Query leaderboard (top 5 users ranked by estimated global score)
    leaderboard = []
    try:
        leaderboard_rows = conn.execute('''
            SELECT u.id, u.name, u.avatar_color, u.bio, u.badges, u.streak, 
                   d.score_math, d.score_reading, d.score_science, d.score_social, d.score_english
            FROM users u
            JOIN diagnostic_results d ON u.id = d.user_id
        ''').fetchall()
        
        user_max_scores = {}
        for row in leaderboard_rows:
            w_sum = (
                row["score_math"] * 3 +
                row["score_reading"] * 3 +
                row["score_science"] * 3 +
                row["score_social"] * 3 +
                row["score_english"] * 1
            )
            score = round((w_sum / 13) * 5)
            uid = row["id"]
            
            if uid not in user_max_scores or score > user_max_scores[uid]["score"]:
                try:
                    badges_list = json.loads(row["badges"]) if row["badges"] else []
                except Exception:
                    badges_list = []
                    
                user_max_scores[uid] = {
                    "id": uid,
                    "name": row["name"],
                    "score": score,
                    "avatar_color": row["avatar_color"] or "#3b82f6",
                    "bio": row["bio"] or "",
                    "streak": row["streak"] or 0,
                    "badges": badges_list
                }
                
        leaderboard = sorted(user_max_scores.values(), key=lambda x: x["score"], reverse=True)[:5]
    except Exception as e:
        print("Error al calcular el ranking:", e)
        
    conn.close()
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "user": user, 
        "diagnostic": diagnostic,
        "proficiency": proficiency,
        "global_score": global_score,
        "history": practice_history,
        "leaderboard": leaderboard
    })


@app.get("/diagnostico", response_class=HTMLResponse)
async def diagnostico_page(request: Request):
    # Guest mode is allowed, so we do not redirect to login
    return templates.TemplateResponse(request=request, name="diagnostico.html")

@app.post("/diagnostico")
async def submit_diagnostico(
    request: Request, 
    math1: int = Form(...), 
    math2: int = Form(...), 
    reading1: int = Form(...), 
    reading2: int = Form(...), 
    social1: int = Form(...), 
    social2: int = Form(...), 
    science1: int = Form(...), 
    science2: int = Form(...), 
    english1: int = Form(...), 
    english2: int = Form(...)
):
    user = get_current_user(request)
    
    if user:
        # User is logged in, calculate averages and save to DB
        math_avg = (math1 + math2) // 2
        reading_avg = (reading1 + reading2) // 2
        social_avg = (social1 + social2) // 2
        science_avg = (science1 + science2) // 2
        english_avg = (english1 + english2) // 2

        s_math = map_diagnostic_score(math_avg)
        s_reading = map_diagnostic_score(reading_avg)
        s_social = map_diagnostic_score(social_avg)
        s_science = map_diagnostic_score(science_avg)
        s_english = map_diagnostic_score(english_avg)
        
        conn = get_db()
        conn.execute('''
            INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user["id"], s_math, s_reading, s_social, s_science, s_english))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # Guest user, save raw answers to a cookie and redirect to /register
        response = RedirectResponse(url="/register", status_code=303)
        scores = {
            "math1": math1, "math2": math2,
            "reading1": reading1, "reading2": reading2,
            "social1": social1, "social2": social2,
            "science1": science1, "science2": science2,
            "english1": english1, "english2": english2
        }
        response.set_cookie(key="guest_diagnostic", value=json.dumps(scores), httponly=True)
        return response



@app.get("/practica", response_class=HTMLResponse)
async def practica_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
    
    has_simulacro = False
    eligible_for_tips = False
    max_score = 0
    if diagnostic:
        has_simulacro = True
        weighted_sum = (
            diagnostic["score_math"] * 3 +
            diagnostic["score_reading"] * 3 +
            diagnostic["score_science"] * 3 +
            diagnostic["score_social"] * 3 +
            diagnostic["score_english"] * 1
        )
        max_score = round((weighted_sum / 13) * 5)
        if max_score > 250:
            eligible_for_tips = True
            
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="practica.html",
        context={
            "user": user,
            "has_simulacro": has_simulacro,
            "eligible_for_tips": eligible_for_tips,
            "max_score": max_score
        }
    )

@app.get("/api/questions/{question_id}/hint")
async def get_question_hint(question_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    conn = get_db()
    try:
        # Check eligibility
        diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
        eligible = False
        if diagnostic:
            weighted_sum = (
                diagnostic["score_math"] * 3 +
                diagnostic["score_reading"] * 3 +
                diagnostic["score_science"] * 3 +
                diagnostic["score_social"] * 3 +
                diagnostic["score_english"] * 1
            )
            score = round((weighted_sum / 13) * 5)
            if score > 250:
                eligible = True
                
        if not eligible:
            raise HTTPException(status_code=403, detail="No elegible para recibir tips de estudio.")
            
        # Fetch question
        q = conn.execute("SELECT area, text, options, correct_answer, explanation FROM questions WHERE id = %s", (question_id,)).fetchone()
        if not q:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada.")
            
        # Call Gemini for a smart hint
        api_key = os.getenv("GEMINI_API_KEY")
        hint_text = ""
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.1-flash-lite')
                prompt = f"""
                Eres un tutor académico experto para el examen Saber 11 en Colombia.
                Para la siguiente pregunta de {q['area']}:
                Enunciado: {q['text']}
                Opciones: {q['options']}
                Respuesta Correcta: {q['correct_answer']}
                
                Genera una AYUDA o TIP de estudio muy breve y pedagógico (máximo 2 líneas o 30 palabras) para que el estudiante pueda resolverla por sí mismo.
                REGLA CRÍTICA: NO menciones cuál es la respuesta correcta ni reveles la clave. Da un consejo de descarte o concepto clave. Responde en español de forma motivadora y amigable.
                """
                response = model.generate_content(prompt)
                hint_text = response.text.strip()
            except Exception as e:
                print("Error generating hint with Gemini:", e)
                
        if not hint_text:
            # Fallback hint
            hint_text = f"Tip de {q['area']}: Recuerda analizar con cuidado los descartes lógicos del enunciado y justificar tu respuesta con base en la teoría del área."
            
        return {"hint": hint_text}
    finally:
        conn.close()


@app.get("/api/questions/{area}")
async def get_practice_questions(area: str):
    conn = get_db()
    # Query 20 random questions matching the selected area
    rows = conn.execute(
        "SELECT id, area, text, options, correct_answer, explanation, difficulty, graphic FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 20",
        (area,)
    ).fetchall()
    
    questions = []
    for r in rows:
        try:
            opts = json.loads(r["options"])
        except Exception:
            opts = [r["correct_answer"], "Opción B", "Opción C", "Opción D"]
            
        q_obj = {
            "id": r["id"],
            "area": r["area"],
            "text": r["text"],
            "options": opts,
            "correct_answer": r["correct_answer"],
            "explanation": r["explanation"],
            "difficulty": r["difficulty"],
            "graphic": r["graphic"]
        }
        q_obj = process_parametric_question(q_obj)
        questions.append(q_obj)
        
    needed = 20 - len(questions)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if needed > 0 and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.1-flash-lite')
            cursor = conn.cursor()
            
            if area == "Matemáticas":
                prompt = f"""
                Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia para el área de Matemáticas.
                Genera una lista de {needed} preguntas de selección múltiple originales, inéditas, altamente didácticas y visuales.
                
                IMPORTANTE: Cada pregunta DEBE ser de una CATEGORÍA DIFERENTE. Selecciona aleatoriamente entre estas categorías:
                
                CATEGORÍA 1 - GRÁFICA CIRCULAR (TORTA):
                - Palabra clave en el enunciado: "gráfica circular" o "gráfica de torta"
                - Contexto: distribución porcentual de datos (asignaturas, deportes, preferencias)
                - SVG: Gráfico de pastel con sectores de colores (#38bdf8, #f43f5e, #10b981, #fbbf24), fondo oscuro (#0f172a), porcentajes dentro de cada sector, y leyenda lateral
                - Pregunta: calcular la cantidad real a partir de un porcentaje dado
                
                CATEGORÍA 2 - GRÁFICA DE BARRAS / HISTOGRAMA:
                - Palabra clave: "frecuencias" o incluir placeholders {{{{frec_1}}}}, {{{{frec_2}}}}, {{{{frec_3}}}}, {{{{frec_4}}}}
                - SVG: Barras verticales con etiquetas de valor, ejes X/Y, colores vibrantes
                - Pregunta: calcular media aritmética, rango o total
                
                CATEGORÍA 3 - DIAGRAMA DE VENN:
                - Palabra clave: "diagrama de Venn" e incluir placeholders {{{{futbol_solo}}}}, {{{{baloncesto_solo}}}}, {{{{ambos}}}}, {{{{ninguno}}}}
                - SVG: Dos círculos superpuestos con valores en cada región, fondo oscuro
                - Pregunta: probabilidad de un evento específico
                
                CATEGORÍA 4 - PLANO CARTESIANO:
                - Palabra clave: "plano cartesiano" e incluir placeholders {{{{a}}}}, {{{{b}}}}, {{{{x2_svg}}}}, {{{{y2_svg}}}}
                - SVG: Ejes coordenados con una recta trazada, puntos marcados
                - Pregunta: calcular pendiente, intercepto o distancia
                
                CATEGORÍA 5 - GEOMETRÍA (Triángulos, Rectángulos):
                - Enunciado: Debe contener las palabras base y altura y usar los placeholders {{{{base}}}} y {{{{altura}}}} únicamente para sus valores numéricos (ej. "Determina el área de un triángulo de base {{{{base}}}} cm y altura {{{{altura}}}} cm."). No uses los placeholders como los nombres de las variables, y no incluyas números fijos en el texto.
                - SVG: Figura geométrica con cotas/medidas, fondo oscuro
                - Pregunta: calcular área o perímetro
                
                CATEGORÍA 6 - ECUACIÓN CUADRÁTICA:
                - Palabra clave: "ecuación cuadrática" o "ecuación de segundo grado"
                - Enunciado con fórmula LaTeX: $$ax^2 + bx + c = 0$$
                - Pregunta: suma de raíces, discriminante o soluciones
                
                CATEGORÍA 7 - FRACCIONES:
                - Palabra clave: "fracciones" en el enunciado
                - Enunciado con fórmula LaTeX: $$\\\\frac{{a}}{{b}} + \\\\frac{{c}}{{d}}$$
                - Pregunta: resultado de la operación simplificado
                
                CATEGORÍA 8 - TABLA DE DATOS (Mediana/Moda):
                - Palabra clave: "mediana" o "moda de" en el enunciado
                - Incluir placeholder {{{{dato_1}}}} en texto
                - SVG: Tabla con celdas estilizadas mostrando datos ordenados
                - Pregunta: calcular mediana o moda
                
                CATEGORÍA 9 - FUNCIONES EXPONENCIALES:
                - Incluir placeholder {{{{x_eval}}}} en el enunciado
                - Enunciado: evaluar función $f(x) = a \\\\cdot 2^{{x+c}} + d$
                - Pregunta: calcular $f(x)$ para un valor dado
                
                REGLAS GENERALES:
                1. Si la categoría requiere SVG, INCLUYE el código SVG completo en "graphic". Usa fondo oscuro (fill="#0f172a"), bordes redondeados, colores brillantes (#38bdf8, #f43f5e, #10b981).
                2. Si la categoría es algebraica (ecuaciones, fracciones, exponenciales), el campo "graphic" puede ser null pero la explicación DEBE usar LaTeX extenso.
                3. Las explicaciones deben ser paso a paso, detalladas, usando $$fórmulas$$ en LaTeX.
                4. Usa **negritas** (markdown) para resaltar conceptos clave.
                5. CRÍTICO: No incluyas números de pregunta (como "1.", "2.") en el texto de los enunciados.
                6. VARÍA las categorías: no repitas la misma categoría en múltiples preguntas.
                
                El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
                   - "area": "Matemáticas"
                   - "text": "[El enunciado con las palabras clave de la categoría]"
                   - "options": ["Opción A", "Opción B", "Opción C", "Opción D"]
                   - "correct_answer": "[Debe ser idéntica a una de las opciones]"
                   - "explanation": "[Justificación detallada paso a paso con LaTeX]"
                   - "difficulty": "Intermedio"
                   - "graphic": "[Código SVG completo o null si es algebraica]"
                """
            else:
                prompt = f"""
                Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
                Genera una lista de {needed} preguntas de selección múltiple originales, inéditas y de alta calidad para el área de {area}.
                
                REGLAS DE DISEÑO ICFES SABER 11:
                1. Para **Lectura Crítica**: Crea un fragmento corto e interesante (filosófico, literario, opinión) y formula una pregunta de inferencia.
                2. Para **Ciencias Naturales**: Plantea una situación de investigación, laboratorio o fenómeno ecológico/físico/químico.
                3. Para **Sociales y Ciudadanas**: Plantea un conflicto social, dilema ético, o análisis de multiperspectivismo.
                4. Para **Inglés**: Gramática y vocabulario de nivel A2/B1 o comprensión lectora.
                
                CRÍTICO: No incluyas números de pregunta (como "1.", "2.") en el texto de los enunciados.
                
                El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
                   - "area": "{area}"
                   - "text": "[El enunciado de la pregunta. Si es Lectura Crítica o Ciencias, incluye primero el texto/contexto seguido de la pregunta]"
                   - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
                   - "correct_answer": "[Debe ser idéntica a una de las opciones]"
                   - "explanation": "[Justificación detallada de por qué es la clave correcta y por qué las demás son distractores]"
                   - "difficulty": "Intermedio"
                """
            
            response = model.generate_content(prompt)
            text_response = response.text.strip()
            text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
            q_list = json.loads(text_response)
            
            if isinstance(q_list, dict):
                q_list = [q_list]
                
            for q_data in q_list:
                graphic_val = q_data.get("graphic")
                if graphic_val and "base64," not in graphic_val and "<svg" in graphic_val:
                    try:
                        import base64
                        graphic_val = "data:image/svg+xml;base64," + base64.b64encode(graphic_val.encode('utf-8')).decode('utf-8')
                    except Exception as e:
                        print("Error encoding generated SVG:", e)
                        
                cursor.execute('''
                    INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (
                    area,
                    q_data["text"],
                    json.dumps(q_data["options"], ensure_ascii=False),
                    q_data["correct_answer"],
                    q_data["explanation"],
                    q_data.get("difficulty", "Intermedio"),
                    graphic_val
                ))
                new_id = cursor.fetchone()[0]
                
                questions.append({
                    "id": new_id,
                    "area": area,
                    "text": q_data["text"],
                    "options": q_data["options"],
                    "correct_answer": q_data["correct_answer"],
                    "explanation": q_data["explanation"],
                    "difficulty": q_data.get("difficulty", "Intermedio"),
                    "graphic": graphic_val
                })
            conn.commit()
        except Exception as e:
            print("Error generating dynamic questions batch with Gemini:", e)
            
    conn.close()
    
    # Fallback if still less than 20
    if len(questions) < 20:
        for i in range(20 - len(questions)):
            questions.append({
                "id": i + 1000,
                "area": area,
                "text": f"Pregunta de práctica {i+1} basada en {area}. ¿Cuál es la opción correcta?",
                "options": ["Opción Correcta", "Opción B", "Opción C", "Opción D"],
                "correct_answer": "Opción Correcta",
                "explanation": f"La opción Correcta es la adecuada para este caso simulado de {area}.",
                "difficulty": "Intermedio",
                "graphic": None
            })
            
    return {"questions": questions}

@app.post("/api/practice_result")
async def save_practice_result(request: Request, data: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_db()
    conn.execute('''
        INSERT INTO practice_sessions (user_id, area, difficulty, score, total_questions)
        VALUES (%s, %s, %s, %s, %s)
    ''', (user["id"], data.get("area"), data.get("difficulty", "Intermedio"), data.get("score"), data.get("total")))
    conn.commit()
    conn.close()
    
    return {"status": "success"}

class QuestionSaveRequest(BaseModel):
    area: str
    text: str
    options: list[str]
    correct_answer: str
    explanation: str
    difficulty: str
    graphic: str | None = None

class QuestionGenerateRequest(BaseModel):
    area: str

@app.get("/api/admin/clear-questions")
async def clear_questions_route(request: Request):
    conn = get_db()
    conn.execute("DELETE FROM questions")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Preguntas eliminadas correctamente de la base de datos"}

@app.post("/api/admin/generate-question")
async def generate_question_route(request: Request, body: QuestionGenerateRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no configurada en las variables de entorno")
    
    prompt = f"""
    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
    Genera 1 pregunta de selección múltiple original, inédita y de alta calidad para el área de {body.area}.
    No te bases en ningún cuadernillo específico. Crea el escenario, problema o texto de forma 100% autónoma.
    
    REGLAS DE DISEÑO ICFES SABER 11:
    1. Para **Matemáticas**: Enfócate en modelación, formulación y ejecución, o argumentación (ej. álgebra, geometría, probabilidad, estadística o razonamiento cuantitativo).
    2. Para **Lectura Crítica**: Crea un fragmento corto e interesante (filosófico, literario, columna de opinión o texto discontinuo descriptivo) y formula una pregunta de inferencia o análisis sobre él.
    3. Para **Ciencias Naturales**: Plantea una situación de investigación, laboratorio o fenómeno ecológico/físico/químico donde se evalúe indagación o explicación de fenómenos.
    4. Para **Sociales y Ciudadanas**: Plantea un conflicto social, dilema ético, mecanismo de participación o análisis de multiperspectivismo donde haya diferentes puntos de vista en juego.
    5. Para **Inglés**: Genera un ejercicio enfocado en comprensión lectora o gramática y vocabulario de nivel A2/B1.
    
    ESTRUCTURA DE RESPUESTA REQUERIDA:
    La respuesta correcta debe ser indiscutible y las otras tres opciones (distractores) deben representar errores conceptuales o interpretativos comunes y verosímiles.
    
    El formato de salida DEBE ser estrictamente un objeto JSON en español, sin envolverlo en bloques markdown (sin ```json) y con las siguientes llaves:
       - "area": "{body.area}"
       - "text": "[El enunciado de la pregunta. Si es Lectura Crítica o Ciencias, incluye primero el texto/contexto seguido de la pregunta]"
       - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
       - "correct_answer": "[Debe ser idéntica a una de las opciones]"
       - "explanation": "[Justificación detallada de por qué es la clave correcta y por qué las demás son distractores]"
       - "difficulty": "[Básico, Intermedio, Avanzado]"
    """
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.1-flash-lite')
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
        question_data = json.loads(text_response)
        return question_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la pregunta con la IA: {str(e)}")

@app.post("/api/admin/save-question")
async def save_question_route(request: Request, body: QuestionSaveRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (
        body.area,
        body.text,
        json.dumps(body.options, ensure_ascii=False),
        body.correct_answer,
        body.explanation,
        body.difficulty,
        body.graphic
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Pregunta guardada correctamente"}

class ChatMessage(BaseModel):
    role: str
    parts: list[str]

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    image_base64: str | None = None
    chat_id: int | None = None

class RenameChatRequest(BaseModel):
    title: str

@app.get("/tutor", response_class=HTMLResponse)
async def tutor_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request=request, name="tutor.html", context={"user": user})

@app.get("/api/chats")
async def get_chats(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = get_db()
    rows = conn.execute("SELECT id, title, created_at FROM tutor_chats WHERE user_id = %s ORDER BY created_at DESC", (user["id"],)).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"]} for r in rows]

@app.post("/api/chats")
async def create_chat_session(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tutor_chats (user_id, title) VALUES (%s, 'Nuevo chat') RETURNING id", (user["id"],))
    chat_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"chat_id": chat_id, "title": "Nuevo chat"}

@app.put("/api/chats/{chat_id}")
async def rename_chat_session(chat_id: int, request: Request, body: RenameChatRequest):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = get_db()
    chat = conn.execute("SELECT 1 FROM tutor_chats WHERE id = %s AND user_id = %s", (chat_id, user["id"])).fetchone()
    if not chat:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    conn.execute("UPDATE tutor_chats SET title = %s WHERE id = %s", (body.title.strip(), chat_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/chats/{chat_id}")
async def delete_chat_session(chat_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = get_db()
    chat = conn.execute("SELECT 1 FROM tutor_chats WHERE id = %s AND user_id = %s", (chat_id, user["id"])).fetchone()
    if not chat:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    conn.execute("DELETE FROM tutor_chats WHERE id = %s", (chat_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    conn = get_db()
    chat = conn.execute("SELECT 1 FROM tutor_chats WHERE id = %s AND user_id = %s", (chat_id, user["id"])).fetchone()
    if not chat:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    rows = conn.execute("SELECT role, content FROM tutor_messages WHERE chat_id = %s ORDER BY created_at ASC", (chat_id,)).fetchall()
    conn.close()
    return [{"role": r["role"], "parts": [r["content"]]} for r in rows]

@app.post("/api/chat")
async def chat_api(request: Request, body: ChatRequest):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    user_msg = body.message
    chat_id = body.chat_id
    
    # 1. Resolve or create chat session
    conn = get_db()
    cursor = conn.cursor()
    
    if chat_id:
        chat = conn.execute("SELECT id, title FROM tutor_chats WHERE id = %s AND user_id = %s", (chat_id, user["id"])).fetchone()
        if not chat:
            conn.close()
            raise HTTPException(status_code=404, detail="Chat no encontrado")
        chat_title = chat["title"]
    else:
        # Create a new chat session automatically
        # Set a tentative title based on user message (limit to 35 chars)
        tentative_title = user_msg.strip()[:35] + ("..." if len(user_msg.strip()) > 35 else "")
        if not tentative_title:
            tentative_title = "Nuevo chat"
        cursor.execute("INSERT INTO tutor_chats (user_id, title) VALUES (%s, %s) RETURNING id", (user["id"], tentative_title))
        chat_id = cursor.fetchone()[0]
        conn.commit()
        chat_title = tentative_title
        
    # 2. Save user message to tutor_messages
    cursor.execute("INSERT INTO tutor_messages (chat_id, role, content) VALUES (%s, 'user', %s)", (chat_id, user_msg))
    conn.commit()
    
    # If the title was "Nuevo chat" or was just created, let's update it if needed
    if chat_title == "Nuevo chat":
        new_title = user_msg.strip()[:35] + ("..." if len(user_msg.strip()) > 35 else "")
        if new_title:
            cursor.execute("UPDATE tutor_chats SET title = %s WHERE id = %s", (new_title, chat_id))
            conn.commit()
            
    # 3. Retrieve chat history from DB for Gemini context
    history_rows = conn.execute("SELECT role, content FROM tutor_messages WHERE chat_id = %s ORDER BY created_at ASC", (chat_id,)).fetchall()
    
    # Format history for Gemini API (excluding the last message we just added to send as user_content)
    gemini_history = []
    for h in history_rows[:-1]:
        gemini_history.append({"role": h["role"], "parts": [h["content"]]})
        
    # Check if Gemini is configured
    api_key = os.getenv("GEMINI_API_KEY")
    response_text = ""
    mode = "local"
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
            
            user_context = f"\n\nCONTEXTO DEL ESTUDIANTE CON EL QUE HABLAS:\n- Nombre: {user['name']}\n"
            if diagnostic:
                user_context += "- Resultados de su último diagnóstico (sobre 100):\n"
                user_context += f"  * Matemáticas: {diagnostic['score_math']}\n"
                user_context += f"  * Lectura Crítica: {diagnostic['score_reading']}\n"
                user_context += f"  * Ciencias Naturales: {diagnostic['score_science']}\n"
                user_context += f"  * Sociales y Ciudadanas: {diagnostic['score_social']}\n"
                user_context += f"  * Inglés: {diagnostic['score_english']}\n"

            # System prompt for strict tutoring context
            system_instruction = (
                "Eres 'David', un Tutor de Inteligencia Artificial enfocado en el proceso educativo, "
                "la investigación y la cultura general. "
                "Tu objetivo principal es ayudar a los estudiantes en su preparación académica, incluyendo "
                "las áreas del ICFES Saber 11 (Matemáticas, Lectura Crítica, Ciencias, Sociales, Inglés), "
                "pero también estás autorizado para proporcionar ayuda con tareas, resolver dudas de investigación, "
                "y responder preguntas de cultura general.\n\n"
                "REGLA CRÍTICA Y MANDATORIA:\n"
                "- Tu propósito es ESTRICTAMENTE EDUCATIVO. Si el usuario te hace una pregunta sobre temas "
                "de ocio no educativo (por ejemplo: videojuegos, chistes, farándula, historias de ficción no "
                "relacionadas a literatura académica, consejos de amor, o charlas sin propósito de aprendizaje), "
                "debes responder de forma amable pero firme que tu rol es el de un Tutor Académico y redirigir "
                "la conversación hacia el aprendizaje o la cultura general.\n"
                "- Responde siempre en español de manera didáctica, clara, motivadora y con base en hechos verificables. "
                f"Usa ejemplos sencillos y fomenta el pensamiento crítico del estudiante.{user_context}"
            )
            
            user_content = [user_msg]
            if body.image_base64:
                b64_str = body.image_base64
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                img_data = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(img_data))
                user_content.append(img)
                
            # Smart fallback between Gemini models
            try:
                model = genai.GenerativeModel(
                    model_name='gemini-3.1-flash-lite',
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_content)
            except Exception as e_model:
                print("Failed with gemini-3.1-flash-lite, trying gemini-2.5-flash-lite fallback:", e_model)
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash-lite',
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_content)
                
            response_text = response.text
            mode = "ai"
        except Exception as e:
            print("Gemini API Error:", e)
            response_text = ""
            mode = "local"
            
    if not response_text:
        # LOCAL AGENT FALLBACK (Keyword-based search in database)
        keywords = {
            "matem": "Matemáticas",
            "cálculo": "Matemáticas",
            "círculo": "Matemáticas",
            "radio": "Matemáticas",
            "geomet": "Matemáticas",
            "númer": "Matemáticas",
            "lectura": "Lectura Crítica",
            "crític": "Lectura Crítica",
            "texto": "Lectura Crítica",
            "autor": "Lectura Crítica",
            "párrafo": "Lectura Crítica",
            "quím": "Ciencias Naturales",
            "físic": "Ciencias Naturales",
            "biol": "Ciencias Naturales",
            "hongo": "Ciencias Naturales",
            "pestalotiopsis": "Ciencias Naturales",
            "gas": "Ciencias Naturales",
            "invernadero": "Ciencias Naturales",
            "poliuretano": "Ciencias Naturales",
            "social": "Sociales y Ciudadanas",
            "ciudadan": "Sociales y Ciudadanas",
            "constituc": "Sociales y Ciudadanas",
            "derech": "Sociales y Ciudadanas",
            "congreso": "Sociales y Ciudadanas",
            "ley": "Sociales y Ciudadanas",
            "ingles": "Inglés",
            "inglés": "Inglés",
            "verb": "Inglés",
            "vocab": "Inglés",
            "grammar": "Inglés",
            "she": "Inglés"
        }
        
        # Detect query area
        query_area = None
        for kw, area in keywords.items():
            if kw in user_msg.lower():
                query_area = area
                break
                
        # Check if the user is asking about out-of-context topics (e.g. food, coding)
        out_of_context_keywords = [
            "receta", "cocinar", "arroz", "fútbol", "chiste", "programación", "python",
            "java", "javascript", "code", "amor", "novia", "novio", "juego", "clima"
        ]
        is_out_of_context = any(okw in user_msg.lower() for okw in out_of_context_keywords)
        
        if is_out_of_context:
            response_text = (
                "Hola. Como Tutor IA de David Saber 11, mi propósito está estrictamente limitado "
                "a ayudarte con temas relacionados a las áreas del examen Saber 11 (Matemáticas, "
                "Lectura Crítica, Ciencias Naturales, Sociales y Ciudadanas, e Inglés). "
                "No puedo responder a preguntas sobre otros temas."
            )
            mode = "local_restricted"
        else:
            # Search for matching questions or content
            found_content = []
            if query_area:
                # Search questions matching query_area and keywords in text
                rows = conn.execute(
                    "SELECT text, options, correct_answer, explanation FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 2",
                    (query_area,)
                ).fetchall()
                for r in rows:
                    try:
                        opts = json.loads(r["options"])
                        opts_str = ", ".join(opts)
                    except Exception:
                        opts_str = "A, B, C, D"
                    found_content.append(
                        f"**Pregunta de {query_area}:** {r['text']}\n"
                        f"*Opciones:* {opts_str}\n"
                        f"*Clave Correcta:* {r['correct_answer']}\n"
                        f"*Explicación:* {r['explanation']}"
                    )
                    
            # If still empty, search general questions with matching keywords
            if not found_content:
                words = [w for w in user_msg.lower().split() if len(w) > 4]
                for w in words[:3]:
                    rows = conn.execute(
                        "SELECT area, text, correct_answer, explanation FROM questions WHERE text LIKE %s LIMIT 1",
                        (f"%{w}%",)
                    ).fetchall()
                    for r in rows:
                        found_content.append(
                            f"**Pregunta de {r['area']}:** {r['text']}\n"
                            f"*Respuesta correcta:* {r['correct_answer']}\n"
                            f"*Explicación:* {r['explanation']}"
                        )
                        
            notice = ""
            if not api_key:
                notice = (
                    "\n\n*(Nota: Configura tu clave `GEMINI_API_KEY` en un archivo `.env` "
                    "en la raíz para habilitar un chat conversacional fluido con IA. "
                    "Actualmente estás en modo de búsqueda local).* "
                )
            else:
                notice = (
                    "\n\n*(Nota: La API de Gemini arrojó un error de cuota o límite. Se activó de forma temporal la respuesta del Tutor local).* "
                )
                
            if found_content:
                response_text = (
                    "He buscado en nuestro banco de preguntas del Saber 11 y encontré material relevante:\n\n"
                    + "\n\n---\n\n".join(found_content) + notice
                )
            else:
                response_text = (
                    "Hola. Soy tu Tutor local de David Saber 11. No encontré una pregunta exacta en "
                    "mi base de datos local relacionada con tu consulta. Puedes preguntarme sobre conceptos específicos "
                    "como 'círculo', 'gas', 'hongo', 'congreso', 'inglés', o configurar una clave `GEMINI_API_KEY` "
                    "para habilitar respuestas de IA personalizadas para cualquier duda." + notice
                )
            mode = "local"
            
    # 4. Save tutor's response to tutor_messages
    cursor.execute("INSERT INTO tutor_messages (chat_id, role, content) VALUES (%s, 'model', %s)", (chat_id, response_text))
    conn.commit()
    conn.close()
    
    return {"response": response_text, "chat_id": chat_id, "mode": mode}

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html")

@app.post("/forgot-password")
async def process_forgot_password(request: Request, email: str = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = %s", (email.strip(),)).fetchone()
    conn.close()
    
    # Simulación local del enlace de recuperación
    reset_link = f"/reset-password?email={email.strip()}&token=simulated_token_123"
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={
        "success": "Se ha enviado un correo con las instrucciones para restablecer tu contraseña.",
        "reset_link": reset_link if user else None
    })

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str, token: str):
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"email": email, "token": token})

@app.post("/reset-password")
async def process_reset_password(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    if not re.match(PASSWORD_REGEX, password):
        return templates.TemplateResponse(request=request, name="reset_password.html", context={
            "error": "La contraseña debe tener mínimo 8 caracteres, al menos una mayúscula, una minúscula, un número y un carácter especial.",
            "email": email
        })
        
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
    if not user:
        conn.close()
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"error": "Usuario no encontrado."})
        
    hashed_pwd = pwd_context.hash(password)
    conn.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_pwd, user["id"]))
    conn.commit()
    conn.close()
    
    return templates.TemplateResponse(request=request, name="login.html", context={"success": "Tu contraseña ha sido restablecida. Inicia sesión con tus nuevas credenciales."})

@app.get("/login/google")
async def google_login(request: Request):
    redirect_uri = request.url_for('auth_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse(url="/login?error=auth_failed")
        
    user_info = token.get('userinfo')
    if not user_info:
        return RedirectResponse(url="/login?error=auth_failed")
        
    email = user_info.get('email')
    name = user_info.get('name', 'Estudiante')
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
    
    if not user:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (name, email, "google_sso_oauth_user")
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
    else:
        user_id = user["id"]
        
    response = RedirectResponse(url="/dashboard", status_code=303)
    request.session["user_id"] = user_id
    
    guest_cookie = request.cookies.get("guest_diagnostic")
    if guest_cookie:
        try:
            scores = json.loads(guest_cookie)
            math_avg = (scores["math1"] + scores["math2"]) // 2
            reading_avg = (scores["reading1"] + scores["reading2"]) // 2
            social_avg = (scores["social1"] + scores["social2"]) // 2
            science_avg = (scores["science1"] + scores["science2"]) // 2
            english_avg = (scores["english1"] + scores["english2"]) // 2
            
            s_math = map_diagnostic_score(math_avg)
            s_reading = map_diagnostic_score(reading_avg)
            s_social = map_diagnostic_score(social_avg)
            s_science = map_diagnostic_score(science_avg)
            s_english = map_diagnostic_score(english_avg)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, s_math, s_reading, s_social, s_science, s_english))
            conn.commit()
            response.delete_cookie("guest_diagnostic")
        except Exception as e:
            print("Error saving guest diagnostic inside Google callback:", e)
            
    conn.close()
    return response


# --- COMMUNITY ROUTES ---

def simulate_tutor_response(post_id: int, content: str, area: str):
    import time
    time.sleep(3)
    
    conn = get_db()
    cursor = conn.cursor()
    
    tutor_row = cursor.execute("SELECT id FROM users WHERE email = 'tutor_david@saber11.edu.co'").fetchone()
    if not tutor_row:
        conn.close()
        return
    tutor_id = tutor_row[0]
    
    response_text = ""
    # Try Gemini if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            system_instruction = (
                f"Eres 'Tutor David', la Inteligencia Artificial moderadora del Muro de Dudas de David Saber 11.\n"
                f"Un estudiante ha publicado la siguiente duda en el área de **{area}**:\n"
                f"\"{content}\"\n\n"
                f"Responde de manera concisa, clara y didáctica (máximo 3-4 líneas). "
                f"Explica el concepto o cómo resolver la duda, y motiva al estudiante. Usa un tono amigable, emojis y responde en español."
            )
            model = genai.GenerativeModel(model_name='gemini-3.1-flash-lite', system_instruction=system_instruction)
            response = model.generate_content(content)
            response_text = response.text.strip()
        except Exception:
            pass
            
    if not response_text:
        fallback_responses = {
            "Matemáticas": "¡Excelente pregunta! Recuerda que para este tipo de problemas de Matemáticas en el Saber 11, lo clave es simplificar la expresión paso a paso y descartar opciones lógicas. ¡Sigue practicando! 📐",
            "Lectura Crítica": "¡Hola! Para responder dudas de Lectura Crítica, lee siempre con atención el enunciado y busca la intención comunicativa del autor. Recuerda que no se trata de tu opinión personal, sino de lo que afirma el texto. 📚",
            "Ciencias Naturales": "¡Muy interesante duda! En Ciencias Naturales, intenta siempre identificar las variables independientes y dependientes del experimento. Eso te dará la clave para descartar opciones incorrectas. 🧪",
            "Sociales y Ciudadanas": "¡Gran duda ciudadana! No olvides que la constitución política es la norma de normas en Colombia. Si la pregunta es sobre derechos fundamentales, la acción de tutela suele ser una herramienta clave. 🌎",
            "Inglés": "¡Hello! Para el área de Inglés, concéntrate en el vocabulario contextual y los tiempos verbales (especialmente pasado y presente perfecto). ¡La práctica hace al maestro! 🇬🇧"
        }
        response_text = fallback_responses.get(area, "¡Hola! Gracias por compartir tu duda en la comunidad. Recuerda revisar nuestro banco de preguntas y practicar diariamente para fortalecer tus competencias en esta área. ¡Tú puedes! 🤖")
        
    cursor.execute("INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)", (post_id, tutor_id, response_text))
    conn.commit()
    conn.close()


@app.get("/comunidad", response_class=HTMLResponse)
async def comunidad_page(request: Request, area: str = None):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    
    query = '''
        SELECT p.id, p.content, p.area, p.likes, p.created_at, 
               u.id as user_id, u.name as user_name, u.avatar_color, u.streak
        FROM posts p
        JOIN users u ON p.user_id = u.id
    '''
    params = []
    if area and area != "Todas":
        query += " WHERE p.area = %s"
        params.append(area)
        
    query += " ORDER BY p.created_at DESC"
    
    post_rows = conn.execute(query, params).fetchall()
    
    posts = []
    for r in post_rows:
        # Check if current user liked this post
        liked_row = conn.execute(
            "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
            (r["id"], user["id"])
        ).fetchone()
        liked = liked_row is not None
        
        # Get comments for this post
        comments_query = '''
            SELECT c.id, c.content, c.created_at, u.name as user_name, u.avatar_color
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
        '''
        comment_rows = conn.execute(comments_query, (r["id"],)).fetchall()
        
        comments_list = []
        for cr in comment_rows:
            comments_list.append({
                "id": cr["id"],
                "content": cr["content"],
                "user_name": cr["user_name"],
                "avatar_color": cr["avatar_color"] or "#3b82f6"
            })
            
        posts.append({
            "id": r["id"],
            "content": r["content"],
            "area": r["area"],
            "likes": r["likes"],
            "user_id": r["user_id"],
            "user_name": r["user_name"],
            "avatar_color": r["avatar_color"] or "#3b82f6",
            "streak": r["streak"] or 0,
            "liked": liked,
            "comments": comments_list
        })
        
    conn.close()
    return templates.TemplateResponse(
        request=request, 
        name="comunidad.html", 
        context={"user": user, "posts": posts, "active_area": area or "Todas"}
    )


@app.post("/comunidad")
async def create_post(
    request: Request,
    background_tasks: BackgroundTasks,
    content: str = Form(...),
    area: str = Form(...)
):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    content_clean = content.strip()
    if not content_clean:
        return RedirectResponse(url="/comunidad", status_code=303)
        
    # Moderation check: vulgar words
    words = content_clean.lower().split()
    if any(w in VULGAR_WORDS for w in words):
        return RedirectResponse(url="/comunidad?error=moderacion", status_code=303)
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, content, area, likes) VALUES (%s, %s, %s, 0) RETURNING id",
        (user["id"], content_clean, area)
    )
    post_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    # Trigger AI response simulation in background
    background_tasks.add_task(simulate_tutor_response, post_id, content_clean, area)
    
    return RedirectResponse(url="/comunidad", status_code=303)


@app.post("/api/posts/{post_id}/like")
async def toggle_like(request: Request, post_id: int):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already liked
    cursor.execute(
        "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
        (post_id, user["id"])
    )
    liked_row = cursor.fetchone()
    
    if liked_row:
        # Unlike
        cursor.execute("DELETE FROM post_likes WHERE post_id = %s AND user_id = %s", (post_id, user["id"]))
        cursor.execute("UPDATE posts SET likes = GREATEST(0, likes - 1) WHERE id = %s", (post_id,))
        liked = False
    else:
        # Like
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (post_id, user["id"]))
        cursor.execute("UPDATE posts SET likes = likes + 1 WHERE id = %s", (post_id,))
        liked = True
        
    conn.commit()
    
    # Get new likes count
    new_likes = cursor.execute("SELECT likes FROM posts WHERE id = %s", (post_id,)).fetchone()[0]
    conn.close()
    
    return {"likes": new_likes, "liked": liked}


@app.post("/api/posts/{post_id}/comment")
async def add_comment(request: Request, post_id: int, content: str = Form(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    content_clean = content.strip()
    if not content_clean:
        return RedirectResponse(url="/comunidad", status_code=303)
        
    # Moderation check: vulgar words
    words = content_clean.lower().split()
    if any(w in VULGAR_WORDS for w in words):
        return RedirectResponse(url="/comunidad?error=moderacion", status_code=303)
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)",
        (post_id, user["id"], content_clean)
    )
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/comunidad", status_code=303)


# --- DUELS ROUTES ---

def check_expired_duels(conn):
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(hours=24)
    # Get all pending duels created more than 24 hours ago
    expired_duels = conn.execute(
        "SELECT id, challenger_id, opponent_id, area FROM tutor_duels WHERE status = 'pending' AND created_at < %s",
        (cutoff,)
    ).fetchall()
    
    if expired_duels:
        cursor = conn.cursor()
        for d in expired_duels:
            cursor.execute(
                "UPDATE tutor_duels SET opponent_score = 0, status = 'resolved', resolved_at = %s WHERE id = %s",
                (datetime.now(), d["id"])
            )
        conn.commit()

@app.get("/duelos", response_class=HTMLResponse)
async def duels_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    # 1. Run expiration check
    try:
        check_expired_duels(conn)
    except Exception as e:
        print("Error checking expired duels:", e)
        
    # 1.5 Fetch diagnostic / simulacro results for study tips eligibility
    diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
    has_simulacro = False
    eligible_for_tips = False
    max_score = 0
    if diagnostic:
        has_simulacro = True
        weighted_sum = (
            diagnostic["score_math"] * 3 +
            diagnostic["score_reading"] * 3 +
            diagnostic["score_science"] * 3 +
            diagnostic["score_social"] * 3 +
            diagnostic["score_english"] * 1
        )
        max_score = round((weighted_sum / 13) * 5)
        if max_score > 250:
            eligible_for_tips = True

    # 1.6 Fetch resolved duels for notifications
    notif_rows = conn.execute('''
        SELECT d.id, d.area, d.challenger_score, d.opponent_score, u.name as opponent_name
        FROM tutor_duels d
        JOIN users u ON d.opponent_id = u.id
        WHERE d.challenger_id = %s AND d.status = 'resolved' AND d.challenger_notified = FALSE
    ''', (user["id"],)).fetchall()
    
    notifications = []
    cursor = conn.cursor()
    for n in notif_rows:
        notifications.append({
            "id": n["id"],
            "area": n["area"],
            "challenger_score": n["challenger_score"],
            "opponent_score": n["opponent_score"],
            "opponent_name": n["opponent_name"]
        })
        cursor.execute("UPDATE tutor_duels SET challenger_notified = TRUE WHERE id = %s", (n["id"],))
    conn.commit()
        
    # 2. Get active incoming challenges (where user is the opponent)
    incoming_rows = conn.execute('''
        SELECT d.id, d.area, d.challenger_score, d.created_at, u.name as challenger_name, u.avatar_color
        FROM tutor_duels d
        JOIN users u ON d.challenger_id = u.id
        WHERE d.opponent_id = %s AND d.status = 'pending'
        ORDER BY d.created_at DESC
    ''', (user["id"],)).fetchall()
    
    incoming_challenges = []
    for r in incoming_rows:
        incoming_challenges.append({
            "id": r["id"],
            "area": r["area"],
            "challenger_name": r["challenger_name"],
            "avatar_color": r["avatar_color"] or "#3b82f6",
            "created_at": r["created_at"].strftime("%d/%m %I:%M %p")
        })

    # 3. Get active outgoing challenges (where user is the challenger)
    outgoing_rows = conn.execute('''
        SELECT d.id, d.area, d.created_at, u.name as opponent_name, u.avatar_color
        FROM tutor_duels d
        JOIN users u ON d.opponent_id = u.id
        WHERE d.challenger_id = %s AND d.status = 'pending'
        ORDER BY d.created_at DESC
    ''', (user["id"],)).fetchall()
    
    outgoing_challenges = []
    for r in outgoing_rows:
        outgoing_challenges.append({
            "id": r["id"],
            "area": r["area"],
            "opponent_name": r["opponent_name"],
            "avatar_color": r["avatar_color"] or "#3b82f6",
            "created_at": r["created_at"].strftime("%d/%m %I:%M %p")
        })

    # 4. Get completed duels history
    completed_rows = conn.execute('''
        SELECT d.id, d.area, d.challenger_score, d.opponent_score, d.resolved_at,
               u1.name as challenger_name, u1.id as challenger_id,
               u2.name as opponent_name, u2.id as opponent_id
        FROM tutor_duels d
        JOIN users u1 ON d.challenger_id = u1.id
        JOIN users u2 ON d.opponent_id = u2.id
        WHERE (d.challenger_id = %s OR d.opponent_id = %s) AND d.status = 'resolved'
        ORDER BY d.resolved_at DESC LIMIT 10
    ''', (user["id"], user["id"])).fetchall()
    
    completed_duels = []
    for r in completed_rows:
        winner_name = "Empate"
        if r["challenger_score"] > r["opponent_score"]:
            winner_name = r["challenger_name"]
        elif r["opponent_score"] > r["challenger_score"]:
            winner_name = r["opponent_name"]
            
        completed_duels.append({
            "id": r["id"],
            "area": r["area"],
            "challenger_name": r["challenger_name"],
            "opponent_name": r["opponent_name"],
            "challenger_score": r["challenger_score"],
            "opponent_score": r["opponent_score"],
            "winner_name": winner_name,
            "resolved_at": r["resolved_at"].strftime("%d/%m %I:%M %p") if r["resolved_at"] else ""
        })

    # 5. Get list of other registered users to challenge
    opponents_rows = conn.execute(
        "SELECT id, name, avatar_color, streak, duel_points, badges FROM users WHERE id != %s ORDER BY name ASC",
        (user["id"],)
    ).fetchall()
    
    opponents = [{
        "id": r["id"],
        "name": r["name"],
        "avatar_color": r["avatar_color"] or "#3b82f6",
        "streak": r["streak"] or 0,
        "duel_points": r["duel_points"] or 0
    } for r in opponents_rows]

    # 6. Calculate Leaderboard (Won Duels ranking)
    leaderboard = {}
    for op in opponents_rows:
        try:
            badges_list = json.loads(op["badges"]) if op["badges"] else []
        except Exception:
            badges_list = []
        leaderboard[op["id"]] = {
            "name": op["name"],
            "avatar_color": op["avatar_color"] or "#3b82f6",
            "wins": 0,
            "streak": op["streak"] or 0,
            "points": op["duel_points"] or 0,
            "points_compact": format_points_compact(op["duel_points"] or 0),
            "level": 1 + (op["duel_points"] or 0) // 50,
            "badges": badges_list
        }
        
    try:
        user_badges_list = json.loads(user["badges"]) if user["badges"] else []
    except Exception:
        user_badges_list = []
        
    leaderboard[user["id"]] = {
        "name": user["name"],
        "avatar_color": user["avatar_color"] or "#3b82f6",
        "wins": 0,
        "streak": user["streak"] or 0,
        "points": user["duel_points"] or 0,
        "points_compact": format_points_compact(user["duel_points"] or 0),
        "level": 1 + (user["duel_points"] or 0) // 50,
        "badges": user_badges_list
    }
    
    all_resolved = conn.execute("SELECT challenger_id, opponent_id, challenger_score, opponent_score FROM tutor_duels WHERE status = 'resolved'").fetchall()
    for d in all_resolved:
        if d["challenger_score"] > d["opponent_score"]:
            if d["challenger_id"] in leaderboard:
                leaderboard[d["challenger_id"]]["wins"] += 1
        elif d["opponent_score"] > d["challenger_score"]:
            if d["opponent_id"] in leaderboard:
                leaderboard[d["opponent_id"]]["wins"] += 1
                
    leaderboard_sorted = sorted(leaderboard.values(), key=lambda x: (x["wins"], x["points"]), reverse=True)[:5]
    
    # Count of total challenges completed
    total_completed = conn.execute(
        "SELECT COUNT(*) FROM tutor_duels WHERE (challenger_id = %s OR opponent_id = %s) AND status = 'resolved'",
        (user["id"], user["id"])
    ).fetchone()[0]
    
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="duelos.html", 
        context={
            "user": user, 
            "opponents": opponents,
            "incoming": incoming_challenges,
            "outgoing": outgoing_challenges,
            "completed": completed_duels,
            "leaderboard": leaderboard_sorted,
            "notifications": notifications,
            "total_completed": total_completed,
            "has_simulacro": has_simulacro,
            "eligible_for_tips": eligible_for_tips,
            "max_score": max_score
        }
    )

@app.post("/api/duelos/start")
async def start_duel(request: Request, body: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    area = body.get("area", "Matemáticas")
    
    conn = get_db()
    # Select opponent: prioritize active in the last 5 minutes
    opponent_row = conn.execute('''
        SELECT id, name, avatar_color, streak FROM users 
        WHERE id != %s AND last_seen > NOW() - INTERVAL '5 minutes'
        ORDER BY RANDOM() LIMIT 1
    ''', (user["id"],)).fetchone()
    
    if not opponent_row:
        opponent_row = conn.execute('''
            SELECT id, name, avatar_color, streak FROM users 
            WHERE id != %s 
            ORDER BY RANDOM() LIMIT 1
        ''', (user["id"],)).fetchone()
        
    if not opponent_row:
        conn.close()
        raise HTTPException(status_code=400, detail="No hay oponentes disponibles para desafiar.")
        
    opponent_id = opponent_row["id"]
    # 1. Fetch 1 random question for this area from DB
    r = conn.execute(
        "SELECT id, area, text, options, correct_answer, explanation, difficulty, graphic FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 1",
        (area,)
    ).fetchone()
    
    # Dynamic generation fallback
    if not r:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.1-flash-lite')
                prompt = f"""
                Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
                Genera 1 pregunta de selección múltiple original, inédita y de alta calidad para el área de {area}.
                
                REGLAS DE DISEÑO ICFES SABER 11:
                1. Para **Matemáticas**: Enfócate en modelación, formulación y ejecución, o argumentación (ej. álgebra, geometría, probabilidad, estadística o razonamiento cuantitativo).
                2. Para **Lectura Crítica**: Crea un fragmento corto e interesante (filosófico, literario, columna de opinión o texto discontinuo descriptivo) y formula una pregunta de inferencia o análisis sobre él.
                3. Para **Ciencias Naturales**: Plantea una situación de investigación, laboratorio o fenómeno ecológico/físico/químico donde se evalúe indagación o explicación de fenómenos.
                4. Para **Sociales y Ciudadanas**: Plantea un conflicto social, dilema ético, mecanismo de participación o análisis de multiperspectivismo donde haya diferentes puntos de vista en juego.
                5. Para **Inglés**: Genera un ejercicio enfocado en comprensión lectora o gramática y vocabulario de nivel A2/B1.
                
                ESTRUCTURA DE RESPUESTA REQUERIDA:
                La respuesta correcta debe ser indiscutible y las otras tres opciones (distractores) deben representar errores conceptuales o interpretativos comunes y verosímiles.
                
                El formato de salida DEBE ser estrictamente un objeto JSON en español, sin envolverlo en bloques markdown (sin ```json) y con las siguientes llaves:
                   - "area": "{area}"
                   - "text": "[El enunciado de la pregunta. Si es Lectura Crítica o Ciencias, incluye primero el texto/contexto seguido de la pregunta]"
                   - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
                   - "correct_answer": "[Debe ser idéntica a una de las opciones]"
                   - "explanation": "[Justificación detallada de por qué es la clave correcta y por qué las demás son distractores]"
                   - "difficulty": "[Básico, Intermedio, Avanzado]"
                """
                response = model.generate_content(prompt)
                text_response = response.text.strip()
                text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                q_data = json.loads(text_response)
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (
                    area,
                    q_data["text"],
                    json.dumps(q_data["options"], ensure_ascii=False),
                    q_data["correct_answer"],
                    q_data["explanation"],
                    q_data["difficulty"],
                    None
                ))
                new_id = cursor.fetchone()[0]
                conn.commit()
                
                r = {
                    "id": new_id,
                    "area": area,
                    "text": q_data["text"],
                    "options": json.dumps(q_data["options"], ensure_ascii=False),
                    "correct_answer": q_data["correct_answer"],
                    "explanation": q_data["explanation"],
                    "graphic": None
                }
            except Exception as e:
                print("Error generating question for duel:", e)
                
    if not r:
        # Static mock questions fallback
        mock_qs = {
            "Matemáticas": {"text": "¿Cuál es la probabilidad de obtener un número par al lanzar un dado de 6 caras?", "options": ["1/2", "1/3", "2/3", "1/6"], "correct_answer": "1/2", "explanation": "Los números pares son 2, 4 y 6 (3 casos favorables de 6 posibles, es decir, 3/6 = 1/2)."}
        }
        fallback_q = mock_qs.get(area, mock_qs["Matemáticas"])
        # Ensure it exists in questions table
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM questions WHERE text = %s", (fallback_q["text"],))
        ex = cursor.fetchone()
        if ex:
            q_id = ex[0]
        else:
            cursor.execute('''
                INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
                VALUES (%s, %s, %s, %s, %s, 'Intermedio') RETURNING id
            ''', (area, fallback_q["text"], json.dumps(fallback_q["options"]), fallback_q["correct_answer"], fallback_q["explanation"]))
            q_id = cursor.fetchone()[0]
            conn.commit()
            
        r = {
            "id": q_id,
            "area": area,
            "text": fallback_q["text"],
            "options": json.dumps(fallback_q["options"]),
            "correct_answer": fallback_q["correct_answer"],
            "explanation": fallback_q["explanation"],
            "graphic": None
        }

    try:
        opts = json.loads(r["options"])
    except Exception:
        opts = [r["correct_answer"], "Opción B", "Opción C", "Opción D"]
        
    question = {
        "id": r["id"],
        "area": r["area"],
        "text": r["text"],
        "options": opts,
        "correct_answer": r["correct_answer"],
        "explanation": r["explanation"],
        "difficulty": r.get("difficulty", "Intermedio") if isinstance(r, dict) else r["difficulty"],
        "graphic": r["graphic"]
    }
    duel_seed = user["id"] + opponent_id + r["id"]
    question = process_parametric_question(question, seed=duel_seed)
    
    opponent_row = conn.execute("SELECT id, name, avatar_color, streak FROM users WHERE id = %s", (opponent_id,)).fetchone()
    conn.close()
    
    opponent = {
        "id": opponent_row["id"],
        "name": opponent_row["name"],
        "avatar_color": opponent_row["avatar_color"] or "#10b981",
        "streak": opponent_row["streak"] or 0
    } if opponent_row else None
    
    return {
        "question": question,
        "opponent": opponent
    }

@app.post("/api/duelos/result")
async def save_duel_result(request: Request, body: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    opponent_id = body.get("opponent_id")
    question_id = body.get("question_id")
    score = body.get("score", 0) # 0 or 1
    area = body.get("area", "Matemáticas")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Save the pending challenge
    cursor.execute('''
        INSERT INTO tutor_duels (challenger_id, opponent_id, area, question_id, challenger_score, opponent_score, status)
        VALUES (%s, %s, %s, %s, %s, NULL, 'pending') RETURNING id
    ''', (user["id"], opponent_id, area, question_id, score))
    duel_id = cursor.fetchone()[0]
    
    # 1 point incentive for sending the challenge
    cursor.execute("UPDATE users SET duel_points = COALESCE(duel_points, 0) + 1 WHERE id = %s", (user["id"],))
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "duel_id": duel_id,
        "message": "Desafío enviado correctamente"
    }

@app.get("/api/notifications/count")
async def get_notifications_count(request: Request):
    user = get_current_user(request)
    if not user:
        return {"count": 0}
    conn = get_db()
    try:
        incoming = conn.execute(
            "SELECT COUNT(*) FROM tutor_duels WHERE opponent_id = %s AND status = 'pending'",
            (user["id"],)
        ).fetchone()[0]
        
        completed = conn.execute(
            "SELECT COUNT(*) FROM tutor_duels WHERE challenger_id = %s AND status = 'resolved' AND challenger_notified = FALSE",
            (user["id"],)
        ).fetchone()[0]
        
        return {"count": incoming + completed}
    except Exception as e:
        print("Error getting notifications count:", e)
        return {"count": 0}
    finally:
        conn.close()

@app.get("/api/duelos/load/{duel_id}")
async def load_pending_duel(duel_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    conn = get_db()
    duel = conn.execute('''
        SELECT d.id, d.area, d.challenger_score, d.challenger_id, d.opponent_id, q.id as q_id, q.text, q.options, q.correct_answer, q.explanation, q.graphic, u.name as challenger_name, u.avatar_color
        FROM tutor_duels d
        JOIN questions q ON d.question_id = q.id
        JOIN users u ON d.challenger_id = u.id
        WHERE d.id = %s AND d.opponent_id = %s AND d.status = 'pending'
    ''', (duel_id, user["id"])).fetchone()
    conn.close()
    
    if not duel:
        raise HTTPException(status_code=404, detail="Desafío no encontrado o ya respondido")
        
    try:
        opts = json.loads(duel["options"])
    except Exception:
        opts = [duel["correct_answer"], "Opción B", "Opción C", "Opción D"]
        
    question_obj = {
        "id": duel["q_id"],
        "area": duel["area"],
        "text": duel["text"],
        "options": opts,
        "correct_answer": duel["correct_answer"],
        "explanation": duel["explanation"],
        "difficulty": "Intermedio",
        "graphic": duel["graphic"]
    }
    duel_seed = duel["challenger_id"] + duel["opponent_id"] + duel["q_id"]
    question_obj = process_parametric_question(question_obj, seed=duel_seed)
        
    return {
        "id": duel["id"],
        "area": duel["area"],
        "challenger_name": duel["challenger_name"],
        "avatar_color": duel["avatar_color"] or "#3b82f6",
        "question": question_obj
    }

@app.post("/api/duelos/respond")
async def respond_to_duel(request: Request, body: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    duel_id = body.get("duel_id")
    score = body.get("score", 0) # 0 or 1
    
    conn = get_db()
    cursor = conn.cursor()
    
    duel = conn.execute('''
        SELECT d.*, u.name as challenger_name, u.streak as challenger_streak
        FROM tutor_duels d
        JOIN users u ON d.challenger_id = u.id
        WHERE d.id = %s AND d.opponent_id = %s AND d.status = 'pending'
    ''', (duel_id, user["id"])).fetchone()
    
    if not duel:
        conn.close()
        raise HTTPException(status_code=404, detail="Desafío no encontrado")
        
    from datetime import datetime, date
    today_str = date.today().isoformat()
    
    cursor.execute('''
        UPDATE tutor_duels 
        SET opponent_score = %s, status = 'resolved', resolved_at = %s
        WHERE id = %s
    ''', (score, datetime.now(), duel_id))
    
    # Calculate winner
    winner = "tie"
    streak_bonus = False
    challenger_score = duel["challenger_score"]
    
    if challenger_score > score:
        winner = "challenger"
        cursor.execute("UPDATE users SET duel_points = COALESCE(duel_points, 0) + 5 WHERE id = %s", (duel["challenger_id"],))
    elif score > challenger_score:
        winner = "opponent"
        user_streak = (user["streak"] or 0) + 1
        streak_bonus = True
        cursor.execute("UPDATE users SET streak = %s, last_active_date = %s, duel_points = COALESCE(duel_points, 0) + 5 WHERE id = %s", (user_streak, today_str, user["id"]))
        
        # Add badge to opponent
        badges = []
        try:
            badges = json.loads(user["badges"]) if user["badges"] else []
        except Exception:
            pass
        if "Duelo Ganado" not in badges:
            badges.append("Duelo Ganado")
            cursor.execute("UPDATE users SET badges = %s WHERE id = %s", (json.dumps(badges), user["id"]))
    else:
        # Tie: 0 points awarded to match losing/tie 0 points requirement
        pass
        
    conn.commit()

    # Process badges/achievements for both users
    for uid in [user["id"], duel["challenger_id"]]:
        row = conn.execute("SELECT duel_points, badges FROM users WHERE id = %s", (uid,)).fetchone()
        if row:
            pts = row["duel_points"] or 0
            try:
                curr_badges = json.loads(row["badges"]) if row["badges"] else []
            except Exception:
                curr_badges = []
            
            badges_map = [
                (10, "Duelista Principiante ⚔️"),
                (50, "Duelista Pro 🛡️"),
                (200, "Duelista de Oro 🏆"),
                (500, "Campeón de Duelos 👑"),
                (1000, "Leyenda del Saber 🌟")
            ]
            new_added = False
            for thresh, bname in badges_map:
                if pts >= thresh and bname not in curr_badges:
                    curr_badges.append(bname)
                    new_added = True
            if new_added:
                cursor.execute("UPDATE users SET badges = %s WHERE id = %s", (json.dumps(curr_badges), uid))
                conn.commit()
    
    # Load updated user streak and badges
    updated_user = conn.execute("SELECT streak, badges FROM users WHERE id = %s", (user["id"],)).fetchone()
    current_user_streak = updated_user["streak"] if updated_user["streak"] is not None else 0
    
    try:
        current_user_badges = json.loads(updated_user["badges"]) if updated_user["badges"] else []
    except Exception:
        current_user_badges = []
        
    conn.close()
    
    return {
        "status": "success",
        "winner": winner,
        "challenger_score": challenger_score,
        "opponent_score": score,
        "streak": current_user_streak,
        "badges": current_user_badges,
        "streak_bonus": streak_bonus
    }


# --- MICROLEARNING (FLASHCARDS) ---

@app.get("/aprender", response_class=HTMLResponse)
async def learn_page(request: Request, area: str = "Todas"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    
    # Fetch questions
    if area == "Todas":
        rows = conn.execute(
            "SELECT id, area, text, correct_answer, explanation, graphic FROM questions ORDER BY RANDOM() LIMIT 5"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, area, text, correct_answer, explanation, graphic FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 5",
            (area,)
        ).fetchall()
        
    questions = []
    for r in rows:
        q_obj = {
            "id": r["id"],
            "area": r["area"],
            "text": r["text"],
            "options": ["A", "B", "C", "D"],
            "correct_answer": r["correct_answer"],
            "explanation": r["explanation"],
            "difficulty": "Intermedio",
            "graphic": r["graphic"]
        }
        q_processed = process_parametric_question(q_obj)
        questions.append({
            "id": q_processed["id"],
            "area": q_processed["area"],
            "text": q_processed["text"],
            "correct_answer": q_processed["correct_answer"],
            "explanation": q_processed["explanation"],
            "graphic": q_processed["graphic"]
        })
        
    needed = 5 - len(questions)
    if needed > 0:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.1-flash-lite')
                
                target_area = area if area != "Todas" else random.choice(["Matemáticas", "Lectura Crítica", "Ciencias Naturales", "Sociales y Ciudadanas", "Inglés"])
                
                prompt = f"""
                Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
                Genera una lista de {needed} preguntas de selección múltiple originales, inéditas y de alta calidad para el área de {target_area}.
                
                REGLAS DE DISEÑO ICFES SABER 11:
                1. Para **Matemáticas**: Enfócate en modelación, formulación y ejecución, o argumentación (ej. álgebra, geometría, probabilidad, estadística o razonamiento cuantitativo).
                2. Para **Lectura Crítica**: Crea un fragmento corto e interesante (filosófico, literario, columna de opinión o texto discontinuo descriptivo) y formula una pregunta de inferencia o análisis sobre él.
                3. Para **Ciencias Naturales**: Plantea una situation de investigación, laboratorio o fenómeno ecológico/físico/químico donde se evalúe indagación o explicación de fenómenos.
                4. Para **Sociales y Ciudadanas**: Plantea un conflicto social, dilema ético, mecanismo de participación o análisis de multiperspectivismo donde haya diferentes puntos de vista en juego.
                5. Para **Inglés**: Genera un ejercicio enfocado en comprensión lectora o gramática y vocabulario de nivel A2/B1.
                
                CRÍTICO: No incluyas números de pregunta (como "1.", "2.") en el texto de los enunciados.
                
                El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
                   - "area": "{target_area}"
                   - "text": "[El enunciado de la pregunta. Si es Lectura Crítica o Ciencias, incluye primero el texto/contexto seguido de la pregunta]"
                   - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
                   - "correct_answer": "[Debe ser idéntica a una de las opciones]"
                   - "explanation": "[Justificación detallada de por qué es la clave correcta]"
                   - "difficulty": "Intermedio"
                """
                
                response = model.generate_content(prompt)
                text_response = response.text.strip()
                text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                q_list = json.loads(text_response)
                
                if isinstance(q_list, dict):
                    q_list = [q_list]
                    
                cursor = conn.cursor()
                for q_data in q_list:
                    cursor.execute('''
                        INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    ''', (
                        q_data["area"],
                        q_data["text"],
                        json.dumps(q_data["options"], ensure_ascii=False),
                        q_data["correct_answer"],
                        q_data["explanation"],
                        q_data.get("difficulty", "Intermedio")
                    ))
                    new_id = cursor.fetchone()[0]
                    q_obj = {
                        "id": new_id,
                        "area": q_data["area"],
                        "text": q_data["text"],
                        "options": q_data["options"],
                        "correct_answer": q_data["correct_answer"],
                        "explanation": q_data["explanation"],
                        "difficulty": q_data.get("difficulty", "Intermedio"),
                        "graphic": None
                    }
                    q_processed = process_parametric_question(q_obj)
                    questions.append({
                        "id": q_processed["id"],
                        "area": q_processed["area"],
                        "text": q_processed["text"],
                        "correct_answer": q_processed["correct_answer"],
                        "explanation": q_processed["explanation"],
                        "graphic": q_processed["graphic"]
                    })
                conn.commit()
            except Exception as e:
                print("Error generating dynamic flashcard questions:", e)
                
    conn.close()
    
    # Fallback to make sure we have 5 cards if Gemini failed or is not available
    if len(questions) < 5:
        fallbacks = [
            {"id": 901, "area": "Matemáticas", "text": "¿Cómo se calcula el área de un círculo?", "correct_answer": "A = π * r²", "explanation": "π es la relación entre el perímetro y el diámetro de un círculo, r es el radio.", "graphic": None},
            {"id": 902, "area": "Ciencias Naturales", "text": "¿Cuál es el gas causante del efecto invernadero más emitido por actividades humanas?", "correct_answer": "Dióxido de Carbono (CO₂)", "explanation": "El CO₂ es emitido principalmente por la quema de combustibles fósiles.", "graphic": None},
            {"id": 903, "area": "Sociales y Ciudadanas", "text": "¿Qué mecanismo protege de forma inmediata los derechos fundamentales en Colombia?", "correct_answer": "La Acción de Tutela", "explanation": "Establecida en el artículo 86 de la Constitución de 1991.", "graphic": None},
            {"id": 904, "area": "Lectura Crítica", "text": "¿Qué es la tesis de un texto argumentativo?", "correct_answer": "La idea u opinión central que el autor defiende", "explanation": "Es la columna vertebral del texto argumentativo y se sustenta con argumentos.", "graphic": None},
            {"id": 905, "area": "Inglés", "text": "What is the correct auxiliary verb for the Present Perfect tense?", "correct_answer": "Have / Has", "explanation": "Present perfect uses have/has + past participle.", "graphic": None}
        ]
        for f in fallbacks:
            if len(questions) >= 5:
                break
            if area == "Todas" or f["area"] == area:
                questions.append(f)
                
    # Format them as flashcards for the UI
    flashcards = []
    for q in questions:
        front_text = q["text"]
        back_text = f"Respuesta Correcta: {q['correct_answer']}\n\nExplicación:\n{q['explanation']}"
        flashcards.append({
            "id": q["id"],
            "area": q["area"],
            "title": f"Pregunta de {q['area']}",
            "front": front_text,
            "back": back_text,
            "graphic": q.get("graphic")
        })
        
    return templates.TemplateResponse(
        request=request, 
        name="aprender.html", 
        context={"user": user, "flashcards": flashcards, "active_area": area}
    )


# --- PROFILE UPDATE API ---

@app.post("/api/profile/update")
async def update_profile(request: Request, bio: str = Form(...), avatar_color: str = Form(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    bio_clean = bio.strip()
    if len(bio_clean) > 160:
        bio_clean = bio_clean[:157] + "..."
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET bio = %s, avatar_color = %s WHERE id = %s",
        (bio_clean, avatar_color, user["id"])
    )
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/dashboard", status_code=303)


# --- SIMULACRO (MOCK EXAM) ---

@app.get("/simulacro", response_class=HTMLResponse)
async def simulacro_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request=request, name="simulacro.html", context={"user": user})

@app.get("/api/simulacro/questions")
async def get_simulacro_questions():
    limits = {
        "Matemáticas": 20,
        "Lectura Crítica": 20,
        "Ciencias Naturales": 20,
        "Sociales y Ciudadanas": 20,
        "Inglés": 25
    }
    areas = ["Matemáticas", "Lectura Crítica", "Ciencias Naturales", "Sociales y Ciudadanas", "Inglés"]
    conn = get_db()
    
    all_questions = []
    
    for area in areas:
        limit = limits[area]
        rows = conn.execute(
            "SELECT id, area, text, options, correct_answer, explanation, difficulty, graphic FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT %s",
            (area, limit)
        ).fetchall()
        
        area_questions = []
        for r in rows:
            try:
                opts = json.loads(r["options"])
            except Exception:
                opts = [r["correct_answer"], "Opción B", "Opción C", "Opción D"]
            q_obj = {
                "id": r["id"],
                "area": r["area"],
                "text": r["text"],
                "options": opts,
                "correct_answer": r["correct_answer"],
                "explanation": r["explanation"],
                "difficulty": r["difficulty"],
                "graphic": r["graphic"]
            }
            q_obj = process_parametric_question(q_obj)
            area_questions.append(q_obj)
            
        needed = limit - len(area_questions)
        if needed > 0:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3.1-flash-lite')
                    cursor = conn.cursor()
                    
                    prompt = f"""
                    Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
                    Genera una lista de {needed} preguntas de selección múltiple originales, inéditas y de alta calidad para el área de {area}.
                    
                    REGLAS DE DISEÑO ICFES:
                    - Para Matemáticas: modelación, formulación y ejecución, o argumentación.
                    - Para Lectura Crítica: fragmento corto y pregunta de inferencia.
                    - Para Ciencias Naturales: indagación o explicación de fenómenos.
                    - Para Sociales y Ciudadanas: dilema ético, conflicto social o multiperspectivismo.
                    - Para Inglés: gramática, vocabulario nivel A2/B1 o comprensión lectora.
                    
                    CRÍTICO: No incluyas números de pregunta (como "1.", "2.") en el texto de los enunciados.
                    
                    El formato de salida DEBE ser estrictamente una lista JSON en español, sin envolverlo en bloques markdown (sin ```json) y cada objeto con las siguientes llaves:
                       - "area": "{area}"
                       - "text": "[El enunciado de la pregunta. Si es Lectura Crítica o Ciencias, incluye primero el texto/contexto seguido de la pregunta]"
                       - "options": ["[Opción A]", "[Opción B]", "[Opción C]", "[Opción D]"]
                       - "correct_answer": "[Debe ser idéntica a una de las opciones]"
                       - "explanation": "[Justificación detallada de por qué es la clave correcta]"
                       - "difficulty": "Intermedio"
                    """
                    response = model.generate_content(prompt)
                    text_response = response.text.strip()
                    text_response = re.sub(r'^```json\s*|\s*```$', '', text_response, flags=re.MULTILINE)
                    q_list = json.loads(text_response)
                    
                    if isinstance(q_list, dict):
                        q_list = [q_list]
                        
                    for q_data in q_list:
                        cursor.execute('''
                            INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                        ''', (
                            area,
                            q_data["text"],
                            json.dumps(q_data["options"], ensure_ascii=False),
                            q_data["correct_answer"],
                            q_data["explanation"],
                            q_data.get("difficulty", "Intermedio")
                        ))
                        new_id = cursor.fetchone()[0]
                        area_questions.append({
                            "id": new_id,
                            "area": area,
                            "text": q_data["text"],
                            "options": q_data["options"],
                            "correct_answer": q_data["correct_answer"],
                            "explanation": q_data["explanation"],
                            "difficulty": q_data.get("difficulty", "Intermedio"),
                            "graphic": None
                        })
                    conn.commit()
                except Exception as e:
                    print(f"Error generating dynamic questions for {area} in mock exam:", e)
                    
        # Fallback if still less than limit
        if len(area_questions) < limit:
            fallbacks = {
                "Matemáticas": {"text": "¿Cuál es el valor de x si 2x + 5 = 15?", "options": ["5", "10", "15", "20"], "correct_answer": "5", "explanation": "Restando 5 a ambos lados queda 2x = 10, por tanto x = 5."},
                "Lectura Crítica": {"text": "En el texto discontinuo de una caricatura, el sarcasmo se usa principalmente para:", "options": ["Criticar de forma indirecta", "Hacer reír sin reflexionar", "Explicar científicamente", "Describir paisajes"], "correct_answer": "Criticar de forma indirecta", "explanation": "El sarcasmo en caricaturas políticas busca la crítica social indirecta."},
                "Ciencias Naturales": {"text": "¿Cuál de los siguientes es un cambio químico?", "options": ["La combustión de la madera", "La evaporación del agua", "La fusión del hielo", "La trituración de una piedra"], "correct_answer": "La combustión de la madera", "explanation": "La combustión altera la composición química de la materia, produciendo nuevas sustancias como CO2 y cenizas."},
                "Sociales y Ciudadanas": {"text": "¿Qué rama del poder público en Colombia se encarga de hacer las leyes?", "options": ["Rama Legislativa", "Rama Ejecutiva", "Rama Judicial", "Órganos de control"], "correct_answer": "Rama Legislativa", "explanation": "El Congreso de la República (Senado y Cámara) conforma la rama legislativa y hace las leyes."},
                "Inglés": {"text": "Choose the correct word: She ____ to the gym every day.", "options": ["goes", "go", "going", "gone"], "correct_answer": "goes", "explanation": "Third person singular in Present Simple requires 'goes'."}
            }
            f_q = fallbacks[area]
            for i in range(limit - len(area_questions)):
                area_questions.append({
                    "id": i + 5000 + (hash(area) % 1000),
                    "area": area,
                    "text": f_q["text"],
                    "options": f_q["options"],
                    "correct_answer": f_q["correct_answer"],
                    "explanation": f_q["explanation"],
                    "difficulty": "Intermedio",
                    "graphic": None
                })
        
        all_questions.extend(area_questions)
        
    conn.close()
    
    # Shuffle slightly so areas are mixed
    random.shuffle(all_questions)
    return {"questions": all_questions}

@app.post("/api/simulacro/result")
async def save_simulacro_result(request: Request, data: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    scores = data.get("scores", {})
    
    score_math = scores.get("Matemáticas", 0)
    score_reading = scores.get("Lectura Crítica", 0)
    score_science = scores.get("Ciencias Naturales", 0)
    score_social = scores.get("Sociales y Ciudadanas", 0)
    score_english = scores.get("Inglés", 0)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO diagnostic_results (user_id, score_math, score_reading, score_social, score_science, score_english)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (user["id"], score_math, score_reading, score_social, score_science, score_english))
    conn.commit()
    conn.close()
    
    # Calculate global score
    weighted_sum = (
        score_math * 3 +
        score_reading * 3 +
        score_science * 3 +
        score_social * 3 +
        score_english * 1
    )
    global_score = round((weighted_sum / 13) * 5)
    
    return {
        "status": "success",
        "global_score": global_score,
        "scores": {
            "Matemáticas": score_math,
            "Lectura Crítica": score_reading,
            "Ciencias Naturales": score_science,
            "Sociales y Ciudadanas": score_social,
            "Inglés": score_english
        }
    }


@app.get("/preview", response_class=HTMLResponse)
async def preview_temp_page(request: Request, type: str = "combinations"):
    if type == "geometry":
        import base64
        rect_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200">
  <rect width="100%" height="100%" fill="#0f172a"/>
  <rect x="40" y="30" width="240" height="120" fill="rgba(56, 189, 248, 0.1)" stroke="#38bdf8" stroke-width="3" />
  <text x="160" y="175" fill="#f8fafc" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle">base = {base} cm</text>
  <text x="25" y="95" fill="#f8fafc" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle" transform="rotate(-90 25 95)">altura = {altura} cm</text>
</svg>"""
        graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(rect_svg.encode('utf-8')).decode('utf-8')
        q_obj = {
            "id": 9997,
            "area": "Matemáticas",
            "text": "Determine el área del rectángulo mostrado en la figura si su base es de {base} cm y su altura es de {altura} cm.",
            "options": ["{correct}", "d1", "d2", "d3"],
            "correct_answer": "{correct}",
            "explanation": "",
            "difficulty": "Fácil",
            "graphic": graphic_uri
        }
    elif type == "algebra":
        q_obj = {
            "id": 9996,
            "area": "Matemáticas",
            "text": "Dada la función exponencial f(x) = {a} \\cdot 2^{{x {c_sign} {c_abs}}} + {d}, determine su valor cuando x = {x_eval}.",
            "options": ["{correct}", "d1", "d2", "d3"],
            "correct_answer": "{correct}",
            "explanation": "",
            "difficulty": "Intermedio",
            "graphic": None
        }
    elif type == "statistics":
        import base64
        chart_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" width="320" height="200">
  <rect width="100%" height="100%" fill="#0f172a"/>
  <line x1="40" y1="20" x2="40" y2="180" stroke="#94a3b8" stroke-width="2"/>
  <line x1="40" y1="180" x2="300" y2="180" stroke="#94a3b8" stroke-width="2"/>
  <rect x="60" y="{y_bar_1}" width="30" height="{h_bar_1}" fill="#f43f5e" rx="3"/>
  <rect x="120" y="{y_bar_2}" width="30" height="{h_bar_2}" fill="#3b82f6" rx="3"/>
  <rect x="180" y="{y_bar_3}" width="30" height="{h_bar_3}" fill="#10b981" rx="3"/>
  <rect x="240" y="{y_bar_4}" width="30" height="{h_bar_4}" fill="#f59e0b" rx="3"/>
  <text x="75" y="195" fill="#94a3b8" font-family="sans-serif" font-size="10" text-anchor="middle">10 pts</text>
  <text x="135" y="195" fill="#94a3b8" font-family="sans-serif" font-size="10" text-anchor="middle">20 pts</text>
  <text x="195" y="195" fill="#94a3b8" font-family="sans-serif" font-size="10" text-anchor="middle">30 pts</text>
  <text x="255" y="195" fill="#94a3b8" font-family="sans-serif" font-size="10" text-anchor="middle">40 pts</text>
  <text x="75" y="{y_txt_1}" fill="#ffffff" font-family="sans-serif" font-size="10" text-anchor="middle">{frec_1}</text>
  <text x="135" y="{y_txt_2}" fill="#ffffff" font-family="sans-serif" font-size="10" text-anchor="middle">{frec_2}</text>
  <text x="195" y="{y_txt_3}" fill="#ffffff" font-family="sans-serif" font-size="10" text-anchor="middle">{frec_3}</text>
  <text x="255" y="{y_txt_4}" fill="#ffffff" font-family="sans-serif" font-size="10" text-anchor="middle">{frec_4}</text>
</svg>"""
        graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(chart_svg.encode('utf-8')).decode('utf-8')
        q_obj = {
            "id": 9995,
            "area": "Matemáticas",
            "text": "La distribución de frecuencias es: {frec_1}, {frec_2}, {frec_3}, {frec_4}",
            "options": ["{correct}", "d1", "d2", "d3"],
            "correct_answer": "{correct}",
            "explanation": "",
            "difficulty": "Intermedio",
            "graphic": graphic_uri
        }
    elif type == "slope":
        import base64
        slope_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 200" width="240" height="200">
  <rect width="100%" height="100%" fill="#0f172a"/>
  <line x1="50" y1="30" x2="50" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="80" y1="30" x2="80" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="110" y1="30" x2="110" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="140" y1="30" x2="140" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="170" y1="30" x2="170" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="200" y1="30" x2="200" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="30" x2="200" y2="30" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="60" x2="200" y2="60" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="90" x2="200" y2="90" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="120" x2="200" y2="120" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="150" x2="200" y2="150" stroke="#334155" stroke-width="1" stroke-dasharray="2,2"/>
  <line x1="50" y1="15" x2="50" y2="165" stroke="#94a3b8" stroke-width="2"/>
  <line x1="35" y1="150" x2="215" y2="150" stroke="#94a3b8" stroke-width="2"/>
  <line x1="50" y1="150" x2="{x2_svg}" y2="{y2_svg}" stroke="#38bdf8" stroke-width="3"/>
  <circle cx="{x2_svg}" cy="{y2_svg}" r="5" fill="#f43f5e"/>
  <text x="{x2_lbl_svg}" y="{y2_lbl_svg}" fill="#f8fafc" font-family="sans-serif" font-size="10" font-weight="bold">P({a},{b})</text>
  <text x="45" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="end">0</text>
  <text x="80" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="middle">1</text>
  <text x="110" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="middle">2</text>
  <text x="140" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="middle">3</text>
  <text x="170" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="middle">4</text>
  <text x="200" y="162" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="middle">5</text>
  <text x="45" y="123" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="end">1</text>
  <text x="45" y="93" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="end">2</text>
  <text x="45" y="63" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="end">3</text>
  <text x="45" y="33" fill="#94a3b8" font-family="sans-serif" font-size="8" text-anchor="end">4</text>
</svg>"""
        graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(slope_svg.encode('utf-8')).decode('utf-8')
        q_obj = {
            "id": 9994,
            "area": "Matemáticas",
            "text": "La imagen representa una recta en el plano cartesiano que pasa por el origen (0,0) y por el punto P.",
            "options": ["{slope}", "d1", "d2", "d3"],
            "correct_answer": "{slope}",
            "explanation": "",
            "difficulty": "Intermedio",
            "graphic": graphic_uri
        }
    else:
        q_obj = {
            "id": 9998,
            "area": "Matemáticas",
            "text": "En un colegio se realiza una preselección de estudiantes para participar en las olimpiadas de matemáticas. De un grupo de {n_estudiantes} estudiantes destacados, el entrenador debe elegir a {k_seleccionados} de ellos para conformar el equipo oficial. ¿De cuántas formas diferentes se puede conformar el equipo?",
            "options": ["{correct_val}", "d1", "d2", "d3"],
            "correct_answer": "{correct_val}",
            "explanation": "",
            "difficulty": "Intermedio",
            "graphic": None
        }
        
    q_resolved = process_parametric_question(q_obj)
    
    return templates.TemplateResponse(
        request=request, 
        name="preview_temp.html", 
        context={"q": q_resolved}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

