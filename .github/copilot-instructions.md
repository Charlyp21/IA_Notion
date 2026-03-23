# Instrucciones del Agente: Neuro-Notion Telegram Bot 🧠🤖

## Contexto del Usuario
- **Perfil:** Estudiante de Neurociencias en la UNAM (4to semestre).
- **Entorno:** EndeavourOS (Arch Linux) con KDE Plasma.
- **Stack:** Python (python-telegram-bot, notion-client, google-generativeai, python-dotenv).
- **Estilo de Código:** Modular (POO), limpio, con manejo de errores peer-to-peer y sin introducciones largas.

## Objetivo del Proyecto
Crear un bot de Telegram que gestione apuntes académicos en Notion, genere resúmenes de alta calidad técnica (Neurociencias/Ciencias Cognitivas) usando la API de Gemini y maneje utilidades escolares.

## Tareas de Generación de Archivos (Pasos Críticos)
El agente debe generar los siguientes archivos siguiendo estas directrices:

1. **`requirements.txt`**: Incluir `python-telegram-bot`, `notion-client`, `google-generativeai`, `python-dotenv`.
2. **`.env.example`**: Plantilla con las llaves necesarias (`TELEGRAM_TOKEN`, `NOTION_TOKEN`, `NOTION_DB_APUNTES_ID`, `NOTION_DB_RESUMENES_ID`, `GEMINI_API_KEY`, `PATH_HORARIO`).
3. **`notion_handler.py`**: 
   - Lógica para filtrar apuntes por `Materia` (Select) y `Fecha de creación` (Date).
   - Función para extraer texto de bloques (párrafos y listas).
   - Función para crear una nueva página en la DB de Resúmenes con la propiedad `Materia` pre-llenada.
4. **`ai_handler.py`**: 
   - Configuración de Gemini Pro.
   - Prompt de sistema especializado en Neurociencias para generar resúmenes académicos.
5. **`bot.py`**: 
   - Comando `/start`.
   - Comando `/horario`: Debe enviar la imagen desde la ruta definida en el `.env`.
   - Comando `/resumir [materia] [fecha]`: Orquestar la extracción de Notion, el procesamiento con Gemini y la subida del resumen.
6. **`README.md`**: Guía de instalación completa para un entorno Linux (venv, pip, configuración de IDs de Notion).

## Reglas de Implementación
- **Manejo de Secretos**: Prohibido hardcodear llaves. Usar siempre `os.getenv()`.
- **Explicación Feynman**: Al generar funciones complejas de la API de Notion (filtros anidados o estructuras de bloques), explica brevemente la lógica como si fuera una analogía simple.
- **Jerarquía Visual**: Usa encabezados y negritas en tus respuestas de chat.
- **Escalabilidad**: El código debe permitir añadir integración con Google Calendar en el futuro sin reescribir la base.

## Nota sobre el Horario
- La imagen se encuentra en la carpeta `assets/horario.png`. El bot debe manejar excepciones si el archivo no existe.

## Paso Final
Una vez generado el código, indica al usuario los pasos para activar el `venv` e instalar los requerimientos en su terminal de EndeavourOS.