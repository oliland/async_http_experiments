#!/bin/bash
set -e
set -x

python -m async_http_experiments.run_asyncio
python -m async_http_experiments.run_curio
python -m async_http_experiments.run_tornado
python -m async_http_experiments.run_trio
