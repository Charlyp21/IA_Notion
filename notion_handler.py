from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from notion_client import Client


class NotionHandler:
    def __init__(self, notion_token: str, apuntes_db_id: str, resumenes_db_id: str) -> None:
        self.client = Client(auth=notion_token)
        self.apuntes_db_id = apuntes_db_id
        self.resumenes_db_id = resumenes_db_id
        self.resumenes_title_property = self._find_title_property(resumenes_db_id)

    def _find_title_property(self, database_id: str) -> str:
        db_info = self.client.databases.retrieve(database_id=database_id)
        properties: dict[str, Any] = db_info.get("properties", {})
        for prop_name, prop_info in properties.items():
            if prop_info.get("type") == "title":
                return prop_name
        raise ValueError("No se encontro una propiedad de tipo title en la DB de Notion.")

    def _build_materia_fecha_filter(self, materia: str, fecha_iso: str) -> dict[str, Any]:
        fecha_dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
        fecha_siguiente = fecha_dt + timedelta(days=1)

        # Feynman: piensa en un colador doble. El primer colador deja pasar
        # solo la materia elegida y el segundo solo lo creado ese dia.
        return {
            "and": [
                {
                    "property": "Materia",
                    "select": {"equals": materia},
                },
                {
                    "timestamp": "created_time",
                    "created_time": {"on_or_after": fecha_dt.date().isoformat()},
                },
                {
                    "timestamp": "created_time",
                    "created_time": {"before": fecha_siguiente.date().isoformat()},
                },
            ]
        }

    def get_apuntes_by_materia_and_fecha(self, materia: str, fecha_iso: str) -> list[dict[str, Any]]:
        query_filter = self._build_materia_fecha_filter(materia=materia, fecha_iso=fecha_iso)
        result = self.client.databases.query(
            database_id=self.apuntes_db_id,
            filter=query_filter,
            page_size=50,
        )
        return result.get("results", [])

    def _extract_rich_text(self, rich_text: list[dict[str, Any]]) -> str:
        return "".join(chunk.get("plain_text", "") for chunk in rich_text)

    def extract_text_from_page_blocks(self, page_id: str) -> str:
        response = self.client.blocks.children.list(block_id=page_id, page_size=100)
        lines: list[str] = []

        # Feynman: cada bloque es como una ficha; leemos solo fichas con texto
        # (parrafo y listas) y luego armamos un solo apunte continuo.
        for block in response.get("results", []):
            block_type = block.get("type")

            if block_type == "paragraph":
                text = self._extract_rich_text(block["paragraph"].get("rich_text", []))
                if text.strip():
                    lines.append(text)
            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(block["bulleted_list_item"].get("rich_text", []))
                if text.strip():
                    lines.append(f"- {text}")
            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(block["numbered_list_item"].get("rich_text", []))
                if text.strip():
                    lines.append(f"1. {text}")

        return "\n".join(lines).strip()

    def create_resumen_page(self, materia: str, titulo: str, contenido: str, fuente_fecha: str) -> str:
        children: list[dict[str, Any]] = []
        for line in contenido.splitlines():
            clean = line.strip()
            if not clean:
                continue
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": clean[:1900]}}],
                    },
                }
            )

        properties: dict[str, Any] = {
            self.resumenes_title_property: {
                "title": [{"type": "text", "text": {"content": titulo[:200]}}],
            },
            "Materia": {"select": {"name": materia}},
        }

        if fuente_fecha:
            properties["Fecha"] = {"date": {"start": fuente_fecha}}

        page = self.client.pages.create(
            parent={"database_id": self.resumenes_db_id},
            properties=properties,
            children=children[:100],
        )
        return page.get("url", "")