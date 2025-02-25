import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from services.openrouter import OpenRouterService
from services.context_manager import ContextManager
from utils.validators import validate_file, extract_text_content

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def split_message(text, max_length=4000):
    """Splits a message into chunks within the Telegram message length limit."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


def escape_markdown(text):
    """Escapes special characters in MarkdownV2 syntax."""
    escape_chars = r"*_`\[\]()~>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)


async def send_markdown_message(update, text):
    """Sends a message with MarkdownV2 formatting while handling long messages."""
    text_parts = split_message(text)
    for part in text_parts:
        await update.message.reply_text(part, parse_mode="MarkdownV2")


async def start(update: Update, _):
    """Handles the /start command"""
    await update.message.reply_text(
        "🤖 Hello! I'm your AI ChatBot. Send me text or files and I'll respond!\n\n"
        "Available commands:\n"
        "/model - Switch between different AI models\n"
        "/clear - Delete your conversation history\n\n"
        "Choose a model to get started!"
    )


async def handle_text(update: Update, _):
    """Handles text messages"""
    user_id = update.effective_user.id
    user_query = update.message.text
    logger.info(f"Received text query from user {user_id}: {user_query}")

    try:
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Processing your request...")

        # Get response from OpenRouter
        response = OpenRouterService.generate_response(user_id, user_query)

        # Format and send response
        formatted_response = escape_markdown(response)
        await processing_msg.delete()
        await send_markdown_message(update, formatted_response)

        # Update context
        ContextManager.add_message(user_id, "user", user_query)
        ContextManager.add_message(user_id, "assistant", response)

    except Exception as error:
        logger.error(f"Error processing text message: {error}")
        await update.message.reply_text("⚠️ An error occurred while processing your request.")


async def handle_media(update: Update, _):
    """Handles media messages (photos, documents)"""
    user_id = update.effective_user.id
    message = update.message

    try:
        # Handle photos
        if message.photo:
            # Select the highest resolution photo (last item in the tuple)
            photo = message.photo[-1]
            file = await photo.get_file()
            # Determine the MIME type based on the file path or extension
            file_path = file.file_path
            if file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                mime_type = "image/jpeg"
            elif file_path.endswith(".png"):
                mime_type = "image/png"
            elif file_path.endswith(".svg"):
                mime_type = "image/svg+xml"
            else:
                mime_type = "image/jpeg"  # Default to JPEG if unknown
        # Handle documents
        elif message.document:
            file = await message.document.get_file()
            mime_type = message.document.mime_type
        else:
            await message.reply_text("❌ Unsupported media type.")
            return

        # Validate file
        is_valid, validation_msg = await validate_file(file, mime_type)
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return

        # Extract text content
        file_content = await extract_text_content(file, mime_type)
        prompt = message.caption or "Please analyze this content"

        # Show processing message
        processing_msg = await message.reply_text("⏳ Processing your file...")

        # Get response from OpenRouter
        response = OpenRouterService.generate_response(
            user_id=user_id,
            prompt=prompt,
            file_content=file_content
        )

        # Format and send response
        formatted_response = escape_markdown(response)
        await processing_msg.delete()
        await send_markdown_message(update, formatted_response)

        # Update context
        context_msg = f"{prompt}\n[Attached: {file.file_path}]"
        ContextManager.add_message(user_id, "user", context_msg)
        ContextManager.add_message(user_id, "assistant", response)

    except Exception as error:
        logger.error(f"Error processing media message: {error}")
        await message.reply_text("⚠️ An error occurred while processing your file.")


async def show_model_menu(update: Update, _):
    """Shows model selection menu"""
    keyboard = [
        [InlineKeyboardButton("Gemini 2.0", callback_data="gemini")],
        [InlineKeyboardButton("DeepSeek Llama", callback_data="deepseek")],
        [InlineKeyboardButton("Dolphin Mistral", callback_data="dolphin")]
    ]
    await update.message.reply_text(
        "🔧 Select AI Model:\n\n"
        "• Gemini 2.0: Best for general-purpose tasks.\n"
        "• DeepSeek Llama: Optimized for coding and technical queries.\n"
        "• Dolphin Mistral: Ideal for creative writing and storytelling.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_model_selection(update: Update, _):
    """Handles model selection callback"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    model = query.data
    ContextManager.update_model(user_id, model)
    await query.edit_message_text(f"✅ Selected model: {model.capitalize()}")


async def error_handler(update: Update, context):
    """Handles errors"""
    logger.error(f"Update {update} caused error: {context.error}")
    if update.message:
        await update.message.reply_text("⚠️ An unexpected error occurred. Please try again.")


async def clear_context(update: Update, _):
    """Handles the /clear command to delete user context"""
    user_id = update.effective_user.id
    ContextManager.clear_context(user_id)
    await update.message.reply_text("✅ Your conversation history has been cleared.")


async def confirm_model_change(update: Update, _):
    """Shows a confirmation menu for model change"""
    query = update.callback_query
    await query.answer()
    model = query.data
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"confirm_{model}")],
        [InlineKeyboardButton("No", callback_data="cancel")]
    ]
    await query.edit_message_text(
        f"⚠️ Are you sure you want to switch to {model.capitalize()}?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_model_confirmation(update: Update, _):
    """Handles model change confirmation"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("confirm_"):
        model = data.split("_")[1]
        ContextManager.update_model(user_id, model)
        await query.edit_message_text(f"✅ Switched to {model.capitalize()}.")
    else:
        await query.edit_message_text("🚫 Model change canceled.")
