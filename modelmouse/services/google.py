from typing import Optional, Any, List, Dict
import json
import time
import random
import tempfile
import os
from pathlib import Path
from google import genai
from google.genai import types


MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30


class GoogleService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def _is_rate_limit_error(self, error: Exception) -> bool:
        error_str = str(error).lower()
        return '429' in error_str or 'resource_exhausted' in error_str or 'rate limit' in error_str

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
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Hi",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            return {"success": True, "message": "API key is valid"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def call_model(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1024,
        temperature: float = 1.0,
        output_schema: Optional[dict] = None,
    ) -> dict:
        start_time = time.time()

        try:
            content = ""
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    content += msg["content"] + "\n"

            config_kwargs = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            if output_schema:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = output_schema

            config = types.GenerateContentConfig(**config_kwargs)

            response = self._call_with_retry(
                self.client.models.generate_content,
                model=model,
                contents=content.strip(),
                config=config,
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = response.text
            output_json = None
            if output_schema:
                try:
                    output_json = json.loads(output_text)
                except json.JSONDecodeError:
                    output_json = {"_raw_text": output_text}

            input_tokens = None
            output_tokens = None
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.candidates[0].finish_reason.name if response.candidates else None,
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
        temp_file_path = None

        try:
            ext = {
                "application/pdf": ".pdf",
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/gif": ".gif",
                "image/webp": ".webp"
            }.get(file_type, "")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.write(file_data)
            temp_file.close()
            temp_file_path = temp_file.name

            file_obj = self.client.files.upload(file=Path(temp_file_path))

            contents = [file_obj]
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    contents.append(msg["content"])

            config_kwargs = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }

            if output_schema:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = output_schema

            config = types.GenerateContentConfig(**config_kwargs)

            response = self._call_with_retry(
                self.client.models.generate_content,
                model=model,
                contents=contents,
                config=config,
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            output_text = response.text
            output_json = None
            if output_schema:
                try:
                    output_json = json.loads(output_text)
                except json.JSONDecodeError:
                    output_json = {"_raw_text": output_text}

            input_tokens = None
            output_tokens = None
            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            return {
                "success": True,
                "model": model,
                "output_text": output_text,
                "output_json": output_json,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 2),
                "stop_reason": response.candidates[0].finish_reason.name if response.candidates else None,
            }

        except Exception as e:
            return {
                "success": False,
                "model": model,
                "error": str(e),
            }
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass


GOOGLE_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]
