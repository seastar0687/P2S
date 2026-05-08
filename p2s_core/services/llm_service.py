from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel


class LLMServiceError(Exception):
    """Raised when the MVP LLM service cannot complete a request."""


class LLMService:
    """Minimal OpenAI-compatible LLM client for MVP 0.5 smoke checks."""

    def __init__(self, config: dict[str, Any], client: httpx.AsyncClient | None = None):
        llm_config = config["llm"]
        self.provider = llm_config["provider"]
        if self.provider != "openai":
            raise ValueError("MVP 0.5 only supports provider='openai'")

        self.model = llm_config["model"]
        self.api_base = llm_config.get("api_base", "https://api.openai.com/v1").rstrip("/")
        self.api_key = llm_config["api_key"]
        self.temperature = llm_config.get("temperature", 0.3)
        self.max_retries = llm_config.get("max_retries", 3)
        self.timeout = llm_config.get("timeout_sec", 120)
        self.client = client or httpx.AsyncClient(timeout=self.timeout)

    async def complete(
        self,
        messages: list[dict[str, str]],
        response_type: type[BaseModel] | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
        retry_delay_sec: float = 1.0,
        debug_dir: str | Path | None = None,
    ) -> str | BaseModel:
        retries = self.max_retries if max_retries is None else max_retries
        attempts = max(1, retries)
        parse_errors: list[str] = []

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "temperature": self.temperature if temperature is None else temperature,
        }
        if response_type is not None:
            payload["response_format"] = {"type": "json_object"}
            payload["messages"] = self._with_schema_instruction(payload["messages"], response_type)

        last_content = ""
        if response_type is None:
            response = await self._post_chat_completions(payload, max_retries=max_retries)
            return self._extract_content(response)

        for attempt in range(attempts):
            response = await self._post_chat_completions(payload, max_retries=1)
            content = self._extract_content(response)
            last_content = content
            try:
                return self._parse_structured_content(content, response_type)
            except Exception as exc:
                parse_errors.append(str(exc))
                if attempt < attempts - 1:
                    payload["messages"] = self._with_retry_instruction(payload["messages"])
                    if retry_delay_sec > 0:
                        import asyncio

                        await asyncio.sleep(retry_delay_sec)

        if debug_dir is not None:
            self._write_debug_raw_response(debug_dir, last_content)
        raise LLMServiceError(f"LLM structured output parse failed: {'; '.join(parse_errors)}")

    async def health_check(self) -> bool:
        try:
            result = await self.complete(
                [{"role": "user", "content": "你好"}],
                temperature=0,
                max_retries=1,
            )
        except Exception:
            return False
        return bool(result)

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _post_chat_completions(
        self,
        payload: dict[str, Any],
        max_retries: int | None = None,
    ) -> dict[str, Any]:
        retries = self.max_retries if max_retries is None else max_retries
        last_error: Exception | None = None

        for _ in range(max(1, retries)):
            try:
                response = await self.client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc

        error_type = type(last_error).__name__ if last_error is not None else "UnknownError"
        raise LLMServiceError(f"LLM request failed ({error_type}): {last_error!r}") from last_error

    @staticmethod
    def _extract_content(response: dict[str, Any]) -> str:
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMServiceError("LLM response did not contain choices[0].message.content") from exc

    @staticmethod
    def _with_schema_instruction(
        messages: list[dict[str, str]],
        response_type: type[BaseModel],
    ) -> list[dict[str, str]]:
        schema = response_type.model_json_schema()
        instruction = (
            "Return only one JSON object that validates against this JSON schema. "
            "Do not include markdown fences or explanatory text.\n"
            f"{schema}"
        )
        return [{"role": "system", "content": instruction}, *messages]

    @staticmethod
    def _with_retry_instruction(messages: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            *messages,
            {
                "role": "user",
                "content": "The prior response was not valid JSON for the requested schema. Return only valid JSON.",
            },
        ]

    @staticmethod
    def _parse_structured_content(content: str, response_type: type[BaseModel]) -> BaseModel:
        candidates = [content]
        fenced = re.search(r"```json\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidates.append(fenced.group(1))
        object_text = LLMService._extract_first_json_object(content)
        if object_text:
            candidates.append(object_text)

        last_error: Exception | None = None
        for candidate in candidates:
            try:
                return response_type.model_validate_json(candidate)
            except Exception as exc:
                last_error = exc
        raise LLMServiceError(f"Could not parse structured response: {last_error}") from last_error

    @staticmethod
    def _extract_first_json_object(content: str) -> str | None:
        start = content.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False
        for index, char in enumerate(content[start:], start=start):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return content[start : index + 1]
        return None

    @staticmethod
    def _write_debug_raw_response(debug_dir: str | Path, content: str) -> None:
        from datetime import UTC, datetime

        directory = Path(debug_dir)
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        (directory / f"llm_raw_{timestamp}.txt").write_text(content, encoding="utf-8")
