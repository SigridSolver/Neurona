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
    text = q.get("text", "")
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
                if "{inclinacion}" in decoded:
                    decoded = decoded.replace("{inclinacion}", str(inclinacion))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = header + "base64," + new_encoded
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
                decoded = decoded.replace("{futbol_solo}", str(futbol_solo))
                decoded = decoded.replace("{ambos}", str(ambos))
                decoded = decoded.replace("{baloncesto_solo}", str(baloncesto_solo))
                decoded = decoded.replace("{ninguno}", str(ninguno))
                new_encoded = base64.b64encode(decoded.encode("utf-8")).decode("utf-8")
                graphic = header + "base64," + new_encoded
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
            
            # Generate the needed questions in a single prompt to prevent timeout
            prompt = f"""
            Eres un diseñador experto de pruebas Saber 11 (ICFES) en Colombia.
            Genera una lista de {needed} preguntas de selección múltiple originales, inéditas y de alta calidad para el área de {area}.
            
            REGLAS DE DISEÑO ICFES SABER 11:
            1. Para **Matemáticas**: Enfócate en modelación, formulación y ejecución, o argumentación.
            2. Para **Lectura Crítica**: Crea un fragmento corto e interesante (filosófico, literario, opinión) y formula una pregunta de inferencia.
            3. Para **Ciencias Naturales**: Plantea una situación de investigación, laboratorio o fenómeno ecológico/físico/químico.
            4. Para **Sociales y Ciudadanas**: Plantea un conflicto social, dilema ético, o análisis de multiperspectivismo.
            5. Para **Inglés**: Gramática y vocabulario de nivel A2/B1 o comprensión lectora.
            
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
                    None
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
                    "graphic": None
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
            "SELECT id, area, text, correct_answer, explanation FROM questions ORDER BY RANDOM() LIMIT 5"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, area, text, correct_answer, explanation FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 5",
            (area,)
        ).fetchall()
        
    questions = []
    for r in rows:
        questions.append({
            "id": r["id"],
            "area": r["area"],
            "text": r["text"],
            "correct_answer": r["correct_answer"],
            "explanation": r["explanation"]
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
                3. Para **Ciencias Naturales**: Plantea una situación de investigación, laboratorio o fenómeno ecológico/físico/químico donde se evalúe indagación o explicación de fenómenos.
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
                    questions.append({
                        "id": new_id,
                        "area": q_data["area"],
                        "text": q_data["text"],
                        "correct_answer": q_data["correct_answer"],
                        "explanation": q_data["explanation"]
                    })
                conn.commit()
            except Exception as e:
                print("Error generating dynamic flashcard questions:", e)
                
    conn.close()
    
    # Fallback to make sure we have 5 cards if Gemini failed or is not available
    if len(questions) < 5:
        fallbacks = [
            {"id": 901, "area": "Matemáticas", "text": "¿Cómo se calcula el área de un círculo?", "correct_answer": "A = π * r²", "explanation": "π es la relación entre el perímetro y el diámetro de un círculo, r es el radio."},
            {"id": 902, "area": "Ciencias Naturales", "text": "¿Cuál es el gas causante del efecto invernadero más emitido por actividades humanas?", "correct_answer": "Dióxido de Carbono (CO₂)", "explanation": "El CO₂ es emitido principalmente por la quema de combustibles fósiles."},
            {"id": 903, "area": "Sociales y Ciudadanas", "text": "¿Qué mecanismo protege de forma inmediata los derechos fundamentales en Colombia?", "correct_answer": "La Acción de Tutela", "explanation": "Establecida en el artículo 86 de la Constitución de 1991."},
            {"id": 904, "area": "Lectura Crítica", "text": "¿Qué es la tesis de un texto argumentativo?", "correct_answer": "La idea u opinión central que el autor defiende", "explanation": "Es la columna vertebral del texto argumentativo y se sustenta con argumentos."},
            {"id": 905, "area": "Inglés", "text": "What is the correct auxiliary verb for the Present Perfect tense?", "correct_answer": "Have / Has", "explanation": "Present perfect uses have/has + past participle."}
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
            "back": back_text
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
async def preview_temp_page(request: Request):
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

    import base64
    pisa_graphic_uri = "data:image/svg+xml;base64," + base64.b64encode(pisa_svg.encode('utf-8')).decode('utf-8')
    
    q_obj = {
        "id": 9999,
        "area": "Matemáticas",
        "text": "Con respecto a la vertical, la torre se ha inclinado {inclinacion}° como se muestra en la gráfica. ¿Cuánto mide el otro ángulo (indicado con el signo de interrogación)?",
        "options": ["{inclinacion}°", "{correct}°", "90°", "180°"],
        "correct_answer": "{correct}°",
        "explanation": "La línea vertical de referencia es perpendicular al suelo, por lo que forma un ángulo recto de 90°. Como la inclinación de la torre es de {inclinacion}° respecto a la vertical, el ángulo interno correspondiente entre la torre y la superficie disminuye en la misma cantidad: 90° - {inclinacion}° = {correct}°.",
        "difficulty": "Fácil",
        "graphic": pisa_graphic_uri
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

