import asyncio
import base64
import contextlib
import os
import unittest.mock

import pytest

# hikari parses the token in GatewayBot.__init__, which runs at import: krcg_bot
# cannot be imported without one. Nothing here ever connects to Discord.
#
# Assembled rather than written out on purpose: a literal of this shape is what
# a secret scanner is built to catch, and it is right to catch it — a fake one
# in a public repo costs a blocked push and a false alarm every time.
os.environ["DISCORD_TOKEN"] = ".".join(
    (
        base64.b64encode(b"123456789012345678").decode(),
        "GaBcDe",
        "FgHiJkLmNoPqRsTuVwXyZ1234567890abcdefg",
    )
)

import krcg  # noqa: E402
import krcg.loader  # noqa: E402
import krcg_bot  # noqa: E402


def _no_fallback(*args, **kwargs):
    raise AssertionError(
        "krcg.load_online fell back to local data: the KRCG static server did not answer, "
        "and the suite must not pass against anything but the corpus the bot serves"
    )


#: every binding that yields local data — the /tmp pickle or the packaged CSVs
LOCAL_LOADERS = [
    (krcg, "load"),
    (krcg, "load_local"),
    (krcg.loader, "load"),
    (krcg.loader, "load_local"),
]


@pytest.fixture(scope="session")
def cards() -> krcg.CardDict:
    """The live corpus, loaded the way the bot loads it.

    `load_online` swallows every failure and falls back to `load()` — a /tmp
    pickle, then krcg's packaged data, which passes this whole suite and even
    carries the same card count. Nothing observable on the result tells them
    apart, so make every local path loud instead: on the live path none of them
    is called.
    """
    with contextlib.ExitStack() as stack:
        for target, name in LOCAL_LOADERS:
            stack.enter_context(unittest.mock.patch.object(target, name, _no_fallback))
        asyncio.run(krcg_bot.load_cards())
    return krcg_bot.CARDS
