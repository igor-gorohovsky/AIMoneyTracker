from decimal import Decimal
from types import CoroutineType
from typing import Callable

import httpx
import pytest
from assertpy import assert_that

from currencies import CURRENCIES
from db.manager import DBManager
from worker.rates.dtos import Rates
from worker.rates.interactor import RatesInteractor
from worker.rates.requesters import ExchangeRatesRequester


@pytest.fixture
def base_currency(create_currency: Callable) -> Callable:
    async def get_base_currency() -> CoroutineType:
        currency_info = CURRENCIES[RatesInteractor.BASE_CURRENCY]
        return await create_currency(
            currency_info["name"],
            RatesInteractor.BASE_CURRENCY,
            currency_info["symbol"],
        )

    return get_base_currency


@pytest.fixture
def mock_rates_response() -> Callable:
    def _mock_response(base_currency: str = "USD") -> dict:
        return {
            "success": True,
            "timestamp": 1619622625,
            "base": base_currency,
            "date": "2023-10-25",
            "rates": {
                "EUR": 0.85,
                "GBP": 0.72,
                "JPY": 110.25,
                "RUB": 75.5,
            },
        }

    return _mock_response


@pytest.mark.asyncio
async def test_fetch_currency_rates(
    base_currency: Callable,
    mock_rates_response: Callable,
    httpx_client: Callable,
    db_manager: DBManager,
) -> None:
    # Arrange
    currency = await base_currency()
    mock_data = mock_rates_response(currency.iso_code)
    expected_result = Rates(
        source_iso_code=mock_data["base"],
        timestamp=mock_data["timestamp"],
        data=mock_data["rates"],
    )

    mock_response = httpx.Response(
        200,
        json=mock_data,
    )
    client = httpx_client(mock_response)

    requester = ExchangeRatesRequester(client)
    sut = RatesInteractor(db_manager, requester)

    # Act
    rates = await sut.fetch_currency_rates(currency)

    # Assert
    assert_that(rates).is_equal_to(expected_result)


@pytest.mark.asyncio
async def test_update_currency_rates(
    db_manager: DBManager,
    mock_rates_response: Callable,
    httpx_client: Callable,
    get_rate: Callable,
    get_currency: Callable,
) -> None:
    # Arrange
    mock_data = mock_rates_response(RatesInteractor.BASE_CURRENCY)

    mock_response = httpx.Response(
        200,
        json=mock_data,
    )
    client = httpx_client(mock_response)

    requester = ExchangeRatesRequester(client)
    sut = RatesInteractor(db_manager, requester)

    # Act
    await sut.update_currency_rates()

    # Assert
    base_currency = await get_currency(RatesInteractor.BASE_CURRENCY)
    eur_currency = await get_currency("EUR")
    gbp_currency = await get_currency("GBP")
    jpy_currency = await get_currency("JPY")
    rub_currency = await get_currency("RUB")

    assert_that(base_currency).is_not_none()
    assert_that(eur_currency).is_not_none()
    assert_that(gbp_currency).is_not_none()
    assert_that(rub_currency).is_not_none()
    assert_that(jpy_currency).is_not_none()

    to_eur_rate = await get_rate(
        base_currency.currency_id,
        eur_currency.currency_id,
    )

    to_gbp_rate = await get_rate(
        base_currency.currency_id,
        gbp_currency.currency_id,
    )

    to_jpy_rate = await get_rate(
        base_currency.currency_id,
        jpy_currency.currency_id,
    )

    to_rub_rate = await get_rate(
        base_currency.currency_id,
        rub_currency.currency_id,
    )

    assert_that(to_eur_rate).is_not_none()
    assert_that(to_eur_rate.rate).is_equal_to(Decimal("0.85"))

    assert_that(to_gbp_rate).is_not_none()
    assert_that(to_gbp_rate.rate).is_equal_to(Decimal("0.72"))

    assert_that(to_jpy_rate).is_not_none()
    assert_that(to_jpy_rate.rate).is_equal_to(Decimal("110.25"))

    assert_that(to_rub_rate).is_not_none()
    assert_that(to_rub_rate.rate).is_equal_to(Decimal("75.5"))


@pytest.mark.asyncio
async def test_update_currency_rates_with_unsupported_currency(
    db_manager: DBManager,
    mock_rates_response: Callable,
    httpx_client: Callable,
    get_rate: Callable,
    get_currency: Callable,
) -> None:
    # Arrange
    mock_data = mock_rates_response(RatesInteractor.BASE_CURRENCY)
    mock_data["rates"]["XYZ"] = 1.23

    mock_response = httpx.Response(
        200,
        json=mock_data,
    )
    client = httpx_client(mock_response)

    requester = ExchangeRatesRequester(client)
    sut = RatesInteractor(db_manager, requester)

    # Act
    await sut.update_currency_rates()

    # Assert
    xyz_currency = await get_currency("XYZ")
    base_currency = await get_currency(RatesInteractor.BASE_CURRENCY)
    eur_currency = await get_currency("EUR")
    gbp_currency = await get_currency("GBP")
    jpy_currency = await get_currency("JPY")
    rub_currency = await get_currency("RUB")

    assert_that(xyz_currency).is_none()
    assert_that(base_currency).is_not_none()
    assert_that(eur_currency).is_not_none()
    assert_that(gbp_currency).is_not_none()
    assert_that(rub_currency).is_not_none()
    assert_that(jpy_currency).is_not_none()

    to_eur_rate = await get_rate(
        base_currency.currency_id,
        eur_currency.currency_id,
    )

    to_gbp_rate = await get_rate(
        base_currency.currency_id,
        gbp_currency.currency_id,
    )

    to_jpy_rate = await get_rate(
        base_currency.currency_id,
        jpy_currency.currency_id,
    )

    to_rub_rate = await get_rate(
        base_currency.currency_id,
        rub_currency.currency_id,
    )

    assert_that(to_eur_rate).is_not_none()
    assert_that(to_eur_rate.rate).is_equal_to(Decimal("0.85"))

    assert_that(to_gbp_rate).is_not_none()
    assert_that(to_gbp_rate.rate).is_equal_to(Decimal("0.72"))

    assert_that(to_jpy_rate).is_not_none()
    assert_that(to_jpy_rate.rate).is_equal_to(Decimal("110.25"))

    assert_that(to_rub_rate).is_not_none()
    assert_that(to_rub_rate.rate).is_equal_to(Decimal("75.5"))
