import logging

import trio

logger = logging.getLogger(__name__)


class TrioDriver(object):

    def __init__(self):
        self.ssl_context = trio.ssl.create_default_context()

    def get_socket(self, http_request):
        ssl = http_request.parsed.scheme == "https"
        return TrioSocket(
            self.ssl_context,
            http_request.parsed.hostname,
            http_request.parsed.port or (443 if ssl else 80),
            ssl=ssl,
        )

    async def get_http_responses_from_coroutines(self, coroutines):
        http_responses = [None] * len(coroutines)
        async def get_response(i, coroutine):
            http_responses[i] = await coroutine

        async with trio.open_nursery() as nursery:
            for i, coroutine in enumerate(coroutines):
                nursery.start_soon(get_response, i, coroutine)
        return http_responses


class TrioSocket(object):

    def __init__(self, ssl_context, host, port, ssl=False):
        self.buffer = []
        self.ssl_context = ssl_context
        self.host = host
        self.port = port
        self.ssl = ssl
        self.stream = None

    async def connect(self):
        logger.debug("trio: opening socket...")
        if self.ssl:
            self.stream = await trio.open_ssl_over_tcp_stream(
                self.host,
                self.port,
                self.ssl_context,
                https_compatible=True,
            )
        else:
            self.stream = await trio.open_tcp_stream(
                self.host,
                self.port,
            )
        logger.debug("trio: opened socket")

    async def read(self, max_bytes):
        logger.debug(f"trio: read {max_bytes} bytes")
        return await self.stream.receive_some(max_bytes)

    async def write(self, some_bytes):
        logger.debug(f"trio: writing {len(some_bytes)} bytes")
        await self.stream.send_all(some_bytes)
