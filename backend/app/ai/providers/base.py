from abc import ABC, abstractmethod

from app.schemas.intelligence import IntelligenceContext, SalesIntelligence


class AIProviderError(RuntimeError):
    """Safe provider error that never includes credentials or raw request data."""


class ProviderConfigurationError(AIProviderError):
    pass


class MalformedProviderResponse(AIProviderError):
    pass


class AIProvider(ABC):
    name: str
    model: str | None = None

    @abstractmethod
    def generate(self, context: IntelligenceContext) -> SalesIntelligence:
        raise NotImplementedError
