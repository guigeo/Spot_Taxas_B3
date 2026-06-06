# uv Quick Reference

> Comandos do dia a dia. NUNCA usar pip install neste projeto.

## Comandos principais

| Operação | Comando |
|----------|---------|
| Iniciar projeto | `uv init` |
| Adicionar dependência | `uv add pandas openpyxl requests` |
| Adicionar dev dependency | `uv add --dev pytest ruff` |
| Remover dependência | `uv remove <pacote>` |
| Instalar dependências | `uv sync` |
| Atualizar tudo | `uv lock --upgrade` |

## Execução

| Operação | Comando |
|----------|---------|
| Rodar script | `uv run python src/main.py` |
| Rodar módulo | `uv run python -m src.pipeline` |
| Rodar teste | `uv run pytest` |
| Shell no venv | `uv shell` (ativa o venv) |

## Ferramentas (global)

| Operação | Comando |
|----------|---------|
| Instalar ferramenta global | `uv tool install ruff` |
| Rodar ferramenta one-off | `uvx ruff check .` |

## Arquivos gerados

| Arquivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Configuração do projeto e dependências |
| `uv.lock` | Lockfile determinístico — commitar no git |
| `.venv/` | Ambiente virtual gerenciado pelo uv — NÃO commitar |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Adicionar lib ao projeto | `uv add <pacote>` |
| Rodar comando uma vez | `uvx <ferramenta>` |
| Ferramenta de uso frequente | `uv tool install <ferramenta>` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `pip install pandas` | `uv add pandas` |
| `python script.py` direto | `uv run python script.py` |
| Commitar `.venv/` | Adicionar `.venv/` ao `.gitignore` |
| `pip freeze > requirements.txt` | `uv lock` — o uv.lock já é o lockfile |

## Related Documentation

| Topic | Path |
|-------|------|
| Iniciar projeto | `patterns/init-project.md` |
| Full Index | `index.md` |
