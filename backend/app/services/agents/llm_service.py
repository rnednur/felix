"""
LLM Service for agent communication
Provides a unified interface for calling LLMs via OpenRouter
"""
import httpx
import json
from typing import Dict, Any, Optional
from app.core.config import settings


class LLMService:
    """Service for LLM API calls"""

    def __init__(self, default_model: Optional[str] = None, default_temperature: float = 0.3):
        self.default_model = default_model or settings.OPENROUTER_MODEL
        self.default_temperature = default_temperature
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
        response_format: str = "text"  # 'text' or 'json'
    ) -> str:
        """
        Generate text from LLM

        Args:
            prompt: Prompt to send to LLM
            model: Model to use (defaults to service default)
            temperature: Temperature (defaults to service default)
            max_tokens: Max tokens to generate
            response_format: 'text' or 'json'

        Returns:
            Generated text (or JSON string if response_format='json')
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Add system message for JSON formatting if needed
        if response_format == "json":
            messages.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant that responds in valid JSON format only."
            })

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )

                # Check response status
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception(f"OpenRouter API error (status {response.status_code}): {error_detail}")

                result = response.json()

                # Check for error in response
                if 'error' in result:
                    raise Exception(f"OpenRouter API error: {result['error']}")

                # Extract content
                if 'choices' not in result or len(result['choices']) == 0:
                    raise Exception(f"Unexpected API response format: {json.dumps(result)}")

                content = result['choices'][0]['message']['content']

                # Clean up JSON if needed
                if response_format == "json":
                    content = self._extract_json(content)

                return content

            except httpx.TimeoutException:
                raise Exception("LLM request timed out")
            except httpx.RequestError as e:
                raise Exception(f"LLM request failed: {str(e)}")

    async def generate_with_context(
        self,
        prompt: str,
        context_messages: list,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate with conversation context

        Args:
            prompt: Current prompt
            context_messages: Previous messages in conversation
            model: Model to use
            temperature: Temperature
            max_tokens: Max tokens

        Returns:
            Generated text
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        # Build messages with context
        messages = context_messages + [{"role": "user", "content": prompt}]

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.text}")

            result = response.json()

            if 'error' in result:
                raise Exception(f"OpenRouter API error: {result['error']}")

            return result['choices'][0]['message']['content']

    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks if present"""
        content = content.strip()

        # Check if wrapped in markdown code blocks
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            content = '\n'.join(lines)

        return content.strip()

    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Raw chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Temperature
            max_tokens: Max tokens

        Returns:
            Full API response
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.text}")

            return response.json()
