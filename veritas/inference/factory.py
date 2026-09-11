"""Local adapter selection. Core verification never imports a concrete provider."""
import os

from veritas.errors import VeritasError
from veritas.inference.base import UnavailableProvider


def provider_for(config):
    if config.inference_provider == 'none':
        return UnavailableProvider()
    if config.inference_provider == 'ollama':
        from veritas.inference.local import LocalInferenceProvider
        return LocalInferenceProvider(config.model, config.inference_url)
    if config.inference_provider == 'external':
        from veritas.inference.external import ExternalInferenceProvider
        return ExternalInferenceProvider(
            config.inference_url, config.model, os.environ.get('VERITAS_API_KEY'))
    raise VeritasError('unknown_inference_provider')
