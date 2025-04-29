from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncEngine

from db.models import (
    Account,
    Category,
    Currency,
    Rate,
    Transaction,
    UserAccount,
)
from db.queries import AsyncQuerier, CreateTransactionParams
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

    async def update_category(
        self,
        category_id: int,
        new_name: str,
    ) -> Category:
        category = await self._querier.update_category(
            category_id=category_id,
            name=new_name,
        )
        assert category is not None
        return category

    async def get_category(
        self,
        user_id: int,
        *,
        category_id: int | None = None,
        name: str | None = None,
    ) -> Category | None:
        if category_id is None and name is None:
            msg = "At least one argument must be passed"
            raise ValueError(msg)

        if category_id:
            return await self._querier.get_category_by_id(
                category_id=category_id,
                user_id=user_id,
            )

        if name:
            return await self._querier.get_category_by_name(
                name=name,
                user_id=user_id,
            )

        return None

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

    async def get_currency(self, iso_code: str) -> Currency | None:
        return await self._querier.get_currency(iso_code=iso_code)

    async def get_user(self, user_tg_id: int) -> UserAccount:
        user = await self._querier.get_user(user_tg_id=user_tg_id)
        assert user is not None
        return user

    async def get_or_create_currency(
        self,
        iso_code: str,
        name: str,
        symbol: str,
    ) -> Currency:
        currency = await self.get_currency(iso_code)

        if not currency:
            currency = await self.create_currency(
                name,
                iso_code,
                symbol,
            )

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
        return await self.create_account(
            user_id,
            "Default",
            Decimal(0),
            currency_id,
        )

    async def _get_querier(self) -> AsyncQuerier:
        if self._querier is not None:
            return self._querier

        conn = await self._engine.connect()
        return AsyncQuerier(conn)

    async def update_currency_rate(
        self,
        from_currency_id: int,
        to_currency_id: int,
        rate_value: Decimal,
    ) -> Rate:
        existing_rate = await self._querier.get_rate(
            from_currency=from_currency_id,
            to_currency=to_currency_id,
        )
        if existing_rate:
            rate = await self._querier.update_rate(
                from_currency=from_currency_id,
                to_currency=to_currency_id,
                rate=rate_value,
            )
        else:
            rate = await self._querier.create_rate(
                from_currency=from_currency_id,
                to_currency=to_currency_id,
                rate=rate_value,
            )

        assert rate is not None
        return rate

    async def get_account_by_name(
        self,
        user_id: int,
        name: str,
    ) -> Account | None:
        return await self._querier.get_account_by_name(
            user_id=user_id,
            name=name,
        )

    async def update_account_balance(
        self,
        account_id: int,
        new_balance: Decimal,
    ) -> Account:
        account = await self._querier.update_account_balance(
            account_id=account_id,
            balance=new_balance,
        )
        assert account is not None
        return account

    async def create_transaction(
        self,
        user_id: int,
        account_id: int,
        category_id: int,
        withdrawal_amount: Decimal,
        expense_amount: Decimal,
        note: str | None = None,
        state: str = "completed",
        date: datetime | None = None,
    ) -> Transaction:
        if date is None:
            date = datetime.now(tz=UTC)

        transaction = await self._querier.create_transaction(
            CreateTransactionParams(
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                withdrawal_amount=withdrawal_amount,
                expense_amount=expense_amount,
                note=note,
                state=state,
                date=date,
            ),
        )
        assert transaction is not None
        return transaction
