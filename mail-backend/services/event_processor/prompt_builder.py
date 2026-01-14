import os
from typing import Optional

class PromptBuilder:
    # A safe default just in case .env is missing
    DEFAULT_TEMPLATE = """
    You are a helpful assistant.

    PREVIOUS CONTEXT:
    {context}

    NEW EMAIL:
    {email_content}

    TASK:
    Summarize the new email. If it refers to the context, explain the connection.
    """

    def __init__(self):
        # We load the template once when the class is initialized
         self.default_template = os.getenv("CONTEXT_AWARE_PROMPT", self.DEFAULT_TEMPLATE)

    def build(self, context_str: str, email_content: str, custom_template: Optional[str] = None) -> str:
        """
        Combines history + new email into the final prompt string.
        Args:
            context_str: The historical context of the conversation.
            email_content: The content of the new email.
            custom_template: An optional custom prompt template provided by the user.
        """
        # Use the user's custom template if provided, otherwise use the default
        template = custom_template if custom_template else self.default_template
        template = custom_template if custom_template and custom_template.strip() else self.default_template
        # If no context exists, we can provide a friendly placeholder
        clean_context = context_str if context_str else "No previous conversation history."

        try:
            # Inject the data into the template
            return template.format(
                context=clean_context,
                email_content=email_content
            )
        except KeyError as e:
            # Fallback if the .env string has broken {placeholders}
            print(f"[Prompt Error] Template format error: {e}. Using default.")
            return self.default_template.format(
                context=clean_context,
                email_content=email_content
            )