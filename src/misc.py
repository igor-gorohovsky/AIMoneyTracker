from enum import StrEnum, auto
from typing import TypedDict


class CategoryType(StrEnum):
    EXPENSE = auto()
    INCOME = auto()


class DefaultCategory(TypedDict):
    name: str
    category_type: CategoryType


DEFAULT_CATEGORIES: list[DefaultCategory] = [
    {"name": "Groceries", "category_type": CategoryType.EXPENSE},
    {"name": "Restaurant", "category_type": CategoryType.EXPENSE},
    {"name": "Leisure", "category_type": CategoryType.EXPENSE},
    {"name": "Transport", "category_type": CategoryType.EXPENSE},
    {"name": "Health", "category_type": CategoryType.EXPENSE},
    {"name": "Gifts", "category_type": CategoryType.EXPENSE},
    {"name": "Family", "category_type": CategoryType.EXPENSE},
    {"name": "Shopping", "category_type": CategoryType.EXPENSE},
    {"name": "Salary", "category_type": CategoryType.INCOME},
]
