import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openrouter_api import get_openrouter_response

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_API_KEY = os.environ['telegram_api_key']


async def start(update: Update, _):
    await update.message.reply_text(
        "Hello! I'm your Gemini ChatBot. Send me some text, and optionally an image, and I'll respond!"
    )


def split_message(text, max_length=4000):
    """Splits a message into chunks within the Telegram message length limit."""
    return [text[i : i + max_length] for i in range(0, len(text), max_length)]


def escape_markdown(text):
    """Escapes special characters in MarkdownV2 syntax."""
    escape_chars = "*_`\[\]()~>#+-=|{}.!"  # Characters that need escaping
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)


async def send_markdown_message(update, text):
    """Sends a message with MarkdownV2 formatting while handling long messages."""
    text_parts = split_message(text)
    for part in text_parts:
        await update.message.reply_text(part, parse_mode="MarkdownV2")


async def handle_text(update: Update, _):
    user_query = update.message.text
    logger.info(f"Received text query: {user_query}")

    # Send processing message
    processing_message = await update.message.reply_text("Processing your request...")

    # Call the OpenRouter API
    response = get_openrouter_response(user_query)

    # Ensure markdown is formatted properly and message is within length limit
    response = escape_markdown(response)
    await processing_message.delete()
    await send_markdown_message(update, response)


async def handle_image(update: Update, _):
    # Get the image file
    photo_file = await update.message.photo[-1].get_file()
    image_url = photo_file.file_path

    # Get the text caption (if any)
    user_query = update.message.caption or "Describe this image."

    logger.info(f"Received image with query: {user_query}")

    # Send processing message
    processing_message = await update.message.reply_text("Processing your request...")

    # Call the OpenRouter API
    response = get_openrouter_response(user_query, image_url)

    # Ensure markdown is formatted properly and message is within length limit
    response = escape_markdown(response)
    await processing_message.delete()
    await send_markdown_message(update, response)


async def error(update: Update, context):
    logger.warning(f"Update {update} caused error {context.error}")


def main():
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_error_handler(error)

    # Start the bot
    application.run_polling()