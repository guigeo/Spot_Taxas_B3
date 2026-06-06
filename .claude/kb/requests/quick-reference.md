# Requests Quick Reference

> Fast lookup. Para exemplos completos, ver patterns/.

## GET básico

| Operação | Código |
|----------|--------|
| GET simples | `r = requests.get(url, timeout=30)` |
| Com params | `r = requests.get(url, params={'key': 'val'}, timeout=30)` |
| Verificar status | `r.raise_for_status()` |
| JSON response | `data = r.json()` |

## Download de arquivo binário

| Operação | Código |
|----------|--------|
| Stream download | `r = requests.get(url, stream=True, timeout=60)` |
| Salvar em disco | `with open('file.ex_', 'wb') as f: f.write(r.content)` |
| Chunks grandes | `for chunk in r.iter_content(8192): f.write(chunk)` |

## Session (reutilizar conexão)

```python
with requests.Session() as s:
    s.headers.update({'User-Agent': 'spot-taxas-b3/1.0'})
    r1 = s.get(url_b3)
    r2 = s.get(url_bacen)
```

## Retry simples

```python
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503])
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

## URLs do projeto

| Fonte | URL |
|-------|-----|
| B3 download | `https://www.b3.com.br/pesquisapregao/download?filelist=ID{YYMMDD}.ex_,` |
| BACEN PTAX todas | `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoTodosComercialDia(dataCotacao=@dataCotacao)?@dataCotacao='{MM-DD-YYYY}'&$format=json` |
| BACEN feriados | `https://olinda.bcb.gov.br/olinda/servico/feriados_nacionais/versao/v1/odata/Feriados(ano=@ano)?@ano='{YYYY}'&$format=json` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Uma chamada simples | `requests.get(url)` |
| Múltiplas chamadas | `requests.Session()` |
| Arquivo grande | `stream=True` + `iter_content` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Sem timeout | Sempre `timeout=(5, 30)` (connect, read) |
| Ignorar status code | `r.raise_for_status()` antes de processar |
| `requests.get` em loop | Criar `Session` fora do loop |

## Related Documentation

| Topic | Path |
|-------|------|
| Download B3 | `patterns/download-binary.md` |
| API BACEN | `patterns/odata-api.md` |
| Full Index | `index.md` |
