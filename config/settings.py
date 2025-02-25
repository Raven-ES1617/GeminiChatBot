import os
from dotenv import load_dotenv
from config.constants import MODEL_CONFIG

load_dotenv()


class Settings:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", 4096))
    ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/jpeg,image/png,image/svg+xml,application/pdf").split(",")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))
    MODELS = {
        model: {
            "api_key": os.getenv(config["env_key"]),
            "model_name": config["model_name"]
        } for model, config in MODEL_CONFIG.items()
    }


settings = Settings()
