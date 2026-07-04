from __future__ import annotations

import json
from io import BytesIO

import pytest
from urllib.error import HTTPError

from yt_live_translator.core.config import DeepSeekConfig
from yt_live_translator.translate.deepseek_client import (
    DeepSeekAPIError,
    DeepSeekClient,
    MissingAPIKeyError,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_translate_uses_chat_completions_payload() -> None:
    captured = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"choices": [{"message": {"content": "大家好，歡迎來到直播。"}}]})

    client = DeepSeekClient(
        config=_config(),
        api_key="secret-key",
        opener=fake_opener,
    )

    translated = client.translate(
        text="Hello everyone, welcome to the stream.",
        target_language="zh-TW",
        source_language="en",
    )

    assert translated == "大家好，歡迎來到直播。"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["timeout"] == 10
    assert captured["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["body"]["model"] == "deepseek-v4-flash"
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["messages"][1]["role"] == "user"


def test_missing_api_key_error_does_not_include_secret() -> None:
    client = DeepSeekClient(config=_config(), api_key=None)

    with pytest.raises(MissingAPIKeyError, match="DEEPSEEK_API_KEY"):
        client.translate("Hello", target_language="zh-TW")


def test_authentication_error_redacts_api_response_detail() -> None:
    def fake_opener(request, timeout):
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":{"message":"Authentication Fails, Your api key: ****abcd is invalid"}}'),
        )

    client = DeepSeekClient(config=_config(), api_key="secret-key", opener=fake_opener)

    with pytest.raises(DeepSeekAPIError) as exc_info:
        client.translate("Hello", target_language="zh-TW")

    message = str(exc_info.value)
    assert "authentication failed" in message
    assert "****abcd" not in message
    assert "secret-key" not in message


def _config() -> DeepSeekConfig:
    return DeepSeekConfig(
        api_key_env="DEEPSEEK_API_KEY",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com",
        timeout_seconds=10,
    )
