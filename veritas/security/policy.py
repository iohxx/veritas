import ipaddress
import re
from urllib.parse import urlsplit, unquote
from veritas.errors import VeritasError


def safe_url(url):
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 33 for c in url) or '\\' in url:
        raise VeritasError('invalid_url')
    try:
        p = urlsplit(url)
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or p.fragment or p.port not in (None, 80, 443):
            raise ValueError()
        host = p.hostname.encode('idna').decode('ascii')
        if host.lower() == 'localhost' or host.lower().endswith(('.localhost', '.local', '.internal')):
            raise ValueError()
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if ip is not None and not ip.is_global:
            raise ValueError()
        if host == 'technocore.chat' and re.search(r'/(say[^/]*|set[^/]*)(/|$)', unquote(p.path)):
            raise ValueError()
        return p
    except (ValueError, UnicodeError) as exc:
        raise VeritasError('unsafe_url') from exc


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'job_[A-Za-z0-9_-]{1,80}', value):
        raise VeritasError('invalid_job_id')
    return value
