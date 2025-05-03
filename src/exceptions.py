class NotSupportedCurrencyError(ValueError):
    pass


class CategoryDuplicateError(ValueError):
    pass


class NotExistingCategoryError(ValueError):
    pass


class AccountNotFoundError(ValueError):
    """Raised when an account is not found."""


class AccountDuplicateError(ValueError):
    """Raised when trying to create an account with a name that already exists for a user."""


class TransactionNotFoundError(ValueError):
    """Raised when a transaction is not found or doesn't belong to the user."""
