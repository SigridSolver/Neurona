from abc import ABC, abstractmethod

class BaseArea(ABC):
    @property
    @abstractmethod
    def area_name(self) -> str:
        """Retorna el nombre oficial del área en el ICFES."""
        pass

    @abstractmethod
    def get_generation_prompt(self, needed_count: int) -> str:
        """Retorna el prompt de generación de preguntas para Gemini."""
        pass

    def process_question(self, q: dict, seed: int = None) -> dict:
        """
        Formatea o procesa la pregunta en tiempo de ejecución.
        Por defecto, devuelve la pregunta sin modificaciones.
        """
        return q
