import pandas as pd
import pytest

from src.calculator import calcular


def _df_b3(registros: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(registros)


def _df_ptax(registros: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(registros)


def test_spread_calculado_corretamente() -> None:
    df_b3 = _df_b3(
        [
            {
                "moeda_iso": "USD",
                "cotacao_b3": 5.0099,
                "instrumento_b3": "DOL-D1",
                "metodo_calculo": "direto",
            }
        ]
    )
    df_ptax = _df_ptax(
        [{"moeda_iso": "USD", "ptax_compra": 5.0049, "ptax_venda": 5.0050}]
    )

    df = calcular(df_b3, df_ptax)

    assert df.iloc[0]["spread_b3_ptax"] == pytest.approx(0.0979, abs=1e-4)


def test_spread_nulo_quando_ptax_ausente() -> None:
    df_b3 = _df_b3(
        [
            {
                "moeda_iso": "RUB",
                "cotacao_b3": 6.5,
                "instrumento_b3": "RRUB-D1",
                "metodo_calculo": "direto",
            }
        ]
    )
    df_ptax = _df_ptax([])
    if df_ptax.empty:
        df_ptax = pd.DataFrame(columns=["moeda_iso", "ptax_compra", "ptax_venda"])

    df = calcular(df_b3, df_ptax)

    assert pd.isna(df.iloc[0]["ptax_venda"])
    assert df.iloc[0]["spread_b3_ptax"] is None


def test_spread_nulo_quando_cotacao_b3_ausente() -> None:
    df_b3 = _df_b3(
        [
            {
                "moeda_iso": "EUR",
                "cotacao_b3": None,
                "instrumento_b3": "REUR-D1",
                "metodo_calculo": "direto",
            }
        ]
    )
    df_ptax = _df_ptax([{"moeda_iso": "EUR", "ptax_compra": 5.4, "ptax_venda": 5.41}])

    df = calcular(df_b3, df_ptax)

    assert df.iloc[0]["spread_b3_ptax"] is None


def test_join_left_mantem_todas_moedas_b3() -> None:
    df_b3 = _df_b3(
        [
            {
                "moeda_iso": "USD",
                "cotacao_b3": 5.0,
                "instrumento_b3": "DOL-D1",
                "metodo_calculo": "direto",
            },
            {
                "moeda_iso": "EUR",
                "cotacao_b3": 5.4,
                "instrumento_b3": "REUR-D1",
                "metodo_calculo": "direto",
            },
        ]
    )
    df_ptax = _df_ptax([{"moeda_iso": "USD", "ptax_compra": 5.0, "ptax_venda": 5.0}])

    df = calcular(df_b3, df_ptax)

    assert len(df) == 2
    assert set(df["moeda_iso"]) == {"USD", "EUR"}
