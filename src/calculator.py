import pandas as pd


def calcular(df_b3: pd.DataFrame, df_ptax: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_b3, df_ptax, on="moeda_iso", how="left")

    def spread(row: pd.Series) -> float | None:
        b3, ptax = row["cotacao_b3"], row["ptax_venda"]
        if b3 is None or ptax is None or pd.isna(b3) or pd.isna(ptax) or ptax == 0:
            return None
        return round((b3 / ptax - 1) * 100, 4)

    df["spread_b3_ptax"] = df.apply(spread, axis=1)
    return df
