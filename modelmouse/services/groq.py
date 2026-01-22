from typing import Optional, Any, List, Dict
import json
import base64
import time
import random
from openai import OpenAI, APIError


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


class GroqService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    def _supports_structured_output(self, model: str) -> bool:
        structured_models = [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ]
        return model in structured_models

    def _is_vision_model(self, model: str) -> bool:
        vision_models = [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ]
        return model in vision_models

    def _is_rate_limit_error(self, error: Exception) -> bool:
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
                model="llama-3.1-8b-instant",
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
                            "name": "benchmark_output",
                            "schema": output_schema,
                            "strict": True
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
        if not self._is_vision_model(model):
            return {
                "success": False,
                "model": model,
                "error": f"{model} does not support document/image inputs"
            }

        supported_types = ["image/png", "image/jpeg", "image/gif", "image/webp"]
        if file_type not in supported_types:
            return {
                "success": False,
                "model": model,
                "error": f"File type {file_type} not supported"
            }

        start_time = time.time()

        try:
            encoded_data = base64.b64encode(file_data).decode("utf-8")

            content = []
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    content.append({"type": "text", "text": msg["content"]})

            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{file_type};base64,{encoded_data}"}
            })

            enhanced_messages = [{"role": "user", "content": content}]

            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": enhanced_messages,
            }

            if output_schema:
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "benchmark_output",
                        "schema": output_schema,
                        "strict": True
                    }
                }

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
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', output_text)
                    if json_match:
                        try:
                            output_json = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            output_json = {"_raw_text": output_text}
                    else:
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


GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
]
