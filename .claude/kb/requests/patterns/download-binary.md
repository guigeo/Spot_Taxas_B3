# Pattern: Download do Arquivo B3 (.ex_)

> Baixar e salvar o arquivo comprimido diário da B3.

## Contexto

A B3 publica um arquivo `.ex_` (comprimido auto-extraível) diariamente. O nome segue o padrão `ID{YYMMDD}.ex_`. Após o download, é necessário extraí-lo para obter o `Indic.txt`.

## Implementação

```python
import zipfile
import requests
from datetime import date
from pathlib import Path


def b3_download_url(ref_date: date) -> str:
    return (
        f"https://www.b3.com.br/pesquisapregao/download"
        f"?filelist=ID{ref_date.strftime('%y%m%d')}.ex_,"
    )


def baixar_arquivo_b3(ref_date: date, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"ID{ref_date.strftime('%y%m%d')}.ex_"
    dest = output_dir / filename
    url = b3_download_url(ref_date)

    with requests.Session() as s:
        s.headers.update({'User-Agent': 'spot-taxas-b3/1.0'})
        with s.get(url, stream=True, timeout=(10, 60)) as r:
            r.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    return dest


def extrair_indic(arquivo_ex: Path, output_dir: Path) -> Path:
    # O arquivo .ex_ é um ZIP com nome diferente
    indic_path = output_dir / 'Indic.txt'
    with zipfile.ZipFile(arquivo_ex) as zf:
        # Pegar o primeiro arquivo dentro do ZIP
        nome_interno = zf.namelist()[0]
        zf.extract(nome_interno, output_dir)
        extraido = output_dir / nome_interno
        extraido.rename(indic_path)
    return indic_path
```

## Uso

```python
ref_date = date(2026, 6, 3)
output_dir = Path('data/raw')

arquivo = baixar_arquivo_b3(ref_date, output_dir)
indic   = extrair_indic(arquivo, output_dir)
```

## Pitfalls

| Don't | Do |
|-------|-----|
| Sem timeout | `timeout=(10, 60)` |
| `open(dest, 'w')` para binário | `open(dest, 'wb')` |
| Assumir que .ex_ é ZIP | Testar com `zipfile.is_zipfile(arquivo)` antes |
