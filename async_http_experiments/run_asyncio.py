import logging

import asyncio

from .drivers.asyncio import AsyncioDriver
from .http import HTTPClient, HTTPRequest


async def main():
    client = HTTPClient(driver=AsyncioDriver())
    http_requests = [
        HTTPRequest(url="http://httpbin.org/delay/2"),
        HTTPRequest(url="http://httpbin.org/delay/2"),
    ]
    http_responses = await client.get_http_responses(http_requests)
    for http_response in http_responses:
        print(http_response.headers, http_response.content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(levelname)s) %(message)s')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
