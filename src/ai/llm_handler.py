"""
TARS LLM Handler
Unified interface for multiple LLM providers (OpenAI, Gemini, LM Studio, Ollama).
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generator
import logging

from openai import OpenAI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ..utils.config import get_config, TARSConfig


logger = logging.getLogger("tars.llm")


class BaseLLMHandler(ABC):
    """Abstract base class for LLM handlers."""
    
    def __init__(self, config: TARSConfig):
        self.config = config
        self.system_prompt = config.get_tars_personality_prompt()
    
    @abstractmethod
    def generate(self, message: str, conversation_history: list[dict] | None = None) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def generate_stream(self, message: str, conversation_history: list[dict] | None = None) -> Generator[str, None, None]:
        """Generate a streaming response from the LLM."""
        pass
    
    def _build_messages(self, message: str, conversation_history: list[dict] | None = None) -> list[dict]:
        """Build the messages list for the LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        return messages

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt


class OpenAIHandler(BaseLLMHandler):
    """Handler for OpenAI API (including LM Studio compatibility)."""
    
    def __init__(
        self,
        config: TARSConfig,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ):
        super().__init__(config)
        
        self.base_url = base_url or "https://api.openai.com/v1"
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.openai_model
        self.reasoning_effort = reasoning_effort
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def generate(self, message: str, conversation_history: list[dict] | None = None) -> str:
        """Generate a response using OpenAI-compatible API."""
        messages = self._build_messages(message, conversation_history)
        request_options = {}
        if self.reasoning_effort:
            request_options["reasoning_effort"] = self.reasoning_effort
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=self.config.max_tokens,
            **request_options,
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise RuntimeError(f"{self.model} returned an empty message content")
        return content.strip()
    
    def generate_stream(self, message: str, conversation_history: list[dict] | None = None) -> Generator[str, None, None]:
        """Generate a streaming response."""
        messages = self._build_messages(message, conversation_history)
        request_options = {}
        if self.reasoning_effort:
            request_options["reasoning_effort"] = self.reasoning_effort
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=self.config.max_tokens,
            stream=True,
            **request_options,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LMStudioHandler(OpenAIHandler):
    """Handler for LM Studio (local LLM server)."""
    
    def __init__(self, config: TARSConfig):
        super().__init__(
            config,
            base_url=config.lm_studio_base_url,
            api_key="lm-studio",  # LM Studio doesn't need a real key
            model=config.lm_studio_model,
            reasoning_effort="none",
        )


class OllamaHandler(BaseLLMHandler):
    """Handler for Ollama (local LLM)."""
    
    def __init__(self, config: TARSConfig):
        super().__init__(config)
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model
        
        # Use OpenAI-compatible endpoint
        self.client = OpenAI(
            base_url=f"{self.base_url}/v1",
            api_key="ollama"  # Ollama doesn't need a real key
        )
    
    def generate(self, message: str, conversation_history: list[dict] | None = None) -> str:
        """Generate a response using Ollama."""
        messages = self._build_messages(message, conversation_history)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=self.config.max_tokens
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise RuntimeError(f"{self.model} returned an empty message content")
        return content.strip()
    
    def generate_stream(self, message: str, conversation_history: list[dict] | None = None) -> Generator[str, None, None]:
        """Generate a streaming response."""
        messages = self._build_messages(message, conversation_history)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=self.config.max_tokens,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class GeminiHandler(BaseLLMHandler):
    """Handler for Google Gemini API."""
    
    def __init__(self, config: TARSConfig):
        super().__init__(config)
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=config.gemini_model,
            system_instruction=self.system_prompt
        )
    
    def generate(self, message: str, conversation_history: list[dict] | None = None) -> str:
        """Generate a response using Gemini."""
        history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
        chat = self.model.start_chat(history=history)
        response = chat.send_message(message)
        content = (response.text or "").strip()
        if not content:
            raise RuntimeError("Gemini returned an empty response")
        return content
    
    def generate_stream(self, message: str, conversation_history: list[dict] | None = None) -> Generator[str, None, None]:
        """Generate a streaming response."""
        history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
        chat = self.model.start_chat(history=history)
        response = chat.send_message(message, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def set_system_prompt(self, prompt: str) -> None:
        super().set_system_prompt(prompt)
        self.model = genai.GenerativeModel(
            model_name=self.config.gemini_model,
            system_instruction=prompt,
        )


def get_llm_handler(config: TARSConfig | None = None) -> BaseLLMHandler:
    """
    Factory function to get the appropriate LLM handler based on config.
    
    Args:
        config: Optional config override. Uses global config if not provided.
        
    Returns:
        Configured LLM handler instance
    """
    if config is None:
        config = get_config()
    
    provider = config.llm_provider.lower()
    
    if provider == "openai":
        return OpenAIHandler(config)
    elif provider == "gemini":
        return GeminiHandler(config)
    elif provider == "lm_studio":
        return LMStudioHandler(config)
    elif provider == "ollama":
        return OllamaHandler(config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


class MultiProviderLLM:
    """
    Multi-provider LLM with automatic fallback.
    Tries the primary provider first, falls back to alternatives on failure.
    """
    
    def __init__(self, config: TARSConfig | None = None):
        self.config = config or get_config()
        self.primary_handler = get_llm_handler(self.config)
        self.fallback_handlers: list[BaseLLMHandler] = []
        
        # Set up fallbacks based on available providers
        self._setup_fallbacks()
    
    def _setup_fallbacks(self) -> None:
        """Set up fallback handlers."""
        providers_to_try = ["lm_studio", "ollama", "gemini", "openai"]
        primary = self.config.llm_provider.lower()
        
        for provider in providers_to_try:
            if provider != primary:
                try:
                    # Create a temporary config for the fallback provider
                    handler = self._create_handler_for_provider(provider)
                    if handler:
                        self.fallback_handlers.append(handler)
                except Exception:
                    pass  # Skip unavailable providers

    def set_system_prompt(self, prompt: str) -> None:
        for handler in [self.primary_handler, *self.fallback_handlers]:
            handler.set_system_prompt(prompt)
    
    def _create_handler_for_provider(self, provider: str) -> BaseLLMHandler | None:
        """Create a handler for a specific provider."""
        if provider == "lm_studio":
            return LMStudioHandler(self.config)
        elif provider == "ollama":
            return OllamaHandler(self.config)
        elif provider == "gemini" and GEMINI_AVAILABLE and self.config.gemini_api_key:
            return GeminiHandler(self.config)
        elif provider == "openai" and self.config.openai_api_key:
            return OpenAIHandler(self.config)
        return None
    
    def generate(self, message: str, conversation_history: list[dict] | None = None) -> str:
        """Generate response with automatic fallback."""
        errors = []
        for handler in [self.primary_handler, *self.fallback_handlers]:
            try:
                response = handler.generate(message, conversation_history)
                if not response.strip():
                    raise RuntimeError("provider returned empty response")
                return response
            except Exception as e:
                errors.append(f"{type(handler).__name__}: {e}")
                logger.warning("LLM provider failed: %s", errors[-1])
        raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))

    def generate_stream(
        self,
        message: str,
        conversation_history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        errors = []
        for handler in [self.primary_handler, *self.fallback_handlers]:
            stream_started = False
            try:
                chunks = iter(handler.generate_stream(message, conversation_history))
                first_chunk = next(chunks, "")
                if not first_chunk:
                    raise RuntimeError("provider returned an empty stream")
                stream_started = True
                yield first_chunk
                yield from chunks
                return
            except Exception as exc:
                if stream_started:
                    raise
                errors.append(f"{type(handler).__name__}: {exc}")
                logger.warning("Streaming LLM provider failed before output: %s", errors[-1])
        raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))
