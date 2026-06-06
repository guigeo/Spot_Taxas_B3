# Pandas Quick Reference

> Fast lookup. Para exemplos completos, ver patterns/.

## Leitura de dados

| Operação | Código |
|----------|--------|
| CSV com separador | `pd.read_csv('f.csv', sep=';', dtype=str)` |
| Texto largura fixa | `pd.read_fwf('f.txt', colspecs=[(0,6),(6,11)], names=['seq','cod'])` |
| JSON (API) | `pd.json_normalize(response['value'])` |

## Seleção e filtro

| Operação | Código |
|----------|--------|
| Filtrar coluna | `df[df['col'] == 'valor']` |
| Múltiplos valores | `df[df['col'].isin(['A','B'])]` |
| Condição composta | `df[(df['a'] > 0) & (df['b'] == 'X')]` |
| Linha com maior data | `df.loc[df['data'].idxmax()]` |

## Transformação

| Operação | Código |
|----------|--------|
| Nova coluna calculada | `df['spread'] = (df['b3'] / df['ptax'] - 1) * 100` |
| Apply função | `df['val'] = df['raw'].apply(decode_valor)` |
| Renomear colunas | `df.rename(columns={'old': 'new'}, inplace=True)` |
| Converter tipo | `df['data'] = pd.to_datetime(df['data'], format='%Y%m%d')` |

## Merge / Join

| Operação | Código |
|----------|--------|
| Inner join | `pd.merge(df1, df2, on='moeda', how='inner')` |
| Left join | `pd.merge(df1, df2, on='moeda', how='left')` |
| Join por índice | `df1.join(df2, how='left')` |

## Exportação

| Operação | Código |
|----------|--------|
| Excel (engine openpyxl) | `df.to_excel('out.xlsx', index=False, engine='openpyxl')` |
| Excel com ExcelWriter | `with pd.ExcelWriter('out.xlsx', engine='openpyxl') as w: df.to_excel(w, sheet_name='Taxas', index=False)` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Arquivo posicional B3 | `read_fwf` ou slicing manual por posição |
| API JSON (BACEN) | `json_normalize` no campo `value` da resposta |
| Join B3 + PTAX | `merge(how='left', on='moeda_iso')` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `df['col'][0]` | `df.loc[0, 'col']` ou `df.iloc[0]['col']` |
| Encadear filtros sem parênteses | `(cond1) & (cond2)` com parênteses explícitos |
| Ignorar `dtype` no read | Especificar `dtype=str` para campos numéricos com zeros à esquerda |

## Related Documentation

| Topic | Path |
|-------|------|
| Parse arquivo B3 | `patterns/parse-fixed-width.md` |
| Full Index | `index.md` |
