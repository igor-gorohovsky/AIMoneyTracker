from db.manager import DBManager
from db.models import Category
from exceptions import CategoryDuplicateError, NotExistingCategoryError
from misc import CategoryType


class CategoriesService:
    def __init__(self, db_manager: DBManager) -> None:
        self._db_manager = db_manager

    async def create_category(
        self,
        user_tg_id: int,
        name: str,
        category_type: CategoryType,
    ) -> Category:
        async with self._db_manager.transaction():
            user = await self._db_manager.get_user(user_tg_id)

            category = await self._db_manager.get_category(
                name=name,
                user_id=user.user_id,
            )
            if category is not None:
                raise CategoryDuplicateError

            return await self._db_manager.create_category(
                user.user_id,
                name,
                category_type,
            )

    async def edit_category(
        self,
        user_tg_id: int,
        old_name: str,
        new_name: str,
    ) -> Category:
        async with self._db_manager.transaction():
            user = await self._db_manager.get_user(user_tg_id)

            category = await self._db_manager.get_category(
                name=old_name,
                user_id=user.user_id,
            )
            if category is None:
                raise NotExistingCategoryError

            return await self._db_manager.update_category(
                category.category_id,
                new_name,
            )
