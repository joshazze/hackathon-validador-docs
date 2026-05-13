"""Agente 6 — Cross-checker (Python puro, sem IA).

Compara o que o cliente DIGITOU no cadastro com o que foi extraido do documento.
E a validacao que pega fraude grosseira: alguem mandando documento de outra pessoa
geralmente nao percebe que o nome do cadastro nao bate com o nome do RG.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


def _normaliza_nome(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.upper()
    s = re.sub(r"[^A-Z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _similaridade_nome(a: str, b: str) -> float:
    """SequenceMatcher: rapido e suficiente pra fuzzy de nome.

    Nao usa Levenshtein puro porque queremos tolerar reordenacao
    parcial (sobrenome antes do nome, omissao de nome do meio).
    """
    if not a or not b:
        return 0.0
    sim_direta = SequenceMatcher(None, a, b).ratio()

    # tambem tenta com tokens ordenados — pega o caso "JOAO SILVA" vs "SILVA JOAO"
    tokens_a = " ".join(sorted(a.split()))
    tokens_b = " ".join(sorted(b.split()))
    sim_tokens = SequenceMatcher(None, tokens_a, tokens_b).ratio()

    return max(sim_direta, sim_tokens)


def crosscheck(*, cadastro: dict[str, Any], extraido: dict[str, Any]) -> dict[str, Any]:
    """Compara cadastro digitado vs dados extraidos do documento."""
    nome_cad = _normaliza_nome(cadastro.get("nome_completo"))
    nome_doc = _normaliza_nome(extraido.get("nome_completo"))
    sim_nome = _similaridade_nome(nome_cad, nome_doc)

    nasc_cad = (cadastro.get("data_nascimento") or "").strip() or None
    nasc_doc = (extraido.get("data_nascimento") or "").strip() or None
    nasc_bate = bool(nasc_cad and nasc_doc and nasc_cad == nasc_doc)

    checks = [
        {
            "regra": "nome_similar",
            "ok": sim_nome >= 0.80,
            "motivo": None if sim_nome >= 0.80 else f"similaridade do nome baixa ({sim_nome:.2f})",
            "valor": round(sim_nome, 3),
        },
        {
            "regra": "data_nascimento_igual",
            "ok": nasc_bate,
            "motivo": None if nasc_bate else "data de nascimento do cadastro nao bate com o documento",
        },
    ]

    # score = media simples; nome pesa mais por ser proxy direto de "mesma pessoa"
    score = (sim_nome * 0.7) + ((1.0 if nasc_bate else 0.0) * 0.3)

    return {
        "agente": "crosscheck",
        "score_consistencia": round(score, 3),
        "similaridade_nome": round(sim_nome, 3),
        "data_nascimento_bate": nasc_bate,
        "checks": checks,
    }
