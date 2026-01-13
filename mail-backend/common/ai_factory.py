import os
from abc import ABC, abstractmethod
import google.generativeai as genai

# Abstract Strategy
class AIService(ABC):
    @abstractmethod
    def summarize(self, text: str, prompt: str) -> str:
        pass

# Concrete Strategy 1: Gemini
class GeminiService(AIService):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        # Pull model from env, default to 'gemini-1.5-flash' if missing
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing in .env")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def summarize(self, text: str, prompt: str) -> str:
        try:
            full_prompt = f"{prompt}\n\nEMAIL CONTENT:\n{text[:8000]}"
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Gemini Error]: {str(e)}"

# Concrete Strategy 2: OpenAI
class OpenAIService(AIService):
    def __init__(self):
        # We import here to avoid crashing if user doesn't have openai installed
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run 'pip install openai' to use OpenAI strategy.")

        api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY missing in .env")
            
        self.client = OpenAI(api_key=api_key)

    def summarize(self, text: str, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Email Content:\n{text[:8000]}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[OpenAI Error]: {str(e)}"

# The Factory
class AIFactory:
    _services = {}

    @staticmethod
    def get_service(provider_name: str) -> AIService:
        # Re-initialize every time to ensure env var changes are picked up (optional)
        # or keep the caching logic if you prefer performance.
        
        if provider_name == "gemini":
            return GeminiService()
        elif provider_name == "openai":
            return OpenAIService()
        else:
            raise ValueError(f"Unknown AI Provider: {provider_name}")