import pytest
import requests
from krcg import config, vtes


def pytest_sessionstart(session):
    # Do not launch tests is there is no proper Internet connection.
    try:
        requests.get("http://www.google.com", timeout=1)
    except requests.exceptions.RequestException:
        pytest.fail("No internet connection")
    try:
        requests.get(config.KRCG_STATIC_SERVER, timeout=1)
    except requests.exceptions.RequestException:
        pytest.fail("KRCG website not available")
    vtes.VTES.load()
