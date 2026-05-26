from app.areas.matematicas import MatematicasArea
from app.areas.lectura_critica import LecturaCriticaArea
from app.areas.ciencias_naturales import CienciasNaturalesArea
from app.areas.sociales import SocialesArea
from app.areas.ingles import InglesArea

AREA_REGISTRY = {
    "Matemáticas": MatematicasArea(),
    "Lectura Crítica": LecturaCriticaArea(),
    "Ciencias Naturales": CienciasNaturalesArea(),
    "Sociales y Ciudadanas": SocialesArea(),
    "Inglés": InglesArea()
}
