from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

from db.manager import DBManager
from service import Service


class Controller:
    def __init__(self, engine: AsyncEngine) -> None:
        self._db_manager = DBManager(engine)
        self._user_service = Service(self._db_manager)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Received a start command")

        assert update.effective_chat is not None
        assert update.effective_user is not None

        _ = await self._user_service.register_user(update.effective_user.id)
