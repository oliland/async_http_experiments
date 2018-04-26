# async_http_experiments

This is an experimental python HTTP client. It's trying to be:

- annoyingly modular & configurable
- compatible with a number of different python async libraries

It is not production ready.

## why?

Python 3 has a number of async "libraries". These all ship with:

- an event loop implementation
- a non-blocking tcp socket implementation

What's interesting is that a lot of these libraries are missing HTTP clients, and those that do often ship with clients that are missing features.

This repositoriy contains an incomplete & untested client that is compatible with many async libraries.

## dependencies

Install dependencies with pipenv:

```
pipenv install
```

## running

To run a test against all of the async backends:

```
pipenv shell
./run_all.sh
```

This code will call http://httpbin.org with a small delay to show that the requests are executing concurrently.
