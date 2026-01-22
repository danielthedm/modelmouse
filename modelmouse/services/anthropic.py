from typing import Optional, Any, List, Dict
import json
import base64
import time
import random
import anthropic
from anthropic import APIError, RateLimitError


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


def add_additional_properties_false(schema: dict) -> dict:
    """Recursively add additionalProperties: false to all object types in a JSON schema."""
    if not isinstance(schema, dict):
        return schema

    result = schema.copy()

    if result.get("type") == "object":
        if "additionalProperties" not in result:
            result["additionalProperties"] = False

        if "properties" in result:
            result["properties"] = {
                key: add_additional_properties_false(value)
                for key, value in result["properties"].items()
            }

    if result.get("type") == "array" and "items" in result:
        result["items"] = add_additional_properties_false(result["items"])

    for keyword in ["anyOf", "oneOf", "allOf"]:
        if keyword in result:
            result[keyword] = [add_additional_properties_false(item) for item in result[keyword]]

    return result


class AnthropicService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)

    def _is_rate_limit_error(self, error: Exception) -> bool:
        if isinstance(error, RateLimitError):
            return True
        error_str = str(error).lower()
        return '429' in error_str or 'rate limit' in error_str or 'overloaded' in error_str

    def _call_with_retry(self, func, *args, **kwargs):
        last_exception = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if not self._is_rate_limit_error(e) or attempt == MAX_RETRIES:
                    raise e

                backoff = min(INITIAL_BACKOFF_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
                jitter = random.uniform(0, backoff * 0.1)
                sleep_time = backoff + jitter

                print(f"Rate limited, retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(sleep_time)

        raise last_exception

    def test_connection(self) -> dict:
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return {"success": True, "message": "API key is valid"}
        except APIError as e:
            return {"success": False, "message": str(e)}

    def call_model(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 1.0,
        output_schema: Optional[dict] = None,
        stream: bool = False,
    ) -> dict:
        start_time = time.time()

        try:
            if output_schema:
                schema_with_constraints = add_additional_properties_false(output_schema)
                response = self._call_with_retry(
                    self.client.messages.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    extra_headers={"anthropic-beta": "structured-outputs-2025-11-13"},
                    extra_body={
                        "output_format": {
                            "type": "json_schema",
                            "schema": schema_with_constraints
                        }
                    },
                    stream=stream
                )
            else:
                response = self._call_with_retry(
                    self.client.messages.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stream=stream
                )

            if stream:
                return {"success": True, "stream": response}

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = ""
            output_json = None
            for block in response.content:
                if block.type == "text":
                    output_text = block.text
                    if output_schema:
                        try:
                            output_json = json.loads(block.text)
                        except json.JSONDecodeError:
                            output_json = {"_raw_text": block.text}
                    break

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.stop_reason,
            }

        except APIError as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }

    def call_model_with_document(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        file_data: bytes,
        file_type: str,
        max_tokens: int = 1024,
        temperature: float = 1.0,
        output_schema: Optional[dict] = None,
    ) -> dict:
        start_time = time.time()

        try:
            encoded_data = base64.standard_b64encode(file_data).decode("utf-8")

            content = []
            if file_type == "application/pdf":
                content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": file_type,
                        "data": encoded_data,
                    },
                })
            else:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": file_type,
                        "data": encoded_data,
                    },
                })

            for msg in messages:
                if isinstance(msg.get("content"), str):
                    content.append({"type": "text", "text": msg["content"]})

            enhanced_messages = [{"role": "user", "content": content}]

            if output_schema:
                schema_with_constraints = add_additional_properties_false(output_schema)
                extra_headers = {"anthropic-beta": "structured-outputs-2025-11-13,pdfs-2024-09-25"}
                extra_body = {
                    "output_format": {
                        "type": "json_schema",
                        "schema": schema_with_constraints
                    }
                }
            else:
                extra_headers = {"anthropic-beta": "pdfs-2024-09-25"} if file_type == "application/pdf" else None
                extra_body = None

            response = self._call_with_retry(
                self.client.messages.create,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=enhanced_messages,
                extra_headers=extra_headers,
                extra_body=extra_body
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = ""
            output_json = None
            for block in response.content:
                if block.type == "text":
                    output_text = block.text
                    if output_schema:
                        try:
                            output_json = json.loads(block.text)
                        except json.JSONDecodeError:
                            output_json = {"_raw_text": block.text}
                    break

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.stop_reason,
            }

        except APIError as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }


ANTHROPIC_MODELS = [
    "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-5-20251101",
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
]
