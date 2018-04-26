import logging

import tornado.gen
import tornado.ioloop

from .drivers.tornado import TornadoDriver
from .http import HTTPClient, HTTPRequest


async def main():
    client = HTTPClient(driver=TornadoDriver())
    http_requests = [
        HTTPRequest(url="http://httpbin.org/delay/2"),
        HTTPRequest(url="http://httpbin.org/delay/2"),
    ]
    http_responses = await client.get_http_responses(http_requests)
    for http_response in http_responses:
        print(http_response.headers, http_response.content)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(levelname)s) %(message)s')
    tornado.ioloop.IOLoop.current().run_sync(main)
