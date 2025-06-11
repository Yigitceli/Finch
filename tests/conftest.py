import pytest
import asyncio

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close() 