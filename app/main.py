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


load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize App
app = FastAPI(title="David Saber 11")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "tu_clave_super_secreta_aqui"))

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
            JOIN (
                SELECT user_id, score_math, score_reading, score_science, score_social, score_english, MAX(date)
                FROM diagnostic_results
                GROUP BY user_id
            ) d ON u.id = d.user_id
        ''').fetchall()
        
        for row in leaderboard_rows:
            w_sum = (
                row["score_math"] * 3 +
                row["score_reading"] * 3 +
                row["score_science"] * 3 +
                row["score_social"] * 3 +
                row["score_english"] * 1
            )
            score = round((w_sum / 13) * 5)
            try:
                badges_list = json.loads(row["badges"]) if row["badges"] else []
            except Exception:
                badges_list = []
                
            leaderboard.append({
                "id": row["id"],
                "name": row["name"],
                "score": score,
                "avatar_color": row["avatar_color"] or "#3b82f6",
                "bio": row["bio"] or "",
                "streak": row["streak"] or 0,
                "badges": badges_list
            })
            
        leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:5]
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
    return templates.TemplateResponse(request=request, name="practica.html")

@app.get("/api/questions/{area}")
async def get_practice_questions(area: str):
    conn = get_db()
    # Query 5 random questions matching the selected area
    rows = conn.execute(
        "SELECT id, area, text, options, correct_answer, explanation, difficulty, graphic FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 5",
        (area,)
    ).fetchall()
    conn.close()
    
    questions = []
    for r in rows:
        try:
            opts = json.loads(r["options"])
            random.shuffle(opts)
        except Exception:
            opts = [r["correct_answer"], "Opción B", "Opción C", "Opción D"]
            random.shuffle(opts)
            
        questions.append({
            "id": r["id"],
            "area": r["area"],
            "text": r["text"],
            "options": opts,
            "correct_answer": r["correct_answer"],
            "explanation": r["explanation"],
            "difficulty": r["difficulty"],
            "graphic": r["graphic"]
        })
        
    # Fallback to simulated questions if none found
    if not questions:
        for i in range(5):
            questions.append({
                "id": i + 1,
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

class ChatMessage(BaseModel):
    role: str
    parts: list[str]

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    image_base64: str | None = None

@app.get("/tutor", response_class=HTMLResponse)
async def tutor_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request=request, name="tutor.html", context={"user": user})

@app.post("/api/chat")
async def chat_api(request: Request, body: ChatRequest):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    user_msg = body.message
    
    # Check if Gemini is configured (only from environment)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            conn = get_db()
            diagnostic = conn.execute("SELECT * FROM diagnostic_results WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user["id"],)).fetchone()
            conn.close()
            
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
            
            # Format history for Gemini API
            gemini_history = []
            for h in body.history:
                # The google-generativeai API requires parts to be a list of strings for simple text
                gemini_history.append({"role": h.role, "parts": h.parts})
                
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
                    model_name='gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_content)
            except Exception as e_model:
                print("Failed with gemini-2.5-flash, trying gemini-1.5-flash fallback:", e_model)
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_content)
                
            return {"response": response.text, "mode": "ai"}
        except Exception as e:
            print("Gemini API Error:", e)
            return {
                "response": f"Hola. La consulta a la API de Gemini falló con el siguiente error: `{str(e)}`. Por favor, verifica la clave API en tus variables de entorno de Render.com (GEMINI_API_KEY).",
                "mode": "local"
            }
            
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
        return {
            "response": (
                "Hola. Como Tutor IA de David Saber 11, mi propósito está estrictamente limitado "
                "a ayudarte con temas relacionados a las áreas del examen Saber 11 (Matemáticas, "
                "Lectura Crítica, Ciencias Naturales, Sociales y Ciudadanas, e Inglés). "
                "No puedo responder a preguntas sobre otros temas."
            ),
            "mode": "local_restricted"
        }
        
    conn = get_db()
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
                
    conn.close()
    
    notice = ""
    if not api_key:
        notice = (
            "\n\n*(Nota: Configura tu clave `GEMINI_API_KEY` en un archivo `.env` "
            "en la raíz para habilitar un chat conversacional fluido con IA. "
            "Actualmente estás en modo de búsqueda local).* "
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
        
    return {"response": response_text, "mode": "local"}

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
            model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=system_instruction)
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

@app.get("/duelos", response_class=HTMLResponse)
async def duels_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    conn = get_db()
    bots = conn.execute(
        "SELECT name, avatar_color, bio, streak, id FROM users WHERE email IN ('carlos@saber11.edu.co', 'sofia@saber11.edu.co', 'mateo@saber11.edu.co', 'valeria@saber11.edu.co')"
    ).fetchall()
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="duelos.html", 
        context={"user": user, "opponents": bots}
    )


@app.post("/api/duelos/start")
async def start_duel(request: Request, body: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    area = body.get("area", "Matemáticas")
    
    conn = get_db()
    rows = conn.execute(
        "SELECT id, area, text, options, correct_answer, explanation, difficulty FROM questions WHERE area = %s ORDER BY RANDOM() LIMIT 3",
        (area,)
    ).fetchall()
    
    questions = []
    for r in rows:
        try:
            opts = json.loads(r["options"])
            random.shuffle(opts)
        except Exception:
            opts = [r["correct_answer"], "Opción B", "Opción C", "Opción D"]
            random.shuffle(opts)
            
        questions.append({
            "id": r["id"],
            "area": r["area"],
            "text": r["text"],
            "options": opts,
            "correct_answer": r["correct_answer"],
            "explanation": r["explanation"]
        })
        
    if len(questions) < 3:
        mock_qs = {
            "Matemáticas": [
                {"text": "¿Cuál es la probabilidad de obtener un número par al lanzar un dado de 6 caras?", "options": ["1/2", "1/3", "2/3", "1/6"], "correct_answer": "1/2", "explanation": "Los números pares son 2, 4 y 6 (3 casos favorables de 6 posibles, es decir, 3/6 = 1/2)."},
                {"text": "Si 3x - 5 = 10, ¿cuál es el valor de x?", "options": ["5", "3", "15", "10"], "correct_answer": "5", "explanation": "Sumando 5 a ambos lados da 3x = 15. Dividiendo por 3 se obtiene x = 5."},
                {"text": "¿Cuál es el área de un rectángulo con base de 8 cm y altura de 5 cm?", "options": ["40 cm²", "26 cm²", "13 cm²", "20 cm²"], "correct_answer": "40 cm²", "explanation": "El área de un rectángulo es base por altura: 8 * 5 = 40 cm²."}
            ],
            "Ciencias Naturales": [
                {"text": "¿Qué organelo celular se encarga de la síntesis de proteínas?", "options": ["Ribosoma", "Mitocondria", "Aparato de Golgi", "Lisosoma"], "correct_answer": "Ribosoma", "explanation": "Los ribosomas son las estructuras celulares donde se realiza la traducción y síntesis de proteínas."},
                {"text": "¿Cuál es el gas más abundante en la atmósfera terrestre?", "options": ["Nitrógeno", "Oxígeno", "Dióxido de carbono", "Argón"], "correct_answer": "Nitrógeno", "explanation": "El nitrógeno compone aproximadamente el 78% de la atmósfera de la Tierra."},
                {"text": "El agua pasa de estado gaseoso a líquido mediante el proceso de:", "options": ["Condensación", "Evaporación", "Solidificación", "Fusión"], "correct_answer": "Condensación", "explanation": "La condensación es el cambio de fase de gas a líquido."}
            ],
            "Lectura Crítica": [
                {"text": "¿Cuál es la función principal de un conector adversativo como 'sin embargo'?", "options": ["Indicar oposición o contraste", "Indicar adición", "Indicar causa", "Indicar consecuencia"], "correct_answer": "Indicar oposición o contraste", "explanation": "Los conectores adversativos introducen un contraste u oposición entre ideas."},
                {"text": "Un texto argumentativo tiene como propósito principal:", "options": ["Persuadir al lector sobre una tesis", "Narrar una historia de ficción", "Describir detalladamente un objeto", "Instruir sobre un procedimiento"], "correct_answer": "Persuadir al lector sobre una tesis", "explanation": "Los textos argumentativos buscan convencer o persuadir a través de razones y argumentos."},
                {"text": "La ironía en un fragmento literario sirve usualmente para:", "options": ["Dar a entender lo contrario de lo que se dice expresamente", "Exagerar las cualidades de un personaje", "Hacer rimas poéticas", "Definir términos científicos"], "correct_answer": "Dar a entender lo contrario de lo que se dice expresamente", "explanation": "La ironía consiste en dar a entender lo contrario de lo que se dice, con tono burlesco o crítico."}
            ],
            "Sociales y Ciudadanas": [
                {"text": "¿Cuál es el mecanismo constitucional para proteger de manera inmediata los Derechos Fundamentales en Colombia?", "options": ["Acción de Tutela", "Acción Popular", "Derecho de Petición", "Plebiscito"], "correct_answer": "Acción de Tutela", "explanation": "La acción de tutela está consagrada en el Artículo 86 de la Constitución para proteger de forma inmediata los derechos constitucionales fundamentales."},
                {"text": "¿Quién ejerce la función de hacer las leyes en la República de Colombia?", "options": ["El Congreso de la República", "El Presidente de la República", "La Corte Suprema de Justicia", "El Alcalde Mayor"], "correct_answer": "El Congreso de la República", "explanation": "La rama legislativa, representada por el Congreso (Senado y Cámara de Representantes), hace las leyes."},
                {"text": "El plebiscito es un mecanismo de participación ciudadana mediante el cual:", "options": ["El Presidente convoca al pueblo para pronunciarse sobre sus políticas", "Se eligen los miembros del Congreso", "Se destituye a un alcalde", "Se aprueba un proyecto de ley ordinaria"], "correct_answer": "El Presidente convoca al pueblo para pronunciarse sobre sus políticas", "explanation": "El plebiscito es el pronunciamiento del pueblo convocado por el Presidente de la República para apoyar o rechazar una decisión del Ejecutivo."}
            ],
            "Inglés": [
                {"text": "Complete: She ________ study English last night.", "options": ["didn't", "don't", "doesn't", "hasn't"], "correct_answer": "didn't", "explanation": "Para el pasado simple negativo se usa el auxiliar 'didn't' seguido del verbo en infinitivo."},
                {"text": "What is the opposite of 'sharp'?", "options": ["dull", "bright", "narrow", "clever"], "correct_answer": "dull", "explanation": "'Sharp' significa afilado o agudo, y su opuesto es 'dull' (desafiliado o apagado)."},
                {"text": "Complete: I have ________ in Bogotá for five years.", "options": ["lived", "live", "living", "lives"], "correct_answer": "lived", "explanation": "El presente perfecto requiere el verbo auxiliar 'have/has' y el participio pasado del verbo principal ('lived')."}
            ]
        }
        questions = mock_qs.get(area, mock_qs["Matemáticas"])[:3]
        
    opponent_name = body.get("opponent_name", "Carlos Gómez")
    opponent_row = conn.execute(
        "SELECT name, avatar_color, bio, streak FROM users WHERE name = %s", 
        (opponent_name,)
    ).fetchone()
    
    if opponent_row:
        opponent = {
            "name": opponent_row["name"],
            "avatar_color": opponent_row["avatar_color"] or "#10b981",
            "bio": opponent_row["bio"] or "",
            "streak": opponent_row["streak"] or 0
        }
    else:
        opponent = {
            "name": "Carlos Gómez",
            "avatar_color": "#10b981",
            "bio": "¡Estudiando duro para Ingeniería! 🚀",
            "streak": 5
        }
        
    conn.close()
    
    return {
        "questions": questions,
        "opponent": opponent
    }


@app.post("/api/duelos/result")
async def save_duel_result(request: Request, body: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
        
    user_score = body.get("score", 0)
    area = body.get("area", "Matemáticas")
    opponent_name = body.get("opponent_name", "Carlos Gómez")
    
    opponent_score = random.choices([0, 1, 2, 3], weights=[10, 20, 45, 25], k=1)[0]
    
    winner = "tie"
    streak_bonus = False
    
    if user_score > opponent_score:
        winner = "user"
    elif user_score < opponent_score:
        winner = "opponent"
        
    conn = get_db()
    cursor = conn.cursor()
    
    from datetime import date
    today_str = date.today().isoformat()
    current_streak = user["streak"] or 0
    
    if winner == "user":
        current_streak += 1
        streak_bonus = True
        
        badges_list = []
        try:
            badges_list = json.loads(user["badges"]) if user["badges"] else []
        except Exception:
            pass
            
        if "Duelos Ganados" not in badges_list:
            badges_list.append("Duelos Ganados")
            cursor.execute("UPDATE users SET badges = %s WHERE id = %s", (json.dumps(badges_list), user["id"]))
            
        cursor.execute("UPDATE users SET streak = %s, last_active_date = %s WHERE id = %s", (current_streak, today_str, user["id"]))
    
    session_title = f"Duelo contra {opponent_name} ({area})"
    cursor.execute('''
        INSERT INTO practice_sessions (user_id, area, difficulty, score, total_questions)
        VALUES (%s, %s, 'Rápido 1v1', %s, 3)
    ''', (user["id"], session_title, user_score))
    
    conn.commit()
    
    updated_user = cursor.execute("SELECT streak, badges FROM users WHERE id = %s", (user["id"],)).fetchone()
    user_streak = updated_user["streak"]
    user_badges = json.loads(updated_user["badges"]) if updated_user["badges"] else []
    
    conn.close()
    
    return {
        "status": "success",
        "winner": winner,
        "user_score": user_score,
        "opponent_score": opponent_score,
        "streak": user_streak,
        "badges": user_badges,
        "streak_bonus": streak_bonus
    }


# --- MICROLEARNING (FLASHCARDS) ---

@app.get("/aprender", response_class=HTMLResponse)
async def learn_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    flashcards = [
        {
            "id": 1,
            "area": "Matemáticas",
            "title": "Área del Círculo",
            "front": "¿Cómo se calcula el área de un círculo y qué representa Pi (π)?",
            "back": "Fórmula: A = π * r²\n\n- π (Pi) es aproximadamente 3.1416.\n- r es el radio del círculo.\n\nTip Saber 11: Muchas veces dejan la respuesta expresada en términos de π (ej. 25π) sin multiplicar. ¡Fíjate bien en las opciones antes de operar!"
        },
        {
            "id": 2,
            "area": "Ciencias Naturales",
            "title": "Efecto Invernadero",
            "front": "¿Qué es el efecto invernadero y qué gas es su principal causante de origen humano?",
            "back": "Es el calentamiento natural de la Tierra provocado por gases en la atmósfera que retienen calor. El principal causante de origen humano es el Dióxido de Carbono (CO₂).\n\nTip Saber 11: Distingue entre efecto invernadero natural (esencial para la vida) y el calentamiento global acelerado por el hombre."
        },
        {
            "id": 3,
            "area": "Sociales y Ciudadanas",
            "title": "Acción de Tutela",
            "front": "¿Qué es la Acción de Tutela y cuándo se debe interponer?",
            "back": "Es un mecanismo constitucional en Colombia para proteger de forma inmediata los Derechos Fundamentales (vida, salud, libre expresión, etc.) cuando estos sean vulnerados o amenazados por autoridades o particulares.\n\nTip Saber 11: Solo se puede usar cuando no exista otro medio de defensa judicial, salvo que sea para evitar un perjuicio irremediable."
        },
        {
            "id": 4,
            "area": "Lectura Crítica",
            "title": "Tesis Textual",
            "front": "¿Qué es la tesis en un texto argumentativo?",
            "back": "Es la postura, opinión o idea central que el autor defiende a lo largo del texto mediante argumentos.\n\nTip Saber 11: La tesis no es un hecho indiscutible, sino una afirmación debatible. Suele estar al inicio (introducción) o al final (conclusión) del fragmento."
        },
        {
            "id": 5,
            "area": "Inglés",
            "title": "Present Perfect vs Simple Past",
            "front": "¿Cuándo se usa Present Perfect ('I have lived') en comparación con Simple Past ('I lived')?",
            "back": "- Simple Past: Acciones que terminaron en un tiempo específico en el pasado. (Ej: 'I visited Paris in 2022').\n- Present Perfect: Acciones que ocurrieron en un tiempo no especificado o que conectan el pasado con el presente. (Ej: 'I have visited Paris twice')."
        },
        {
            "id": 6,
            "area": "Matemáticas",
            "title": "Teorema de Pitágoras",
            "front": "¿En qué tipo de triángulos se aplica el Teorema de Pitágoras y cuál es su fórmula?",
            "back": "Se aplica exclusivamente en triángulos rectángulos (que tienen un ángulo de 90°).\n\nFórmula: h² = a² + b² (donde h es la hipotenusa y a, b son los catetos).\n\nTip Saber 11: Aprende los tríos pitagóricos más comunes: (3, 4, 5) y (5, 12, 13). Te ahorrarán mucho tiempo en el examen."
        }
    ]
    
    return templates.TemplateResponse(
        request=request, 
        name="aprender.html", 
        context={"user": user, "flashcards": flashcards}
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

