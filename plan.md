# Transaction Creation Functionality Implementation Plan

## 1. Update SQL Queries

Add new SQL queries in `src/db/queries.sql`:

```sql
-- name: CreateTransaction :one
INSERT INTO transaction(
    user_id, account_id, category_id, withdrawal_amount, expense_amount, note, state, date
) VALUES (
    :p1, :p2, :p3, :p4, :p5, :p6, :p7, :p8
)
RETURNING *;

-- name: GetTransactions :many
SELECT *
FROM transaction
WHERE user_id = :p1
ORDER BY date DESC;

-- name: GetAccountByName :one
SELECT *
FROM account
WHERE user_id = :p1 AND name = :p2;

-- name: GetAccountById :one
SELECT *
FROM account
WHERE account_id = :p1;

-- name: UpdateAccountBalance :one
UPDATE account
SET balance = :p2
WHERE account_id = :p1
RETURNING *;
```

## 2. Update DBManager

Add methods to the `DBManager` class in `src/db/manager.py`:

```python
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
        date = datetime.now()
    
    transaction = await self._querier.create_transaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        withdrawal_amount=withdrawal_amount,
        expense_amount=expense_amount,
        note=note,
        state=state,
        date=date,
    )
    assert transaction is not None
    return transaction
```

## 4. Add Exception Classes

In `src/exceptions.py`, add:

```python
class AccountNotFoundError(ValueError):
    """Raised when an account is not found."""
```

## 5. Update Service Class

Add a method to the `Service` class in `src/service.py`:

```python
async def create_transaction(
    self,
    user_tg_id: int,
    account_name: str,
    category_name: str,
    withdrawal_amount: Decimal,
    expense_amount: Decimal,
    note: str | None = None,
    state: str = "completed",
    date: datetime | None = None,
) -> Transaction:
    """
    Create a new transaction.
    
    Args:
        user_tg_id: Telegram user ID
        account_name: Name of the account to withdraw from
        category_name: Name of the category for the transaction
        withdrawal_amount: Amount to withdraw in account's currency (positive for expense, negative for income)
        expense_amount: Amount in user's preferred currency
        note: Optional note for the transaction
        state: Transaction state (default: "completed")
        date: Optional date for the transaction (defaults to current time)
        
    Returns:
        The created transaction
        
    Raises:
        AccountNotFoundError: If the account is not found
        NotExistingCategoryError: If the category is not found
    """
    async with self._db_manager.transaction():
        user = await self._db_manager.get_user(user_tg_id)
        
        account = await self._db_manager.get_account_by_name(
            user.user_id,
            account_name,
        )
        if account is None:
            raise AccountNotFoundError(f"Account '{account_name}' not found")
        
        category = await self._db_manager.get_category(
            user_id=user.user_id,
            name=category_name,
        )
        if category is None:
            raise NotExistingCategoryError(f"Category '{category_name}' not found")
        
        transaction = await self._db_manager.create_transaction(
            user.user_id,
            account.account_id,
            category.category_id,
            withdrawal_amount,
            expense_amount,
            note,
            state,
            date,
        )
        
        new_balance = account.balance - withdrawal_amount

        _ = await self._db_manager.update_account_balance(
            account.account_id,
            new_balance,
        )
        
        return transaction
```

## 7. Testing

Create a test file `tests/test_transactions.py` with test cases for:
- Creating a transaction
- Handling errors (account not found, category not found, insufficient funds)
- Verifying account balance updates

## Implementation Details

The key logic in the `create_transaction` method will:

1. Get the user by Telegram ID
2. Find the account by name
3. Find the category by name
4. Validate that the account has sufficient funds (for expenses)
5. Create the transaction
6. Update the account balance
7. Return the created transaction

All of this should be wrapped in a transaction context to ensure atomicity.
