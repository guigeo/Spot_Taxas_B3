# Tratamento de Resposta

> Status codes, JSON e download de arquivos binários.

## Verificação de status

```python
r = session.get(url, timeout=30)
r.raise_for_status()   # lança HTTPError para 4xx/5xx
```

## Resposta JSON (API BACEN)

```python
r = session.get(url_bacen, timeout=30)
r.raise_for_status()
data = r.json()            # dict/list
registros = data['value']  # campo OData
```

## Download de arquivo binário (B3 .ex_)

```python
# Opção 1: conteúdo completo em memória (arquivo pequeno)
r = session.get(url_b3, timeout=60)
r.raise_for_status()
with open('ID260603.ex_', 'wb') as f:
    f.write(r.content)

# Opção 2: stream para arquivos grandes
with session.get(url_b3, stream=True, timeout=60) as r:
    r.raise_for_status()
    with open('ID260603.ex_', 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
```

## Tratamento de erros

```python
from requests.exceptions import HTTPError, ConnectionError, Timeout

try:
    r = session.get(url, timeout=30)
    r.raise_for_status()
except Timeout:
    raise RuntimeError(f"Timeout ao acessar: {url}")
except HTTPError as e:
    raise RuntimeError(f"HTTP {e.response.status_code}: {url}")
except ConnectionError:
    raise RuntimeError(f"Sem conexão: {url}")
```

## Encoding

Para a API BACEN (JSON), `r.json()` cuida do encoding automaticamente. Para o arquivo B3 binário, salvar como `'wb'` e depois abrir o `.ex_` para extrair.
