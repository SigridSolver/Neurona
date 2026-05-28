import re
import json
import base64
from pathlib import Path

from app.database import get_db_connection
from app.exams.registry import EXAM_REGISTRY
from app.main import ensure_svg_xmlns


def strip_markdown_blocks(text: str) -> str:
    """Remove surrounding markdown fences like ```json``` from a string."""
    # Remove leading/trailing markdown fences if present
    pattern = r"^\s*```(?:json)?\s*|\s*```\s*$"
    return re.sub(pattern, "", text, flags=re.MULTILINE).strip()


def parse_llm_response(response_text: str) -> list:
    """Parse the LLM response text into a list of question dicts.
    Handles possible markdown code fences and ensures a list return.
    """
    cleaned = strip_markdown_blocks(response_text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"    Error parsing JSON from LLM response: {e}")
        return []
    if isinstance(data, dict):
        data = [data]
    return data


def save_questions_to_db(q_list: list, area: str, exam_type: str) -> int:
    """Insert questions into the DB, avoiding duplicates and handling SVG graphics.
    Returns the number of inserted questions.
    """
    conn = get_db_connection()
    cursor = conn
    inserted = 0
    for q_data in q_list:
        # Duplicate check
        try:
            exists = cursor.execute(
                "SELECT id FROM questions WHERE exam_type = %s AND text = %s",
                (exam_type, q_data["text"])
            ).fetchone()
        except Exception as e:
            print(f"    DB duplicate check failed: {e}")
            continue
        if exists:
            continue
        graphic_val = q_data.get("graphic")
        if graphic_val and "base64," not in graphic_val and "<svg" in graphic_val:
            try:
                import base64
                graphic_val = ensure_svg_xmlns(graphic_val)
                graphic_val = "data:image/svg+xml;base64," + base64.b64encode(graphic_val.encode('utf-8')).decode('utf-8')
            except Exception as e:
                print(f"    Error encoding SVG: {e}")
                graphic_val = None
        # Validate SVG proportionality
        if graphic_val:
            from scripts.generate_ai_questions_utils import validate_svg_proportionality
            if not validate_svg_proportionality(graphic_val):
                print("    SVG validation failed, skipping graphic.")
                graphic_val = None
        try:
            cursor.execute('''
                INSERT INTO questions (area, text, options, correct_answer, explanation, difficulty, graphic, exam_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                area,
                q_data["text"],
                json.dumps(q_data["options"], ensure_ascii=False),
                q_data["correct_answer"],
                q_data.get("explanation", ""),
                q_data.get("difficulty", "Intermedio"),
                graphic_val,
                exam_type
            ))
            inserted += 1
        except Exception as e:
            print(f"    Error inserting question: {e}")
            continue
    conn.commit()
    conn.close()
    return inserted


def validate_svg_proportionality(svg: str) -> bool:
    """Very naive placeholder: check that the SVG contains a <svg> tag.
    Real implementation would parse arcs and compare angles to percentages.
    Returns True if something looks like an SVG, False otherwise.
    """
    if not svg:
        return False
    if "<svg" not in svg.lower():
        return False
    # Simple check: ensure there is at least one <path> element (common for arcs)
    return bool(re.search(r"<path", svg, re.IGNORECASE))
