import logging

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)

from controller import Controller
from env import DATABASE_URL, TG_TOKEN

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    if not TG_TOKEN:
        msg = "You need to set up TG bot token..."
        raise ValueError(msg)

    if not DATABASE_URL:
        msg = "You need to pass DATABASE_URL env var"
        raise ValueError(msg)

    logger.warning(DATABASE_URL)
    engine = create_async_engine(DATABASE_URL, echo=True)
    controller = Controller(engine)
    app = ApplicationBuilder().token(TG_TOKEN).build()
    start_handler = CommandHandler("start", controller.start)

    app.add_handler(start_handler)

    logger.info("Starting the server...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Stopping the server")
