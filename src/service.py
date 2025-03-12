from db.manager import DBManager


class Service:
    def __init__(self, db_manager: DBManager) -> None:
        self._db_manager = db_manager

    async def register_user(self, user_tg_id: int) -> None:
        async with self._db_manager.transaction():
            currency = await self._db_manager.get_currency("USD")
            user = await self._db_manager.create_user(
                user_tg_id=user_tg_id,
                currency_id=currency.currency_id,
            )
            _ = await self._db_manager.create_default_categories(user.user_id)
            _ = await self._db_manager.create_default_account(
                user.user_id,
                user.currency_id,
            )
