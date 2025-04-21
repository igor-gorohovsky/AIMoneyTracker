from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from db.manager import DBManager
from env import DATABASE_URL
from worker.broker import broker
from worker.rates.interactor import RatesInteractor
from worker.rates.requesters import ExchangeRatesRequester


@broker.task(
    schedule=[
        {"cron": "* * * * *"},
    ],
)
async def update_currency_rates() -> None:
    engine = create_async_engine(DATABASE_URL)
    db_manager = DBManager(engine)
    requester = ExchangeRatesRequester()

    interactor = RatesInteractor(db_manager, requester)

    _ = await interactor.update_currency_rates()

    logger.info("Finishing update of currencies rates...")
