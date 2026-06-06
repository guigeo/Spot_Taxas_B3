# Pattern: Inicializar Projeto Python do Zero com uv

> Sequência completa e reproduzível para criar um projeto Python usando uv.

## Quando usar

- Projeto novo sem `pyproject.toml` configurado
- Replicando ambiente em nova máquina após `git clone`

## Implementação

```bash
# 1. Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh
# ou: brew install uv

# 2. Inicializar o projeto (dentro do diretório)
uv init
uv python pin 3.12

# 3. Adicionar dependências do projeto
uv add pandas openpyxl requests
# Cria .venv, atualiza pyproject.toml, gera uv.lock

# 4. Dependências de dev
uv add --dev pytest ruff

# 5. Verificar
uv run python -c "import pandas; print(pandas.__version__)"

# 6. Executar
uv run python main.py
uv run pytest
uvx ruff check .     # ferramenta avulsa sem instalar permanentemente
```

## pyproject.toml resultante para Spot_Taxas_B3

```toml
[project]
name = "spot-taxas-b3"
version = "0.1.0"
description = "Pipeline de taxas B3 vs PTAX BACEN"
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

## .gitignore mínimo

```
.venv/
__pycache__/
*.pyc
dist/
*.ex_
*.xlsx
output/
```

## Substituição pip → uv

| Pip (nunca usar) | uv (sempre usar) |
|------------------|------------------|
| `pip install pandas` | `uv add pandas` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip uninstall pandas` | `uv remove pandas` |
| `python script.py` | `uv run python script.py` |
