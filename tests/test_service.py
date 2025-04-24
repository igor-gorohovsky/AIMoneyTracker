from typing import Callable
from unittest.mock import MagicMock

import pytest
from assertpy import assert_that
from sqlalchemy.ext.asyncio import AsyncEngine

from db.manager import DBManager
from db.models import Category
from misc import CategoryType
from service import Service


def sort(categories: list[Category]):
    return sorted(categories, key=lambda x: x.category_id)


@pytest.fixture
def db_manager(engine: AsyncEngine) -> DBManager:
    return DBManager(engine)


@pytest.fixture
def sut(db_manager: DBManager) -> Service:
    return Service(db_manager, MagicMock())


@pytest.fixture
def expected_categories():
    return [
        Category(
            category_id=1,
            user_id=1,
            name="Groceries",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=2,
            user_id=1,
            name="Restaurant",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=3,
            user_id=1,
            name="Leisure",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=4,
            user_id=1,
            name="Transport",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=5,
            user_id=1,
            name="Health",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=6,
            user_id=1,
            name="Gifts",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=7,
            user_id=1,
            name="Family",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=8,
            user_id=1,
            name="Shopping",
            type=CategoryType.EXPENSE,
        ),
        Category(
            category_id=9,
            user_id=1,
            name="Salary",
            type=CategoryType.INCOME,
        ),
    ]


@pytest.mark.asyncio
async def test_register_user(
    sut: Service,
    create_currency: Callable,
    get_user: Callable,
    get_accounts: Callable,
    get_user_categories: Callable,
    expected_categories: list[Category],
) -> None:
    currency = await create_currency("United States dollar", "USD", "$")
    user_tg_id = 1

    _ = await sut.register_user(user_tg_id)

    expected_user = await get_user(user_tg_id)
    accounts = await get_accounts(expected_user.user_id)
    categories = await get_user_categories(expected_user.user_id)

    assert_that(expected_user).is_not_none()
    assert_that(expected_user).has_balance(0)
    assert_that(expected_user).has_currency_id(currency.currency_id)

    assert_that(accounts).is_length(1)
    assert_that(accounts[0]).has_name("Default")
    assert_that(accounts[0]).has_balance(0)
    assert_that(accounts[0]).has_currency_id(currency.currency_id)

    assert_that(categories).is_length(9)
    assert_that(sort(categories)).is_equal_to(sort(expected_categories))
