from abc import ABC, abstractmethod
from typing import override

import httpx

from db.models import Currency
from env import CURRENCY_API_KEY, CURRENCY_URL
from worker.rates.dtos import Rates


class RatesRequester(ABC):
    @abstractmethod
    async def fetch(self, base_currency: Currency) -> Rates:
        pass


class ExchangeRatesRequester(RatesRequester):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient()

    @override
    async def fetch(self, base_currency: Currency) -> Rates:
        async with self._client:
            response = await self._client.get(
                CURRENCY_URL,
                params={
                    "access_key": CURRENCY_API_KEY,
                    "base": base_currency.iso_code,
                },
            )
            response.raise_for_status()
            data = response.json()

        return await self._format_response(data)

    # We are not handling success=False in response
    async def _format_response(self, response: dict) -> Rates:
        return Rates(
            source_iso_code=response["base"],
            timestamp=response["timestamp"],
            data=response["rates"],
        )
