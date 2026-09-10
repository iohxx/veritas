import http.client
import ipaddress
import queue
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, urljoin
from veritas.security.policy import safe_url
from veritas.errors import NetworkError, VeritasError


class PinnedConnection(http.client.HTTPConnection):
    # Keep the socket handle until the bounded body read ends, including close-delimited responses.
    defer_close = False

    def close(self):
        if not self.defer_close:
            super().close()


def resolve_public(host, port, timeout):
    result = queue.Queue(maxsize=1)
    def resolve():
        try:
            result.put(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
        except OSError:
            result.put(None)
    threading.Thread(target=resolve, daemon=True).start()
    try:
        records = result.get(timeout=timeout)
    except queue.Empty:
        raise NetworkError()
    if not records:
        raise NetworkError()
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in records):
        raise VeritasError('unsafe_dns_target')
    return records[0]


def request(url, method='GET', body=None, headers=None, maximum=1048576, timeout=15, local=False):
    deadline = time.monotonic() + timeout
    for redirect in range(4):
        if local:
            p = urlsplit(url)
            if p.scheme != 'http' or p.hostname not in ('127.0.0.1', '::1') or p.username or p.password:
                raise VeritasError('invalid_local_provider_url')
            port = p.port or 80
            family = socket.AF_INET6 if p.hostname == '::1' else socket.AF_INET
            address = (p.hostname, port)
        else:
            p = safe_url(url)
            port = p.port or (443 if p.scheme == 'https' else 80)
            family, _, _, _, address = resolve_public(p.hostname, port, max(0.01, deadline-time.monotonic()))
        conn = PinnedConnection(p.hostname, port, timeout=timeout)
        sock = None
        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.settimeout(max(0.01, deadline-time.monotonic()))
            sock.connect(address)  # Pinned, validated IP; never resolves again.
            if p.scheme == 'https':
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=p.hostname)
            conn.sock = sock
            conn.defer_close = True
            outgoing = {'User-Agent':'VERITAS/0.1', 'Accept-Encoding':'identity', 'Connection':'close'}
            outgoing.update(headers or {})
            conn.request(method, p.path + ('?' + p.query if p.query else '') or '/', body=body, headers=outgoing)
            response = conn.getresponse()
            if response.status in (301,302,303,307,308):
                if method != 'GET' or local:
                    raise NetworkError(response.status)
                location = response.getheader('Location')
                if not location:
                    raise NetworkError(response.status)
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise NetworkError(response.status)
            if response.getheader('Content-Encoding', 'identity') != 'identity':
                raise VeritasError('unsupported_content_encoding')
            chunks, size = [], 0
            while True:
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise NetworkError()
                sock.settimeout(remaining)
                chunk = response.read1(min(65536, maximum-size+1))
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum:
                    raise VeritasError('oversized_source')
                chunks.append(chunk)
            return b''.join(chunks), dict(response.getheaders()), url
        except (OSError, http.client.HTTPException) as exc:
            raise NetworkError() from exc
        finally:
            conn.defer_close = False
            conn.close()
            if sock:
                sock.close()
    raise VeritasError('too_many_redirects')
