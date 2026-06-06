# DataFrame Basics

> Estrutura central do pandas — tabela bidimensional com índice e colunas tipadas.

## Estrutura

```
         moeda_iso  cotacao_b3  ptax_compra
índice →    0          USD        5.0099       5.0050
            1          EUR        5.5210       5.5100
```

- **Índice**: identificador de linha (inteiro por padrão)
- **Colunas**: identificadas por nome, cada uma com um `dtype`
- **Series**: uma única coluna isolada (`df['col']` retorna Series)

## Tipos (dtype) importantes

| dtype | Uso |
|-------|-----|
| `object` | Strings (default para texto) |
| `float64` | Números decimais (taxas de câmbio) |
| `int64` | Inteiros |
| `datetime64` | Datas — resultado de `pd.to_datetime()` |

## Operações fundamentais

```python
# Criar a partir de lista de dicts
df = pd.DataFrame([
    {'moeda': 'USD', 'cotacao_b3': 5.0099},
    {'moeda': 'EUR', 'cotacao_b3': 5.5210},
])

# Inspecionar
df.dtypes          # tipos por coluna
df.shape           # (linhas, colunas)
df.head(5)         # primeiras 5 linhas

# Selecionar coluna
df['cotacao_b3']   # Series
df[['moeda', 'cotacao_b3']]  # DataFrame com subset de colunas

# Filtrar linhas
df[df['moeda'] == 'USD']
df.query("moeda == 'USD'")
```

## Conversão de tipos

```python
# String → float
df['valor'] = df['valor_str'].astype(float)

# String → datetime
df['data'] = pd.to_datetime(df['data_str'], format='%Y%m%d')
```
