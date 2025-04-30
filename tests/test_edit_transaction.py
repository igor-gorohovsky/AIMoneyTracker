import datetime
from decimal import Decimal
from typing import Callable
from unittest.mock import create_autospec

import pytest

from db.manager import DBManager
from db.models import Account, Category, Transaction, UserAccount
from exceptions import (
    AccountNotFoundError,
    NotExistingCategoryError,
    TransactionNotFoundError,
)
from misc import CategoryType
from requesters import RatesRequester
from service import Service, TransactionState


@pytest.fixture
def sut(db_manager: DBManager) -> Service:
    mock_requester = create_autospec(RatesRequester)
    return Service(db_manager, mock_requester)


@pytest.fixture
async def user(
    create_user: Callable,
    create_currency: Callable,
) -> UserAccount:
    currency = await create_currency("US Dollar", "USD", "$")
    return await create_user(123456789, currency.currency_id)


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
async def transaction(
    sut: Service,
    account: Account,
    expense_category: Category,
    user: UserAccount,
) -> Transaction:
    return await sut.create_transaction(
        user_tg_id=user.user_tg_id,
        account_name=account.name,
        category_name=expense_category.name,
        withdrawal_amount=Decimal("-100.00"),
        expense_amount=Decimal("-100.00"),
        note="Original transaction",
        state=TransactionState.VISIBLE,
    )


@pytest.fixture
async def transactions_setup(
    sut: Service,
    account: Account,
    expense_category: Category,
    income_category: Category,
    user: UserAccount,
) -> tuple[Transaction, Category]:
    """Set up a transaction and a category for testing."""
    transaction = await sut.create_transaction(
        user_tg_id=user.user_tg_id,
        account_name=account.name,
        category_name=expense_category.name,
        withdrawal_amount=Decimal("-100.00"),
        expense_amount=Decimal("-100.00"),
        note="Original transaction",
        state=TransactionState.VISIBLE,
    )
    return transaction, income_category


@pytest.fixture
async def second_account(
    user: UserAccount,
    db_manager: DBManager,
) -> Account:
    """Create a second test account for transaction transfer tests."""
    async with db_manager.transaction():
        return await db_manager.create_account(
            user_id=user.user_id,
            name="Second Test Account",
            balance=Decimal("500.00"),
            currency_id=user.currency_id,
        )


@pytest.fixture
def get_transactions(db_manager: DBManager) -> Callable:
    """Get all transactions for a user."""
    async def wrapper(user_id: int) -> list[Transaction]:
        async with db_manager.transaction():
            return await db_manager.get_user_transactions(user_id)
    return wrapper


@pytest.mark.asyncio
async def test_edit_transaction(
    sut: Service,
    user: UserAccount,
    account: Account,
    transactions_setup: tuple[Transaction, Category],
    get_account_by_id: Callable,
    get_transactions: Callable,
):
    # Arrange
    transaction, new_category = transactions_setup
    initial_balance = account.balance

    new_withdrawal_amount = Decimal("-150.00")
    new_expense_amount = Decimal("-150.00")
    new_note = "Updated transaction"

    # Act
    updated_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=account.name,
        category_name=new_category.name,
        withdrawal_amount=new_withdrawal_amount,
        expense_amount=new_expense_amount,
        note=new_note,
    )

    # Assert
    # 1. Verify we got a new transaction with the updated values
    assert updated_transaction is not None
    assert updated_transaction.transaction_id != transaction.transaction_id
    assert updated_transaction.withdrawal_amount == new_withdrawal_amount
    assert updated_transaction.expense_amount == new_expense_amount
    assert updated_transaction.note == new_note
    assert updated_transaction.category_id == new_category.category_id
    assert (
        updated_transaction.original_transaction_id
        == transaction.transaction_id
    )

    # 2. Check the account balance
    updated_account = await get_account_by_id(account.account_id)
    assert updated_account.balance == Decimal("850")

    # 3. Verify that we now have 3 transactions
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3  # noqa: PLR2004

    # 4. Check that the reversal transaction exists and links to the original
    reversal_transaction = None
    for t in transactions:
        if (
            t.transaction_id != transaction.transaction_id
            and t.transaction_id != updated_transaction.transaction_id
        ):
            reversal_transaction = t
            break

    assert reversal_transaction is not None
    assert (
        reversal_transaction.original_transaction_id
        == transaction.transaction_id
    )
    assert (
        reversal_transaction.withdrawal_amount
        == -transaction.withdrawal_amount
    )
    assert reversal_transaction.expense_amount == -transaction.expense_amount


@pytest.mark.asyncio
async def test_edit_transaction_between_accounts(
    sut: Service,
    user: UserAccount,
    account: Account,
    transactions_setup: tuple[Transaction, Category],
    db_manager: DBManager,
    get_account_by_id: Callable,
    get_transactions: Callable,
):
    # Arrange
    transaction, new_category = transactions_setup

    # Create a second account
    async with db_manager.transaction():
        second_account = await db_manager.create_account(
            user_id=user.user_id,
            name="Second Account",
            balance=Decimal("500.00"),
            currency_id=user.currency_id,
        )

    new_withdrawal_amount = Decimal("-75.00")
    new_expense_amount = Decimal("-75.00")

    # Act
    updated_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=second_account.name,  # Different account
        category_name=new_category.name,
        withdrawal_amount=new_withdrawal_amount,
        expense_amount=new_expense_amount,
    )

    # Assert
    # 1. Check that the new transaction is created with the right account
    assert updated_transaction.account_id == second_account.account_id

    # 2. Verify both account balances are updated correctly
    first_account_updated = await get_account_by_id(account.account_id)
    second_account_updated = await get_account_by_id(second_account.account_id)

    assert first_account_updated.balance == Decimal("1000")
    assert second_account_updated.balance == Decimal("425")

    # 3. Verify that we have 3 transactions in the ledger
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3


@pytest.mark.asyncio
async def test_edit_transaction_not_found(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
):
    # Arrange
    non_existent_id = 999999

    # Act & Assert
    with pytest.raises(TransactionNotFoundError) as exc_info:
        await sut.edit_transaction(
            user_tg_id=user.user_tg_id,
            transaction_id=non_existent_id,
            account_name=account.name,
            category_name=expense_category.name,
            withdrawal_amount=Decimal("-50.00"),
            expense_amount=Decimal("-50.00"),
        )



@pytest.mark.asyncio
async def test_edit_transaction_custom_date(
    sut: Service,
    user: UserAccount,
    account: Account,
    transactions_setup: tuple[Transaction, Category],
    get_transactions: Callable,
):
    # Arrange
    transaction, new_category = transactions_setup

    custom_date = datetime.datetime(2025, 5, 1, 12, 0, 0, tzinfo=datetime.UTC)

    # Act
    updated_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=account.name,
        category_name=new_category.name,
        withdrawal_amount=Decimal("-120.00"),
        expense_amount=Decimal("-120.00"),
        date=custom_date,
    )

    # Assert
    assert updated_transaction.date == custom_date

    # Both the reversal and new transaction should have the same date
    transactions = await get_transactions(user.user_id)

    # Find the reversal transaction
    reversal_transaction = None
    for t in transactions:
        if (
            t.transaction_id != transaction.transaction_id
            and t.transaction_id != updated_transaction.transaction_id
        ):
            reversal_transaction = t
            break

    assert reversal_transaction is not None
    assert reversal_transaction.date == custom_date


@pytest.mark.asyncio
async def test_edit_transaction_account_not_found(
    sut: Service,
    user: UserAccount,
    transaction: Transaction,
):
    """Test editing a transaction with a non-existent account."""
    # Arrange
    non_existent_account = "Non-existent Account"

    # Act & Assert
    with pytest.raises(AccountNotFoundError) as exc_info:
        await sut.edit_transaction(
            user_tg_id=user.user_tg_id,
            transaction_id=transaction.transaction_id,
            account_name=non_existent_account,
            category_name="Test Expense",
            withdrawal_amount=Decimal("-50.00"),
            expense_amount=Decimal("-50.00"),
        )

    assert f"Account '{non_existent_account}' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_edit_transaction_category_not_found(
    sut: Service,
    user: UserAccount,
    account: Account,
    transaction: Transaction,
):
    """Test editing a transaction with a non-existent category."""
    # Arrange
    non_existent_category = "Non-existent Category"

    # Act & Assert
    with pytest.raises(NotExistingCategoryError) as exc_info:
        await sut.edit_transaction(
            user_tg_id=user.user_tg_id,
            transaction_id=transaction.transaction_id,
            account_name=account.name,
            category_name=non_existent_category,
            withdrawal_amount=Decimal("-50.00"),
            expense_amount=Decimal("-50.00"),
        )

    assert f"Category '{non_existent_category}' not found" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_edit_transaction_only_amount(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    transaction: Transaction,
    get_account_by_id: Callable,
    get_transactions: Callable,
):
    """Test editing only the amount fields."""
    # Arrange
    original_account_balance = account.balance
    new_withdrawal_amount = Decimal("-50.00")
    new_expense_amount = Decimal("-50.00")

    # Act
    edited_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=account.name,
        category_name=expense_category.name,
        withdrawal_amount=new_withdrawal_amount,
        expense_amount=new_expense_amount,
        note=transaction.note,
    )

    # Assert
    assert edited_transaction is not None
    assert edited_transaction.withdrawal_amount == new_withdrawal_amount
    assert edited_transaction.expense_amount == new_expense_amount
    assert edited_transaction.account_id == account.account_id
    assert edited_transaction.category_id == expense_category.category_id
    assert edited_transaction.note == transaction.note

    # Check account balance - should be updated
    updated_account = await get_account_by_id(account.account_id)

    # Reversing original -100 and adding new -50
    assert updated_account.balance == Decimal("950")

    # Verify transactions
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3  # Original, reversal, and new


@pytest.mark.asyncio
async def test_edit_transaction_only_note(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    transaction: Transaction,
    get_transactions: Callable,
):
    """Test editing only the note field."""
    # Arrange
    new_note = "Updated note text"

    # Act
    edited_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=account.name,
        category_name=expense_category.name,
        withdrawal_amount=transaction.withdrawal_amount,
        expense_amount=transaction.expense_amount,
        note=new_note,
    )

    # Assert
    assert edited_transaction is not None
    assert edited_transaction.note == new_note
    assert edited_transaction.account_id == account.account_id
    assert edited_transaction.category_id == expense_category.category_id
    assert (
        edited_transaction.withdrawal_amount == transaction.withdrawal_amount
    )
    assert edited_transaction.expense_amount == transaction.expense_amount

    # Verify transactions
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3  # Original, reversal, and new


@pytest.mark.asyncio
async def test_edit_transaction_only_category(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    income_category: Category,
    transaction: Transaction,
    get_transactions: Callable,
):
    """Test editing only the category field."""
    # Act
    edited_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=account.name,
        category_name=income_category.name,  # Changed from expense to income
        withdrawal_amount=transaction.withdrawal_amount,
        expense_amount=transaction.expense_amount,
        note=transaction.note,
    )

    # Assert
    assert edited_transaction is not None
    assert edited_transaction.category_id == income_category.category_id
    assert edited_transaction.account_id == account.account_id
    assert (
        edited_transaction.withdrawal_amount == transaction.withdrawal_amount
    )
    assert edited_transaction.expense_amount == transaction.expense_amount

    # Verify transactions
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3  # Original, reversal, and new


@pytest.mark.asyncio
async def test_edit_transaction_different_currency(
    sut: Service,
    user: UserAccount,
    account: Account,
    expense_category: Category,
    transaction: Transaction,
    get_account_by_id: Callable,
    create_currency: Callable,
    db_manager: DBManager,
):
    """Test editing a transaction with different withdrawal and expense amounts."""
    # Arrange
    original_account_balance = account.balance

    # Create another currency and account
    eur_currency = await create_currency("Euro", "EUR", "€")

    # Create EUR account
    async with db_manager.transaction():
        eur_account = await db_manager.create_account(
            user_id=user.user_id,
            name="EUR Account",
            balance=Decimal("500.00"),
            currency_id=eur_currency.currency_id,
        )

    withdrawal_amount = Decimal("-75.00")  # EUR
    expense_amount = Decimal("-85.00")  # USD (converted)
    note = "Currency conversion transaction"

    # Act
    edited_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=eur_account.name,
        category_name=expense_category.name,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note=note,
    )

    # Assert
    assert edited_transaction is not None
    assert edited_transaction.withdrawal_amount == withdrawal_amount
    assert edited_transaction.expense_amount == expense_amount
    assert edited_transaction.account_id == eur_account.account_id

    # Check account balances
    updated_original_account = await get_account_by_id(account.account_id)
    updated_eur_account = await get_account_by_id(eur_account.account_id)

    # Original account should be credited back
    assert updated_original_account.balance == Decimal("1000")
    # EUR account should be debited the new withdrawal amount
    assert updated_eur_account.balance == Decimal("425")

@pytest.mark.asyncio
async def test_edit_transaction_all_fields_changed(
    sut: Service,
    user: UserAccount,
    account: Account,
    second_account: Account,
    expense_category: Category,
    income_category: Category,
    transaction: Transaction,
    get_account_by_id: Callable,
    get_transactions: Callable,
):
    """Test editing all fields of a transaction at once."""
    # Arrange
    original_account_balance = account.balance
    second_account_balance = second_account.balance

    # All fields are different
    new_withdrawal_amount = Decimal("150.00")  # Changed from -100 to +150
    new_expense_amount = Decimal("150.00")
    new_note = "Completely edited transaction"
    new_date = datetime.datetime(2025, 5, 1, 12, 0, 0, tzinfo=datetime.UTC)

    # Act
    edited_transaction = await sut.edit_transaction(
        user_tg_id=user.user_tg_id,
        transaction_id=transaction.transaction_id,
        account_name=second_account.name,  # Different account
        category_name=income_category.name,  # Different category
        withdrawal_amount=new_withdrawal_amount,  # Different amount and sign
        expense_amount=new_expense_amount,
        note=new_note,  # Different note
        date=new_date,  # Different date
    )

    # Assert
    # Verify all fields changed
    assert edited_transaction is not None
    assert edited_transaction.account_id == second_account.account_id
    assert edited_transaction.category_id == income_category.category_id
    assert edited_transaction.withdrawal_amount == new_withdrawal_amount
    assert edited_transaction.expense_amount == new_expense_amount
    assert edited_transaction.note == new_note
    assert edited_transaction.date == new_date

    # Check account balances
    updated_original_account = await get_account_by_id(account.account_id)
    updated_second_account = await get_account_by_id(second_account.account_id)

    # Original account should be credited back
    assert updated_original_account.balance == Decimal("1000")

    # Second account should be debited with new amount
    assert updated_second_account.balance == Decimal("650")

    # Verify transactions
    transactions = await get_transactions(user.user_id)
    assert len(transactions) == 3  # Original, reversal, and new

    # Find the reversal transaction
    reversal_transaction = None
    for t in transactions:
        if (
            t.transaction_id != transaction.transaction_id
            and t.transaction_id != edited_transaction.transaction_id
        ):
            reversal_transaction = t
            break

    assert reversal_transaction is not None
    assert (
        reversal_transaction.withdrawal_amount
        == -transaction.withdrawal_amount
    )
    assert reversal_transaction.date == new_date
