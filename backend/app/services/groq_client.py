from dataclasses import dataclass
from typing import cast

from groq import Groq
from groq.types.chat import ChatCompletionMessageParam
from groq.types.chat.completion_create_params import (
    ResponseFormatResponseFormatJsonObject,
)
from typing import Protocol

from app.core.config import settings
from app.models.auth import EncryptedApiCredential
from app.services.encryption import decrypt_secret


class GroqClient(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        response_format: dict[str, str] | None = None,
    ) -> str:
        ...

    def list_models(self) -> list[dict[str, object]]:
        ...


class GroqProviderError(RuntimeError):
    pass


class RealGroqClient:
    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        response_format: dict[str, str] | None = None,
    ) -> str:
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=cast(list[ChatCompletionMessageParam], messages),
                max_tokens=max_tokens,
                response_format=cast(
                    ResponseFormatResponseFormatJsonObject | None, response_format
                ),
            )
            content = response.choices[0].message.content
        except Exception as exc:
            raise GroqProviderError("Groq request failed") from exc
        if not content:
            raise GroqProviderError("Groq returned an empty response")
        return content

    def list_models(self) -> list[dict[str, object]]:
        try:
            response = self._client.models.list()
            return [
                {"id": model.id, "owned_by": getattr(model, "owned_by", None)}
                for model in response.data
            ]
        except Exception as exc:
            raise GroqProviderError("Groq model listing failed") from exc


@dataclass
class FakeGroqClient:
    response: str = '{"name":"Test agent","purpose":"Test purpose","system_prompt":"Be helpful.","capabilities":[]}'
    models: list[dict[str, object]] | None = None
    calls: int = 0

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        response_format: dict[str, str] | None = None,
    ) -> str:
        self.calls += 1
        return self.response

    def list_models(self) -> list[dict[str, object]]:
        return self.models or [{"id": settings.groq_builder_model, "owned_by": "fake"}]


def create_groq_client(credential: EncryptedApiCredential) -> RealGroqClient:
    try:
        api_key = decrypt_secret(credential.ciphertext, credential.key_id)
    except ValueError as exc:
        raise GroqProviderError("Groq credential cannot be decrypted") from exc
    return RealGroqClient(api_key)
