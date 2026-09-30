import json
from typing import Protocol

from anthropic import Anthropic

from ...core.config import Settings
from ...core.exceptions import ConfigurationError, LLMResponseError, LLMServiceError


class LLMClient(Protocol):
    def generate_from_blocks(
        self,
        *,
        system: str,
        user_msg: str,
        content_blocks: list[dict],
        response_schema: dict,
        metadata: dict | None = None,
    ) -> str: ...


class AnthropicLLMClient:
    """Anthropic-compatible client for direct Terrax or LiteLLM access."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.anthropic_model
        self._max_request_size = settings.max_llm_request_size_bytes

        if settings.anthropic_auth_token:
            if not settings.anthropic_base_url:
                raise ConfigurationError(
                    "ANTHROPIC_BASE_URL is required when ANTHROPIC_AUTH_TOKEN is set."
                )
            token = settings.anthropic_auth_token
            base_url = settings.anthropic_base_url
        else:
            if not settings.litellm_proxy_url or not settings.litellm_master_key:
                raise ConfigurationError(
                    "Set ANTHROPIC_AUTH_TOKEN and ANTHROPIC_BASE_URL, or configure "
                    "LITELLM_PROXY_URL and LITELLM_MASTER_KEY."
                )
            token = settings.litellm_master_key
            base_url = settings.litellm_proxy_url

        self._client = Anthropic(auth_token=token, base_url=base_url)

    @staticmethod
    def _schema_instruction(system: str, response_schema: dict) -> str:
        return (
            f"{system}\n\n"
            "Return raw JSON only; do not add Markdown fences or commentary. "
            f"Match this schema:\n{json.dumps(response_schema, ensure_ascii=False)}"
        )

    @staticmethod
    def _response_text(response: object) -> str:
        content = getattr(response, "content", [])
        text = "".join(
            block.text for block in content if getattr(block, "type", None) == "text"
        ).strip()
        lines = text.splitlines()
        if (
            len(lines) >= 2
            and lines[0].strip().startswith("```")
            and lines[-1].strip() == "```"
        ):
            text = "\n".join(lines[1:-1]).strip()
        if not text:
            raise LLMResponseError("The language model returned an empty response.")
        return text

    def generate_from_blocks(
        self,
        *,
        system: str,
        user_msg: str,
        content_blocks: list[dict],
        response_schema: dict,
        metadata: dict | None = None,
    ) -> str:
        request_metadata = {}
        if metadata and metadata.get("transaction_id"):
            request_metadata["user_id"] = str(metadata["transaction_id"])

        params = {
            "model": self._model_name,
            "max_tokens": 8192,
            "system": self._schema_instruction(system, response_schema),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        *content_blocks,
                        {"type": "text", "text": user_msg},
                    ],
                }
            ],
        }
        if request_metadata:
            params["metadata"] = request_metadata

        request_size = len(json.dumps(params, ensure_ascii=False).encode("utf-8"))
        if request_size > self._max_request_size:
            raise LLMServiceError(
                "The prepared model request exceeds the configured size limit."
            )

        try:
            response = self._client.messages.create(**params)
        except Exception as exc:
            raise LLMServiceError() from exc
        return self._response_text(response)
