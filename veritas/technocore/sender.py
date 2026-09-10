import time
from veritas.attestation.canonical import canonical
from veritas.attestation.verify import verify_signature
from veritas.identity.signing import sign
from veritas.technocore.reader import authenticated
from veritas.errors import VeritasError, NetworkError


def publish(attestation,identity,client,store,limit):
    if not verify_signature(attestation) or attestation['verifier']!=identity.did:
        raise VeritasError('cannot_publish_invalid_attestation')
    key=f'outbox:{client.url}:{attestation["job_id"]}'
    outbox=store.get(key)
    if outbox and outbox['state']=='published':
        return outbox['receipt']
    if outbox is None:
        before=client.read(0,0)['last_seq']
        nonce_key=f'nonce:{client.url}:{identity.did}'
        nonce=max(int(time.time()*1000),store.get(nonce_key,0)+1)
        store.set(nonce_key,nonce)
        text=canonical({'type':'ATTEST','attestation':attestation}).decode('ascii')
        if len(text)>4096:
            raise VeritasError('oversized_publication')
        envelope={'did':identity.did,'nonce':str(nonce),'text':text,'sig':sign(identity.key,f'{client.room}|{nonce}|{text}'.encode())}
        outbox={'state':'ready','envelope':envelope,'since':before}
        store.set(key,outbox)
    envelope=outbox['envelope']
    def receipt(response):
        for m in response['messages']:
            if m.get('from')==identity.did and str(m.get('nonce'))==envelope['nonce'] and m.get('text')==envelope['text'] and authenticated(client.room,m):
                return {'room':client.room,'seq':m['seq'],'did':identity.did,'nonce':envelope['nonce']}
        return None
    if outbox['state']=='uncertain':
        found=receipt(client.read(outbox['since'],0))
        if found:
            store.set(key,dict(outbox,state='published',receipt=found))
            return found
        raise VeritasError('publication_uncertain_manual_review_required')
    if outbox['state']=='rejected':
        raise VeritasError('publication_rejected_manual_review_required')
    store.quota('posts',limit)
    store.set(key,dict(outbox,state='uncertain'))
    try:
        response=client.post(envelope)
    except NetworkError as exc:
        if exc.status==429:
            store.set(key,dict(outbox,state='ready'))
        elif exc.status in (400,403,409,422):
            store.set(key,dict(outbox,state='rejected'))
        raise
    found=receipt(response)
    if found is None:
        raise VeritasError('publication_receipt_missing')
    store.set(key,dict(outbox,state='published',receipt=found))
    return found
