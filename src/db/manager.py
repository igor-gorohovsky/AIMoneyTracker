from contextlib import asynccontextmanager
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncEngine

from db.models import Account, Category, Currency, UserAccount
from db.queries import AsyncQuerier
from misc import DEFAULT_CATEGORIES, CategoryType


# TODO: implement mechanism to use functions outside transaction
class DBManager:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._querier = None
        self._in_transaction = False

    @asynccontextmanager
    async def transaction(self):
        async with self._engine.begin() as conn:
            self._querier = AsyncQuerier(conn)
            self._in_transaction = True
            try:
                yield
            except Exception:
                await conn.rollback()
                raise
            finally:
                self._querier = None
                self._in_transaction = False

    async def create_category(
        self,
        user_id: int,
        name: str,
        category_type: CategoryType,
    ) -> Category:
        category = await self._querier.create_category(
            user_id=user_id,
            name=name,
            type=category_type,
        )
        assert category is not None
        return category

    async def create_currency(
        self,
        name: str,
        iso_code: str,
        symbol: str,
    ) -> Currency:
        currency = await self._querier.create_currency(
            name=name,
            iso_code=iso_code,
            symbol=symbol,
        )
        assert currency is not None
        return currency

    async def create_user(
        self,
        user_tg_id: int,
        currency_id: int,
    ) -> UserAccount:
        user = await self._querier.create_user(
            user_tg_id=user_tg_id,
            currency_id=currency_id,
        )
        assert user is not None
        return user

    async def create_account(
        self,
        user_id: int,
        name: str,
        balance: Decimal,
        currency_id: int,
    ) -> Account:
        account = await self._querier.create_account(
            user_id=user_id,
            name=name,
            balance=balance,
            currency_id=currency_id,
        )
        assert account is not None
        return account

    async def get_currency(self, iso_code: str) -> Currency:
        currency = await self._querier.get_currency(iso_code=iso_code)
        assert currency is not None
        return currency

    async def create_default_categories(self, user_id: int) -> list[Category]:
        return [
            await self.create_category(
                user_id,
                category["name"],
                category["category_type"],
            )
            for category in DEFAULT_CATEGORIES
        ]

    async def create_default_account(
        self,
        user_id: int,
        currency_id: int,
    ) -> Account:
        return await self.create_account(user_id, "Default", 0, currency_id)

    async def _get_querier(self) -> AsyncQuerier:
        if self._querier is not None:
            return self._querier

        conn = await self._engine.connect()
        return AsyncQuerier(conn)
