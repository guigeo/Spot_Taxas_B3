from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.parser import _decode_valor, parsear


@pytest.mark.parametrize(
    "valor_raw, esperado",
    [
        ("+00000000000000000005009904", 5.0099),
        ("+00000000000000000031340307", pytest.approx(0.0313403, abs=1e-7)),
        ("+00000000000000000017419700", 174197.0),
        ("-00000000000000000005009904", -5.0099),
    ],
)
def test_decode_valor(valor_raw: str, esperado: float) -> None:
    assert _decode_valor(valor_raw) == esperado


def _codifica_valor(decodificado: float, casas: int = 4, largura: int = 24) -> str:
    inteiro = round(decodificado * (10**casas))
    sinal = "-" if inteiro < 0 else "+"
    digitos = f"{abs(inteiro):0{largura}d}{casas:02d}"
    return f"{sinal}{digitos}"


def _linha(
    seq: str,
    codigo_campo: str,
    data: str,
    tipo: str,
    nome: str,
    valor_decodificado: float,
) -> str:
    valor_raw = _codifica_valor(valor_decodificado)
    return f"{seq:<6}{codigo_campo:<5}{data:<8}{tipo:<2}{nome:<25}{valor_raw}\n"


def _montar_arquivo(tmp_path: Path, linhas: list[str]) -> Path:
    indic = tmp_path / "Indic.txt"
    indic.write_text("".join(linhas), encoding="latin-1")
    return indic


def test_parsear_filtra_data_d_e_codigo_campo(tmp_path: Path) -> None:
    linhas = [
        _linha("000001", "00101", "20260602", "RT", "DOL-D1", 5.0001),
        _linha("000002", "00101", "20260603", "RT", "DOL-D1", 5.0099),
        _linha("000003", "99999", "20260603", "RT", "DOL-D1", 9.9999),
    ]
    indic = _montar_arquivo(tmp_path, linhas)

    df = parsear(indic, date(2026, 6, 3))

    usd = df[df["moeda_iso"] == "USD"].iloc[0]
    assert usd["cotacao_b3"] == pytest.approx(5.0099)


def test_parsear_instrumento_ausente_retorna_none(tmp_path: Path) -> None:
    linhas = [
        _linha("000001", "00101", "20260603", "RT", "DOL-D1", 5.0099),
    ]
    indic = _montar_arquivo(tmp_path, linhas)

    df = parsear(indic, date(2026, 6, 3))

    eur = df[df["moeda_iso"] == "EUR"].iloc[0]
    assert pd.isna(eur["cotacao_b3"])


def test_parsear_processa_usd_antes_de_gbp_nzd_cny(tmp_path: Path) -> None:
    linhas = [
        _linha("000001", "00101", "20260603", "RT", "GBP-PF", 13.5),
        _linha("000002", "00101", "20260603", "RT", "DOL-D1", 5.0),
        _linha("000003", "00101", "20260603", "RT", "CNY-PF", 7.0),
    ]
    indic = _montar_arquivo(tmp_path, linhas)

    df = parsear(indic, date(2026, 6, 3))

    usd_spot = df[df["moeda_iso"] == "USD"].iloc[0]["cotacao_b3"]
    gbp = df[df["moeda_iso"] == "GBP"].iloc[0]["cotacao_b3"]
    cny = df[df["moeda_iso"] == "CNY"].iloc[0]["cotacao_b3"]

    assert usd_spot == pytest.approx(5.0)
    assert gbp == pytest.approx(usd_spot * 13.5)
    assert cny == pytest.approx(usd_spot / 7.0)
