from datetime import date
from pathlib import Path

import pandas as pd

from src.config import INSTRUMENTOS


def _decode_valor(valor_raw: str) -> float:
    digits = valor_raw.lstrip("+").lstrip("-")
    casas = int(digits[-2:])
    inteiro = int(digits[:-2])
    valor = inteiro / (10**casas)
    return -valor if valor_raw.startswith("-") else valor


def _buscar_instrumento(df: pd.DataFrame, tipo: str, sufixo: str) -> float | None:
    mask = (df["tipo"] == tipo) & df["nome"].str.endswith(sufixo)
    rows = df[mask]
    return rows.iloc[0]["valor"] if not rows.empty else None


def parsear(indic_path: Path, data_ref: date) -> pd.DataFrame:
    rows = []
    with open(indic_path, encoding="latin-1") as f:
        for line in f:
            if len(line) < 47 or line[6:11] != "00101":
                continue
            rows.append(
                {
                    "data": line[11:19].strip(),
                    "tipo": line[19:21].strip(),
                    "nome": line[21:46].strip(),
                    "valor": _decode_valor(line[46:].strip()),
                }
            )

    df = pd.DataFrame(rows)
    data_d = df["data"].max()
    df = df[df["data"] == data_d].copy()

    resultados = []
    usd_spot: float | None = None

    for moeda, inst in INSTRUMENTOS.items():
        valor = _buscar_instrumento(df, inst.tipo, inst.nome_sufixo)

        if moeda == "USD" and valor is not None:
            usd_spot = valor

        cotacao: float | None = None
        if valor is not None:
            if inst.metodo == "direto":
                cotacao = valor
            elif inst.metodo == "paridade_multiplicada" and usd_spot:
                cotacao = usd_spot * valor
            elif inst.metodo == "paridade_dividida" and usd_spot and valor != 0:
                cotacao = usd_spot / valor

        resultados.append(
            {
                "moeda_iso": moeda,
                "cotacao_b3": cotacao,
                "instrumento_b3": inst.nome_sufixo,
                "metodo_calculo": inst.metodo,
            }
        )

    return pd.DataFrame(resultados)
