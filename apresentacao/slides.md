---
marp: true
theme: default
size: 16:9
paginate: true
backgroundColor: "#0d1117"
color: "#e6edf3"
style: |
  section {
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    padding: 56px 72px;
    background: #0d1117;
    color: #e6edf3;
    font-size: 22px;
    line-height: 1.45;
  }
  h1 {
    color: #e6edf3;
    font-size: 44px;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
  }
  h2 {
    color: #58a6ff;
    font-size: 18px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 24px;
  }
  h3 { color: #e6edf3; font-size: 24px; margin-top: 18px; }
  strong { color: #58a6ff; }
  em { color: #d29922; font-style: normal; font-weight: 600; }
  table {
    border-collapse: collapse;
    width: 100%;
    font-size: 18px;
  }
  th, td {
    padding: 8px 14px;
    border-bottom: 1px solid #30363d;
    text-align: left;
  }
  th { color: #8b949e; font-weight: 500; font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; }
  ul, ol { padding-left: 24px; }
  li { margin: 6px 0; }
  code {
    background: #161b22;
    color: #58a6ff;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 18px;
  }
  blockquote {
    border-left: 3px solid #58a6ff;
    padding: 4px 16px;
    margin: 18px 0;
    color: #c9d1d9;
    background: #161b22;
    border-radius: 0 6px 6px 0;
  }
  .ok { color: #3fb950; font-weight: 600; }
  .warn { color: #d29922; font-weight: 600; }
  .bad { color: #f85149; font-weight: 600; }
  section.title {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.title h1 { font-size: 56px; margin-bottom: 16px; }
  section.title h2 { color: #8b949e; text-transform: none; letter-spacing: 0; font-size: 22px; font-weight: 400; }
  footer { color: #6e7681; font-size: 14px; }
---

<!-- _class: title -->

# Parlamento de Agentes

## Validação inteligente de documentos no cadastro de plano de saúde

<br>

**Hackathon Grupo Fácil** — Programa de Estágio IA

Antonia Silva Santos

---

## O problema

# Validar documento na mão não escala

Quando um cliente faz cadastro ou inclui dependente em um plano de saúde, envia **RG ou CNH**. Hoje, analista humano confere campo por campo.

- **Lento**: 5 a 10 min por documento, em alta demanda
- **Erra**: cansaço, distração, regras subjetivas
- **Caro**: cada hora de analista poderia estar em casos complexos
- **Não escala**: dobrar volume = dobrar equipe

> Precisamos validar automaticamente *sem* terceirizar a decisão final pra uma IA que ninguém audita.

---

## A solução em uma frase

# Parlamento de Agentes

Em vez de **uma chamada de IA** que faz tudo, vários **agentes especializados** opinam em paralelo. Cada um responde uma pergunta específica. A **decisão final é determinística em código puro**.

<br>

### IA percebe. Código julga.

---

## Arquitetura

# Os 7 agentes

| # | Agente | Tipo | Pergunta |
|---|---|---|---|
| 1 | Classificador | Haiku 4.5 | Que documento é esse? |
| 2 | Extrator | Sonnet 4.6 | Quais os campos? |
| 3 | Legibilidade | Haiku 4.5 | Está legível? |
| 4 | Anomalia | Sonnet 4.6 | Tem sinal de fraude? |
| 5 | Validador | **Python puro** | Dígitos, datas plausíveis? |
| 6 | Cross-checker | **Python puro** | Bate com o cadastro? |
| 7 | Relator | **Python puro** | Veredito final |

Modelo leve (Haiku) para porteiro e legibilidade; modelo robusto (Sonnet) para extração e análise forense.

---

## Fluxo

# Curto-circuito e paralelismo

```
upload (jpg/png/pdf)
    │
    ▼
Classificador (Haiku)  ← porteiro
    │
    ├── ILEGIVEL → REJEITADO  (economiza 3 chamadas)
    ├── OUTRO    → REVISAR
    └── RG / CNH
            │
            ▼
    ┌── Extrator     (Sonnet) ─┐
    ├── Legibilidade (Haiku)   ├── paralelo
    └── Anomalia     (Sonnet) ─┘
            │
            ▼
    Validador + Cross-check   ← código puro, instantâneo
            │
            ▼
        Relator → veredito
```

---

## Decisão

# A fórmula é determinística

```
score_final =
    0.25 × legibilidade
  + 0.20 × extração
  + 0.20 × validação
  + 0.20 × consistência
  + 0.15 × (1 − anomalia)
```

<br>

| Score | Veredito | Ação |
|---|---|---|
| ≥ 0.80 | **<span class="ok">APROVADO</span>** | Segue o cadastro |
| ≥ 0.50 | **<span class="warn">REVISAR</span>** | Vai pra analista humano |
| < 0.50 | **<span class="bad">REJEITADO</span>** | Pede reenvio |

Três níveis, não dois: REVISAR reconhece o limite da automação.

---

<!-- _class: title -->

# Demo ao vivo

## Três documentos, três vereditos diferentes

1. RG válido → <span class="ok">APROVADO</span>
2. CNH borrada → <span class="warn">REVISAR</span>
3. Não é documento → <span class="bad">REJEITADO</span> (curto-circuito na fase 1)

---

## Reflexão crítica

# Onde discordei da IA

| Sugestão | Decisão | Motivo |
|---|---|---|
| IA decide aprovar/rejeitar | **Rejeitada** | IA é complacente. Código decide. |
| Validar RG com regex nacional | **Rejeitada** | RG não tem padrão nacional |
| Tesseract para OCR local | **Adiada** | Em 2h não dá pra calibrar. Limitação anotada. |
| Confiança declarada pelo modelo | **Ignorada** | LLM chuta 0.95. Score em código. |

# Onde concordei

- **Cross-check com cadastro digitado** — pega fraude grosseira
- **Pré-processar PDF para imagem** antes do multimodal
- **Separar percepção em agentes especializados**

---

## Quando a IA erra

# Exemplo previsível

**Cenário:** CNH legítima com reflexo cobrindo o nome.

- Extrator alucina um nome (LLMs fazem isso sob input ambíguo)
- Auditor de legibilidade detecta reflexo → score 0.4
- Validador confere dígito da CNH → OK
- **Cross-checker não bate** → o nome alucinado não casa com o cadastro

**Veredito: <span class="warn">REVISAR</span>**, não rejeita injustamente.

> O parlamento absorve o erro de um agente porque outros 6 ainda opinam.

---

## Limitações

# O que ainda não cobre

| Limitação | Caminho futuro |
|---|---|
| Depende de API multimodal paga | OCR local + modelo open-source |
| Não detecta deepfake/montagem perfeita | Análise EXIF, moiré, hash perceptual |
| RG sem validação de número | Integração Serpro / Receita |
| Latência 3-5s | Fila assíncrona + cache por hash |
| Não cobre passaporte, comprovante | Mais agentes especialistas |

---

<!-- _class: title -->

# Obrigada!

## Código aberto

`github.com/joshazze/hackathon-validador-docs`

<br>

**Antonia Silva Santos** — Hackathon Grupo Fácil
