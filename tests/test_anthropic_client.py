from types import SimpleNamespace

import pytest

from app.core.exceptions import LLMResponseError
from app.infrastructure.llm.anthropic_client import AnthropicLLMClient


def test_response_text_removes_markdown_fence() -> None:
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='```json\n{"ok": true}\n```')]
    )

    assert AnthropicLLMClient._response_text(response) == '{"ok": true}'


def test_response_text_rejects_an_empty_response() -> None:
    response = SimpleNamespace(content=[])

    with pytest.raises(LLMResponseError):
        AnthropicLLMClient._response_text(response)
