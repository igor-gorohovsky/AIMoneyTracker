from decimal import Decimal
from typing import Callable
from unittest.mock import create_autospec

import pytest
from assertpy import assert_that

from db.manager import DBManager
from db.models import Account, Currency, UserAccount
from exceptions import AccountDuplicateError
from requesters import RatesRequester
from service import Service


@pytest.fixture
def sut(db_manager: DBManager) -> Service:
    mock_requester = create_autospec(RatesRequester)
    return Service(db_manager, mock_requester)


@pytest.fixture
async def currency(create_currency: Callable) -> Currency:
    return await create_currency("US Dollar", "USD", "$")


@pytest.fixture
async def user(create_user: Callable, currency: Currency) -> UserAccount:
    return await create_user(currency.currency_id)


@pytest.fixture
def get_account_by_name(db_manager: DBManager) -> Callable:
    async def wrapper(user_id: int, name: str) -> Account | None:
        async with db_manager.transaction():
            return await db_manager.get_account(user_id, name=name)

    return wrapper


@pytest.mark.asyncio
async def test_create_account_success(
    sut: Service,
    user: UserAccount,
    currency: Currency,
    get_account_by_id: Callable,
):
    # Arrange
    account_name = "Test Account"
    initial_balance = Decimal("500.00")

    # Act
    account = await sut.create_account(
        user_id=user.user_id,
        name=account_name,
        currency_id=currency.currency_id,
        initial_balance=initial_balance,
    )

    # Assert
    assert_that(account).is_not_none()
    assert_that(account.name).is_equal_to(account_name)
    assert_that(account.balance).is_equal_to(initial_balance)
    assert_that(account.currency_id).is_equal_to(currency.currency_id)
    assert_that(account.user_id).is_equal_to(user.user_id)

    # Verify the account was persisted
    stored_account = await get_account_by_id(account.account_id)
    assert_that(stored_account).is_not_none()
    assert_that(stored_account.name).is_equal_to(account_name)
    assert_that(stored_account.balance).is_equal_to(initial_balance)


@pytest.mark.asyncio
async def test_create_account_default_balance(
    sut: Service,
    user: UserAccount,
    currency: Currency,
):
    # Arrange
    account_name = "Zero Balance Account"

    # Act
    account = await sut.create_account(
        user_id=user.user_id,
        name=account_name,
        currency_id=currency.currency_id,
    )

    # Assert
    assert_that(account).is_not_none()
    assert_that(account.balance).is_equal_to(Decimal("0"))


@pytest.mark.asyncio
async def test_create_account_duplicate_name(
    sut: Service,
    user: UserAccount,
    currency: Currency,
):
    # Arrange
    account_name = "Duplicate Account"

    # Create the first account
    await sut.create_account(
        user_id=user.user_id,
        name=account_name,
        currency_id=currency.currency_id,
    )

    # Act & Assert
    with pytest.raises(AccountDuplicateError) as exc_info:
        await sut.create_account(
            user_id=user.user_id,
            name=account_name,
            currency_id=currency.currency_id,
        )

    assert_that(str(exc_info.value)).contains(account_name)
    assert_that(str(exc_info.value)).contains(str(user.user_id))


@pytest.mark.asyncio
async def test_create_multiple_accounts(
    sut: Service,
    user: UserAccount,
    currency: Currency,
    get_account_by_name: Callable,
):
    # Arrange
    account_names = ["Checking", "Savings", "Investment"]

    # Act
    accounts = []
    for name in account_names:
        account = await sut.create_account(
            user_id=user.user_id,
            name=name,
            currency_id=currency.currency_id,
            initial_balance=Decimal("100.00"),
        )
        accounts.append(account)

    # Assert
    for name, account in zip(account_names, accounts):
        stored_account = await get_account_by_name(user.user_id, name)
        assert_that(stored_account).is_not_none()
        assert_that(stored_account.account_id).is_equal_to(account.account_id)
        assert_that(stored_account.balance).is_equal_to(Decimal("100.00"))


@pytest.mark.asyncio
async def test_create_account_different_currencies(
    sut: Service,
    user: UserAccount,
    create_currency: Callable,
):
    # Arrange
    usd_currency = await create_currency("US Dollar", "USD", "$")
    eur_currency = await create_currency("Euro", "EUR", "€")
    gbp_currency = await create_currency("British Pound", "GBP", "£")

    # Act
    usd_account = await sut.create_account(
        user_id=user.user_id,
        name="USD Account",
        currency_id=usd_currency.currency_id,
        initial_balance=Decimal("100.00"),
    )

    eur_account = await sut.create_account(
        user_id=user.user_id,
        name="EUR Account",
        currency_id=eur_currency.currency_id,
        initial_balance=Decimal("200.00"),
    )

    gbp_account = await sut.create_account(
        user_id=user.user_id,
        name="GBP Account",
        currency_id=gbp_currency.currency_id,
        initial_balance=Decimal("300.00"),
    )

    # Assert
    assert_that(usd_account.currency_id).is_equal_to(usd_currency.currency_id)
    assert_that(eur_account.currency_id).is_equal_to(eur_currency.currency_id)
    assert_that(gbp_account.currency_id).is_equal_to(gbp_currency.currency_id)

