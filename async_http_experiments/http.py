import asyncio
import collections
from types import coroutine

from urllib.parse import urlparse


NEW_LINE = "\r\n"
NEW_LINE_BYTES = NEW_LINE.encode("ascii")


class HTTPResponse(object):
    __slots__ = (
        "request",
        "headers",
        "content",
    )
    def __init__(self, request, headers, content):
        self.request = request
        self.headers = headers
        self.content = content


class HTTPRequest(object):
    __slots__ = (
        "method",
        "url",
        "parsed",
    )

    def __init__(self, method="GET", url=None):
        self.method = method
        self.url = url
        self.parsed = urlparse(url)


class HTTPEncoder(object):

    def encode_headers(self, http_request):
        components = http_request.parsed
        headers = (
            f"{http_request.method} {http_request.parsed.path} HTTP/1.1",
            f"Host: {http_request.parsed.hostname}",
            f"User-Agent: github/oliland/async_http_experiments",
            f"Accept: */*",
        )
        return NEW_LINE.join(headers).encode('ascii')

    def encode_body(self, http_request):
        return b""


class HTTPDecoder(object):

    def decode_headers(self, headers):
        return headers

    def decode_body(self, headers, body_bytes):
        return body_bytes


class HTTPBuffer(object):

    def __init__(self, socket, chunk_size=64000):
        """
        Not all underlying sockets support readline()
        So we need to buffer the data ourselves.
        """
        self.chunk_size = chunk_size
        self.buffer = bytearray()
        self.socket = socket

    async def fill(self):
        chunk = await self.socket.read(self.chunk_size)
        self.buffer.extend(chunk)

    async def read_next_line(self):
        index = self.buffer.find(NEW_LINE_BYTES)
        if index == 0:
            return b""  # End of headers
        elif index == -1:
            await self.fill()
            return await self.read_next_line()
        else:
            output = self.read(index + len(NEW_LINE_BYTES))
            return output[:-len(NEW_LINE_BYTES)]

    async def read_content(self, content_length):
        if len(self.buffer) < content_length:
            await self.fill()
        return self.read(content_length)

    def read(self, num_bytes):
        output = self.buffer[:num_bytes]
        self.buffer = self.buffer[num_bytes:]
        return bytes(output)


class HTTPConnection(object):

    def __init__(self, socket, encoder, decoder):
        """
        An HTTP connection.
        Initialised connections are not thread or coroutine safe.
        We rely on the pool to ensure that a connection is never shared.
        """
        self.encoder = encoder
        self.decoder = decoder
        self.socket = socket
        self.buffer = HTTPBuffer(socket)

    async def request(self, http_request):
        return await self.write_request_read_response(http_request)

    async def write_request_read_response(self, http_request):
        await self.write_request(http_request)
        return await self.read_response(http_request)

    async def write_request(self, http_request):
        headers = self.encoder.encode_headers(http_request)
        await self.socket.write(headers)
        body = self.encoder.encode_body(http_request)
        await self.socket.write(body + NEW_LINE_BYTES + NEW_LINE_BYTES)

    async def read_response(self, http_request):
        headers = []
        body_bytes = b""
        content_length = 0
        status = await self.buffer.read_next_line()
        while True:
            header_line_bytes = await self.buffer.read_next_line()
            if not header_line_bytes:
                break
            header, value = header_line_bytes.split(b": ")
            headers.append((header, value))
            if header == b"Content-Length":
                content_length = int(value)
        if content_length:
            body_bytes = await self.buffer.read_content(content_length)
        # TODO(Oli): Ensure we have no bytes left :o)
        headers = self.decoder.decode_headers(headers)
        body = self.decoder.decode_body(headers, body_bytes)
        return HTTPResponse(
            headers=headers,
            content=body,
            request=http_request,
        )


class HTTPPool(object):
    """
    we need a pool because http is request then response.
    we can't confuse our socket by issueing two requests before reading them, for example.
    """
    def __init__(self, driver, encoder, decoder):
        self.driver = driver
        self.encoder = encoder
        self.decoder = decoder
        # deque is probably both thread and coro safe, it's atomic
        self.sockets_by_hostname = collections.defaultdict(collections.deque)

    async def get_http_response(self, http_request):
        socket = await self.get_or_create_socket(http_request)
        connection = HTTPConnection(
            socket=socket,
            encoder=self.encoder,
            decoder=self.decoder,
        )
        http_response = await connection.request(http_request)
        return http_response

    async def get_or_create_socket(self, http_request):
        # Check to see if we have a socket that we can re-use
        try:
            # if we do have a socket, pop it (so it doesn't get used)
            return self.sockets_by_hostname[http_request.parsed.hostname].popleft()
        except IndexError:
            # if we don't, we either haven't connected yet, or something else popped it
            # so add a new one
            return await self.create_socket(http_request)

    async def create_socket(self, http_request):
        socket = self.driver.get_socket(http_request)
        await socket.connect()
        self.sockets_by_hostname[http_request.parsed.hostname].append(socket)
        return socket


class HTTPClient(object):

    def __init__(self, driver, encoder=None, decoder=None):
        self.driver = driver
        self.pool = HTTPPool(
            driver=driver,
            encoder=encoder or HTTPEncoder(),
            decoder=decoder or HTTPDecoder(),
        )

    async def get_http_responses(self, http_requests):
        return await self.driver.get_http_responses_from_coroutines([
            self.get_http_response(http_request)
            for http_request in http_requests
        ])

    async def get_http_response(self, http_request):
        return await self.pool.get_http_response(http_request)
