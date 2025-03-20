import os
import logging
from dotenv import load_dotenv
from typing import cast
import base64

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# Load environment variables from the .env file
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "5242880"))  # Maximum file size (default: 5 MB)
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/jpeg,image/png,application/pdf").split(',')

# Models and their corresponding API keys
MODELS = {
    "Gemini 2.0": {
        "model_id": "google/gemini-2.0-flash-lite-preview-02-05:free",
        "api_key": os.getenv("OPENROUTER_API_KEY_GEMINI_2_0")
    },
    "Deepseek Llama": {
        "model_id": "meta-llama/llama-3-70b-instruct:nitro",
        "api_key": os.getenv("OPENROUTER_API_KEY_DEEPSEEK_LLAMA")
    },
    "Dolphin 3.0 R1 Mistal": {
        "model_id": "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
        "api_key": os.getenv("OPENROUTER_API_KEY_DOLPHIN_3_0_R1_MISTAL")
    }
}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store user sessions
user_sessions = {}


class UserSession:
    """Class to store user data."""
    def __init__(self):
        self.current_model = "Gemini 2.0"  # Default model
        self.history = []  # Message history


def split_message(text, max_length=4096):
    """Splits text into parts that do not exceed the maximum message length."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


def clean_response(text):
    """Cleans text from unnecessary symbols and formatting."""
    return text.replace('**', '').replace('*', '').strip('<>')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    chat_id = update.effective_chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()

    # Keyboard with buttons
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Choose Model", callback_data="choose_model")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Use the buttons below to get started.",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command and Help button."""
    help_text = (
        "Available Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "Choose Model - Change the language model via the button\n\n"
        "You can chat using text, emojis (smiles), stickers, and attach files or images. "
        "If you attach a file or image, the bot will forward it to the OpenRouter API."
    )
    if update.message:
        await update.message.reply_text(help_text)
    elif update.callback_query and update.callback_query.message:
        message = cast(Message, update.callback_query.message)
        await message.reply_text(help_text)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for inline button clicks."""
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    if data == "help":
        await help_command(update, context)
    elif data == "choose_model":
        # Keyboard with model options
        keyboard = [
            [InlineKeyboardButton(model, callback_data=f"model_{model}")]
            for model in MODELS.keys()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message:
            await query.message.reply_text("Select a language model:", reply_markup=reply_markup)
        else:
            logger.warning("Unable to send model selection: message is inaccessible.")
    elif data.startswith("model_"):
        selected_model = data.split("model_")[1]
        if chat_id not in user_sessions:
            user_sessions[chat_id] = UserSession()
        user_sessions[chat_id].current_model = selected_model
        if query.message:
            await query.message.reply_text(f"Language model changed to: {selected_model}")
        else:
            logger.warning("Unable to send model change confirmation: message is inaccessible.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming messages (text, stickers, photos, documents)."""
    if not update.message:
        logger.warning("Received an update without a message.")
        return

    chat_id = update.effective_chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession()
    session = user_sessions[chat_id]

    file_data = None
    file_type = None

    # Handle text, stickers, photos, and documents
    if update.message.text:
        content = update.message.text
    elif update.message.sticker:
        content = f"[Sticker: {update.message.sticker.emoji}]"
    elif update.message.photo:
        photo = update.message.photo[-1]
        file_obj = await photo.get_file()
        if file_obj.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("Image is too large.")
            return
        file_data = await file_obj.download_as_bytearray()
        file_type = "image/jpeg"
        content = "[Image attached]"
    elif update.message.document:
        document = update.message.document
        if document.mime_type not in ALLOWED_FILE_TYPES:
            await update.message.reply_text("File type not allowed.")
            return
        if document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("File is too large.")
            return
        file_obj = await document.get_file()
        file_data = await file_obj.download_as_bytearray()
        file_type = document.mime_type
        content = f"[File attached: {document.file_name}]"
    else:
        await update.message.reply_text("Unsupported message type.")
        return

    # Add the message to the history
    session.history.append({"role": "user", "content": content})

    # Send a processing message
    processing_message = await update.message.reply_text("Processing your request...")

    # Send a request to the OpenRouter API
    response_text = await send_to_openrouter(
        model=session.current_model,
        history=session.history,
        file_data=file_data,
        file_type=file_type
    )

    # Clean the response from unnecessary symbols
    cleaned_response = clean_response(response_text)

    # Add the response to the history
    session.history.append({"role": "assistant", "content": cleaned_response})

    # Delete the processing message
    await processing_message.delete()

    # Split the response into parts and send them
    response_chunks = split_message(cleaned_response)
    for chunk in response_chunks:
        await update.message.reply_text(chunk)


async def send_to_openrouter(model, history, file_data=None, file_type=None):
    """Sends a request to the OpenRouter API."""
    model_info = MODELS.get(model)
    if not model_info:
        return "Selected model is not available."

    api_key = model_info["api_key"]
    if not api_key:
        return "API key for the selected model is not available."

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Prepare messages
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]

    # Handle files
    if file_data and file_type:
        base64_data = base64.b64encode(file_data).decode("utf-8")

        if file_type.startswith("image/"):
            messages[-1]["content"] = [
                {"type": "text", "text": messages[-1]["content"]},
                {"type": "image_url", "image_url": {"url": f"data:{file_type};base64,{base64_data}"}}
            ]
        elif file_type == "application/pdf":
            messages[-1]["content"] = f"{messages[-1]['content']}\n[PDF file attached: The content of the PDF cannot be processed directly.]"

    try:
        completion = client.chat.completions.create(
            model=model_info["model_id"],
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error communicating with OpenRouter API: {e}", exc_info=True)
        return f"An error occurred while processing your request: {str(e)}"


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.add_error_handler(error)

    # Run the bot
    application.run_polling()


if __name__ == "__main__":
    main()