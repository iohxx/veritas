import http.server
import socket
import threading
import unittest
from unittest.mock import patch
from veritas.security.network import request,resolve_public
from veritas.errors import VeritasError,NetworkError


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302)
            self.send_header('Location','http://127.0.0.1/private')
            self.end_headers()
            return
        if self.path=='/missing':
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Type','text/plain')
        self.end_headers()
        self.wfile.write(b'public evidence')


class NetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_close_delimited_body_and_size(self):
        url=f'http://127.0.0.1:{self.server.server_port}/'
        self.assertEqual(request(url,local=True)[0],b'public evidence')
        with self.assertRaises(VeritasError): request(url,local=True,maximum=2)
        with self.assertRaises(NetworkError): request(url+'missing',local=True)

    def test_dns_and_redirect_ssrf(self):
        with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,0,'',('127.0.0.1',80))]):
            with self.assertRaises(VeritasError): resolve_public('example.com',80,1)
        # The test transport maps only the initial public URL to this fixture.
        with patch('veritas.security.network.resolve_public',return_value=(socket.AF_INET,socket.SOCK_STREAM,0,'',('127.0.0.1',self.server.server_port))):
            with self.assertRaises(VeritasError): request('http://example.com/redirect')

    def test_local_provider_does_not_accept_remote_or_redirect(self):
        with self.assertRaises(VeritasError): request('http://example.com/api/chat',local=True)
        with self.assertRaises(NetworkError): request(f'http://127.0.0.1:{self.server.server_port}/redirect',local=True)
