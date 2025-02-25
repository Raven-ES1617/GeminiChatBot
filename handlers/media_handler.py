from telegram import Update
from telegram.ext import ContextTypes
from services.openrouter import OpenRouterService
from services.context_manager import ContextManager  # Added missing import
from utils.validators import validate_file, extract_text_content


async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = await update.message.effective_attachment.get_file()

    # Validate file
    valid, message = await validate_file(file)
    if not valid:
        await update.message.reply_text(f"❌ {message}")
        return

    # Process file content
    file_content = await extract_text_content(file)
    prompt = update.message.caption or "Please analyze this content"

    try:
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Processing your file...")

        # Get response from OpenRouter
        response = OpenRouterService.generate_response(user_id, prompt, file_content)

        # Update context
        ContextManager.add_message(user_id, "user", f"{prompt}\n[Attached: {file.file_path}]")
        ContextManager.add_message(user_id, "assistant", response)

        # Send response
        await processing_msg.delete()
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing media message: {e}")
        await update.message.reply_text("⚠️ Error processing your file. Please try again.")