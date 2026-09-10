import re
from urllib.parse import urlsplit
from veritas.security.policy import safe_url
from veritas.security.network import request
from veritas.attestation.canonical import canonical, parse_json
from veritas.errors import VeritasError


class TechnocoreClient:
    def __init__(self, base_url='https://technocore.chat', room='veritas', timeout=15, transport=request):
        p = safe_url(base_url)
        if p.scheme != 'https' or p.path not in ('','/') or p.query or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}',room):
            raise VeritasError('invalid_technocore_configuration')
        self.url=base_url.rstrip('/')+'/r/'+room
        self.room,self.timeout,self.transport=room,timeout,transport

    def _decode(self,raw):
        p=parse_json(raw,2000000)
        if not isinstance(p,dict) or p.get('room')!=self.room or type(p.get('last_seq')) is not int or p['last_seq']<0 or not isinstance(p.get('messages'),list) or len(p['messages'])>200:
            raise VeritasError('malformed_technocore_response')
        seq=-1
        for m in p['messages']:
            if not isinstance(m,dict) or type(m.get('seq')) is not int or m['seq']<=seq or m['seq']>p['last_seq'] or not isinstance(m.get('text'),str) or len(m['text'])>4096:
                raise VeritasError('malformed_technocore_message')
            seq=m['seq']
        return p

    def read(self,since=0,wait=10):
        if type(since) is not int or since<0 or type(wait) is not int or not 0<=wait<=10:
            raise VeritasError('invalid_cursor')
        raw,_,_=self.transport(f'{self.url}?format=json&since={since}&wait={wait}&limit=200',maximum=2000000,timeout=max(self.timeout,wait+5))
        return self._decode(raw)

    def post(self,envelope):
        raw,_,_=self.transport(self.url+'?format=json',method='POST',body=canonical(envelope),headers={'Content-Type':'application/json'},maximum=2000000,timeout=self.timeout)
        return self._decode(raw)
