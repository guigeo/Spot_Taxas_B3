# DEFINE: Pipeline Core — Parser B3, PTAX BACEN e Geração de Excel

> Pipeline local Python que baixa o arquivo posicional da B3, consulta a PTAX do BACEN e gera uma planilha Excel com as cotações spot de 19 moedas comparadas às taxas oficiais.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PIPELINE_CORE |
| **Date** | 2026-06-05 |
| **Author** | Guilherme Ramos |
| **Status** | ✅ Shipped |
| **Clarity Score** | 15/15 |

---

## Problem Statement

A B3 publica diariamente um arquivo posicional (`.ex_`) com taxas de câmbio em formato de largura fixa com indicador de casas decimais implícito — difícil de parsear corretamente. O BACEN publica a PTAX via API OData. Conciliar essas duas fontes manualmente para 19 moedas é trabalhoso, sujeito a erros de escala e paridade (especialmente EUR, GBP, NZD, CNY), e impede o uso rápido dessas taxas para precificação, auditoria e compliance cambial.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Guilherme Ramos | Usuário solo — precificação e compliance cambial | Processo manual lento e propenso a erros de escala/paridade ao conciliar B3 vs PTAX |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Baixar o arquivo `.ex_` da B3 para a data de referência (D útil) |
| **MUST** | Fazer parse do arquivo posicional e decodificar o campo numérico com indicador de casas decimais |
| **MUST** | Mapear os 19 instrumentos B3 para as moedas ISO corretas com seus divisores e paridades |
| **MUST** | Consultar a API PTAX do BACEN (`CotacaoTodosComercialDia`, `tipoBoletim=Fechamento`) |
| **MUST** | Calcular o spread percentual B3 vs PTAX para cada moeda |
| **MUST** | Gerar planilha Excel formatada em `data/output/taxas_spot_b3_{YYYYMMDD}.xlsx` |
| **SHOULD** | Tratar dias não úteis (sábados, domingos, feriados nacionais) recuando para o último dia útil |
| **SHOULD** | Alertar quando instrumento não encontrado no arquivo B3 |
| **COULD** | Alertar quando divergência B3 vs PTAX for superior a 20% (possível erro de escala) |

---

## Success Criteria

- [x] Pipeline executa sem intervenção manual para qualquer data útil via `uv run python main.py`
- [x] Planilha Excel gerada em `data/output/taxas_spot_b3_{YYYYMMDD}.xlsx` com 8 colunas do PRD
- [x] As 19 moedas aparecem na planilha (`null` quando ausente — não é erro fatal)
- [x] USD, EUR e JPY corretamente escalados (USD e JPY ÷ 1.000; EUR ÷ 10.000.000)
- [x] GBP e NZD calculados via paridade com USD (multiplicação)
- [x] CNY calculado via paridade inversa com USD (divisão)
- [x] PTAX filtrada apenas com `tipoBoletim = 'Fechamento'`
- [x] Dados sempre referentes à data D (mais recente do arquivo), nunca D-1

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Happy path — dia útil | Data útil (ex: 2026-06-03), arquivo B3 e PTAX disponíveis | `uv run python main.py` | ✅ Planilha gerada com 19 moedas, spread calculado, sem erros |
| AT-002 | Dia não útil (sábado) | Data = sábado ou feriado | Pipeline iniciado | ✅ Usa automaticamente o último dia útil anterior |
| AT-003 | Instrumento ausente no B3 | Arquivo B3 não contém uma moeda da lista | Pipeline processa o arquivo | ✅ Moeda registrada com `cotacao_b3 = null`, alerta no log, pipeline não para |
| AT-004 | PTAX ausente para uma moeda | BACEN não publicou PTAX para uma moeda naquele dia | Pipeline consulta BACEN | ✅ `ptax_compra` e `ptax_venda` registrados como `null`, pipeline continua |
| AT-005 | Escala do EUR | Arquivo B3 do dia contém `REUR-D1` | Parse do valor numérico | ✅ Valor real calculado com divisor 10^7 (não 10^3), resultado próximo ao mercado |
| AT-006 | Paridade GBP | Arquivo B3 contém `GBP-PF` e `DOL-D1` | Cálculo do GBP spot | ✅ GBP/BRL = USD_spot × paridade_GBP_USD |
| AT-007 | Paridade CNY | Arquivo B3 contém `CNY-PF` e `DOL-D1` | Cálculo do CNY spot | ✅ CNY/BRL = USD_spot ÷ paridade_CNY_USD |
| AT-008 | Spread correto | Cotação B3 = 5.0099, PTAX venda = 5.0050 | Cálculo do spread | ✅ `spread_b3_ptax ≈ 0.0978%` (arredondado 4 casas) |

---

## Out of Scope

- Interface gráfica ou web — output é somente a planilha Excel
- Agendamento automático (cron/scheduler) — execução manual via `uv run`
- Histórico multi-data — uma execução = uma data = uma planilha
- Armazenamento em banco de dados — sem persistência além dos arquivos
- Notificações (email, Slack, webhook)
- Testes de carga ou performance — volume é fixo (~3.800 linhas/dia)
- Suporte a datas futuras — apenas dias úteis passados/presente

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Gerenciador | **uv obrigatório** — `pip install` proibido | Todo `uv add`, execução via `uv run python` |
| Ambiente | Não instalar nada no ambiente local global | `.venv` gerenciado pelo uv, isolado no projeto |
| Infra | Execução local — sem cloud | Sem Docker, sem Lambda, sem cloud run |
| Fonte de verdade | PRD em `instruction/PRD_Taxas_Spot_B3.md` | Qualquer ambiguidade resolve-se consultando o PRD |
| Disponibilidade | B3 publica ~19h BRT, BACEN ~18h BRT | Pipeline só deve rodar após 19h para garantir ambos disponíveis |
| Encoding | Arquivo B3 em `latin-1` | Usar `encoding='latin-1'` ao abrir o `Indic.txt` |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Entrypoint** | `main.py` (raiz) | `uv run python main.py` |
| **Módulos** | `src/` | Separar em módulos: downloader, parser, ptax, calculator, exporter |
| **KB Domains** | `pandas`, `openpyxl`, `requests`, `uv` | Consultar `.claude/kb/` para padrões |
| **IaC Impact** | None | Execução local, sem infraestrutura |
| **Dependências** | pandas 3.0.3, openpyxl 3.1.5, requests 2.34.2 | Já instaladas via `uv add` |

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Arquivo `.ex_` da B3 é um ZIP válido extraível com `zipfile` | Precisaria de outra lib de descompressão (ex: `py7zr`) | [x] Nested ZIP com PKSFX inner archive — resolvido com `io.BytesIO` |
| A-002 | Indicador de casas decimais dos instrumentos listados no PRD está estável | Revisão manual do divisor por moeda a cada release | [x] Decodificação validada contra dados reais B3 |
| A-003 | API BACEN `CotacaoTodosComercialDia` retorna todas as 19 moedas em uma chamada | Necessitaria chamadas individuais por moeda | [x] Endpoint não existe — trocado por loop `CotacaoMoedaDia` por moeda |
| A-004 | Feriados nacionais da API BACEN cobrem todos os dias em que B3 não opera | Manter lista local de fallback para casos de borda | [x] Endpoint não existe — trocado por BrasilAPI (`brasilapi.com.br/api/feriados`) |
| A-005 | Conexão de internet estável disponível no momento da execução | Adicionar retry com backoff exponencial | [x] Retry 3x com backoff 1s/2s/4s implementado |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Bem documentado no PRD — fontes, formato, dor e casos de uso claros |
| Users | 3 | Projeto solo com persona e casos de uso definidos |
| Goals | 3 | Prioridades MoSCoW explícitas derivadas do PRD |
| Success | 3 | Critérios testáveis com valores específicos por moeda |
| Scope | 3 | Out of scope explícito e detalhado |
| **Total** | **15/15** | |

---

## Open Questions

Todas resolvidas durante o build end-to-end contra dados reais B3 e BACEN.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-05 | define-agent | Versão inicial — extraído do PRD_Taxas_Spot_B3.md |
| 1.1 | 2026-06-07 | build-agent | Status atualizado para Complete após build bem-sucedido |
| 1.2 | 2026-06-07 | ship-agent | Status atualizado para Shipped; assumptions validadas contra dados reais; 5 bugs corrigidos antes do ship |

---

## Next Step

✅ SHIPPED
