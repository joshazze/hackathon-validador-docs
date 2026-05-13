"""Agente 1 — Classificador (Haiku 4.5).

Porteiro do parlamento: decide se vale gastar os outros agentes.
Resposta possível: RG, CNH, OUTRO, ILEGIVEL.
"""
from __future__ import annotations

from typing import Any, Literal

from ._client import MODEL_HAIKU, ask_vision, parse_json_loose

DocType = Literal["RG", "CNH", "OUTRO", "ILEGIVEL"]

_SYSTEM = """Voce e um classificador de documentos de identidade brasileiros.
Responde APENAS com JSON valido, sem markdown, sem comentarios."""

_PROMPT = """Olhe a imagem e diga que tipo de documento e.

Categorias permitidas:
- "RG"        : carteira de identidade civil (RG, CIN, RIC ou equivalente estadual)
- "CNH"       : carteira nacional de habilitacao (em qualquer modelo - fisica ou digital)
- "OUTRO"    : e um documento, mas nao e RG nem CNH (passaporte, CTPS, comprovante, etc)
- "ILEGIVEL" : a imagem nao permite identificar o tipo (muito escura, borrada, recortada, em branco)

Retorne:
{
  "tipo": "RG" | "CNH" | "OUTRO" | "ILEGIVEL",
  "confianca": 0.0 a 1.0,
  "justificativa": "uma frase curta explicando"
}
"""


def classify(image_block: dict[str, Any]) -> dict[str, Any]:
    raw = ask_vision(
        model=MODEL_HAIKU,
        system=_SYSTEM,
        user_text=_PROMPT,
        image_block=image_block,
        max_tokens=300,
    )
    data = parse_json_loose(raw)
    tipo = data.get("tipo", "ILEGIVEL")
    if tipo not in ("RG", "CNH", "OUTRO", "ILEGIVEL"):
        tipo = "ILEGIVEL"
    return {
        "agente": "classificador",
        "tipo": tipo,
        "confianca": float(data.get("confianca", 0.0)),
        "justificativa": data.get("justificativa", ""),
    }
