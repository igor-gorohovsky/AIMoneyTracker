from typing import Callable

import pytest
from assertpy import assert_that

from currencies import CURRENCIES
from db.manager import DBManager
from db.models import Category, UserAccount
from exceptions import CategoryDuplicateError
from misc import CategoryType
from services.categories.service import CategoriesService


@pytest.fixture
async def user(
    create_user: Callable,
    create_currency: Callable,
) -> UserAccount:
    currency = await create_currency(
        CURRENCIES["USD"]["name"],
        "USD",
        CURRENCIES["USD"]["symbol"],
    )
    return await create_user(user_tg_id=1, currency_id=currency.currency_id)


@pytest.mark.asyncio
async def test_create_category(db_manager: DBManager, user: UserAccount):
    # Arrange
    name = "Food"
    category_type = CategoryType.EXPENSE

    expected_category = Category(
        category_id=1,
        user_id=user.user_id,
        name=name,
        type=category_type,
    )
    sut = CategoriesService(db_manager)

    # Act
    category = await sut.create_category(user.user_tg_id, name, category_type)

    # Assert
    assert_that(category).is_equal_to(expected_category)


@pytest.mark.asyncio
async def test_create_category__already_exist(
    db_manager: DBManager,
    user: UserAccount,
    create_category: Callable,
):
    # Arrange
    category = await create_category(
        user_id=user.user_id,
        name="Food",
        category_type=CategoryType.EXPENSE,
    )
    sut = CategoriesService(db_manager)

    # Act/Assert
    with pytest.raises(CategoryDuplicateError):
        await sut.create_category(
            user.user_tg_id,
            category.name,
            category.type,
        )


@pytest.mark.asyncio
async def test_edit_category__change_name(
    db_manager: DBManager,
    user: UserAccount,
    create_category: Callable,
):
    # Arrange
    original_category = await create_category(
        user_id=user.user_id,
        name="Food",
        category_type=CategoryType.EXPENSE,
    )
    sut = CategoriesService(db_manager)
    expected_name = "Transport"

    # Act
    category = await sut.edit_category(
        user.user_tg_id, original_category.name, expected_name
    )

    # Assert
    assert_that(category.category_id).is_equal_to(
        original_category.category_id,
    )
    assert_that(category.name).is_equal_to(expected_name)
