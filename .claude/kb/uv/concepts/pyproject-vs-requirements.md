# pyproject.toml + uv.lock vs requirements.txt

> Por que o uv usa pyproject.toml com uv.lock e como configurar corretamente.

## Conceito

O uv usa `pyproject.toml` (declaração de dependências com restrições) + `uv.lock` (lockfile determinístico com versões exatas). O `uv.lock` garante que `uv sync` produza o mesmo ambiente em qualquer máquina.

## Estrutura do pyproject.toml

```toml
[project]
name = "spot-taxas-b3"
version = "0.1.0"
description = "Pipeline de taxas B3"
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.0",
    "openpyxl>=3.1",
    "requests>=2.31",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
]
```

## Comandos

```bash
uv add pandas                   # adiciona + atualiza pyproject.toml e uv.lock
uv add "pandas>=2.0,<3.0"       # com restrição de versão
uv add --dev pytest ruff        # dependências de desenvolvimento
uv sync                         # instalar tudo do uv.lock
uv sync --no-dev                # apenas produção
uv sync --frozen                # sync sem alterar lockfile (CI)
```

## Tabela de arquivos

| Arquivo | Função | Commitar? |
|---------|--------|-----------|
| `pyproject.toml` | Declara dependências com restrições | Sim |
| `uv.lock` | Versões exatas determinísticas | Sim |
| `.venv/` | Ambiente virtual local | Não |

## Pitfall: Editar pyproject.toml manualmente

**Errado:** Editar `pyproject.toml` diretamente — `uv.lock` fica desatualizado.

**Certo:** `uv add <pacote>` — atualiza `pyproject.toml` E `uv.lock` atomicamente.
