import logging

import curio

logger = logging.getLogger(__name__)


class CurioDriver(object):

    def get_socket(self, http_request):
        ssl = http_request.parsed.scheme == "https"
        return CurioSocket(
            http_request.parsed.hostname,
            http_request.parsed.port or (443 if ssl else 80),
            ssl=ssl,
        )

    async def get_http_responses_from_coroutines(self, coroutines):
        async def gather(tasks):
            results = []
            for task in tasks:
                result = await task.join()
                results.append(result)
            return results

        return await gather([
            await curio.spawn(coroutine)
            for coroutine in coroutines
        ])


class CurioSocket(object):

    def __init__(self, host, port, ssl=False):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.stream = None

    async def connect(self):
        logger.debug("curio: opening socket...")
        socket = await curio.open_connection(
            self.host,
            self.port,
            ssl=self.ssl,
            alpn_protocols=['h2', 'http/1.1'],
        )
        self.stream = socket.as_stream()
        logger.debug("curio: opened socket")

    async def read(self, max_bytes):
        logger.debug(f"curio: read {max_bytes} bytes")
        return await self.stream.read(max_bytes)

    async def write(self, some_bytes):
        logger.debug(f"curio: writing {len(some_bytes)} bytes")
        await self.stream.write(some_bytes)
