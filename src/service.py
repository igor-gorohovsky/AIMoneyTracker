from decimal import Decimal

from loguru import logger

from currencies import CURRENCIES
from db.manager import DBManager
from db.models import Category, Currency
from dtos import Rates
from exceptions import CategoryDuplicateError, NotExistingCategoryError
from misc import CategoryType
from requesters import RatesRequester


class Service:
    BASE_CURRENCY = "EUR"

    def __init__(
        self,
        db_manager: DBManager,
        requester: RatesRequester,
    ) -> None:
        self._db_manager = db_manager
        self._rates_requester = requester

    async def register_user(self, user_tg_id: int) -> None:
        async with self._db_manager.transaction():
            currency = await self._db_manager.get_currency("USD")
            user = await self._db_manager.create_user(
                user_tg_id=user_tg_id,
                currency_id=currency.currency_id,
            )
            _ = await self._db_manager.create_default_categories(user.user_id)
            _ = await self._db_manager.create_default_account(
                user.user_id,
                user.currency_id,
            )

    async def create_category(
        self,
        user_tg_id: int,
        name: str,
        category_type: CategoryType,
    ) -> Category:
        async with self._db_manager.transaction():
            user = await self._db_manager.get_user(user_tg_id)

            category = await self._db_manager.get_category(
                name=name,
                user_id=user.user_id,
            )
            if category is not None:
                raise CategoryDuplicateError

            return await self._db_manager.create_category(
                user.user_id,
                name,
                category_type,
            )

    async def edit_category(
        self,
        user_tg_id: int,
        old_name: str,
        new_name: str,
    ) -> Category:
        async with self._db_manager.transaction():
            user = await self._db_manager.get_user(user_tg_id)

            category = await self._db_manager.get_category(
                name=old_name,
                user_id=user.user_id,
            )
            if category is None:
                raise NotExistingCategoryError

            return await self._db_manager.update_category(
                category.category_id,
                new_name,
            )

    async def fetch_currency_rates(self, base_currency: Currency) -> Rates:
        return await self._rates_requester.fetch(base_currency)

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
