from db.manager import DBManager
from db.models import Category
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
            return await self._db_manager.create_category(
                user.user_id,
                name,
                category_type,
            )
