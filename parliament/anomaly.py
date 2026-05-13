"""Agente 4 — Detector de Anomalia (Sonnet 4.6).

Procura sinais de adulteracao ou fraude.
Sonnet aqui porque o raciocinio e mais sutil — analisar fontes,
alinhamento, ruido de compressao.
"""
from __future__ import annotations

from typing import Any

from ._client import MODEL_SONNET, ask_vision, parse_json_loose

_SYSTEM = """Voce e um analista forense de documentos.
Sua tarefa NAO e avaliar legibilidade — outro agente faz isso.
Sua tarefa e procurar sinais de adulteracao.
Responde APENAS com JSON valido."""

_PROMPT = """Procure sinais de adulteracao ou fraude no documento da imagem.

Sinais a investigar:
- fontes inconsistentes entre campos (ex: nome em fonte diferente da data)
- alinhamento estranho de textos (campo torto, sobreposto)
- ruido de compressao em areas especificas (sugere edicao)
- bordas suspeitas (rasura, recorte digital)
- foto de cópia / cópia de cópia (perda generica de qualidade)
- elementos faltando (selo, holograma, brasao)
- texto sobre elemento de seguranca (numero escrito por cima do brasao, etc)

IMPORTANTE: Se a imagem so esta de baixa qualidade visual (sem reflexo, sem
movimento, sem moire) sem sinal especifico de edicao, score_anomalia deve
ser baixo. Nao confundir qualidade ruim com fraude.

Retorne:
{
  "score_anomalia": 0.0 a 1.0,
  "suspeitas": ["lista curta de sinais especificos encontrados"],
  "comentario": "uma frase resumindo"
}

Escala:
- 0.0  : nada suspeito
- 0.3  : leve inconsistencia, provavelmente artefato
- 0.6  : sinal forte de edicao
- 1.0  : fraude evidente
"""


def detect(image_block: dict[str, Any]) -> dict[str, Any]:
    raw = ask_vision(
        model=MODEL_SONNET,
        system=_SYSTEM,
        user_text=_PROMPT,
        image_block=image_block,
        max_tokens=500,
    )
    data = parse_json_loose(raw)
    score = float(data.get("score_anomalia", 0.0))
    score = max(0.0, min(1.0, score))
    return {
        "agente": "anomalia",
        "score_anomalia": score,
        "suspeitas": data.get("suspeitas", []),
        "comentario": data.get("comentario", ""),
    }
