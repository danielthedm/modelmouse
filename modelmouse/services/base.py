from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseModelService(ABC):
    """Base interface for all model provider services."""

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection.

        Returns:
            Dict with 'success' bool and optional 'error' string
        """
        pass

    @abstractmethod
    def call_model(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 1.0,
        output_schema: Optional[dict] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Call a model with the given parameters.

        Args:
            model: Model identifier
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            output_schema: Optional JSON schema for structured output
            stream: Whether to stream the response

        Returns:
            Dict with:
                - success: bool
                - content: str (model response)
                - input_tokens: int
                - output_tokens: int
                - latency_ms: float
                - stop_reason: str
                - error: str (if failed)
        """
        pass

    @abstractmethod
    def call_model_with_document(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        file_data: bytes,
        file_type: str,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        output_schema: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Call a model with document/image input.

        Args:
            model: Model identifier
            messages: List of message dicts
            file_data: Raw file bytes
            file_type: MIME type (e.g., 'image/png', 'application/pdf')
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            output_schema: Optional JSON schema for structured output

        Returns:
            Same format as call_model()
        """
        pass
