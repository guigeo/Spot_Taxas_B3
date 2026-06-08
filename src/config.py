from dataclasses import dataclass
from typing import Literal

Method = Literal["direto", "paridade_multiplicada", "paridade_dividida"]


@dataclass(frozen=True)
class Instrumento:
    tipo: str
    nome_sufixo: str
    metodo: Method


INSTRUMENTOS: dict[str, Instrumento] = {
    "USD": Instrumento("RT", "DOL-D1", "direto"),
    "EUR": Instrumento("RT", "REUR-D1", "direto"),
    "JPY": Instrumento("TX", "JPY", "direto"),
    "AUD": Instrumento("RT", "AUD-T1", "direto"),
    "DKK": Instrumento("RT", "DKK-T1", "direto"),
    "SEK": Instrumento("RT", "RSEK-D1", "direto"),
    "CHF": Instrumento("RT", "RCHF-D1", "direto"),
    "ZAR": Instrumento("RT", "RZAR-D1", "direto"),
    "CLP": Instrumento("RT", "RCLP-D1", "direto"),
    "TRY": Instrumento("RT", "RTRY-D1", "direto"),
    "NOK": Instrumento("RT", "RNOK-D1", "direto"),
    "MXN": Instrumento("RT", "RMXN-D1", "direto"),
    "CNH": Instrumento("RT", "RCNH-D1", "direto"),
    "RUB": Instrumento("RT", "RRUB-D1", "direto"),
    "CAD": Instrumento("RT", "RCAD-D1", "direto"),
    "ARS": Instrumento("RT", "RARS-D1", "direto"),
    "GBP": Instrumento("RT", "GBP-PF", "paridade_multiplicada"),
    "NZD": Instrumento("RT", "NZD-PF", "paridade_multiplicada"),
    "CNY": Instrumento("RT", "CNY-PF", "paridade_dividida"),
    "AED": Instrumento("RT", "AED-T1", "direto"),
    "BOB": Instrumento("RT", "BOB-T1", "direto"),
    "COP": Instrumento("RT", "COP-T1", "direto"),
    "CRC": Instrumento("RT", "CRC-T1", "direto"),
    "CZK": Instrumento("RT", "CZK-T1", "direto"),
    "HKD": Instrumento("RT", "HKD-T1", "direto"),
    "HUF": Instrumento("RT", "HUF-T1", "direto"),
    "IDR": Instrumento("RT", "IDR-T1", "direto"),
    "INR": Instrumento("RT", "INR-T1", "direto"),
    "KWD": Instrumento("RT", "KWD-T1", "direto"),
    "MYR": Instrumento("RT", "MYR-T1", "direto"),
    "PEN": Instrumento("RT", "PEN-T1", "direto"),
    "PHP": Instrumento("RT", "PHP-T1", "direto"),
    "PLN": Instrumento("RT", "PLN-T1", "direto"),
    "PYG": Instrumento("RT", "PYG-T1", "direto"),
    "QAR": Instrumento("RT", "QAR-T1", "direto"),
    "RON": Instrumento("RT", "RON-T1", "direto"),
    "SAR": Instrumento("RT", "SAR-T1", "direto"),
    "SGD": Instrumento("RT", "SGD-T1", "direto"),
    "THB": Instrumento("RT", "THB-T1", "direto"),
    "TWD": Instrumento("RT", "TWD-T1", "direto"),
    "UYU": Instrumento("RT", "UYU-T1", "direto"),
    "VND": Instrumento("RT", "VND-T1", "direto"),
}

# Schemas de DataFrame (documentação — não validação em runtime)
# df_b3 colunas:   moeda_iso, cotacao_b3, instrumento_b3, metodo_calculo
# df_ptax colunas: moeda_iso (codISO), ptax_compra, ptax_venda
# df_final colunas: data_referencia, moeda_iso, cotacao_b3, ptax_compra,
#                   ptax_venda, spread_b3_ptax, instrumento_b3, metodo_calculo
