# Spot Taxas B3

> Pipeline Python que extrai taxas spot de câmbio do arquivo diário da B3, compara com a PTAX do BACEN e gera uma planilha Excel.

---

## Contexto do Projeto

**Problema:** A B3 e o BACEN publicam taxas de câmbio diariamente em formatos distintos (arquivo posicional e API OData). Conciliar essas fontes manualmente é trabalhoso e sujeito a erros de escala/paridade.

**Solução:** Pipeline local Python que automatiza o download, parse, transformação e comparação das 19 principais moedas, gerando uma planilha Excel pronta para uso em precificação, conciliação, auditoria e compliance cambial.

**Stack:** Python 3.12 + pandas + openpyxl + requests — gerenciado com **uv**

**Mantenedor:** Guilherme Ramos — projeto solo

---

## Restrições Absolutas

| Restrição | Regra |
|-----------|-------|
| Gerenciador de pacotes | **SEMPRE** `uv add <pacote>` — NUNCA `pip install` |
| Execução de scripts | `uv run python <script>` |
| Ambiente local | Não instalar nada diretamente no ambiente local |
| Fonte de verdade | `instruction/PRD_Taxas_Spot_B3.md` |

---

## Arquitetura do Pipeline

```text
[B3] ID{YYMMDD}.ex_  →  baixar  →  extrair  →  Indic.txt
                                                    ↓
                                               parse posicional
                                               decode campo numérico
                                               filtrar data D
                                               mapear instrumento → moeda
                                               aplicar divisor/paridade
                                                    ↓
[BACEN] CotacaoTodosComercialDia  →  filtrar Fechamento  →  PTAX por moeda
                                                    ↓
                            merge B3 + PTAX  →  calcular spread
                                                    ↓
                                          taxas_spot_b3_{YYYYMMDD}.xlsx
```

---

## Contexto de Negócio

### Entidades

| Entidade | Descrição |
|----------|-----------|
| `Indic.txt` | Arquivo posicional B3, ~3.600–3.800 linhas, publicado ~19h BRT |
| Taxa Spot | Cotação para liquidação imediata (D+0 ou D+1) |
| PTAX | Taxa de câmbio de referência oficial do Banco Central |
| Data D | Data mais recente do arquivo — usar sempre D, nunca D-1 |
| Paridade | Razão entre duas moedas (ex: GBP/USD = 1.35) |

### 19 moedas cobertas

USD, EUR, AUD, GBP, CAD, CHF, JPY, NZD, SEK, NOK, DKK, ZAR, MXN, ARS, CLP, TRY, CNY, CNH, RUB

### Regras de negócio críticas

1. Usar **data D** (mais recente do arquivo), nunca D-1
2. **Indicador de casas decimais:** últimos 2 dígitos do campo numérico definem a escala
3. **EUR tem divisor especial:** 10^7 (demais: 10^3)
4. **NZD e GBP** dependem do USD spot — processar USD primeiro
5. **CNY** é paridade inversa: `USD_BRL ÷ paridade_CNY_USD`
6. PTAX ausente → `null` (não é erro fatal)
7. Instrumento ausente → `null` + alerta
8. Busca de instrumento por **sufixo** (não match exato) — nomes podem mudar
9. Dias não úteis → recuar para o último dia útil (consultar API feriados BACEN)
10. Divergência > 20% B3 vs PTAX → gerar alerta

### Janela de disponibilidade

| Fonte | Disponível | Endpoint |
|-------|-----------|----------|
| PTAX BACEN fechamento | ~18h BRT | `CotacaoTodosComercialDia` |
| Arquivo B3 `.ex_` | ~19h BRT | `pesquisapregao/download` |
| Execução ideal | Após 19h BRT | — |

---

## Estrutura do Projeto

```text
Spot_Taxas_B3/
├── instruction/
│   └── PRD_Taxas_Spot_B3.md   # PRD — fonte de verdade
├── src/                        # Código-fonte do pipeline
│   └── __init__.py
├── data/
│   ├── raw/                    # Arquivos .ex_ e Indic.txt baixados (não versionado)
│   └── output/                 # Planilhas Excel geradas (não versionado)
├── tests/
│   └── __init__.py
├── main.py                     # Entrypoint: uv run python main.py
├── pyproject.toml              # Dependências: pandas, openpyxl, requests
├── .python-version             # Python 3.12 fixado
├── uv.lock                     # Lockfile determinístico — commitar
└── .claude/
    ├── CLAUDE.md               # Este arquivo
    ├── kb/                     # Knowledge Base (pandas, openpyxl, requests, uv)
    └── agents/domain/          # b3-pipeline-developer, spot-taxas-b3-expert
```

---

## Workflows de Desenvolvimento

### AgentSpec 4.2 (Spec-Driven Development)

```text
/brainstorm → /define → /design → /build → /ship
  (Opus)      (Opus)    (Opus)   (Sonnet)  (Haiku)
```

### Dev Loop

```bash
/dev "Quero construir X"
/dev tasks/PROMPT_FEATURE.md
```

---

## Diretrizes de Uso de Agentes

| Categoria | Agentes | Quando usar |
|-----------|---------|-------------|
| **Domínio** | `b3-pipeline-developer` | Parse B3, download, decodificação, paridades |
| **Domínio** | `spot-taxas-b3-expert` | Decisões arquiteturais, regras de negócio |
| **Workflow** | brainstorm, define, design, build, ship | Construir features com SDD |
| **Qualidade** | code-reviewer, test-generator | Revisar e testar código |
| **Exploração** | codebase-explorer | Mapear estrutura atual |

---

## Comandos

| Comando | Propósito |
|---------|-----------|
| `/brainstorm` | Explorar ideias |
| `/define` | Capturar requisitos |
| `/design` | Criar arquitetura |
| `/build` | Executar implementação |
| `/ship` | Arquivar feature concluída |
| `/dev` | Dev Loop |
| `/create-kb` | Criar domínio de KB |
| `/review` | Revisão de código |
| `/sync-context` | Atualizar esta seção de Arquitetura |

---

## Knowledge Base

| Domínio | Propósito | Ponto de entrada |
|---------|-----------|-----------------|
| `pandas` | Manipulação e transformação de dados | `.claude/kb/pandas/index.md` |
| `openpyxl` | Geração de planilha Excel | `.claude/kb/openpyxl/index.md` |
| `requests` | HTTP — download B3 e API BACEN | `.claude/kb/requests/index.md` |
| `uv` | Gerenciador de dependências | `.claude/kb/uv/index.md` |

---

## Features Ativas

| Feature | Status | Descrição |
|---------|--------|-----------|
| Setup inicial | ✅ | KBs, agentes de domínio e CLAUDE.md configurados |

---

## Features Shipadas (SDD Archive)

| Feature | Shipped | Descrição |
|---------|---------|-----------|
| Pipeline core | 2026-06-07 | Parser B3 + PTAX BACEN + join + Excel — `.claude/sdd/archive/PIPELINE_CORE/` |

---

## Ajuda

- **PRD:** [instruction/PRD_Taxas_Spot_B3.md](../instruction/PRD_Taxas_Spot_B3.md)
- **Workflow SDD:** [.claude/sdd/_index.md](.claude/sdd/_index.md)
- **Agentes:** [.claude/agents/domain/](.claude/agents/domain/)
- **KB Index:** [.claude/kb/_index.yaml](.claude/kb/_index.yaml)
