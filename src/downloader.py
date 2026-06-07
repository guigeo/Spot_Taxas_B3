import io
import time
import zipfile
from datetime import date
from pathlib import Path

import requests

B3_DOWNLOAD_URL = "https://www.b3.com.br/pesquisapregao/download"


def _nome_arquivo(data_ref: date) -> str:
    return f"ID{data_ref.strftime('%y%m%d')}.ex_"


def _baixar(data_ref: date, raw_dir: Path) -> Path:
    nome = _nome_arquivo(data_ref)
    destino = raw_dir / nome
    params = {"filelist": f"{nome},"}

    for tentativa in range(3):
        try:
            with requests.Session() as s:
                r = s.get(B3_DOWNLOAD_URL, params=params, timeout=(5, 30))
                r.raise_for_status()
            if not r.content.startswith(b"PK"):
                raise RuntimeError("resposta vazia ou não-ZIP")
            break
        except (requests.RequestException, RuntimeError):
            if tentativa == 2:
                raise RuntimeError(
                    f"Falha ao baixar arquivo B3 para {data_ref.isoformat()}: {nome}"
                ) from None
            time.sleep(2**tentativa)

    raw_dir.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    return destino


def _extrair(arquivo_zip: Path, raw_dir: Path) -> Path:
    try:
        with zipfile.ZipFile(arquivo_zip) as zf_externo:
            nomes_externos = zf_externo.namelist()
            if not nomes_externos:
                raise RuntimeError(f"Arquivo B3 vazio: {arquivo_zip.name}")
            sfx_bytes = zf_externo.read(nomes_externos[0])
    except zipfile.BadZipFile as exc:
        raise RuntimeError(
            f"Arquivo B3 inválido (não é um ZIP extraível): {arquivo_zip.name}"
        ) from exc

    try:
        with zipfile.ZipFile(io.BytesIO(sfx_bytes)) as zf_interno:
            zf_interno.extract("Indic.txt", raw_dir)
    except (zipfile.BadZipFile, KeyError) as exc:
        raise RuntimeError(
            f"Indic.txt não encontrado dentro do arquivo SFX de {arquivo_zip.name}"
        ) from exc

    indic_path = raw_dir / "Indic.txt"
    if not indic_path.exists():
        raise RuntimeError(f"Indic.txt não encontrado após extrair {arquivo_zip.name}")
    return indic_path


def baixar_e_extrair(data_ref: date, raw_dir: Path) -> Path:
    arquivo_zip = _baixar(data_ref, raw_dir)
    return _extrair(arquivo_zip, raw_dir)
