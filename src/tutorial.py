import logging
import os

from loguru import logger
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("TG_TOKEN")
logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received a start command")

    assert update.effective_chat is not None

    _ = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello, World!",
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received a message to echo")

    assert update.effective_chat
    assert update.effective_message
    assert update.effective_message.text

    _ = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.effective_message.text,
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received a message to caps")

    assert update.effective_chat
    assert update.effective_message
    assert context.args

    caps_text = " ".join(context.args).upper()

    _ = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=caps_text,
    )


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received unknown command")

    assert update.effective_chat

    _ = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Ahahaha, you made a mistake, I don't know this command...xD",
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    start_handler = CommandHandler("start", start)
    caps_handler = CommandHandler("caps", caps)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    unknown_cmd_handler = MessageHandler(filters.COMMAND, unknown_cmd)

    app.add_handlers(
        [
            start_handler,
            echo_handler,
            caps_handler,
            unknown_cmd_handler,
        ],
    )

    logger.info("Starting the server...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Stopping the server")
