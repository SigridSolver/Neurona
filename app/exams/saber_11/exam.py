from app.exams.base_exam import BaseExam
from app.exams.saber_11.matematicas import MatematicasArea
from app.exams.saber_11.lectura_critica import LecturaCriticaArea
from app.exams.saber_11.ciencias_naturales import CienciasNaturalesArea
from app.exams.saber_11.sociales import SocialesArea
from app.exams.saber_11.ingles import InglesArea

class Saber11Exam(BaseExam):
    @property
    def exam_id(self) -> str:
        return "saber_11"

    @property
    def display_name(self) -> str:
        return "Saber 11°"

    @property
    def areas(self):
        return {
            "Matemáticas": MatematicasArea(),
            "Lectura Crítica": LecturaCriticaArea(),
            "Ciencias Naturales": CienciasNaturalesArea(),
            "Sociales y Ciudadanas": SocialesArea(),
            "Inglés": InglesArea()
        }
