import sys
from datetime import date
from pathlib import Path

import pandas as pd

from src.calculator import calcular
from src.calendario import resolver_data_util
from src.downloader import baixar_e_extrair
from src.exporter import gerar_excel
from src.parser import parsear
from src.ptax import buscar as buscar_ptax

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
OUT_DIR = DATA_DIR / "output"

LIMIAR_DIVERGENCIA = 20.0


def main() -> None:
    data_ref = resolver_data_util(date.today())
    print(f"[INFO] Data de referência: {data_ref.isoformat()}")

    print("[INFO] Baixando arquivo B3...")
    indic_path = baixar_e_extrair(data_ref, RAW_DIR)

    print("[INFO] Parseando arquivo...")
    df_b3 = parsear(indic_path, data_ref)

    print("[INFO] Buscando PTAX BACEN...")
    df_ptax = buscar_ptax(data_ref)

    print("[INFO] Calculando spread...")
    df_final = calcular(df_b3, df_ptax)

    sem_b3 = df_final[df_final["cotacao_b3"].isna()]["moeda_iso"].tolist()
    sem_ptax = df_final[df_final["ptax_venda"].isna()]["moeda_iso"].tolist()
    if sem_b3:
        print(f"[WARN] Sem cotação B3: {sem_b3}")
    if sem_ptax:
        print(f"[WARN] Sem PTAX: {sem_ptax}")

    spreads = pd.to_numeric(df_final["spread_b3_ptax"], errors="coerce")
    divergentes = df_final[spreads.abs() > LIMIAR_DIVERGENCIA]
    for _, row in divergentes.iterrows():
        print(
            f"[WARN] Divergência > {LIMIAR_DIVERGENCIA}% para "
            f"{row['moeda_iso']}: spread = {row['spread_b3_ptax']}%"
        )

    print("[INFO] Gerando planilha...")
    caminho = gerar_excel(df_final, data_ref, OUT_DIR)
    print(f"[INFO] Planilha gerada: {caminho}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
