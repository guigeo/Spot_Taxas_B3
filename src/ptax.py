import time
from datetime import date

import pandas as pd
import requests

from src.config import INSTRUMENTOS

PTAX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)"
)

TIPO_BOLETIM_FECHAMENTO = "Fechamento PTAX"


def _buscar_moeda(moeda: str, data_str: str) -> dict | None:
    params = {"@moeda": f"'{moeda}'", "@dataCotacao": f"'{data_str}'", "$format": "json"}

    for tentativa in range(3):
        try:
            with requests.Session() as s:
                r = s.get(PTAX_URL, params=params, timeout=(5, 30))
                r.raise_for_status()
            break
        except requests.RequestException:
            if tentativa == 2:
                raise
            time.sleep(2**tentativa)

    fechamentos = [
        registro
        for registro in r.json().get("value", [])
        if registro.get("tipoBoletim") == TIPO_BOLETIM_FECHAMENTO
    ]
    return fechamentos[-1] if fechamentos else None


def buscar(data_ref: date) -> pd.DataFrame:
    data_str = data_ref.strftime("%m-%d-%Y")

    linhas = []
    for moeda_iso in INSTRUMENTOS:
        registro = _buscar_moeda(moeda_iso, data_str)
        linhas.append(
            {
                "moeda_iso": moeda_iso,
                "ptax_compra": registro["cotacaoCompra"] if registro else None,
                "ptax_venda": registro["cotacaoVenda"] if registro else None,
            }
        )

    return pd.DataFrame(linhas, columns=["moeda_iso", "ptax_compra", "ptax_venda"])
