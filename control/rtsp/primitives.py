class RTSPResponse:
    LINE_SPLIT = '\r\n'
    HEADER_END = LINE_SPLIT * 2

    def __init__(self, response):
        self.version = None
        self.status = None
        self.body = None
        self.headers = {}
        self.response = response

    def __repr__(self):
        return f'<RTSPResponse [{self.status}]>'

    @staticmethod
    def _parse_header(header):
        lines = header.splitlines()
        version, status = lines[0].split(None,2)[:2]

        headers = dict()
        for l in lines[1:]:
            if l.strip():
                k, v = l.split(':', 1)
                if k not in headers:
                    headers[k] = v.strip()

        return version, int(status), headers

    @property
    def response(self):
        return self.__response

    @response.setter
    def response(self, data):
        header, body = data.split(self.HEADER_END)[:2]

        self.body = body
        self.version, self.status, self.headers = self._parse_header(header)
        self.__response = data


class RTSPRequest:
    VERSION = 'RTSP/1.0'
    LINE_SPLIT = '\r\n'
    HEADER_END = LINE_SPLIT * 2

    def __init__(self, socket, method, url, headers={}):
        self.socket = socket
        self.method = method.upper()
        self.url = url
        self.headers = headers

    def __repr__(self):
        return f'<RTSPRequest [{self.method}]>'

    def _prepare_headers(self):
        prep = str()
        for k, v in self.headers.items():
            prep += f'{self.LINE_SPLIT}{k}: {v}'

        return prep

    def send(self):
        msg = f'{self.method} {self.url} {self.VERSION}'
        msg += self._prepare_headers()
        msg += self.HEADER_END

        self.socket.send(bytes(msg,'utf-8'))

        data = self.socket.recv(2048).decode()
        while not self.HEADER_END in data:
            recv += self.socket.recv(2048).decode()
            if not recv:
                break

            data += recv

        return RTSPResponse(data)
