# Ambiente Virtual Gerenciado pelo uv

> Como o uv cria e gerencia `.venv` automaticamente, sem ativação manual.

## Conceito

O uv gerencia o `.venv` automaticamente na raiz do projeto. Qualquer `uv run` detecta o projeto via `pyproject.toml`, cria o `.venv` se não existir, e executa dentro dele — sem necessidade de `source .venv/bin/activate`.

## Como funciona

```bash
# uv cria .venv automaticamente no primeiro uv add
uv add pandas          # cria .venv + instala pandas

# uv run usa .venv sem ativar manualmente
uv run python script.py

# Criar .venv explicitamente (raramente necessário)
uv venv
uv venv --python 3.12  # versão específica
```

## Tabela de operações

| Ação | Resultado | Notas |
|------|-----------|-------|
| `uv add pandas` | `.venv` criado + pandas instalado | Automático na 1ª execução |
| `uv run python x.py` | Executa no `.venv` | Sem ativar o ambiente |
| `uv sync` | Sincroniza `.venv` com `uv.lock` | Usar após `git clone` |

## Certo vs Errado

**Errado:**
```bash
source .venv/bin/activate
pip install pandas
python script.py
```

**Certo:**
```bash
uv add pandas
uv run python script.py
```

## .gitignore obrigatório

```
.venv/
```

O `uv.lock` **deve** ser commitado — é o lockfile determinístico.
