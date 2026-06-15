"""Парсер текста в список продуктов. Сейчас — правила/regex; единая точка под будущий LLM."""
from __future__ import annotations

import re

from app.models import Unit
from app.schemas import ParsedProduct
from app.services.ingestion.base import IngestResult, TextParser

# Сопоставление текстовых единиц со значениями enum Unit.
_UNIT_MAP = {
    "шт": Unit.pcs, "штук": Unit.pcs, "штука": Unit.pcs, "штуки": Unit.pcs, "pcs": Unit.pcs,
    "г": Unit.g, "гр": Unit.g, "грамм": Unit.g, "g": Unit.g,
    "кг": Unit.kg, "килограмм": Unit.kg, "kg": Unit.kg,
    "мл": Unit.ml, "ml": Unit.ml,
    "л": Unit.l, "литр": Unit.l, "литра": Unit.l, "литров": Unit.l, "l": Unit.l,
}

# "<название> <кол-во> <ед>" или "<кол-во> <ед> <название>" — допускаем оба порядка.
_QTY_RE = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?P<unit>шт|штук[аи]?|гр?|грамм|кг|килограмм|мл|л|литр[аов]*|pcs|g|kg|ml|l)\b",
    re.IGNORECASE,
)


class RuleTextParser(TextParser):
    """Простой парсер: строки/запятые разбиваются на позиции, ищется количество и единица."""

    def parse(self, text: str) -> IngestResult:
        products: list[ParsedProduct] = []
        for chunk in re.split(r"[\n,;]+", text):
            chunk = chunk.strip()
            if not chunk:
                continue
            products.append(_parse_chunk(chunk))
        return IngestResult(products=products, raw_text=text, configured=True)


def _parse_chunk(chunk: str) -> ParsedProduct:
    qty = 1.0
    unit = Unit.pcs
    m = _QTY_RE.search(chunk)
    if m:
        qty = float(m.group("qty").replace(",", "."))
        unit = _UNIT_MAP.get(m.group("unit").lower(), Unit.pcs)
        chunk = (chunk[: m.start()] + chunk[m.end():]).strip()
    name = re.sub(r"\s+", " ", chunk).strip(" -–—") or "Без названия"
    return ParsedProduct(name=name, quantity=qty, unit=unit)


# Singleton-парсер для переиспользования.
rule_parser = RuleTextParser()
