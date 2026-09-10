import re
from veritas.identity.signing import verify
from veritas.attestation.canonical import parse_json, canonical
from veritas.security.sanitizer import parse_job
from veritas.errors import VeritasError


def authenticated(room,message):
    did,nonce,text=message.get('from'),message.get('nonce'),message.get('text')
    if type(nonce) not in (str,int) or not re.fullmatch(r'[0-9]{1,19}',str(nonce)) or not isinstance(text,str):
        return False
    return verify(did,message.get('sig'),f'{room}|{nonce}|{text}'.encode('utf-8'))


def receive_job(room,message,max_size):
    if not authenticated(room,message):
        raise VeritasError('unauthenticated_job_message')
    payload=parse_json(message['text'].encode(),max_size)
    if isinstance(payload,dict) and payload.get('type')=='JOB':
        payload=payload.get('job')
    if not isinstance(payload,dict) or payload.get('type')!='VERITAS_JOB':
        return None
    job=parse_job(canonical(payload),max_size)
    if job.requester!=message['from']:
        raise VeritasError('requester_signature_mismatch')
    return job
