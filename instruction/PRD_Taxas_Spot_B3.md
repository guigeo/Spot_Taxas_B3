# PRD — Pipeline de Taxas Spot B3 vs PTAX BACEN

## 1. Contexto e Objetivo

A B3 publica diariamente um arquivo posicional (formato texto fixo) com taxas e índices de mercado. O BACEN publica diariamente a PTAX — taxa de câmbio oficial do governo brasileiro.

O objetivo deste processo é **extrair as taxas spot de câmbio do arquivo da B3, convertê-las para a escala correta em BRL e compará-las com a PTAX do BACEN**, gerando uma tabela com as cotações das principais moedas nas duas fontes para a mesma data de referência.

**Casos de uso:**
- Precificação de derivativos cambiais
- Conciliação de posições de câmbio
- Auditoria de spread B3 vs PTAX
- Controle de risco e compliance cambial

---

## 2. Entradas (Inputs)

### 2.1 Arquivo Bruto da B3

- **Nome padrão:** `Indic.txt` (após extração — ver abaixo)
- **Formato:** texto posicional de largura fixa, uma linha por instrumento/data
- **Frequência:** diário (D útil)
- **Cobertura:** dois dias de referência por arquivo (D-1 e D)
- **Volume típico:** ~3.600 a 3.800 linhas

**Download:**

| Campo | Detalhe |
|-------|---------|
| URL base | `https://www.b3.com.br/pesquisapregao/download` |
| Parâmetro | `filelist=ID{YYMMDD}.ex_` |
| Exemplo (03/06/2026) | `https://www.b3.com.br/pesquisapregao/download?filelist=ID260603.ex_,` |
| Convenção de data | `YYMMDD` — ano com 2 dígitos, mês, dia |
| Formato do arquivo | Comprimido `.ex_` (auto-extraível); extrair antes de processar |
| Autenticação | Nenhuma — endpoint público |

**Lógica para construir o nome do arquivo:**
```python
from datetime import date

def b3_filename(ref_date: date) -> str:
    # YYMMDD: ano 2 dígitos
    return f"ID{ref_date.strftime('%y%m%d')}.ex_"

def b3_download_url(ref_date: date) -> str:
    return f"https://www.b3.com.br/pesquisapregao/download?filelist={b3_filename(ref_date)},"
```

> **Atenção:** o job deve ajustar automaticamente para o dia útil anterior caso a data solicitada seja fim de semana ou feriado — a B3 não publica arquivo em dias não úteis.

**Estrutura de cada linha (116 caracteres úteis + espaços):**

```
Posições  Campo              Exemplo
──────────────────────────────────────────────────────────────────
1–6       Sequencial         000001
7–11      Código de campo    00101  (sempre 00101 = taxa spot)
12–19     Data (YYYYMMDD)    20260603
20–21     Tipo instrumento   RT, BT, BV, TX, DF, DE, EI, BW...
22–46     Nome instrumento   RTDOL-D1 (até 25 chars, padded)
47+       Valor numérico     +00000000000000000005009904
```

**Codificação do valor numérico:**
- Sinal `+` ou `-` seguido de dígitos zerados à esquerda
- Os **últimos 2 dígitos** do campo numérico indicam o número de casas decimais implícitas
- O valor real é: `digits_sem_os_2_ultimos / 10^(indicador_casas)`

Exemplos:
```
+00000000000000000005009904  →  0000000000500 / 10⁴  =  5.0099  (USD/BRL)
+00000000000000000017419700  →  0000000001741 / 10⁰  =  175419  (IBOVESPA pts)
+00000000000000000031340307  →  0000000003134 / 10⁷  =  0.003134 (JPY/BRL)
```

### 2.2 PTAX do BACEN

- **Fonte:** API pública do Banco Central do Brasil (OData)
- **Data de referência:** usar a data D do arquivo B3 (data mais recente das duas presentes no arquivo)
- **Autenticação:** nenhuma — endpoint público

**Endpoint por moeda (individual):**
```
GET https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/
    CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)
    ?@moeda='USD'&@dataCotacao='06-03-2026'&$format=json
```

**Endpoint em lote — todas as moedas de um boletim (recomendado):**
```
GET https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/
    CotacaoMoedaAberturaOuIntermediario(codigoMoeda=@codigoMoeda,dataCotacao=@dataCotacao)
```

**Ou boletim de fechamento completo:**
```
GET https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/
    CotacaoTodosComercialDia(dataCotacao=@dataCotacao)
    ?@dataCotacao='06-03-2026'&$format=json
```

> Preferir o endpoint `CotacaoTodosComercialDia` — retorna todas as moedas de uma só chamada e evita rate limit.

**Formato da data na API:** `MM-DD-YYYY` (mês-dia-ano, com zeros à esquerda)

```python
from datetime import date

def bacen_date_param(ref_date: date) -> str:
    return ref_date.strftime('%m-%d-%Y')  # ex: '06-03-2026'
```

**Campos relevantes na resposta:**

| Campo | Descrição |
|-------|-----------|
| `dataCotacao` | Data no formato `MM-DD-YYYY` |
| `codISO` | Código ISO 4217 da moeda (ex: USD, EUR) |
| `cotacaoCompra` | Taxa de compra em BRL |
| `cotacaoVenda` | Taxa de venda em BRL |
| `tipoBoletim` | `Fechamento` (usar este) ou `Abertura` / `Intermediário` |

> Filtrar apenas registros com `tipoBoletim = 'Fechamento'` para consistência com o fechamento do mercado.

---

## 3. Mapeamento de Instrumentos B3 → Moeda

Cada moeda é extraída de um instrumento específico do arquivo B3. Abaixo a tabela completa com o nome do instrumento, o divisor aplicado e as regras especiais.

### 3.1 Instrumentos diretos (cotação já em BRL ou USD com divisor simples)

| Moeda ISO | Instrumento B3 (tipo\|nome) | Divisor extra | Observação |
|-----------|----------------------------|---------------|------------|
| USD | `RT\|DOL-D1` | ÷ 1.000 | Taxa de câmbio USD/BRL D+1 |
| AUD | `RT\|AUD-T1` | ÷ 1.000 | Taxa de câmbio AUD/BRL |
| DKK | `RT\|DKK-T1` | ÷ 1.000 | Já vem em BRL diretamente |
| SEK | `RT\|RSEK-D1` | ÷ 1.000 | — |
| CHF | `RT\|RCHF-D1` | ÷ 1.000 | — |
| ZAR | `RT\|RZAR-D1` | ÷ 1.000 | — |
| CLP | `RT\|RCLP-D1` | ÷ 1.000 | — |
| TRY | `RT\|RTRY-D1` | ÷ 1.000 | — |
| NOK | `RT\|RNOK-D1` | ÷ 1.000 | — |
| MXN | `RT\|RMXN-D1` | ÷ 1.000 | — |
| CNH | `RT\|RCNH-D1` | ÷ 1.000 | — |
| RUB | `RT\|RRUB-D1` | ÷ 1.000 | — |
| CAD | `RT\|RCAD-D1` | ÷ 1.000 | — |
| ARS | `RT\|RARS-D1` | ÷ 1.000 | — |
| EUR | `RT\|REUR-D1` | ÷ 10.000.000 | Escala diferente no arquivo B3 |
| JPY | `TX\|JPY` | ÷ 1.000 | Instrumento do tipo TX (taxa) |

### 3.2 Instrumentos via paridade USD (cálculo derivado)

Esses instrumentos não têm cotação direta em BRL no arquivo B3 — a B3 publica apenas a **paridade** da moeda em relação ao USD. A cotação em BRL é calculada multiplicando o USD spot pela paridade.

| Moeda ISO | Instrumento paridade B3 | Fórmula |
|-----------|------------------------|---------|
| NZD | `RT\|NZD-PF` | `USD_BRL_spot × paridade_NZD_USD` |
| GBP | `RT\|GBP-PF` | `USD_BRL_spot × paridade_GBP_USD` |

### 3.3 Instrumento via divisão (paridade inversa)

| Moeda ISO | Instrumento paridade B3 | Fórmula |
|-----------|------------------------|---------|
| CNY | `RT\|CNY-PF` | `USD_BRL_spot ÷ paridade_CNY_USD` |

> A B3 publica a paridade CNY por USD. Para obter o spot CNY/BRL é necessário dividir o USD spot pela paridade CNY/USD.

---

## 4. Processo de Transformação (Passo a Passo)

### Passo 1 — Parse do arquivo bruto

Para cada linha do arquivo B3:

```python
sequencial     = linha[0:6]
codigo_campo   = linha[6:11]
data           = linha[11:19]   # YYYYMMDD
tipo_instrumento = linha[19:21]
nome_instrumento = linha[21:46].strip()
valor_raw      = linha[46:].strip()  # ex: "+00000000000000000005009904"
```

### Passo 2 — Extração e decodificação do valor

```python
# Remover sinal e zeros à esquerda
digits = valor_raw.lstrip('+').lstrip('-')

# Últimos 2 dígitos = indicador de casas decimais
indicador_casas = int(digits[-2:])
valor_inteiro   = int(digits[:-2])

# Valor real
valor_real = valor_inteiro / (10 ** indicador_casas)

# Se o sinal for negativo
if valor_raw.startswith('-'):
    valor_real = -valor_real
```

### Passo 3 — Seleção dos instrumentos por moeda

Filtrar o resultado do Passo 2 usando a tabela do item 3 como lookup pelo campo `tipo_instrumento + nome_instrumento`. Selecionar a linha com a **data mais recente** presente no arquivo (data D).

### Passo 4 — Aplicação dos divisores e casos especiais

- **Instrumentos diretos:** aplicar o divisor da tabela 3.1
- **NZD e GBP:** multiplicar o USD spot (já calculado) pela paridade do instrumento -PF
- **CNY:** dividir o USD spot pela paridade do instrumento CNY-PF
- **EUR:** o divisor é 10^7 em vez de 10^3 — confirmar com o valor real esperado se mudou

### Passo 5 — Carregamento da PTAX

Buscar a PTAX do BACEN para a **mesma data D** do arquivo B3. Extrair os campos `cotacaoCompra` e `cotacaoVenda` para cada moeda da lista.

### Passo 6 — Join e resultado final

Para cada moeda: `{ moeda, cotacao_b3, ptax_compra, ptax_venda, spread_b3_ptax }`

---

## 5. Saída Esperada (Output)

Tabela com as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| `data_referencia` | Data D do arquivo B3 |
| `moeda_iso` | Código ISO 4217 |
| `cotacao_b3` | Spot extraído do arquivo B3 (em BRL) |
| `ptax_compra` | PTAX de compra do BACEN |
| `ptax_venda` | PTAX de venda do BACEN |
| `spread_b3_ptax` | Diferença percentual entre B3 e PTAX |
| `instrumento_b3` | Nome do instrumento de origem |
| `metodo_calculo` | `direto`, `paridade_multiplicada`, `paridade_dividida` |

**Moedas cobertas (19):** USD, EUR, AUD, GBP, CAD, CHF, JPY, NZD, SEK, NOK, DKK, ZAR, MXN, ARS, CLP, TRY, CNY, CNH, RUB

---

## 6. Regras de Negócio e Validações

| Regra | Descrição |
|-------|-----------|
| Data de referência | Usar sempre a data D (mais recente) do arquivo, não D-1 |
| PTAX ausente | Se o BACEN não publicou PTAX para determinada moeda no dia, registrar como `null` |
| Instrumento ausente | Se o instrumento não for encontrado no arquivo B3 do dia, registrar `null` e alertar |
| Mudança de nome | Os nomes de instrumento podem mudar entre arquivos (ex: `ARS-D1` → `RARS-D1`); busca deve ser por sufixo, não match exato |
| Indicador de casas | Verificar se o indicador de casas decimais está consistente com o valor esperado; divergência acima de 20% vs PTAX deve gerar alerta |
| Escala do EUR | Historicamente o EUR usa divisor 10^7; confirmar a cada arquivo |
| NZD/GBP | Dependem do USD spot estar disponível — processar USD primeiro |

---

## 7. Dependências, Frequência e Download

### Janela de disponibilidade

| Fonte | Disponível a partir de | Observação |
|-------|------------------------|------------|
| PTAX BACEN (fechamento) | ~18h BRT | Endpoint `tipoBoletim=Fechamento` |
| Arquivo B3 (`ID{YYMMDD}.ex_`) | ~19h BRT | Após fechamento do pregão |
| Execução ideal do job | Após 19h BRT | Garante ambos disponíveis |

### Fluxo de download do job

```
1. Calcular data D (hoje se dia útil, senão último dia útil)
2. Baixar arquivo B3:
      GET https://www.b3.com.br/pesquisapregao/download?filelist=ID{YYMMDD}.ex_,
      → Salvar como ID{YYMMDD}.ex_
      → Extrair → Indic.txt
3. Baixar PTAX BACEN:
      GET https://olinda.bcb.gov.br/.../CotacaoTodosComercialDia
          ?@dataCotacao='{MM-DD-YYYY}'&$format=json
      → Filtrar tipoBoletim = 'Fechamento'
4. Processar conforme seção 4
```

### Tratamento de dias não úteis

- Se a data calculada for sábado, domingo ou feriado nacional brasileiro, recuar para o último dia útil
- O job deve manter uma lista de feriados nacionais ou consultar a API de calendário do BACEN:
  ```
  GET https://olinda.bcb.gov.br/olinda/servico/feriados_nacionais/versao/v1/odata/
      Feriados(ano=@ano)?@ano='2026'&$format=json
  ```

---

## 8. Glossário

| Termo | Significado |
|-------|-------------|
| Spot | Cotação para liquidação imediata (D+0 ou D+1) |
| PTAX | Taxa de câmbio de referência oficial do Banco Central do Brasil |
| D+1 (-D1) | Liquidação em 1 dia útil |
| Paridade | Razão entre duas moedas estrangeiras (ex: GBP/USD = 1.35) |
| Tipo A (PTAX) | Moeda cotada diretamente em BRL |
| Tipo B (PTAX) | Moeda cotada via paridade com USD |
| Indicador de casas | Últimos 2 dígitos do campo numérico B3, define quantas casas decimais aplicar |
