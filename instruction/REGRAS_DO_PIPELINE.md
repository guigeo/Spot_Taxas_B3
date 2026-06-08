# Regras do Pipeline Spot Taxas B3 — Guia de Entendimento

> Documento de apoio para quem já conhece o domínio (câmbio, B3, PTAX) e quer entender
> rapidamente o que o pipeline faz e como ele faz, sem precisar ler o código.
> Reflete o comportamento **real e validado** do pipeline (rodado contra dados de produção
> em 2026-06-05), não apenas o que estava planejado no PRD original.

---

## 1. O que o pipeline faz, em uma frase

Todo dia (depois das 19h BRT), o pipeline baixa o arquivo de indicadores da B3, extrai a
cotação spot de 42 moedas contra o real, busca a PTAX de fechamento do BACEN para essas
mesmas moedas, calcula o spread entre as duas fontes e gera uma planilha Excel comparativa
pronta para conciliação/auditoria.

```
B3 (Indic.txt)  ──┐
                  ├──► merge por moeda ──► spread % ──► Excel
BACEN (PTAX)    ──┘
```

---

## 2. O fluxo passo a passo

### Passo 1 — Determinar a "data de referência" (data D)
- O pipeline sempre roda "para hoje", mas **nem todo dia tem pregão**.
- Antes de qualquer coisa, ele resolve qual é o último **dia útil** (consulta a lista de
  feriados nacionais — ver regra R9). Esse é o "dia D" usado em todas as etapas seguintes.
- **Nunca usa D-1** como fallback "de propósito" — D-1 só aparece se hoje cair em
  fim de semana/feriado, caso em que o último dia útil *é* D-1 (ou anterior).

### Passo 2 — Baixar e abrir o arquivo da B3
- A B3 disponibiliza um arquivo `ID{AAMMDD}.ex_` por dia, baixado de
  `b3.com.br/pesquisapregao/download`.
- **Detalhe que pegou todo mundo de surpresa:** esse `.ex_` não é o arquivo de texto
  diretamente — é um ZIP, e dentro dele tem **outro arquivo compactado autoextraível
  (formato PKSFX/.exe do Windows)**, que por sua vez contém o `Indic.txt` de verdade.
  Ou seja: ZIP → SFX → `Indic.txt`. O pipeline abre as duas camadas em memória
  (sem gravar a camada intermediária em disco) para não correr o risco de o arquivo
  intermediário sobrescrever o arquivo original durante a extração.
- O servidor da B3 também é instável: às vezes devolve uma resposta "200 OK" mas vazia.
  O pipeline valida que o conteúdo baixado realmente começa com a assinatura de um ZIP
  (`PK`) e tenta de novo se não for o caso.

### Passo 3 — Ler o arquivo posicional `Indic.txt`
- Formato de largura fixa (uma linha por instrumento/data). Os campos relevantes são:

| Posição (0-indexed) | Campo | Exemplo |
|---|---|---|
| `[6:11]` | código do registro | `00101` (só processamos esse tipo) |
| `[11:19]` | data | `20260605` |
| `[19:21]` | tipo do instrumento | `RT`, `TX`, `BT`... |
| `[21:46]` | nome do instrumento | `RTDOL-D1`, `TXJPY` |
| `[46:]` | valor numérico codificado | `+00000000000000000005078504` |

- O arquivo traz **duas datas** (geralmente D e D-1, lado a lado). O pipeline filtra
  e mantém apenas as linhas da **data mais recente presente no arquivo** (regra R1).

### Passo 4 — Decodificar o valor numérico
- O campo de valor é tipo `+00000000000000000005078504`.
- **Os dois últimos dígitos indicam quantas casas decimais o número tem** (regra R2).
- Fórmula: `valor = inteiro_sem_os_2_últimos_dígitos / 10^(últimos_2_dígitos)`
- Exemplo real: `+...5078504` → últimos 2 = `04` (4 casas) → `50785 / 10^4 = 5.0785`
  (USD/BRL — bate com a cotação real do dia).
- **Importante:** esse valor decodificado **já é a taxa final**, pronta para uso.
  Não existe nenhum "divisor extra" por moeda — o PRD original sugeria um (ex: ÷1.000,
  ÷10.000.000 para EUR), mas isso estava **errado**: aplicar um divisor em cima do valor
  já decodificado distorcia a cotação em 3-4 ordens de grandeza. Foi removido.

### Passo 5 — Encontrar o instrumento certo para cada moeda
- Cada moeda tem um "tipo + sufixo de nome" configurado (ex: USD → tipo `RT`,
  sufixo `DOL-D1`; JPY → tipo `TX`, sufixo `JPY`; EUR → tipo `RT`, sufixo `REUR-D1`).
- A busca é feita por **tipo exato + nome terminando no sufixo configurado**
  (regra R8) — nunca por nome igual/exato, porque a B3 já trocou nomes de instrumento
  no passado (ex: `ARS-D1` virou `RARS-D1`, e o sufixo `ARS-D1` continua batendo).
- Se não encontrar o instrumento daquela moeda no arquivo do dia → cotação fica `null`
  e é gerado um alerta `[WARN]` (regra R7).

### Passo 6 — Casos especiais de paridade (GBP, NZD, CNY)
- Para a maioria das moedas, o instrumento já traz a cotação direta em BRL.
- **GBP, NZD e CNY são diferentes**: a B3 não publica a cotação direta dessas moedas
  contra o real — publica apenas a **paridade contra o dólar**. Por isso:
  - **USD precisa ser processado primeiro** (regra R4) — o "USD spot" fica guardado
    e reaproveitado nos cálculos seguintes.
  - **GBP e NZD** (paridade "moeda por dólar", ex: GBP/USD ≈ 1,34):
    `cotação_BRL = USD_spot × paridade`
  - **CNY** é o caso inverso — a B3 publica "dólares por iene chinês" (USD/CNY ≈ 6,77),
    então para chegar em CNY/BRL é preciso **dividir** (regra R5):
    `cotação_BRL = USD_spot ÷ paridade`

### Passo 7 — Buscar a PTAX de fechamento no BACEN
- A API do BACEN usada é a `PTAX` (OData), função `CotacaoMoedaDia(moeda, dataCotacao)`
  — **uma chamada por moeda** (não existe um endpoint único que devolva todas de
  uma vez, ao contrário do que o desenho original supunha).
- Cada chamada devolve vários boletins do dia (Abertura, Intermediário, Fechamento...).
  O pipeline filtra exatamente o boletim **`"Fechamento PTAX"`** — esse é o nome real
  que o BACEN usa (não apenas `"Fechamento"`).
- **Nem toda moeda tem PTAX de fechamento publicada pelo BACEN** — moedas como ZAR,
  CLP, TRY, MXN, CNH, RUB, ARS, NZD e CNY simplesmente não aparecem na API do BACEN
  para boletim de fechamento. Isso **não é erro**: o pipeline registra `null`
  (regra R6) e segue normalmente.

### Passo 8 — Calcular o spread B3 vs PTAX
- Para cada moeda com as duas cotações disponíveis:
  `spread % = (cotação_B3 / PTAX_venda − 1) × 100`
- Se faltar uma das duas pontas (B3 ou PTAX), o spread fica `null`.
- Se o spread (em módulo) passar de **20%**, é gerado um alerta de divergência
  (regra R10) — sinal de que algo pode estar errado (ex: instrumento errado, dia
  diferente, problema na fonte).

### Passo 9 — Gerar a planilha Excel
- Uma linha por moeda, com: data de referência, código ISO, cotação B3, PTAX
  compra/venda, spread %, instrumento de origem e método de cálculo usado
  (`direto`, `paridade_multiplicada`, `paridade_dividida`).
- Salva em `data/output/taxas_spot_b3_{AAAAMMDD}.xlsx`.

---

## 3. As 10 regras de negócio, explicadas em linguagem simples

| # | Regra | O que significa na prática |
|---|---|---|
| **R1** | Usar sempre a data D (mais recente do arquivo), nunca D-1 | O arquivo da B3 traz duas datas lado a lado; sempre ficamos com a mais nova. D-1 só vale se hoje não for dia útil (aí "D" recua sozinho). |
| **R2** | Os últimos 2 dígitos do campo numérico definem as casas decimais | É assim que a B3 codifica valores de tamanhos/precisões diferentes em um campo de largura fixa. Sem essa decodificação, o número não faz sentido. |
| **R3** *(revisada)* | ~~EUR tem divisor especial 10^7~~ → **Não existe divisor extra para nenhuma moeda** | O PRD original previa divisores por moeda; na prática o valor decodificado pela regra R2 **já é** a cotação final. Aplicar divisor em cima distorcia tudo. |
| **R4** | NZD e GBP dependem do USD spot — processar USD primeiro | A B3 só publica a paridade dessas moedas contra o dólar, não a cotação direta em reais. Sem o USD calculado antes, não dá pra calcular GBP/NZD. |
| **R5** | CNY é paridade inversa: `USD_BRL ÷ paridade_CNY_USD` | A B3 publica "quantos CNY equivalem a 1 USD" (~6,77); para chegar em CNY/BRL é preciso dividir, não multiplicar — o oposto de GBP/NZD. |
| **R6** | PTAX ausente → `null` (não é erro fatal) | Várias moedas simplesmente não têm boletim de fechamento PTAX no BACEN. O pipeline segue em frente e marca como "sem PTAX" — não trava o processo. |
| **R7** | Instrumento ausente no arquivo B3 → `null` + alerta | Se a B3 não publicou aquele instrumento naquele dia, a cotação fica vazia e um aviso `[WARN]` é exibido — para investigação manual, mas sem travar o pipeline. |
| **R8** | Busca de instrumento por sufixo, não por nome exato | Nomes de instrumento mudam ao longo do tempo (ex: `ARS-D1` → `RARS-D1`). Buscar pelo final do nome torna o pipeline resistente a essas mudanças. |
| **R9** | Dias não úteis → recuar para o último dia útil | Sábados, domingos e feriados nacionais não têm pregão nem PTAX. O calendário de feriados é consultado (hoje via BrasilAPI) para encontrar o último dia útil. |
| **R10** | Divergência > 20% entre B3 e PTAX → gerar alerta | Um spread tão grande normalmente indica problema (instrumento errado, datas descasadas, etc.) e merece olhar humano — por isso vira um `[WARN]` na execução. |

---

## 4. As moedas e como cada uma é calculada

| Moeda | Instrumento B3 (tipo \| sufixo) | Método |
|---|---|---|
| USD | `RT \| DOL-D1` | direto (processado **primeiro** — vira a base para GBP/NZD/CNY) |
| EUR | `RT \| REUR-D1` | direto |
| JPY | `TX \| JPY` | direto |
| AUD | `RT \| AUD-T1` | direto |
| DKK | `RT \| DKK-T1` | direto |
| SEK | `RT \| RSEK-D1` | direto |
| CHF | `RT \| RCHF-D1` | direto |
| ZAR | `RT \| RZAR-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| CLP | `RT \| RCLP-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| TRY | `RT \| RTRY-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| NOK | `RT \| RNOK-D1` | direto |
| MXN | `RT \| RMXN-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| CNH | `RT \| RCNH-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| RUB | `RT \| RRUB-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| CAD | `RT \| RCAD-D1` | direto |
| ARS | `RT \| RARS-D1` | direto *(sem PTAX de fechamento no BACEN)* |
| GBP | `RT \| GBP-PF` | paridade × USD spot |
| NZD | `RT \| NZD-PF` | paridade × USD spot *(sem PTAX de fechamento no BACEN)* |
| CNY | `RT \| CNY-PF` | USD spot ÷ paridade *(sem PTAX de fechamento no BACEN)* |
| AED, BOB, COP, CRC, CZK, HKD, HUF, IDR, INR, KWD, MYR, PEN, PHP, PLN, PYG, QAR, RON, SAR, SGD, THB, TWD, UYU, VND | `RT \| {CÓDIGO}-T1` | direto *(sem PTAX de fechamento no BACEN — todas)* |

> **Por que essas 23 moedas só foram adicionadas depois (2026-06-07)?** O arquivo da B3
> não tem nenhum campo dizendo "isto é uma moeda" — ele tem ~1.800 instrumentos por dia,
> a maioria ações e derivativos. As 19 moedas originais foram identificadas via curadoria
> manual (cruzando o PRD com nomes reais do arquivo). Ao revisar o arquivo de novo,
> percebemos que a B3 também publica cotações diretas em BRL para muitas outras moedas
> através de instrumentos `{CÓDIGO}-T1`/`{CÓDIGO}-T2` — mesmo padrão já usado para AUD e
> DKK. Cada uma dessas 23 foi validada decodificando o valor e checando se o resultado é
> uma cotação BRL plausível (ex: `HKD-T1 = 0.6453` ≈ HKD/BRL real, `KWD-T1 = 16.49` ≈
> KWD/BRL real) e rodando o pipeline ponta a ponta sem disparar alerta de divergência.

---

## 5. Resultado de execuções reais

### Execução de referência (05/06/2026, antes da expansão para 42 moedas)

| Moeda | B3 | PTAX venda | Spread |
|---|---|---|---|
| USD | 5,1453 | 5,1244 | +0,41% |
| EUR | 5,9279 | 5,9100 | +0,30% |
| JPY | 0,0322 | 0,0320 | +0,58% |
| GBP | 6,8613 | 6,8462 | +0,22% |
| CNY | 0,7605 | — (sem PTAX) | — |

Spreads consistentemente pequenos (entre 0% e ~0,6%) e nenhum alerta de divergência
(>20%) — sinal de que o cálculo está coerente e batendo com o mercado real.

### Validação da expansão para 42 moedas (07/06/2026, dado de 29/05/2026)

Após adicionar as 23 moedas novas (regra "23 moedas" acima), o pipeline foi rodado
ponta a ponta contra dados reais de 29/05/2026 para validar as novas entradas:

| Moeda | B3 | PTAX venda | Spread |
|---|---|---|---|
| USD | 5,0438 | 5,0569 | -0,26% |
| EUR | 5,8831 | 5,9060 | -0,39% |
| GBP | 6,7890 | 6,8147 | -0,38% |
| AED *(nova)* | 1,3768 | — (sem PTAX) | — |
| KWD *(nova)* | 16,4935 | — (sem PTAX) | — |
| VND *(nova)* | 0,000193 | — (sem PTAX) | — |

Nenhuma das 42 moedas disparou alerta de divergência (>20%). As 23 novas moedas
decodificaram para valores plausíveis em BRL e ficaram corretamente sem PTAX (R6) —
o BACEN não publica boletim de fechamento para nenhuma delas.

### Execuções históricas adicionais (validação de múltiplas datas)

O pipeline também foi rodado para datas passadas (30/01, 27/02, 30/03 e 30/04/2026),
gerando planilhas separadas (`taxas_spot_b3_{AAAAMMDD}.xlsx`) e confirmando spreads
saudáveis e ausência de alertas em todas:

| Data | USD/BRL B3 | USD/BRL PTAX | EUR/BRL B3 | EUR/BRL PTAX |
|---|---|---|---|---|
| 30/01/2026 | 5,2627 | 5,2301 | 6,2526 | 6,2217 |
| 27/02/2026 | 5,1381 | 5,1495 | 6,0717 | 6,0795 |
| 30/03/2026 | 5,2475 | 5,2353 | 6,0136 | 5,9970 |
| 30/04/2026 | 4,9587 | 4,9886 | 5,8210 | 5,8511 |

---

## 6. Pontos de atenção para quem for dar manutenção

- **Fontes externas mudam sem aviso.** Três das regras documentadas no PRD original
  (endpoint de feriados do BACEN, endpoint PTAX em lote, divisor por moeda) **não
  existiam de fato** ou estavam erradas — só foram descobertas rodando o pipeline
  contra dados reais. Sempre que algo parecer "estranho demais para ser verdade"
  (valores 1000x menores, endpoints "convenientes demais"), vale a pena confirmar
  contra a fonte real antes de confiar no documento.
- **O download da B3 é instável** — às vezes devolve resposta vazia. Há retry com
  validação de conteúdo, mas se o problema persistir, o arquivo simplesmente não
  estará disponível ainda (lembrar da janela: B3 ~19h BRT, PTAX ~18h BRT).
- **PTAX ausente é normal para várias moedas** — não tratar isso como bug.
- **Adicionar uma nova moeda exige curadoria manual, não detecção automática.** O arquivo
  da B3 não identifica quais instrumentos são moedas — várias siglas de 3 letras parecem
  código de câmbio mas são tickers de ações (ex: `RYN`, `RDC`, `SEL`). Antes de adicionar
  uma moeda em `INSTRUMENTOS` (config.py): (1) confirme que o sufixo escolhido decodifica
  para um valor plausível em BRL comparando com a cotação real do dia, e (2) rode o
  pipeline ponta a ponta e confirme que não dispara alerta de divergência > 20% (R10).
  Pular essa validação foi exatamente o que causou os 5 bugs documentados em
  `SHIPPED_20260607.md`.
