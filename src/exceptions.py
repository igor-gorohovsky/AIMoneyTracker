class NotSupportedCurrencyError(ValueError):
    pass


class CategoryDuplicateError(ValueError):
    pass


class NotExistingCategoryError(ValueError):
    pass


class AccountNotFoundError(ValueError):
    """Raised when an account is not found."""
