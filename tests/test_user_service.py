import random
from datetime import UTC, datetime
from typing import Callable
from unittest.mock import Mock

import pytest
from assertpy import assert_that
from telegram import Chat, Message, Update, User

from bot import Bot
from db.models import Category
from misc import CategoryType


@pytest.mark.asyncio
async def test(
    bot: Bot,
    create_currency: Callable,
    get_user: Callable,
    get_accounts: Callable,
    get_user_categories: Callable,
    context_mock: Mock,
) -> None:
    currency = await create_currency("United States dollar", "USD", "$")
    update_obj = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(tz=UTC),
            chat=Chat(id=1, type="chat"),
            from_user=User(
                id=random.randint(0, 10),
                first_name="Alex",
                last_name="O",
                is_bot=False,
            ),
        ),
    )
    expected_categories = [
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

    _ = await bot.start(update_obj, context_mock)

    expected_user = await get_user(update_obj.effective_user.id)
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
    assert_that(categories).is_equal_to(expected_categories)


def test_user_duplicate_is_not_created():
    pass
