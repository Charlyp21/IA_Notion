from __future__ import annotations

import logging
from typing import Any

try:
    import google.genai as genai
except ImportError as err:
    raise ImportError(
        "No se pudo importar google.genai. Instala/actualiza dependencias con: "
        "pip install -r requirements.txt"
    ) from err


SYSTEM_PROMPT = """
Eres un asistente academico experto en Neurociencias y Ciencias Cognitivas.
Tu tarea es redactar resumenes de alto rigor tecnico y claridad pedagogica.

Reglas:
- Mantener precision conceptual y terminologia cientifica.
- Explicar relaciones causales entre sistemas, estructuras y procesos.
- Incluir definiciones breves para terminos complejos.
- Organizar por secciones con subtitulos claros.
- Cerrar con un bloque llamado 'Puntos clave para examen'.
""".strip()


LOGGER = logging.getLogger(__name__)


class GeminiServiceError(RuntimeError):
    def __init__(self, user_message: str, debug_message: str, error_type: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.debug_message = debug_message
        self.error_type = error_type


class AIHandler:
    def __init__(self, gemini_api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        self.client = genai.Client(api_key=gemini_api_key)
        self.model_name = model_name

    @staticmethod
    def _classify_gemini_error(err: Exception) -> GeminiServiceError:
        status_code = getattr(err, "status_code", None)
        error_text = str(err).lower()

        if status_code == 429 or "429" in error_text or "rate" in error_text or "quota" in error_text:
            return GeminiServiceError(
                user_message="Gemini alcanzo el limite de uso. Intenta de nuevo en unos minutos.",
                debug_message=f"Rate limit o cuota agotada: {err}",
                error_type="rate_limit",
            )

        if status_code in (408, 503, 504) or "timeout" in error_text or "deadline" in error_text:
            return GeminiServiceError(
                user_message="Gemini no respondio a tiempo. Intenta de nuevo en un momento.",
                debug_message=f"Timeout o servicio no disponible: {err}",
                error_type="timeout",
            )

        return GeminiServiceError(
            user_message="Error de comunicacion con Gemini. Intenta nuevamente.",
            debug_message=f"Fallo de API Gemini: {err}",
            error_type="api_error",
        )

    def _generate_content_text(self, prompt: str) -> str:
        final_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}".strip()
        try:
            response: Any = self.client.models.generate_content(
                model=self.model_name,
                contents=final_prompt,
            )
        except GeminiServiceError:
            raise
        except Exception as err:
            raise self._classify_gemini_error(err) from err

        text = getattr(response, "text", "")
        return text.strip()

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def generate_summary(self, materia: str, fecha: str, apuntes_texto: str) -> str:
        prompt = f"""
Genera un resumen tecnico para la materia '{materia}' usando estos apuntes del dia {fecha}.

Formato obligatorio:
1) Titulo
2) Resumen estructurado por secciones
3) Puntos clave para examen

Apuntes fuente:
{apuntes_texto}
""".strip()
        return self._generate_content_text(prompt)

    def generate_definition(self, concepto: str) -> str:
        prompt = f"""
Define el concepto '{concepto}' en contexto de Neurociencias.

Formato obligatorio:
- Definicion clara y tecnica.
- Menciona su relevancia neurocientifica.
- Incluye un ejemplo breve de aplicacion.
- Respuesta maxima de 2000 caracteres.
""".strip()

        text = self._generate_content_text(prompt)
        if not text:
            LOGGER.warning("Gemini devolvio una definicion vacia para concepto: %s", concepto)
            return "No se pudo generar una definicion para ese concepto."
        return self._truncate_text(text, max_chars=2000)