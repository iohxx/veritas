import json
from urllib.parse import urlsplit
from veritas.inference.base import InferenceProvider
from veritas.security.network import request
from veritas.attestation.canonical import parse_json
from veritas.errors import VeritasError


class LocalInferenceProvider(InferenceProvider):
    def __init__(self, model='qwen3:4b', url='http://127.0.0.1:11434/api/chat', timeout=120):
        self.model, self.url, self.timeout = model, url, timeout
        p = urlsplit(url)
        if p.hostname not in ('127.0.0.1','::1') or p.path != '/api/chat' or p.query or p.fragment or p.scheme != 'http':
            raise VeritasError('invalid_local_provider_url')

    def generate(self, prompt, context):
        body = json.dumps({'model':self.model,'stream':False,'think':False,'format':'json','options':{'temperature':0,'num_predict':2048,'num_ctx':16384},'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(context, ensure_ascii=True)}]}).encode()
        try:
            raw, _, _ = request(self.url, method='POST', body=body, headers={'Content-Type':'application/json'}, maximum=65536, timeout=self.timeout, local=True)
            reply = json.loads(raw)
            return parse_json(reply['message']['content'].encode(), 32768)
        except (VeritasError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise VeritasError('ollama_unavailable_or_invalid_response') from exc
