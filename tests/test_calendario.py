from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.calendario import resolver_data_util


def _mock_response(feriados: list[str]) -> MagicMock:
    resposta = MagicMock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = [
        {"date": data_str, "name": "Feriado", "type": "national"} for data_str in feriados
    ]
    return resposta


@patch("src.calendario.requests.Session")
def test_dia_util_retorna_a_propria_data(mock_session: MagicMock) -> None:
    mock_session.return_value.__enter__.return_value.get.return_value = _mock_response(
        []
    )

    resultado = resolver_data_util(date(2026, 6, 3))

    assert resultado == date(2026, 6, 3)


@patch("src.calendario.requests.Session")
def test_sabado_recua_para_sexta(mock_session: MagicMock) -> None:
    mock_session.return_value.__enter__.return_value.get.return_value = _mock_response(
        []
    )

    resultado = resolver_data_util(date(2026, 6, 6))

    assert resultado == date(2026, 6, 5)
    assert resultado.weekday() == 4


@patch("src.calendario.requests.Session")
def test_domingo_recua_para_sexta(mock_session: MagicMock) -> None:
    mock_session.return_value.__enter__.return_value.get.return_value = _mock_response(
        []
    )

    resultado = resolver_data_util(date(2026, 6, 7))

    assert resultado == date(2026, 6, 5)


@patch("src.calendario.requests.Session")
def test_feriado_recua_para_dia_util_anterior(mock_session: MagicMock) -> None:
    mock_session.return_value.__enter__.return_value.get.return_value = _mock_response(
        ["2026-06-03"]
    )

    resultado = resolver_data_util(date(2026, 6, 3))

    assert resultado == date(2026, 6, 2)


@patch("src.calendario.requests.Session")
def test_feriado_em_segunda_recua_para_sexta_anterior(mock_session: MagicMock) -> None:
    mock_session.return_value.__enter__.return_value.get.return_value = _mock_response(
        ["2026-04-20"]
    )

    resultado = resolver_data_util(date(2026, 4, 20))

    assert resultado == date(2026, 4, 17)


def test_data_futura_levanta_erro() -> None:
    futuro = date(2099, 1, 1)

    with pytest.raises(ValueError):
        resolver_data_util(futuro)
