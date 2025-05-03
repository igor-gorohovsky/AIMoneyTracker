import datetime
from decimal import Decimal
from typing import Callable
from unittest.mock import create_autospec

import pytest

from db.manager import DBManager
from db.models import Account, Category, Transaction, UserAccount
from exceptions import AccountNotFoundError, NotExistingCategoryError
from misc import CategoryType
from requesters import RatesRequester
from service import Service


@pytest.fixture
async def user(
    create_user: Callable,
    create_currency: Callable,
) -> UserAccount:
    currency = await create_currency("US Dollar", "USD", "$")
    return await create_user(currency.currency_id)


@pytest.fixture
async def account(
    user: UserAccount,
    db_manager: DBManager,
) -> Account:
    async with db_manager.transaction():
        return await db_manager.create_account(
            user_id=user.user_id,
            name="Test Account",
            balance=Decimal("1000.00"),
            currency_id=user.currency_id,
        )


@pytest.fixture
async def expense_category(
    create_category: Callable,
    user: UserAccount,
) -> Category:
    return await create_category(
        user.user_id,
        "Test Expense",
        CategoryType.EXPENSE,
    )


@pytest.fixture
async def income_category(
    create_category: Callable,
    user: UserAccount,
) -> Category:
    return await create_category(
        user.user_id,
        "Test Income",
        CategoryType.INCOME,
    )


@pytest.fixture
def create_transaction(db_manager: DBManager) -> Callable:
    async def wrapper(
        user_id: int,
        account_id: int,
        category_id: int,
        withdrawal_amount: Decimal,
        expense_amount: Decimal,
        note: str | None = None,
    ) -> Transaction:
        return await db_manager.create_transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            withdrawal_amount=withdrawal_amount,
            expense_amount=expense_amount,
            note=note,
        )

    return wrapper


@pytest.fixture
def get_account(get_account_by_id: Callable) -> Callable:
    async def wrapper(account_id: int) -> Account:
        return await get_account_by_id(account_id)

    return wrapper


@pytest.fixture
def sut(db_manager: DBManager) -> Service:
    mock_requester = create_autospec(RatesRequester)
    return Service(db_manager, mock_requester)


@pytest.mark.asyncio
async def test_create_expense_transaction(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    get_account: Callable,
):
    # Arrange
    withdrawal_amount = Decimal("-100.00")
    expense_amount = Decimal("-100.00")
    note = "Test expense transaction"

    # Act
    transaction = await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=expense_category.category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note=note,
    )

    # Assert
    assert transaction is not None
    assert transaction.withdrawal_amount == withdrawal_amount
    assert transaction.expense_amount == expense_amount
    assert transaction.note == note

    updated_account = await get_account(account.account_id)
    assert updated_account.balance == account.balance + withdrawal_amount


@pytest.mark.asyncio
async def test_create_income_transaction(
    sut: Service,
    user: UserAccount,
    account: Account,
    income_category: Category,
    get_account: Callable,
):
    # Arrange
    withdrawal_amount = Decimal("50.00")
    expense_amount = Decimal("50.00")
    note = "Test income transaction"

    # Act
    transaction = await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=income_category.category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note=note,
    )

    # Assert
    assert transaction is not None
    assert transaction.withdrawal_amount == withdrawal_amount
    assert transaction.expense_amount == expense_amount
    assert transaction.note == note

    updated_account = await get_account(account.account_id)
    assert (
        updated_account.balance == account.balance + withdrawal_amount
    )


@pytest.mark.asyncio
async def test_create_transaction_with_custom_date(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
):
    # Arrange
    withdrawal_amount = Decimal("-75.00")
    expense_amount = Decimal("-75.00")
    custom_date = datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)

    # Act
    transaction = await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=expense_category.category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        date=custom_date,
    )

    # Assert
    assert transaction is not None
    assert transaction.date == custom_date


@pytest.mark.asyncio
async def test_create_transaction_account_not_found(
    sut: Service,
    user: UserAccount,
    expense_category: Category,
):
    # Arrange
    non_existent_account_id = 9999
    withdrawal_amount = Decimal("-50.00")
    expense_amount = Decimal("-50.00")

    # Act & Assert
    with pytest.raises(AccountNotFoundError) as exc_info:
        await sut.create_transaction(
            user_id=user.user_id,
            account_id=non_existent_account_id,
            category_id=expense_category.category_id,
            withdrawal_amount=withdrawal_amount,
            expense_amount=expense_amount,
        )

    assert f"Account with ID {non_existent_account_id} not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_transaction_category_not_found(
    sut: Service,
    user: UserAccount,
    account: Account,
):
    # Arrange
    non_existent_category_id = 9999
    withdrawal_amount = Decimal("-50.00")
    expense_amount = Decimal("-50.00")

    # Act & Assert
    with pytest.raises(NotExistingCategoryError) as exc_info:
        await sut.create_transaction(
            user_id=user.user_id,
            account_id=account.account_id,
            category_id=non_existent_category_id,
            withdrawal_amount=withdrawal_amount,
            expense_amount=expense_amount,
        )

    assert f"Category with ID {non_existent_category_id} not found" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_create_multiple_transactions(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    income_category: Category,
    get_account: Callable,
):
    # Arrange
    initial_balance = account.balance

    # First transaction - expense
    await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=expense_category.category_id,
        withdrawal_amount=Decimal("-200.00"),
        expense_amount=Decimal("-200.00"),
        note="First expense",
    )

    # Second transaction - income
    await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=income_category.category_id,
        withdrawal_amount=Decimal("150.00"),
        expense_amount=Decimal("150.00"),
        note="Income transaction",
    )

    # Third transaction - expense
    await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=expense_category.category_id,
        withdrawal_amount=Decimal("-75.00"),
        expense_amount=Decimal("-75.00"),
        note="Second expense",
    )

    # Assert final balance
    updated_account = await get_account(account.account_id)
    expected_balance = (
        initial_balance
        - Decimal("200.00")
        + Decimal("150.00")
        - Decimal("75.00")
    )
    assert updated_account.balance == expected_balance


@pytest.mark.asyncio
async def test_transaction_with_different_amounts(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    get_account: Callable,
):
    # Arrange
    withdrawal_amount = Decimal("-100.00")
    expense_amount = Decimal("-85.00")

    # Act
    transaction = await sut.create_transaction(
        user_id=user.user_id,
        account_id=account.account_id,
        category_id=expense_category.category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note="Transaction with currency conversion",
    )

    # Assert
    assert transaction is not None
    assert transaction.withdrawal_amount == withdrawal_amount
    assert transaction.expense_amount == expense_amount
    
    updated_account = await get_account(account.account_id)
    assert updated_account.balance == account.balance + withdrawal_amount
