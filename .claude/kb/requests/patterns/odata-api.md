# Pattern: API OData BACEN (PTAX)

> Consultar a API pública do Banco Central para obter PTAX de fechamento.

## Endpoint recomendado

`CotacaoTodosComercialDia` — retorna todas as moedas em uma chamada, evitando rate limit.

```
GET https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/
    CotacaoTodosComercialDia(dataCotacao=@dataCotacao)
    ?@dataCotacao='06-03-2026'&$format=json
```

**Formato da data:** `MM-DD-YYYY` (mês-dia-ano, zeros à esquerda)

## Implementação

```python
import requests
import pandas as pd
from datetime import date


def bacen_date_param(ref_date: date) -> str:
    return ref_date.strftime('%m-%d-%Y')   # ex: '06-03-2026'


def buscar_ptax(ref_date: date) -> pd.DataFrame:
    base = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
    endpoint = "CotacaoTodosComercialDia(dataCotacao=@dataCotacao)"
    params = {
        '@dataCotacao': f"'{bacen_date_param(ref_date)}'",
        '$format': 'json',
    }

    with requests.Session() as s:
        s.headers.update({'Accept': 'application/json'})
        r = s.get(f"{base}/{endpoint}", params=params, timeout=(5, 30))
        r.raise_for_status()

    data = r.json().get('value', [])
    df = pd.DataFrame(data)

    # Filtrar apenas fechamento
    df = df[df['tipoBoletim'] == 'Fechamento'].copy()

    return df[['codISO', 'cotacaoCompra', 'cotacaoVenda', 'dataCotacao']]
```

## Campos relevantes na resposta

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `codISO` | str | Código ISO 4217 (USD, EUR...) |
| `cotacaoCompra` | float | Taxa de compra em BRL |
| `cotacaoVenda` | float | Taxa de venda em BRL |
| `tipoBoletim` | str | `Fechamento`, `Abertura`, `Intermediário` |
| `dataCotacao` | str | Data no formato `MM-DD-YYYY` |

## PTAX ausente

Se o BACEN não publicou para uma moeda, o DataFrame não terá a linha. Tratar com `merge(how='left')` e registrar como `null`.

## Endpoint de feriados

```python
def buscar_feriados(ano: int) -> list[str]:
    base = "https://olinda.bcb.gov.br/olinda/servico/feriados_nacionais/versao/v1/odata"
    params = {'@ano': f"'{ano}'", '$format': 'json'}
    r = requests.get(f"{base}/Feriados(ano=@ano)", params=params, timeout=15)
    r.raise_for_status()
    return [f['data'] for f in r.json().get('value', [])]
```
