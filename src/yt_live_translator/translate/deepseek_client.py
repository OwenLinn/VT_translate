"""DeepSeek API client for translation smoke tests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from yt_live_translator.core.config import DeepSeekConfig
from yt_live_translator.core.models import SourceLanguage, TargetLanguage
from yt_live_translator.translate.prompt_builder import GlossaryTerm, build_translation_prompt


class DeepSeekClientError(RuntimeError):
    """Base class for DeepSeek client failures."""


class MissingAPIKeyError(DeepSeekClientError):
    """Raised when no DeepSeek API key is available."""


class DeepSeekAPIError(DeepSeekClientError):
    """Raised when DeepSeek returns an unusable response."""


class UrlOpener(Protocol):
    def __call__(self, request: Request, timeout: float):
        """Open a URL request."""


@dataclass(frozen=True)
class DeepSeekClient:
    config: DeepSeekConfig
    api_key: str | None
    opener: UrlOpener = urlopen

    def translate(
        self,
        text: str,
        target_language: TargetLanguage,
        source_language: SourceLanguage = "auto",
        glossary_terms: list[GlossaryTerm] | None = None,
    ) -> str:
        if not self.api_key:
            raise MissingAPIKeyError(
                f"DeepSeek API key is missing. Set {self.config.api_key_env} or add "
                "deepseek.api_key to config.toml."
            )

        prompt = build_translation_prompt(
            text=text,
            target_language=target_language,
            source_language=source_language,
            glossary_terms=glossary_terms,
        )
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "temperature": 0.2,
        }

        request = Request(
            url=_chat_completions_url(self.config.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with self.opener(request, timeout=self.config.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = _safe_error_detail(exc)
            raise DeepSeekAPIError(f"DeepSeek API request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise DeepSeekAPIError(f"DeepSeek API request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise DeepSeekAPIError("DeepSeek API request timed out") from exc

        return _parse_translation(response_body)


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def _parse_translation(response_body: str) -> str:
    try:
        payload = json.loads(response_body)
        content = payload["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise DeepSeekAPIError("DeepSeek API returned an unexpected response shape") from exc

    if not isinstance(content, str) or not content.strip():
        raise DeepSeekAPIError("DeepSeek API returned an empty translation")
    return content.strip()


def _safe_error_detail(error: HTTPError) -> str:
    if error.code in (401, 403):
        return "authentication failed; check the configured API key"

    try:
        body = error.read().decode("utf-8")
    except Exception:
        return error.reason or "no error detail"
    if not body:
        return error.reason or "no error detail"
    return _redact_possible_secrets(body[:500])


def _redact_possible_secrets(text: str) -> str:
    text = re.sub(
        r"(api key\s*:\s*)[^\"',}\s]+",
        r"\1[redacted]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(authorization\s*:\s*bearer\s+)[^\"',}\s]+",
        r"\1[redacted]",
        text,
        flags=re.IGNORECASE,
    )
    return text
