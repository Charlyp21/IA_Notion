from __future__ import annotations

import google.generativeai as genai


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


class AIHandler:
    def __init__(self, gemini_api_key: str, model_name: str = "gemini-1.5-pro") -> None:
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

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

        response = self.model.generate_content(prompt)
        text = getattr(response, "text", "")
        return text.strip()