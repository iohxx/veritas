import json
from veritas.inference.base import InferenceProvider
from veritas.security.network import request
from veritas.security.policy import safe_url
from veritas.attestation.canonical import parse_json
from veritas.errors import VeritasError


class ExternalInferenceProvider(InferenceProvider):
    """Optional remote Ollama-compatible HTTPS endpoint, explicitly selected locally."""
    def __init__(self, url, model, api_key=None, timeout=120):
        if safe_url(url).scheme != 'https':
            raise VeritasError('external_provider_requires_https')
        self.url, self.model, self._api_key, self.timeout = url, model, api_key, timeout

    def generate(self, prompt, context):
        headers = {'Content-Type':'application/json'}
        if self._api_key:
            headers['Authorization'] = 'Bearer ' + self._api_key
        body = json.dumps({'model':self.model,'stream':False,'format':'json','messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(context)}]}).encode()
        try:
            raw, _, _ = request(self.url, method='POST', body=body, headers=headers, maximum=65536, timeout=self.timeout)
            return parse_json(json.loads(raw)['message']['content'].encode(), 32768)
        except (VeritasError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise VeritasError('external_inference_unavailable_or_invalid_response') from exc
