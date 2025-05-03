from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum, auto

from loguru import logger

from currencies import CURRENCIES
from db.manager import DBManager
from db.models import Category, Currency, Transaction
from dtos import Rates
from exceptions import (
    AccountNotFoundError,
    CategoryDuplicateError,
    NotExistingCategoryError,
    TransactionNotFoundError,
)
from misc import CategoryType
from requesters import RatesRequester


class TransactionState(StrEnum):
    VISIBLE = auto()


class Service:
    BASE_CURRENCY = "EUR"

    def __init__(
        self,
        db_manager: DBManager,
        requester: RatesRequester,
    ) -> None:
        self._db_manager = db_manager
        self._rates_requester = requester

    async def register_user(self) -> int:
        async with self._db_manager.transaction():
            currency = await self._db_manager.get_currency("USD")
            user = await self._db_manager.create_user(
                currency_id=currency.currency_id,
            )
            _ = await self._db_manager.create_default_categories(user.user_id)
            _ = await self._db_manager.create_default_account(
                user.user_id,
                user.currency_id,
            )
            return user.user_id

    async def create_category(
        self,
        user_id: int,
        name: str,
        category_type: CategoryType,
    ) -> Category:
        async with self._db_manager.transaction():
            category = await self._db_manager.get_category(
                name=name,
                user_id=user_id,
            )
            if category is not None:
                raise CategoryDuplicateError

            return await self._db_manager.create_category(
                user_id,
                name,
                category_type,
            )

    async def edit_category(
        self,
        user_id: int,
        category_id: int,
        new_name: str,
    ) -> Category:
        async with self._db_manager.transaction():
            category = await self._db_manager.get_category(
                category_id=category_id,
                user_id=user_id,
            )
            if category is None:
                raise NotExistingCategoryError

            return await self._db_manager.update_category(
                category_id,
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

    async def create_transaction(
        self,
        user_id: int,
        account_id: int,
        category_id: int,
        withdrawal_amount: Decimal,
        expense_amount: Decimal,
        note: str | None = None,
        state: str = TransactionState.VISIBLE,
        date: datetime | None = None,
    ) -> Transaction:
        async with self._db_manager.transaction():
            account = await self._db_manager.get_account_by_id(account_id)
            if account is None:
                msg = f"Account with ID {account_id} not found"
                raise AccountNotFoundError(msg)

            category = await self._db_manager.get_category(
                user_id=user_id,
                category_id=category_id,
            )
            if category is None:
                msg = f"Category with ID {category_id} not found"
                raise NotExistingCategoryError(msg)

            transaction = await self._db_manager.create_transaction(
                user_id,
                account_id,
                category_id,
                withdrawal_amount,
                expense_amount,
                note,
                state,
                date,
            )

            # expense will be with - sign, top up with + sign
            new_balance = account.balance + withdrawal_amount

            _ = await self._db_manager.update_account_balance(
                account_id,
                new_balance,
            )

            return transaction

    async def edit_transaction(
        self,
        user_id: int,
        transaction_id: int,
        account_id: int,
        category_id: int,
        withdrawal_amount: Decimal,
        expense_amount: Decimal,
        note: str | None = None,
        date: datetime | None = None,
    ) -> Transaction:
        async with self._db_manager.transaction():
            original_transaction = (
                await self._db_manager.get_transaction_by_id(
                    transaction_id=transaction_id,
                    user_id=user_id,
                )
            )

            if not original_transaction:
                msg = f"Transaction with ID {transaction_id} not found"
                raise TransactionNotFoundError(msg)

            account = await self._db_manager.get_account_by_id(account_id)
            if account is None:
                msg = f"Account with ID {account_id} not found"
                raise AccountNotFoundError(msg)

            category = await self._db_manager.get_category(
                user_id=user_id,
                category_id=category_id,
            )
            if category is None:
                msg = f"Category with ID {category_id} not found"
                raise NotExistingCategoryError(msg)

            reversal_transaction = await self._db_manager.create_transaction(
                user_id=user_id,
                account_id=original_transaction.account_id,
                category_id=original_transaction.category_id,
                withdrawal_amount=-original_transaction.withdrawal_amount,
                expense_amount=-original_transaction.expense_amount,
                note=None,
                state=TransactionState.VISIBLE,
                date=date or datetime.now(UTC),
                original_transaction_id=original_transaction.transaction_id,
            )

            original_account = await self._db_manager.get_account_by_id(
                account_id=original_transaction.account_id,
            )

            if original_account:
                new_original_balance = (
                    original_account.balance
                    + reversal_transaction.withdrawal_amount
                )
                original_account = (
                    await self._db_manager.update_account_balance(
                        original_account.account_id,
                        new_original_balance,
                    )
                )

            # Get account again to get the updated balance
            account = await self._db_manager.get_account_by_id(account_id)
            new_transaction = await self._db_manager.create_transaction(
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                withdrawal_amount=withdrawal_amount,
                expense_amount=expense_amount,
                note=note or original_transaction.note,
                state=TransactionState.VISIBLE,
                date=date or datetime.now(UTC),
                original_transaction_id=original_transaction.transaction_id,
            )

            new_account_balance = account.balance + withdrawal_amount
            account = await self._db_manager.update_account_balance(
                account_id,
                new_account_balance,
            )

            return new_transaction
