# src/llm/eppy_openai_llm.py
"""
EppyOpenAILLM — OpenAI-compatible LLM wrapper for CrewAI
Author: Huiwen Zhou (PhD Project)
Description:
  Provides a lightweight, OpenAI-only version
  used in the Agentic-BEM project. It standardizes the LLM interface and
  ensures consistent return format for CrewAI agents and tools.
"""

import os
import requests
from typing import Any, Dict, List, Optional, Union
from crewai import BaseLLM


class EppyOpenAILLM(BaseLLM):
    """OpenAI LLM wrapper for CrewAI-compatible tools and agents."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        stop: Optional[List[str]] = None,
    ):
        # Allow env fallback
        model = model or os.getenv("MODEL", "gpt-5")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

        super().__init__(model=model, temperature=temperature)

        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else None
        self.stop = stop

        if not self.api_key:
            raise ValueError("Missing OpenAI API key. Please set OPENAI_API_KEY in .env.")

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
    ) -> str:
        """Call the OpenAI chat completion endpoint."""

        # Convert simple string to message format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        payload = {
            "model": self.model,
            "messages": messages,
        }
        if self.model not in ["gpt-5", "gpt-4o", "gpt-4o-mini"]:
            payload["temperature"] = self.temperature

        if self.stop:
            payload["stop"] = self.stop

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180,
        )

        if not response.ok:
            raise RuntimeError(
                f"OpenAI API Error {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def supports_function_calling(self) -> bool:
        """Explicitly declare function calling support."""
        return True

    def get_context_window_size(self) -> int:
        """Return estimated context window size."""
        return {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-5": 128000,
            "gpt-3.5-turbo": 4096,
        }.get(self.model, 8192)
