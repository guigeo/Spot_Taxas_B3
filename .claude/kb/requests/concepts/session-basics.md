# Session e Reutilização de Conexão

> Por que usar `requests.Session` em vez de `requests.get` direto.

## Conceito

`requests.Session` reutiliza conexões TCP (keep-alive), compartilha headers e cookies entre requisições. Para o projeto B3, onde fazemos 2+ chamadas HTTP por execução, usar Session reduz latência e é a prática correta.

## Session vs get direto

```python
# Errado para múltiplas chamadas
r1 = requests.get(url_b3)
r2 = requests.get(url_bacen)   # abre nova conexão

# Certo
with requests.Session() as s:
    s.headers.update({'User-Agent': 'spot-taxas-b3/1.0'})
    r1 = s.get(url_b3)          # conexão reutilizada
    r2 = s.get(url_bacen)
```

## Headers comuns

```python
s.headers.update({
    'User-Agent': 'spot-taxas-b3/1.0',
    'Accept': 'application/json',
})
```

## Timeout padrão

```python
# Sempre definir timeout
r = s.get(url, timeout=(5, 30))   # (connect_timeout, read_timeout) em segundos
```

## Context manager (obrigatório)

Sempre usar `with requests.Session() as s:` — garante que a sessão seja fechada corretamente mesmo em caso de erro.
