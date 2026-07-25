import asyncio

import aiohttp
import pytest

#: krcg.load_online falls back to a /tmp pickle then to packaged data, silently:
#: probe first, so the suite fails rather than testing anything but the live corpus
CARDS_URL = "https://static.krcg.org/data/v5/vtes.json"


async def _probe_corpus() -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(CARDS_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()


def pytest_sessionstart(session):
    try:
        asyncio.run(_probe_corpus())
    except (aiohttp.ClientError, TimeoutError) as exc:
        pytest.fail(f"KRCG static server not available: {exc}")
