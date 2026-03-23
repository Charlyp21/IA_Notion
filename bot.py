from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from ai_handler import AIHandler
from notion_handler import NotionHandler


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


@dataclass
class Services:
    notion: NotionHandler
    ai: AIHandler
    path_horario: Path


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    await update.message.reply_text(
        "Hola. Soy tu bot de apuntes en Notion.\n"
        "Usa /horario para ver tu horario y /resumir [materia] [YYYY-MM-DD] para resumir"
        " todos los apuntes de esa materia desde esa fecha hasta hoy."
    )


async def horario_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services: Services = context.application.bot_data["services"]

    if not services.path_horario.exists():
        await update.message.reply_text(
            f"No encontre la imagen del horario en: {services.path_horario}"
        )
        return

    with services.path_horario.open("rb") as image_file:
        await update.message.reply_photo(photo=image_file)


async def resumir_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    services: Services = context.application.bot_data["services"]

    if len(context.args) < 2:
        await update.message.reply_text(
            "Uso: /resumir [materia] [YYYY-MM-DD]\n"
            "Toma apuntes de la materia desde esa fecha hasta hoy."
        )
        return

    fecha = context.args[-1]
    materia = " ".join(context.args[:-1]).strip()
    if not materia:
        await update.message.reply_text("La materia no puede estar vacia.")
        return

    await update.message.reply_text("Buscando apuntes en Notion...")

    try:
        apuntes = services.notion.get_apuntes_by_materia_and_fecha(materia=materia, fecha_iso=fecha)
    except Exception as err:
        LOGGER.exception("Error consultando Notion")
        await update.message.reply_text(f"Error consultando Notion: {err}")
        return

    if not apuntes:
        await update.message.reply_text(
            "No encontre apuntes para esa materia desde la fecha indicada hasta hoy."
        )
        return

    textos: list[str] = []
    for page in apuntes:
        try:
            text = services.notion.extract_text_from_page_blocks(page_id=page["id"])
            if text:
                textos.append(text)
        except Exception:
            LOGGER.exception("Error leyendo bloques de la pagina %s", page.get("id"))

    if not textos:
        await update.message.reply_text("Encontre apuntes, pero no habia texto util en bloques.")
        return

    texto_fuente = "\n\n".join(textos)

    await update.message.reply_text("Generando resumen con Gemini...")
    try:
        resumen = services.ai.generate_summary(
            materia=materia,
            fecha=fecha,
            apuntes_texto=texto_fuente,
        )
    except Exception as err:
        LOGGER.exception("Error generando resumen con Gemini")
        await update.message.reply_text(f"Error usando Gemini: {err}")
        return

    if not resumen:
        await update.message.reply_text("Gemini no devolvio contenido para el resumen.")
        return

    await update.message.reply_text("Subiendo resumen a Notion...")
    try:
        page_url = services.notion.create_resumen_page(
            materia=materia,
            titulo=f"Resumen {materia} - {fecha}",
            contenido=resumen,
            fuente_fecha=fecha,
        )
    except Exception as err:
        LOGGER.exception("Error creando pagina de resumen en Notion")
        await update.message.reply_text(f"No pude guardar el resumen en Notion: {err}")
        return

    message = "Resumen creado y guardado en Notion."
    if page_url:
        message += f"\nURL: {page_url}"
    await update.message.reply_text(message)


def _build_services() -> tuple[str, Services]:
    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_TOKEN", "")
    notion_token = os.getenv("NOTION_TOKEN", "")
    db_apuntes = os.getenv("NOTION_DB_APUNTES_ID", "")
    db_resumenes = os.getenv("NOTION_DB_RESUMENES_ID", "")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    path_horario_env = os.getenv("PATH_HORARIO", "assets/horario.png")

    missing = [
        name
        for name, value in {
            "TELEGRAM_TOKEN": telegram_token,
            "NOTION_TOKEN": notion_token,
            "NOTION_DB_APUNTES_ID": db_apuntes,
            "NOTION_DB_RESUMENES_ID": db_resumenes,
            "GEMINI_API_KEY": gemini_api_key,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Variables faltantes en .env: {', '.join(missing)}")

    notion = NotionHandler(
        notion_token=notion_token,
        apuntes_db_id=db_apuntes,
        resumenes_db_id=db_resumenes,
    )
    ai = AIHandler(gemini_api_key=gemini_api_key)

    path_horario = Path(path_horario_env)
    if not path_horario.is_absolute():
        path_horario = Path(__file__).resolve().parent / path_horario

    services = Services(notion=notion, ai=ai, path_horario=path_horario)
    return telegram_token, services


def main() -> None:
    telegram_token, services = _build_services()

    app = ApplicationBuilder().token(telegram_token).build()
    app.bot_data["services"] = services

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("horario", horario_command))
    app.add_handler(CommandHandler("resumir", resumir_command))

    app.run_polling()


if __name__ == "__main__":
    main()