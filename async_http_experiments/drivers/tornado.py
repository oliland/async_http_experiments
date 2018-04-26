import logging
import ssl as ssl_module

import tornado
from tornado.tcpclient import TCPClient


logger = logging.getLogger(__name__)


class TornadoDriver(object):

    def __init__(self):
        self.client = TCPClient(resolver=None)

    def get_socket(self, http_request):
        ssl = http_request.parsed.scheme == "https"
        return TornadoSocket(
            self.client,
            http_request.parsed.hostname,
            http_request.parsed.port or (443 if ssl else 80),
            ssl=ssl,
        )

    async def get_http_responses_from_coroutines(self, coroutines):
        return await tornado.gen.multi(coroutines)


class TornadoSocket(object):

    def __init__(self, client, host, port, ssl=False):
        self.host = host
        self.port = port
        self.ssl_options = ssl_module.Options if ssl else None
        self.client = client
        self.io_stream = None

    async def connect(self):
        logger.debug("tornado: opening socket...")
        self.io_stream = await self.client.connect(
            self.host,
            self.port,
            ssl_options=self.ssl_options,
        )
        logger.debug("tornado: opened socket")

    async def read(self, max_bytes):
        logger.debug(f"tornado: read {max_bytes} bytes")
        return await self.io_stream.read_bytes(max_bytes, partial=True)

    async def write(self, some_bytes):
        logger.debug(f"tornado: writing {len(some_bytes)} bytes")
        self.io_stream.write(some_bytes)
