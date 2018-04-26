import logging

import asyncio


logger = logging.getLogger(__name__)


class AsyncioDriver(object):

    def get_socket(self, http_request):
        ssl = http_request.parsed.scheme == "https"
        return AsyncioSocket(
            http_request.parsed.hostname,
            http_request.parsed.port or (443 if ssl else 80),
            ssl=ssl,
        )

    async def get_http_responses_from_coroutines(self, coroutines):
        return await asyncio.gather(*coroutines)


class AsyncioSocket(object):

    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.reader, self.writer = None, None

    async def connect(self):
        logger.debug("asyncio: opening socket...")
        pair = await asyncio.open_connection(self.host, self.port, ssl=self.ssl)
        logger.debug("asyncio: opened socket")
        self.reader, self.writer = pair

    async def read(self, max_bytes):
        logger.debug(f"asyncio: read {max_bytes} bytes")
        return await self.reader.read(max_bytes)

    async def write(self, some_bytes):
        logger.debug(f"asyncio: writing {len(some_bytes)} bytes")
        self.writer.write(some_bytes)
