"""Cliente Anthropic compartilhado e utilitários de imagem.

Centraliza acesso à API e preparação de imagens para envio multimodal,
para que cada agente foque apenas na sua pergunta de domínio.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
from functools import lru_cache
from typing import Any

from anthropic import Anthropic
from PIL import Image

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

MAX_IMAGE_DIM = 1568


@lru_cache(maxsize=1)
def client() -> Anthropic:
    return Anthropic()


def prepare_image(raw_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Normaliza imagem e devolve bloco `image` pronto pra mensagem Anthropic.

    Reduz lado maior pra MAX_IMAGE_DIM (limite recomendado da API) e
    converte tudo pra JPEG pra simplificar o handling.
    """
    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    if max(img.size) > MAX_IMAGE_DIM:
        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": b64,
        },
    }


def ask_vision(
    *,
    model: str,
    system: str,
    user_text: str,
    image_block: dict[str, Any],
    max_tokens: int = 600,
) -> str:
    """Chamada de visão padronizada — todos os agentes IA passam por aqui."""
    resp = client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [image_block, {"type": "text", "text": user_text}],
            }
        ],
    )
    return resp.content[0].text


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_json_loose(text: str) -> dict[str, Any]:
    """Extrai o primeiro objeto JSON encontrado no texto.

    LLM às vezes embrulha JSON em markdown ou comenta antes/depois;
    isolar com regex evita falha por enfeite.
    """
    match = _JSON_BLOCK.search(text)
    if not match:
        raise ValueError(f"Resposta sem JSON identificável: {text[:200]}")
    return json.loads(match.group(0))
