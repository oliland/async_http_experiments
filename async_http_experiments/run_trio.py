import logging

import trio

from .drivers.trio import TrioDriver
from .http import HTTPClient, HTTPRequest


async def main():
    client = HTTPClient(driver=TrioDriver())
    http_requests = [
        HTTPRequest(url="http://httpbin.org/delay/2"),
        HTTPRequest(url="http://httpbin.org/delay/2"),
    ]
    http_responses = await client.get_http_responses(http_requests)
    for http_response in http_responses:
        print(http_response.headers, http_response.content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(levelname)s) %(message)s')
    trio.run(main)
