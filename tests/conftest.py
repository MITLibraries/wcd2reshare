import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture
def base_url():
    return "https://mit-borrowdirect.reshare.indexdata.com/Search/Results?"
