"""Agente 3 — Auditor de Legibilidade (Haiku 4.5).

Avalia se a imagem permite leitura confiavel: reflexo, borrao, recorte,
foto-de-tela, baixa iluminacao.
"""
from __future__ import annotations

from typing import Any

from ._client import MODEL_HAIKU, ask_vision, parse_json_loose

_SYSTEM = """Voce e um auditor de qualidade visual de documentos.
Responde APENAS com JSON valido."""

_PROMPT = """Avalie a qualidade visual da imagem do documento.
NAO avalie o conteudo — apenas se da pra ler com seguranca.

Problemas comuns a procurar:
- reflexo / flash sobre o documento
- borrao por movimento ou foco ruim
- foto de tela (moire, pixelizacao, brilho de monitor)
- recorte (campos importantes cortados)
- baixa iluminacao ou contraste
- dobra / amassado cobrindo informacao

Retorne:
{
  "score_legibilidade": 0.0 a 1.0,
  "problemas": ["lista de strings curtas, ex: 'reflexo na area do nome'"],
  "comentario": "uma frase resumindo"
}

Escala:
- 1.0  : nitido, todos os campos legiveis
- 0.7  : usavel, com pequenos defeitos
- 0.4  : alguns campos comprometidos
- 0.0  : ilegivel
"""


def audit(image_block: dict[str, Any]) -> dict[str, Any]:
    raw = ask_vision(
        model=MODEL_HAIKU,
        system=_SYSTEM,
        user_text=_PROMPT,
        image_block=image_block,
        max_tokens=400,
    )
    data = parse_json_loose(raw)
    score = float(data.get("score_legibilidade", 0.0))
    score = max(0.0, min(1.0, score))
    return {
        "agente": "legibilidade",
        "score_legibilidade": score,
        "problemas": data.get("problemas", []),
        "comentario": data.get("comentario", ""),
    }
