from typing import Optional, Any, List, Dict
import json
import base64
import time
import random
from openai import OpenAI, APIError, RateLimitError


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


def prepare_schema_for_openai(schema: dict) -> dict:
    """Recursively prepare a JSON schema for OpenAI's strict structured outputs."""
    if not isinstance(schema, dict):
        return schema

    result = schema.copy()

    if result.get("type") == "object":
        if "additionalProperties" not in result:
            result["additionalProperties"] = False

        if "properties" in result:
            result["properties"] = {
                key: prepare_schema_for_openai(value)
                for key, value in result["properties"].items()
            }
            result["required"] = list(result["properties"].keys())

    if result.get("type") == "array" and "items" in result:
        result["items"] = prepare_schema_for_openai(result["items"])

    for keyword in ["anyOf", "oneOf", "allOf"]:
        if keyword in result:
            result[keyword] = [prepare_schema_for_openai(item) for item in result[keyword]]

    return result


class OpenAIService:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)

    def _supports_structured_output(self, model: str) -> bool:
        structured_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06", "gpt-4o-2024-11-20",
            "gpt-4o-mini-2024-07-18", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
            "o1", "o1-mini", "o1-preview", "o3-mini",
        ]
        for supported in structured_models:
            if model == supported or model.startswith(f"{supported}-"):
                return True
        return False

    def _is_rate_limit_error(self, error: Exception) -> bool:
        if isinstance(error, RateLimitError):
            return True
        error_str = str(error).lower()
        return '429' in error_str or 'rate limit' in error_str

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
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return {"success": True, "message": "API key is valid"}
        except APIError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
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
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "stream": stream,
            }

            if output_schema:
                if self._supports_structured_output(model):
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "extraction_result",
                            "strict": True,
                            "schema": prepare_schema_for_openai(output_schema)
                        }
                    }
                else:
                    kwargs["response_format"] = {"type": "json_object"}

            response = self._call_with_retry(
                self.client.chat.completions.create,
                **kwargs
            )

            if stream:
                return {"success": True, "stream": response}

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = response.choices[0].message.content
            output_json = None
            if output_schema:
                try:
                    output_json = json.loads(output_text)
                except json.JSONDecodeError:
                    output_json = {"_raw_text": output_text}

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.choices[0].finish_reason,
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
            if file_type.startswith("image/"):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{file_type};base64,{encoded_data}"}
                })
            elif file_type == "application/pdf":
                content.append({
                    "type": "file",
                    "file": {
                        "filename": "document.pdf",
                        "file_data": f"data:{file_type};base64,{encoded_data}"
                    }
                })
            else:
                return {
                    "success": False,
                    "model": model,
                    "error": f"File type {file_type} not supported"
                }

            for msg in messages:
                if isinstance(msg.get("content"), str):
                    content.append({"type": "text", "text": msg["content"]})

            enhanced_messages = [{"role": "user", "content": content}]

            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": enhanced_messages,
            }

            if output_schema:
                if self._supports_structured_output(model):
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "extraction_result",
                            "strict": True,
                            "schema": prepare_schema_for_openai(output_schema)
                        }
                    }
                else:
                    kwargs["response_format"] = {"type": "json_object"}

            response = self._call_with_retry(
                self.client.chat.completions.create,
                **kwargs
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = response.choices[0].message.content
            output_json = None
            if output_schema:
                try:
                    output_json = json.loads(output_text)
                except json.JSONDecodeError:
                    output_json = {"_raw_text": output_text}

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.choices[0].finish_reason,
            }

        except Exception as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }


OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]
