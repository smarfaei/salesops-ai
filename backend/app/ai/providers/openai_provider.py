import json
import socket
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.ai.providers.base import (
    AIProvider,
    AIProviderError,
    MalformedProviderResponse,
    ProviderConfigurationError,
)
from app.schemas.intelligence import IntelligenceContext, SalesIntelligence

Transport = Callable[[dict, float], dict]


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str | None,
        timeout_seconds: float = 20.0,
        transport: Transport | None = None,
    ) -> None:
        self._api_key = api_key or ""
        self.model = model or None
        self._timeout_seconds = timeout_seconds
        self._transport = transport or self._request

    def generate(self, context: IntelligenceContext) -> SalesIntelligence:
        if not self._api_key:
            raise ProviderConfigurationError("OpenAI API key is not configured")
        if not self.model:
            raise ProviderConfigurationError("OpenAI model is not configured")

        payload = {
            "model": self.model,
            "store": False,
            "instructions": (
                "You are a cautious B2B sales analyst. Use only supplied facts. "
                "Do not invent intent, timelines, competitors, or commitments."
            ),
            "input": context.model_dump_json(),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "sales_intelligence",
                    "strict": True,
                    "schema": SalesIntelligence.model_json_schema(),
                }
            },
        }
        try:
            response = self._transport(payload, self._timeout_seconds)
            output_text = self._extract_output_text(response)
            return SalesIntelligence.model_validate_json(output_text)
        except AIProviderError:
            raise
        except (TimeoutError, socket.timeout, URLError) as exc:
            raise AIProviderError("OpenAI request failed or timed out") from exc
        except (KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise MalformedProviderResponse("OpenAI returned malformed structured output") from exc

    def _request(self, payload: dict, timeout_seconds: float) -> dict:
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise AIProviderError(f"OpenAI request failed with HTTP status {exc.code}") from exc
        except (URLError, TimeoutError, socket.timeout) as exc:
            raise AIProviderError("OpenAI request failed or timed out") from exc
        except json.JSONDecodeError as exc:
            raise MalformedProviderResponse("OpenAI returned a non-JSON response") from exc

    @staticmethod
    def _extract_output_text(response: dict) -> str:
        direct = response.get("output_text")
        if isinstance(direct, str) and direct:
            return direct
        for item in response.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return content["text"]
        raise MalformedProviderResponse("OpenAI response did not contain output text")
