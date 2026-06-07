import time
from datetime import date, datetime, timedelta

import requests

FERIADOS_URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"


def _buscar_feriados(ano: int) -> set[date]:
    for tentativa in range(3):
        try:
            with requests.Session() as s:
                r = s.get(FERIADOS_URL.format(ano=ano), timeout=(5, 30))
                r.raise_for_status()
            break
        except requests.RequestException:
            if tentativa == 2:
                raise
            time.sleep(2**tentativa)

    registros = r.json()
    feriados: set[date] = set()
    for registro in registros:
        data_str = registro.get("date")
        if not data_str:
            continue
        feriados.add(datetime.strptime(data_str, "%Y-%m-%d").date())
    return feriados


def resolver_data_util(referencia: date) -> date:
    if referencia > date.today():
        raise ValueError(f"Data futura não suportada: {referencia.isoformat()}")

    feriados = _buscar_feriados(referencia.year)
    if referencia.year != (referencia - timedelta(days=1)).year:
        feriados |= _buscar_feriados(referencia.year - 1)

    candidata = referencia
    while candidata.weekday() >= 5 or candidata in feriados:
        candidata -= timedelta(days=1)
        if candidata.year != referencia.year and candidata.year not in {
            referencia.year,
            referencia.year - 1,
        }:
            feriados |= _buscar_feriados(candidata.year)

    return candidata
