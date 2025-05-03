import datetime
from decimal import Decimal
from typing import Callable
from unittest.mock import create_autospec

import pytest
from assertpy import assert_that

from db.manager import DBManager
from db.models import Account, Category, Transaction, UserAccount
from requesters import RatesRequester
from service import Service

SetupType = tuple[
    UserAccount,
    Account,
    Account,
    Category,
    Category,
    Transaction,
]


@pytest.fixture
def sut(db_manager: DBManager) -> Service:
    mock_requester = create_autospec(RatesRequester)
    return Service(db_manager, mock_requester)


@pytest.fixture
async def setup(
    sut: Service,
    db_manager: DBManager,
    create_currency: Callable,
) -> SetupType:
    _ = await create_currency("United States dollar", "USD", "$")
    user = await sut.register_user()

    async with db_manager.transaction():
        default_account = await db_manager.get_account(
            user_id=user.user_id,
            name="Default",
        )
    second_account = await sut.create_account(
        user.user_id,
        "New account",
        user.currency_id,
        500,
    )
    user_categories = await sut.get_user_categories(user.user_id)
    default_category = user_categories[0]
    new_category = user_categories[1]

    transaction = await sut.create_transaction(
        user.user_id,
        default_account.account_id,
        default_category.category_id,
        Decimal("-100"),
        Decimal("-100"),
        note="test note",
    )

    assert default_account is not None
    return (
        user,
        default_account,
        second_account,
        default_category,
        new_category,
        transaction,
    )


@pytest.mark.asyncio
async def test_edit_transaction_account_changed(
    sut: Service,
    setup: SetupType,
    get_account_by_id: Callable,
):
    # Arrange
    user, account, new_account, category, _, original_transaction = setup
    expected_transaction = Transaction(
        **original_transaction.model_dump()
        | {"account_id": new_account.account_id},
    )

    # Act
    transaction = await sut.edit_transaction(
        user_id=user.user_id,
        transaction_id=original_transaction.transaction_id,
        account_id=new_account.account_id,
        category_id=category.category_id,
        withdrawal_amount=-100,
        expense_amount=-100,
        note=original_transaction.note,
        date=original_transaction.date,
    )

    # Assert
    updated_default_account = await get_account_by_id(account.account_id)
    assert_that(updated_default_account.balance).is_equal_to(Decimal("0"))

    updated_new_account = await get_account_by_id(new_account.account_id)
    assert_that(updated_new_account.balance).is_equal_to(Decimal("400"))

    assert_that(transaction).is_equal_to(expected_transaction)


@pytest.mark.asyncio
async def test_edit_transaction_category_changed(
    sut: Service,
    setup: SetupType,
):
    # Arrange
    user, account, _, category, new_category, original_transaction = setup
    expected_transaction = Transaction(
        **original_transaction.model_dump()
        | {"category_id": new_category.category_id},
    )

    # Act
    transaction = await sut.edit_transaction(
        user_id=user.user_id,
        transaction_id=original_transaction.transaction_id,
        account_id=account.account_id,
        category_id=new_category.category_id,
        withdrawal_amount=-100,
        expense_amount=-100,
        note=original_transaction.note,
        date=original_transaction.date,
    )

    # Assert
    assert_that(transaction).is_equal_to(expected_transaction)


@pytest.mark.asyncio
async def test_edit_transaction_amounts_changed(
    sut: Service,
    setup: SetupType,
    get_account_by_id: Callable,
):
    # Arrange
    withdrawal_amount = -120
    expense_amount = -130
    user, account, _, category, _, original_transaction = setup
    expected_transaction = Transaction(
        **original_transaction.model_dump()
        | {
            "withdrawal_amount": withdrawal_amount,
            "expense_amount": expense_amount,
        },
    )

    # Act
    transaction = await sut.edit_transaction(
        user_id=user.user_id,
        transaction_id=original_transaction.transaction_id,
        account_id=account.account_id,
        category_id=category.category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note=original_transaction.note,
        date=original_transaction.date,
    )

    # Assert
    updated_account = await get_account_by_id(account.account_id)
    assert_that(updated_account.balance).is_equal_to(Decimal("-120"))

    assert_that(transaction).is_equal_to(expected_transaction)


@pytest.mark.asyncio
async def test_edit_transaction_note_changed(
    sut: Service,
    setup: SetupType,
):
    # Arrange
    note = "Updated note"
    user, account, _, category, _, original_transaction = setup
    expected_transaction = Transaction(
        **original_transaction.model_dump() | {"note": note},
    )

    # Act
    transaction = await sut.edit_transaction(
        user_id=user.user_id,
        transaction_id=original_transaction.transaction_id,
        account_id=account.account_id,
        category_id=category.category_id,
        withdrawal_amount=float(original_transaction.withdrawal_amount),
        expense_amount=float(original_transaction.expense_amount),
        note=note,
        date=original_transaction.date,
    )

    # Assert
    assert_that(transaction).is_equal_to(expected_transaction)

@pytest.mark.asyncio
async def test_edit_transaction_date_changed(
    sut: Service,
    setup: SetupType,
):
    # Arrange
    date = datetime.datetime(2000, 10, 29, 7, 0, 0, tzinfo=datetime.UTC)
    user, account, _, category, _, original_transaction = setup
    expected_transaction = Transaction(
        **original_transaction.model_dump() | {"date": date},
    )

    # Act
    transaction = await sut.edit_transaction(
        user_id=user.user_id,
        transaction_id=original_transaction.transaction_id,
        account_id=account.account_id,
        category_id=category.category_id,
        withdrawal_amount=float(original_transaction.withdrawal_amount),
        expense_amount=float(original_transaction.expense_amount),
        note=original_transaction.note,
        date=date,
    )

    # Assert
    assert_that(transaction).is_equal_to(expected_transaction)

