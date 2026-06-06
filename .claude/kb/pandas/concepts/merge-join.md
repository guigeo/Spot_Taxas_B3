# Merge e Join

> Combinação de DataFrames — equivalente ao SQL JOIN.

## merge() — join por coluna

```python
# Inner join (só moedas em ambos)
resultado = pd.merge(df_b3, df_ptax, on='moeda_iso', how='inner')

# Left join (mantém todas as moedas do B3, null onde PTAX ausente)
resultado = pd.merge(df_b3, df_ptax, on='moeda_iso', how='left')

# Colunas com nomes diferentes
resultado = pd.merge(df_b3, df_ptax,
                     left_on='moeda_b3', right_on='codISO',
                     how='left')
```

## Sufixos quando há colunas duplicadas

```python
resultado = pd.merge(df_b3, df_ptax, on='moeda_iso',
                     suffixes=('_b3', '_ptax'))
# → colunas: cotacao_b3, cotacao_ptax
```

## Resultado esperado no projeto

```python
# df_b3: moeda_iso, cotacao_b3, instrumento_b3, metodo_calculo
# df_ptax: moeda_iso, ptax_compra, ptax_venda

final = pd.merge(df_b3, df_ptax, on='moeda_iso', how='left')
final['spread_b3_ptax'] = (final['cotacao_b3'] / final['ptax_venda'] - 1) * 100
```

## Verificação após merge

```python
# Quantas moedas ficaram sem PTAX?
sem_ptax = final[final['ptax_venda'].isna()]
if not sem_ptax.empty:
    print(f"PTAX ausente: {sem_ptax['moeda_iso'].tolist()}")
```
