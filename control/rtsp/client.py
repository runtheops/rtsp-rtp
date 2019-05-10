import re
import socket

from urllib.parse import urlparse

from .auth import BasicAuth, DigestAuth
from .primitives import RTSPRequest


class RTSPClientError(Exception):
    pass


class RTSPClientRetryError(RTSPClientError):
    pass


class RTSPClientFatalError(RTSPClientError):
    pass


class RTSPClient:
    def __init__(self, url):
        self.username = None
        self.password = None
        self.host = None
        self.ip = None
        self.port = 514
        self.path = None
        self.safe_url = None
        self.url = url

        self._cseq = 0
        self._socket = None
        self._session = None
        self._realm = None
        self._nonce = None
        self._auth = None
        self._auth_attempts = 0

    def __repr__(self):
        return f'<RTSPClient [{self.host}]>'

    @staticmethod
    def _parse_trackid(response):
        regex = r'a=control:(.*)/(?P<trackid>\w+=\d+)'
        match = re.search(regex, response.body, re.S)

        return match.group('trackid')

    @staticmethod
    def _parse_digest_auth_header(header):
        realm = re.search(r'realm=\"([^\"]+)\"',header).group(1)
        nonce = re.search(r'nonce=\"([\w]+)\"',header).group(1)

        return realm, nonce

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url):
        parsed = urlparse(url)

        if parsed.scheme != "rtsp":
            raise RTSPClientFatalError(
                f'Protocol mismatch: expecting "rtsp", got "{parsed.scheme}"')

        try:
            self.host = parsed.hostname
            self.ip = socket.gethostbyname(self.host)
        except:
            raise RTSPClientFatalError(
                f'Failed to resolve {parsed.hostname} to IP address')

        self.username = parsed.username
        self.password = parsed.password
        self.port = parsed.port
        self.path = parsed.path
        self.safe_url = f'rtsp://{self.host}:{self.port}{self.path}'
        self.__url = url

    def _next_cseq(self):
        self._cseq += 1
        return self._cseq

    def _session_headers(self, method, url):
        headers = {}

        if self._auth:
            try:
                auth = self._auth(
                    self.username, self.password,
                    self._realm, self._nonce, method.upper(), url)

                headers['Authorization'] = auth.header
            except Exception as e:
                raise RTSPClientError(
                    f'Failed to process authentication: {e}')

        if self._session:
            headers['Session'] = self._session

        headers['Cseq'] = self._next_cseq()

        return headers

    def _request(self, method, url, headers={}):
        headers.update(self._session_headers(method, url))

        request = RTSPRequest(
            socket=self._socket,
            method=method,
            url=url,
            headers=headers)

        response = request.send()
        if response.status == 401:
            self._auth_attempts += 1

            if self._auth_attempts > 3:
                raise RTSPClientFatalError(
                    f'Maximum number of authentication attempts reached')

            h = response.headers['WWW-Authenticate']
            if h.startswith('Digest'):
                self._realm, self._nonce = self._parse_digest_auth_header(h)
                self._auth = DigestAuth
            else:
                self._auth = BasicAuth

            response = self._request(method, url, headers)

        return response

    @property
    def _connected(self):
        if not self._socket:
            return False

        try:
            response = self.options()
            if response.status != 200:
                return False
        except:
            return False

        return True

    def connect(self):
        if not self._connected:
            try:
                self._socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self._socket.connect((self.ip, self.port))
            except Exception as e:
                raise RTSPClientError(
                    f'Failed to connect to {self.ip}. {e}')

    def options(self):
        response = self._request(
            method='options',
            url=self.safe_url)

        if response.status != 200:
            raise RTSPClientError(
                f'Failed to list options for {self.url}')

        return response

    def describe(self):
        response = self._request(
            method='describe',
            url=self.safe_url)

        if response.status != 200:
            raise RTSPClientError(
                f'Failed to obtain stream description for {self.url}')

        return response

    def setup(self, rtp_port):
        trackid = self._parse_trackid(self.describe())

        response = self._request(
            method='setup',
            url=f'{self.url}/{trackid}',
            headers={
                'Transport': f'RTP/AVP/UDP;unicast;client_port={rtp_port}-{rtp_port}'
            })

        if response.status != 200:
            raise RTSPClientError(
                f'Failed to setup stream for {self.url}')

        return response

    def play(self, npt="0.000-"):
        response = self._request(
            method='play',
            url=self.safe_url,
            headers={
                'Range': f'npt="{npt}"'
            })

        if response.status != 200:
            raise RTSPClientError(
                f'Failed to play stream from {self.url}')

        return response

    def teardown(self):
        response = self._request(
            method='teardown',
            url=self.safe_url)

        self._socket.close()
        self._cseq = 0
        self._socket = None

        return response

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_t, exc_v, traceback):
        self.teardown()

    def __del__(self):
        self.teardown()
