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
    padding: 44px 60px;
    background: #0d1117;
    color: #e6edf3;
    font-size: 22px;
    line-height: 1.5;
  }
  h1 {
    color: #ffffff;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0 0 6px;
    line-height: 1.15;
  }
  h2 {
    color: #79c0ff;
    font-size: 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    margin: 0 0 18px;
  }
  h3 { color: #e6edf3; font-size: 24px; margin: 18px 0 10px; font-weight: 600; }
  p { margin: 10px 0; }
  strong { color: #79c0ff; font-weight: 700; }
  em { color: #f0b429; font-style: normal; font-weight: 700; }
  table {
    border-collapse: collapse;
    width: 100%;
    font-size: 19px;
    margin: 6px 0;
    background: transparent;
  }
  tr, tbody, thead { background: transparent !important; }
  tr:nth-child(even), tr:nth-child(odd) { background: transparent !important; }
  th, td {
    padding: 9px 14px;
    border-bottom: 1px solid #30363d;
    text-align: left;
    line-height: 1.35;
    background: transparent !important;
    color: #e6edf3;
  }
  th {
    color: #79c0ff !important;
    font-weight: 700;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 2px solid #58a6ff;
  }
  ul, ol { padding-left: 26px; margin: 8px 0; }
  li { margin: 7px 0; }
  code {
    background: #161b22;
    color: #79c0ff;
    padding: 1px 7px;
    border-radius: 4px;
    font-size: 19px;
    font-weight: 600;
  }
  pre {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 16px;
    line-height: 1.45;
    overflow: hidden;
  }
  pre code {
    background: transparent;
    padding: 0;
    font-size: 16px;
    color: #c9d1d9;
    font-weight: 400;
  }
  blockquote {
    border-left: 4px solid #58a6ff;
    padding: 10px 18px;
    margin: 16px 0;
    color: #e6edf3;
    background: #161b22;
    border-radius: 0 8px 8px 0;
    font-size: 22px;
    font-style: italic;
  }
  .ok   { color: #56d364; font-weight: 700; }
  .warn { color: #f0b429; font-weight: 700; }
  .bad  { color: #ff7b72; font-weight: 700; }
  section.title {
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.title h1 { font-size: 56px; margin-bottom: 18px; line-height: 1.1; }
  section.title h2 { color: #c9d1d9; text-transform: none; letter-spacing: 0; font-size: 24px; font-weight: 400; }
  section.title p { font-size: 20px; color: #8b949e; }
  footer { color: #6e7681; font-size: 14px; }
  section::after { font-size: 14px; color: #6e7681; }
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
| IA decide aprovar/rejeitar | Rejeitada | IA é complacente. Código decide. |
| Validar RG com regex nacional | Rejeitada | RG não tem padrão nacional |
| Tesseract para OCR local | Adiada | Em 2h não dá pra calibrar |
| Confiança declarada pelo modelo | Ignorada | LLM chuta 0.95. Score em código |

---

## Reflexão crítica

# Onde concordei com a IA

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

## Perguntas?

<br>

**Antonia Silva Santos**
Hackathon Grupo Fácil — Programa de Estágio IA
