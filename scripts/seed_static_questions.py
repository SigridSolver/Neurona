import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection

# Banco de preguntas estáticas de alta calidad tipo Saber 11
STATIC_QUESTIONS = [
    {
        "area": "Ciencias Naturales",
        "text": "Un grupo de investigación estudia la degradación de un polímero usando hongos del género Pestalotiopsis. Si observan que en ausencia de oxígeno el polímero se degrada un 80% más lento, ¿cuál es la conclusión correcta sobre el metabolismo del hongo?",
        "options": [
            "El hongo realiza respiración principalmente aerobia para degradar el polímero de forma eficiente.",
            "El hongo es anaerobio estricto y el oxígeno actúa como un inhibidor de sus enzimas.",
            "La degradación del polímero no depende de la temperatura ni de la concentración de oxígeno.",
            "El hongo degrada el polímero mediante procesos fermentativos anaerobios únicamente."
        ],
        "correct_answer": "El hongo realiza respiración principalmente aerobia para degradar el polímero de forma eficiente.",
        "explanation": "El oxígeno actúa como aceptor final de electrones en la respiración aerobia, permitiendo una mayor producción de energía (ATP). Si la degradación disminuye significativamente en ausencia de oxígeno, significa que el metabolismo del hongo es principalmente aerobio o se ve altamente favorecido por la presencia de oxígeno.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Sociales y Ciudadanas",
        "text": "En una región del país, un proyecto de minería a gran escala es aprobado por el Gobierno Nacional sin consultar a la comunidad indígena local que habita el territorio. Según la Constitución de 1991, ¿qué mecanismo constitucional protege directamente el derecho de esta comunidad?",
        "options": [
            "La Consulta Previa y la Acción de Tutela",
            "El Referendo Derogatorio de la licencia ambiental",
            "La Acción Popular para la protección del suelo",
            "La Consulta Popular convocada por el alcalde municipal"
        ],
        "correct_answer": "La Consulta Previa y la Acción de Tutela",
        "explanation": "La Consulta Previa es un derecho fundamental de los grupos étnicos para decidir sobre proyectos que afecten sus territorios. Al no realizarse, se vulnera el debido proceso y la diversidad étnica, lo cual hace procedente la Acción de Tutela para suspender el proyecto y exigir la consulta.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Lectura Crítica",
        "text": "Considere la siguiente afirmación: 'Si bien la ciencia nos proporciona herramientas poderosas para manipular el entorno físico, carece por completo de la capacidad para resolver dilemas morales o definir qué es lo moralmente correcto'. La intención principal del autor al formular esta frase es:",
        "options": [
            "Delimitar el alcance epistemológico de la ciencia frente a la ética.",
            "Desacreditar los avances científicos recientes.",
            "Demostrar que la ética debe subordinarse al método científico.",
            "Promover la investigación ética en laboratorios científicos."
        ],
        "correct_answer": "Delimitar el alcance epistemológico de la ciencia frente a la ética.",
        "explanation": "Al señalar que la ciencia aporta herramientas materiales pero carece de facultad para decidir sobre dilemas morales, el autor establece una frontera o límite entre el conocimiento científico (hechos) y el juicio de valor ético (moral).",
        "difficulty": "Intermedio"
    },
    {
        "area": "Matemáticas",
        "text": "Un tanque de agua tiene la forma de un cilindro recto con un radio de 2 metros y una altura de 5 metros. Si el tanque se está llenando a un ritmo de 3 metros cúbicos por hora, ¿cuál es aproximadamente el tiempo total necesario para llenar el tanque por completo? (Aproxima pi a 3.14)",
        "options": [
            "20.9 horas",
            "10.5 horas",
            "15.2 horas",
            "31.4 horas"
        ],
        "correct_answer": "20.9 horas",
        "explanation": "El volumen de un cilindro es V = pi * r^2 * h. Sustituyendo: V = 3.14 * (2^2) * 5 = 3.14 * 4 * 5 = 62.8 metros cúbicos. Si se llena a 3 m^3/hora, el tiempo es 62.8 / 3 = 20.93 horas.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Inglés",
        "text": "Choose the correct option to complete the sentence: 'If I __________ about the heavy traffic, I would have taken a different route to the airport.'",
        "options": [
            "have known",
            "knew",
            "had known",
            "know"
        ],
        "correct_answer": "had known",
        "explanation": "Esta oración es un Condicional de Tercer Tipo (Third Conditional), que se utiliza para hablar de situaciones hipotéticas en el pasado. Su estructura requiere el pasado perfecto (had + participio) en la cláusula 'if'.",
        "difficulty": "Intermedio"
    },
    {
        "area": "Ciencias Naturales",
        "text": "La gráfica muestra que a mayor altitud, la presión atmosférica disminuye. Considerando esto, ¿por qué el agua hierve a menor temperatura en Bogotá (2.600 m s.n.m.) que en Cartagena (nivel del mar)?",
        "options": [
            "Porque la presión atmosférica menor facilita que las moléculas de agua alcancen la presión de vapor requerida para ebullir.",
            "Porque en Bogotá el calor se disipa más rápido debido al clima frío.",
            "Porque la gravedad es significativamente menor en Bogotá, afectando los enlaces moleculares.",
            "Porque a mayor altitud el agua pierde densidad y requiere más energía."
        ],
        "correct_answer": "Porque la presión atmosférica menor facilita que las moléculas de agua alcancen la presión de vapor requerida para ebullir.",
        "explanation": "El punto de ebullición se alcanza cuando la presión de vapor del líquido iguala a la presión atmosférica. Al ser menor la presión atmosférica en Bogotá, se requiere menos temperatura (menos energía) para que las moléculas escapen en forma de gas.",
        "difficulty": "Intermedio"
    },
    {
        "area": "Sociales y Ciudadanas",
        "text": "Durante el Frente Nacional en Colombia (1958-1974), los partidos Liberal y Conservador acordaron alternarse la presidencia y repartirse milimétricamente la burocracia. Una consecuencia política directa a largo plazo de este acuerdo fue:",
        "options": [
            "La exclusión sistemática de movimientos y partidos políticos alternativos, fomentando la creación de guerrillas.",
            "La erradicación total de la pobreza rural mediante reformas agrarias exitosas.",
            "La disolución de los partidos tradicionales y la creación de un modelo de partido único.",
            "El fin definitivo y absoluto de cualquier tipo de violencia en el territorio nacional."
        ],
        "correct_answer": "La exclusión sistemática de movimientos y partidos políticos alternativos, fomentando la creación de guerrillas.",
        "explanation": "El Frente Nacional excluyó del poder político a cualquier disidencia o tercer partido que no fuera el Liberal o el Conservador. Esta falta de vías democráticas de participación ciudadana para otros sectores fue uno de los detonantes de la insurgencia armada en los años 60.",
        "difficulty": "Intermedio"
    },
    {
        "area": "Matemáticas",
        "text": "En un estudio estadístico sobre los ingresos mensuales de 100 familias, se observa que la media (promedio) es de $5.000.000, pero la mediana es de $2.000.000. ¿Qué conclusión se puede sacar sobre la distribución de estos ingresos?",
        "options": [
            "Existe una gran desigualdad, con unas pocas familias ganando ingresos extremadamente altos que elevan el promedio.",
            "La mayoría de las familias ganan exactamente $5.000.000.",
            "Hay un error en el cálculo, ya que la media y la mediana siempre deben ser iguales.",
            "Los ingresos están distribuidos de manera perfectamente simétrica."
        ],
        "correct_answer": "Existe una gran desigualdad, con unas pocas familias ganando ingresos extremadamente altos que elevan el promedio.",
        "explanation": "Cuando la media es significativamente mayor que la mediana, indica una distribución sesgada a la derecha. Esto significa que hay valores atípicos muy altos (familias muy ricas) que jalan el promedio matemático hacia arriba, mientras que el valor central (mediana) muestra que el 50% de las familias ganan 2 millones o menos.",
        "difficulty": "Avanzado"
    },
    {
        "area": "Lectura Crítica",
        "text": "Lee el siguiente fragmento: 'No te pido que me lo expliques todo. Hay misterios en este mundo que perderían su encanto si fuesen reducidos a fórmulas. Solo te pido que no me mientas disfrazando tu ignorancia de certeza'. ¿Cuál es la actitud del narrador frente al interlocutor?",
        "options": [
            "Reclama honestidad intelectual y tolerancia hacia la incertidumbre.",
            "Exige una explicación científica de todos los fenómenos naturales.",
            "Justifica la mentira cuando se usa para proteger un misterio.",
            "Muestra indiferencia total frente al conocimiento científico."
        ],
        "correct_answer": "Reclama honestidad intelectual y tolerancia hacia la incertidumbre.",
        "explanation": "El narrador prefiere que el interlocutor acepte que hay cosas que no sabe (tolerancia al misterio o incertidumbre) en lugar de que finja tener la verdad absoluta (falsa certeza). Por ende, reclama honestidad intelectual.",
        "difficulty": "Intermedio"
    },
    {
        "area": "Inglés",
        "text": "Read the text: 'Renewable energy sources like solar and wind power are becoming increasingly cost-competitive with fossil fuels. However, energy storage remains a major hurdle.' What does the word 'hurdle' mean in this context?",
        "options": [
            "An obstacle or problem to be overcome.",
            "A fast type of renewable energy.",
            "A cheaper alternative to fossil fuels.",
            "A structural part of a wind turbine."
        ],
        "correct_answer": "An obstacle or problem to be overcome.",
        "explanation": "En este contexto, 'hurdle' se refiere a un obstáculo o dificultad técnica (el almacenamiento de energía) que aún debe resolverse en la industria de las energías renovables.",
        "difficulty": "Básico"
    }
]

def seed_static_db():
    print("Conectando a la base de datos de PostgreSQL...")
    conn = get_db_connection()
    cursor = conn
    
    # Limpiamos las preguntas antiguas para que quede limpio
    cursor.execute("DELETE FROM questions")
    
    inserted_count = 0
    
    for q in STATIC_QUESTIONS:
        cursor.execute('''
            INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (q["area"], q["text"], json.dumps(q["options"], ensure_ascii=False), q["correct_answer"], q["explanation"], q["difficulty"]))
        inserted_count += 1
        
    conn.commit()
    conn.close()
    print(f"¡Éxito! Se han sembrado {inserted_count} preguntas estáticas de alta calidad en la base de datos.")

if __name__ == "__main__":
    seed_static_db()
