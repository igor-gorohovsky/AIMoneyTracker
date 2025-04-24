from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from db.manager import DBManager
from env import DATABASE_URL
from requesters import ExchangeRatesRequester
from service import Service
from worker.broker import broker


@broker.task(
    schedule=[
        {"cron": "*/5 * * * *"},
    ],
)
async def update_currency_rates() -> None:
    engine = create_async_engine(DATABASE_URL)
    db_manager = DBManager(engine)
    requester = ExchangeRatesRequester()

    interactor = Service(db_manager, requester)

    _ = await interactor.update_currency_rates()

    logger.info("Finished update of currencies rates...")
