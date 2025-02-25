# main.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import settings
from handlers import message_handler


def main():
    app = Application.builder().token(settings.Settings.TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", message_handler.start))
    app.add_handler(CommandHandler("model", message_handler.show_model_menu))
    app.add_handler(CommandHandler("clear", message_handler.clear_context))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, message_handler.handle_media))
    app.add_handler(CallbackQueryHandler(message_handler.handle_model_selection, pattern="^(gemini|deepseek|dolphin)$"))
    app.add_handler(CallbackQueryHandler(message_handler.confirm_model_change, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(message_handler.handle_model_confirmation))
    app.add_error_handler(message_handler.error_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
