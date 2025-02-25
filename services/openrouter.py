import requests
from config import settings
from services.context_manager import ContextManager


class OpenRouterService:
    BASE_URL = "https://openrouter.ai/api/v1"

    @classmethod
    def generate_response(cls, user_id, prompt, file_content=None):
        # Get user context
        ctx = ContextManager.get_context(user_id)

        # Get model configuration
        model_config = settings.Settings.MODELS.get(ctx["model"])
        if not model_config or not model_config.get("api_key"):
            raise ValueError("Invalid model configuration")

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {model_config['api_key']}",
            "Content-Type": "application/json"
        }

        # Prepare messages
        messages = ctx["history"] + [{"role": "user", "content": prompt}]

        # Prepare payload
        payload = {
            "model": model_config["model_name"],
            "messages": messages,
            "max_tokens": settings.Settings.MAX_CONTEXT_LENGTH
        }

        # Add file content if available
        if file_content:
            payload["file_content"] = file_content

        # Make API request
        response = requests.post(
            f"{cls.BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )

        # Handle response
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
