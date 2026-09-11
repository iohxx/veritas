from datetime import datetime, timezone
from html.parser import HTMLParser
from veritas.security.network import request
from veritas.attestation.canonical import digest
from veritas.errors import VeritasError


def now():
    return datetime.now(timezone.utc).isoformat()


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript'):
            self.hidden = max(0, self.hidden-1)
    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text)


def retrieve(url, config):
    record = {'url':url, 'retrieved_at':now(), 'accessible':False, 'supports_claim':False}
    try:
        raw, headers, final = request(url, maximum=config.max_source_size, timeout=config.request_timeout)
        content_type = next((v for k,v in headers.items() if k.lower() == 'content-type'), '').split(';')[0].lower()
        record.update(accessible=True, final_url=final, sha256=digest(raw), content_type=content_type, size=len(raw))
        if content_type not in ('text/plain','text/html','application/json','text/csv','application/xml','text/xml'):
            record.update(usable=False, reason='unsupported_media_type', text='')
        else:
            decoded = raw.decode('utf-8', errors='replace')
            if content_type == 'text/html':
                parser = TextExtractor()
                parser.feed(decoded)
                decoded = ' '.join(parser.parts)
            record.update(usable=True, text=decoded[:40000], text_truncated=len(decoded)>40000)
        return record, raw
    except VeritasError as exc:
        record.update(usable=False, reason=str(exc), text='')
        return record, None
