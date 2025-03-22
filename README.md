# GeminiChatBot

A Telegram chatbot that leverages multiple language models via the OpenRouter API to generate dynamic responses. The bot supports various message types—including text, stickers, images, and PDFs—and allows users to switch between different language models on the fly.

## Overview

GeminiChatBot is built with Python using the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library. It integrates with the OpenRouter API to process and respond to user inputs using different language models. By default, it uses the Gemini 2.0 model, but users can easily switch between models such as Deepseek Llama and Dolphin 3.0 R1 Mistal through an inline keyboard.

## Features

- **Multi-model support:** Easily switch between different language models.
- **Rich message handling:** Processes text, stickers, images, and PDF documents.
- **File validation:** Ensures that file uploads conform to size and type restrictions.
- **Inline keyboards:** Offers buttons for help and model selection.
- **User session management:** Stores conversation history and model settings per user.
- **Environment-based configuration:** Sensitive data and settings are managed via a `.env` file.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/GeminiChatBot.git
   cd GeminiChatBot
   ```

2. **Create a virtual environment and activate it:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   _Dependencies include:_
   - `python-telegram-bot`
   - `python-dotenv`
   - `openai` (for integration with OpenRouter API)
   - Standard libraries such as `logging` and `base64`

## Setup

1. **Create a `.env` file** in the project root with the following variables:

   ```ini
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   MAX_FILE_SIZE=5242880  # Maximum file size in bytes (default: 5 MB)
   ALLOWED_FILE_TYPES=image/jpeg,image/png,application/pdf

   OPENROUTER_API_KEY_GEMINI_2_0=your_gemini_2_0_api_key_here
   OPENROUTER_API_KEY_DEEPSEEK_LLAMA=your_deepseek_llama_api_key_here
   OPENROUTER_API_KEY_DOLPHIN_3_0_R1_MISTAL=your_dolphin_3_0_r1_mistal_api_key_here
   ```

2. **Secure the `.env` file** by ensuring it is excluded from version control.

## Running the Bot

Start the bot by executing the main Python script:

```bash
python main.py
```

The bot will start polling for updates from Telegram. Ensure that your tokens and API keys are correctly configured in the `.env` file.

## Usage

- **/start:** Initializes a new session and displays an inline keyboard with options.
- **/help:** Displays usage instructions and a list of available commands.
- **Inline Buttons:**
  - **Help:** Shows help text.
  - **Choose Model:** Opens a menu to select a different language model.
  - **Model Selection:** Updates the current session’s default language model.
- **Message Handling:**
  - **Text:** Directly forwarded to the API.
  - **Stickers:** Extracts and forwards the sticker emoji.
  - **Photos:** Checks the size of the largest photo, downloads, and processes it.
  - **Documents (PDF):** Validates file type and size before processing.
- **Processing Flow:**
  - User messages are added to a session-specific conversation history.
  - The conversation, along with any file data, is sent to the OpenRouter API.
  - The API’s response is cleaned, split into acceptable message chunks, and then sent back to the user.

## Code Structure

- **Configuration and Setup:**
  - **Environment Variables:** Loaded via `dotenv` to manage API tokens and configuration.
  - **Logging:** Configured to provide informational and error messages.
- **User Session Management:**
  - **UserSession class:** Stores the current language model and conversation history for each user.
- **Core Functions:**
  - `split_message(text, max_length=4096)`: Splits long messages into chunks that meet Telegram's limits.
  - `clean_response(text)`: Cleans up the response text by removing unnecessary formatting.
  - `start(update, context)`: Handles the `/start` command to initialize user sessions and display the inline keyboard.
  - `help_command(update, context)`: Provides help information through the `/help` command or help button.
  - `button_handler(update, context)`: Manages inline keyboard interactions for help and model selection.
  - `handle_message(update, context)`: Processes incoming messages, including text, stickers, photos, and documents.
  - `send_to_openrouter(model, history, file_data, file_type)`: Forwards the conversation history (and file data, if any) to the OpenRouter API and returns the generated response.
  - `error(update, context)`: Logs errors that occur during message handling.
  - `main()`: Sets up the Telegram application and starts polling for updates.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and open a pull request.
4. For major changes, please open an issue first to discuss your ideas.

## License

This project is licensed under the [MIT License](LICENSE).
