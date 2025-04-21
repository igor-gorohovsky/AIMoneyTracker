from decimal import Decimal

from loguru import logger

from currencies import CURRENCIES
from db.manager import DBManager
from db.models import Currency
from services.rates.dtos import Rates
from services.rates.requesters import RatesRequester


class CurrenciesRatesService:
    BASE_CURRENCY = "EUR"

    def __init__(
        self,
        db_manager: DBManager,
        requester: RatesRequester,
    ) -> None:
        self._db_manager = db_manager
        self._requester = requester

    async def fetch_currency_rates(self, base_currency: Currency) -> Rates:
        return await self._requester.fetch(base_currency)

    async def update_currency_rates(self) -> None:
        async with self._db_manager.transaction():
            base_currency_info = CURRENCIES[self.BASE_CURRENCY]
            base_currency = await self._db_manager.get_or_create_currency(
                self.BASE_CURRENCY,
                base_currency_info["name"],
                base_currency_info["symbol"],
            )

            rates = await self.fetch_currency_rates(base_currency)

            for iso_code, rate in rates.data.items():
                currency_info = CURRENCIES.get(iso_code)

                if not currency_info:
                    logger.warning(
                        "Got a rate for unsupported "
                        f"{iso_code} currency, skipping it...",
                    )
                    continue

                target_currency = (
                    await self._db_manager.get_or_create_currency(
                        iso_code,
                        currency_info["name"],
                        currency_info["symbol"],
                    )
                )

                _ = await self._db_manager.update_currency_rate(
                    base_currency.currency_id,
                    target_currency.currency_id,
                    Decimal(str(rate)),
                )
