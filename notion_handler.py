from __future__ import annotations

from datetime import datetime
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError


class NotionHandler:
    def __init__(
        self,
        notion_token: str,
        apuntes_db_id: str,
        resumenes_db_id: str,
        resumenes_title_property: str | None = None,
    ) -> None:
        self.client = Client(auth=notion_token)
        self.apuntes_db_id = apuntes_db_id
        self.resumenes_db_id = resumenes_db_id
        self.apuntes_data_source_id = self._get_primary_data_source_id(apuntes_db_id)
        self.resumenes_data_source_id = self._get_primary_data_source_id(resumenes_db_id)
        self.resumenes_title_property = self._find_title_property(
            resumenes_db_id,
            preferred_title_property=resumenes_title_property,
        )

    @staticmethod
    def _properties_debug(properties: dict[str, Any]) -> str:
        if not properties:
            return "(sin propiedades)"
        return ", ".join(f"{name}:{info.get('type', 'unknown')}" for name, info in properties.items())

    def _get_primary_data_source_id(self, database_id: str) -> str | None:
        try:
            db_info = self.client.databases.retrieve(database_id=database_id)
        except APIResponseError:
            return None

        data_sources = db_info.get("data_sources", [])
        if not data_sources:
            return None

        first = data_sources[0]
        return first.get("id")

    def _find_title_property(
        self,
        database_id: str,
        preferred_title_property: str | None = None,
    ) -> str:
        try:
            db_info = self.client.databases.retrieve(database_id=database_id)
        except APIResponseError as err:
            raise RuntimeError(
                "No se pudo acceder a la base de datos de Resumenes en Notion. "
                "Verifica el ID y comparte la DB con tu integracion. "
                f"Detalle: {err}"
            ) from err

        properties: dict[str, Any] = db_info.get("properties", {})

        # En el modelo nuevo de Notion, las propiedades pueden venir en data_sources.
        if not properties and self.resumenes_data_source_id:
            try:
                ds_info = self.client.data_sources.retrieve(
                    data_source_id=self.resumenes_data_source_id
                )
            except APIResponseError as err:
                raise RuntimeError(
                    "La DB de Resumenes usa data_sources, pero no se pudo leer su esquema. "
                    f"Data source id: {self.resumenes_data_source_id}. Detalle: {err}"
                ) from err

            properties = ds_info.get("properties", {})

        if preferred_title_property:
            if preferred_title_property in properties:
                return preferred_title_property
            raise ValueError(
                "La propiedad de titulo configurada en NOTION_RESUMEN_TITLE_PROPERTY "
                f"('{preferred_title_property}') no existe en la DB de Resumenes. "
                f"Propiedades detectadas: {self._properties_debug(properties)}"
            )

        for prop_name, prop_info in properties.items():
            if prop_info.get("type") == "title":
                return prop_name

        # Fallback pragmatico: en muchas DB la columna principal se llama Name.
        if "Name" in properties:
            return "Name"

        raise ValueError(
            "No se encontro una propiedad de tipo title en la DB de Resumenes. "
            f"Propiedades detectadas: {self._properties_debug(properties)}"
        )

    def _build_materia_fecha_filter(self, materia: str, fecha_iso: str) -> dict[str, Any]:
        fecha_dt = datetime.strptime(fecha_iso, "%Y-%m-%d")

        # Feynman: imagina una puerta con 2 reglas: misma materia y
        # fecha de creacion desde el dia de inicio en adelante (hasta hoy).
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
            ]
        }

    def get_apuntes_by_materia_and_fecha(self, materia: str, fecha_iso: str) -> list[dict[str, Any]]:
        query_filter = self._build_materia_fecha_filter(materia=materia, fecha_iso=fecha_iso)

        # Traemos todas las paginas desde la fecha de inicio usando paginacion.
        pages: list[dict[str, Any]] = []
        next_cursor: str | None = None

        while True:
            if self.apuntes_data_source_id:
                result = self.client.data_sources.query(
                    data_source_id=self.apuntes_data_source_id,
                    filter=query_filter,
                    sorts=[{"timestamp": "created_time", "direction": "ascending"}],
                    page_size=100,
                    start_cursor=next_cursor,
                )
            else:
                result = self.client.databases.query(
                    database_id=self.apuntes_db_id,
                    filter=query_filter,
                    sorts=[{"timestamp": "created_time", "direction": "ascending"}],
                    page_size=100,
                    start_cursor=next_cursor,
                )
            pages.extend(result.get("results", []))

            if not result.get("has_more"):
                break
            next_cursor = result.get("next_cursor")
            if not next_cursor:
                break

        return pages

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

        parent = (
            {"data_source_id": self.resumenes_data_source_id}
            if self.resumenes_data_source_id
            else {"database_id": self.resumenes_db_id}
        )

        page = self.client.pages.create(
            parent=parent,
            properties=properties,
            children=children[:100],
        )
        return page.get("url", "")