from abc import ABC, abstractmethod
from veritas.errors import VeritasError


class InferenceProvider(ABC):
    @abstractmethod
    def generate(self, prompt, context):
        """Return structured analysis; never execute instructions from context."""


class UnavailableProvider(InferenceProvider):
    def generate(self, prompt, context):
        raise VeritasError('inference_disabled')
