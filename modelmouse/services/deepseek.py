from typing import Optional, Any, List, Dict
import json
import time
import random
from openai import OpenAI, APIError


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


class DeepSeekService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

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
                model="deepseek-chat",
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
        return {
            "success": False,
            "model": model,
            "error": "DeepSeek does not support document/image inputs"
        }


DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-coder",
]
