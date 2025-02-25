from config.settings import Settings


class ContextManager:
    _user_contexts = {}

    @classmethod
    def get_context(cls, user_id):
        """Retrieves the context for a given user."""
        return cls._user_contexts.get(user_id, {
            "model": "gemini",  # Default model
            "history": [],
            "current_file": None
        })

    @classmethod
    def add_message(cls, user_id, role, content):
        """Adds a message to the user's context."""
        if user_id not in cls._user_contexts:
            cls._user_contexts[user_id] = {
                "model": "gemini",
                "history": [],
                "current_file": None
            }
        cls._user_contexts[user_id]["history"].append({
            "role": role,
            "content": content
        })
        cls._truncate_history(user_id)

    @classmethod
    def update_model(cls, user_id, model):
        """Updates the model for a given user."""
        if user_id not in cls._user_contexts:
            cls._user_contexts[user_id] = {
                "model": model,
                "history": [],
                "current_file": None
            }
        else:
            cls._user_contexts[user_id]["model"] = model

    @classmethod
    def clear_context(cls, user_id):
        """Clears the conversation history for a given user."""
        if user_id in cls._user_contexts:
            cls._user_contexts[user_id]["history"] = []

    @classmethod
    def _truncate_history(cls, user_id):
        """Truncates the history to stay within the maximum context length."""
        if user_id in cls._user_contexts:
            while sum(len(m["content"]) for m in cls._user_contexts[user_id]["history"]) > Settings.MAX_CONTEXT_LENGTH:
                cls._user_contexts[user_id]["history"].pop(0)
