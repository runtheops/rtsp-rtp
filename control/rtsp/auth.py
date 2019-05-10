import base64
from hashlib import md5


class BasicAuth:
    '''
    Basic authentication
    '''

    def __init__(self, username, password, *args, **kwargs):
        self.username = username
        self.password = password

    @property
    def header(self):
        b64 = base64.encodebytes(f'{self.username}:{self.password}'.encode())
        return b64.decode().strip()


class DigestAuth:
    '''
    Digest authentication as of RFC 2069
    '''

    def __init__(self, username, password, realm, nonce, method, uri):
        self.username = username
        self.password = password
        self.realm = realm
        self.nonce = nonce
        self.method = method
        self.uri = uri

    def __repr__(self):
        return f'<RTSPDigestAuth [{self.realm}]>'

    @property
    def _h1(self):
        h = md5(f'{self.username}:{self.realm}:{self.password}'.encode('utf-8'))
        return h.hexdigest()

    @property
    def _h2(self):
        h = md5(f'{self.method}:{self.uri}'.encode('utf-8'))
        return h.hexdigest()

    @property
    def response(self):
        h = md5(f'{self._h1}:{self.nonce}:{self._h2}'.encode('utf-8'))
        return h.hexdigest()

    @property
    def header(self):
        base = 'Digest '
        base += f'username="{self.username}", '
        base += f'realm="{self.realm}", '
        base += f'nonce="{self.nonce}", '
        base += f'uri="{self.uri}", '
        base += f'response="{self.response}"'

        return base
