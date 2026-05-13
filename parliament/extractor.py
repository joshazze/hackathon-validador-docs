"""Agente 2 — Extrator (Sonnet 4.6).

Le os campos relevantes do documento.
Precisao e critica: alucinacao aqui propaga pro cross-checker.
"""
from __future__ import annotations

from typing import Any

from ._client import MODEL_SONNET, ask_vision, parse_json_loose

_SYSTEM = """Voce extrai dados de documentos de identidade brasileiros.
Responde APENAS com JSON valido, sem markdown.

Regras duras:
- Se um campo nao estiver visivel ou legivel, retorne null. NUNCA invente.
- Nomes em CAIXA ALTA exatamente como aparecem no documento.
- Datas no formato AAAA-MM-DD.
- Numeros sem pontos, tracos ou espacos."""

_PROMPT_RG = """Extraia os campos do RG na imagem:

{
  "nome_completo": "string ou null",
  "data_nascimento": "AAAA-MM-DD ou null",
  "numero_documento": "string ou null",
  "data_emissao": "AAAA-MM-DD ou null",
  "orgao_expedidor": "string ou null (ex: SSP/MG)",
  "campos_visiveis": ["lista dos campos que voce conseguiu ler com confianca"]
}
"""

_PROMPT_CNH = """Extraia os campos da CNH na imagem:

{
  "nome_completo": "string ou null",
  "data_nascimento": "AAAA-MM-DD ou null",
  "numero_documento": "string ou null (numero de registro - 11 digitos)",
  "data_emissao": "AAAA-MM-DD ou null (data da 1a habilitacao ou emissao deste documento)",
  "orgao_expedidor": "string ou null (ex: DETRAN/MG)",
  "categoria": "string ou null (A, B, AB, etc)",
  "campos_visiveis": ["lista dos campos que voce conseguiu ler com confianca"]
}
"""


def extract(image_block: dict[str, Any], doc_type: str) -> dict[str, Any]:
    prompt = _PROMPT_CNH if doc_type == "CNH" else _PROMPT_RG

    raw = ask_vision(
        model=MODEL_SONNET,
        system=_SYSTEM,
        user_text=prompt,
        image_block=image_block,
        max_tokens=600,
    )
    data = parse_json_loose(raw)

    obrigatorios = ["nome_completo", "data_nascimento", "numero_documento"]
    preenchidos = sum(1 for k in obrigatorios if data.get(k))
    score_extracao = preenchidos / len(obrigatorios)

    return {
        "agente": "extrator",
        "campos": data,
        "score_extracao": score_extracao,
        "obrigatorios_preenchidos": preenchidos,
        "obrigatorios_total": len(obrigatorios),
    }
