from abc import ABC, abstractmethod
from app.exams.base_area import BaseArea

class BaseExam(ABC):
    @property
    @abstractmethod
    def exam_id(self) -> str:
        """Retorna el ID interno del examen (ej: 'saber_11', 'saber_pro')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nombre legible (ej: 'Saber 11°', 'Saber Pro')."""
        pass

    @property
    @abstractmethod
    def areas(self) -> dict[str, BaseArea]:
        """Diccionario de áreas/materias que evalúa este examen."""
        pass
