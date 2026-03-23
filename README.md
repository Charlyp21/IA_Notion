# Neuro-Notion Telegram Bot

Bot de Telegram para consultar apuntes en Notion, generar resumenes tecnicos con Gemini y guardarlos en una base de Resumenes.

## Requisitos

- Linux (probado para flujo con EndeavourOS/Arch).
- Python 3.10 o superior.
- Un bot de Telegram creado con BotFather.
- Integracion de Notion creada y compartida con ambas bases de datos.
- API key de Gemini.

## Estructura del proyecto

- `bot.py`: comandos de Telegram y orquestacion del flujo.
- `notion_handler.py`: consulta de apuntes y creacion de paginas en Notion.
- `ai_handler.py`: generacion de resumenes con Gemini.
- `.env.example`: plantilla de variables de entorno.
- `requirements.txt`: dependencias de Python.

## Configuracion de Notion

1. Crea (o reutiliza) dos bases de datos:
   - DB de apuntes (debe tener propiedad `Materia` de tipo `Select`).
   - DB de resumenes (debe tener una propiedad de tipo `Title` y `Materia` tipo `Select`).
2. Comparte ambas bases con tu integracion de Notion.
3. Copia los IDs de las bases desde la URL de Notion.

## Instalacion en Linux (venv + pip)

```bash
cd IA_Notion
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Variables de entorno

1. Copia el ejemplo:

```bash
cp .env.example .env
```

2. Llena los valores en `.env`:

- `TELEGRAM_TOKEN`
- `NOTION_TOKEN`
- `NOTION_DB_APUNTES_ID`
- `NOTION_DB_RESUMENES_ID`
- `GEMINI_API_KEY`
- `PATH_HORARIO` (por defecto `assets/horario.png`)

## Ejecucion

```bash
python bot.py
```

## Comandos del bot

- `/start`: mensaje inicial.
- `/horario`: envia la imagen del horario usando `PATH_HORARIO`.
- `/resumir [materia] [YYYY-MM-DD]`: obtiene apuntes por materia desde la fecha indicada hasta hoy, genera resumen y lo guarda en Notion.

## Nota de escalabilidad

El codigo separa la logica por servicios (`NotionHandler`, `AIHandler`) para poder agregar nuevas integraciones, por ejemplo Google Calendar, sin reescribir la base del bot.