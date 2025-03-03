from importlib import reload
from unittest.mock import MagicMock

import pytest
import requests_mock

from lambdas import wcd2reshare


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture
def base_url():
    return "https://borrowdirect.reshare.indexdata.com/Search/Results?"


def test_configures_sentry_if_dsn_present(caplog, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    reload(wcd2reshare)
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test" in caplog.text
    )


def test_doesnt_configure_sentry_if_dsn_not_present(caplog, monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    reload(wcd2reshare)
    assert "Sentry DSN found" not in caplog.text


def test_query_formatter():
    params = {
        "rft.isbn": "978-3-16-148410-0",
        "rft.title": "salad days",
        "rft_id": "info%3Aoclcnum%2F12345678",
    }
    search_strings = wcd2reshare.query_formatter(params)
    assert search_strings["oclc"] == "type=oclc_num&lookfor=12345678"
    assert search_strings["isbn"] == "type=ISN&lookfor=978-3-16-148410-0"
    assert search_strings["title"] == "type=title&lookfor=salad+days"


def test_query_formatter_title_with_author():
    params = {"rft.title": "salad days", "rft.aulast": "ranch"}
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_no_rft_fields_of_interest():
    params = {"rft.popcorn": "sure"}
    assert wcd2reshare.query_formatter(params) == {}


def test_query_formatter_title_priority():
    params = {
        "rft.btitle": "b title",
        "rft.ctitle": "c title",
        "rft.jtitle": "j title",
        "rft.aulast": "ranch",
        "rft.title": "salad days",
    }
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_btitle_priority():
    params = {
        "rft.ctitle": "c title",
        "rft.jtitle": "j title",
        "rft.aulast": "ranch",
        "rft.btitle": "b title",
    }
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=b+title&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_ctitle_priority():
    params = {"rft.jtitle": "j title", "rft.aulast": "ranch", "rft.ctitle": "c title"}
    assert wcd2reshare.query_formatter(params)["title"] == (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=c+title&type0%5B%5D=author&"
        "lookfor0%5B%5D=ranch"
    )


def test_query_formatter_fields_of_no_interest_ignored():
    params = {"rft.popcorn": "sure", "rft.isbn": "978-3-16-148410-0"}
    assert wcd2reshare.query_formatter(params)["isbn"] == (
        "type=ISN&lookfor=978-3-16-148410-0"
    )


def test_search_has_results_is_true_when_results_are_returned():
    search_string = "successful search string"
    with requests_mock.Mocker() as m:
        m.request(requests_mock.ANY, requests_mock.ANY, json={"resultCount": 1})
        assert wcd2reshare.search_has_results(search_string) is True


def test_search_has_results_is_false_when_results_are_not_returned():
    search_string = "failing search string"
    with requests_mock.Mocker() as m:
        m.request(requests_mock.ANY, requests_mock.ANY, json={"resultCount": 0})
        assert wcd2reshare.search_has_results(search_string) is False


def test_build_title_search_string_no_author():
    title = "salad days"
    assert wcd2reshare.build_title_search_string(title, aulast=None) == [
        ("type", "title"),
        ("lookfor", title),
    ]


def test_select_search_strategy_no_success():
    search_strings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    expected_call_count = 3
    wcd2reshare.search_has_results = MagicMock(side_effect=[False, False, False])
    selected_strategy = wcd2reshare.select_search_strategy(search_strings)
    assert wcd2reshare.search_has_results.call_count == expected_call_count
    assert selected_strategy == ""


def test_select_search_strategy_oclc_success():
    search_strings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    expected_call_count = 1
    wcd2reshare.search_has_results = MagicMock(side_effect=[True])
    selected_strategy = wcd2reshare.select_search_strategy(search_strings)
    assert wcd2reshare.search_has_results.call_count == expected_call_count
    assert selected_strategy == search_strings["oclc"]


def test_select_search_strategy_isbn_success():
    search_strings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    expected_call_count = 2
    wcd2reshare.search_has_results = MagicMock(side_effect=[False, True])
    selected_strategy = wcd2reshare.select_search_strategy(search_strings)
    assert wcd2reshare.search_has_results.call_count == expected_call_count
    assert selected_strategy == search_strings["isbn"]


def test_select_search_strategy_title_success():
    search_strings = {
        "oclc": "type=oclc_num&lookfor=12345678",
        "isbn": "type=ISN&lookfor=978-3-16-148410-0",
        "title": "type=title&lookfor=salad+days",
    }
    expected_call_count = 3
    wcd2reshare.search_has_results = MagicMock(side_effect=[False, False, True])
    selected_strategy = wcd2reshare.select_search_strategy(search_strings)
    assert wcd2reshare.search_has_results.call_count == expected_call_count
    assert selected_strategy == search_strings["title"]


def test_build_title_search_string_with_author():
    title = "salad days"
    aulast = "ranch"
    assert wcd2reshare.build_title_search_string(title, aulast) == [
        ("join", "AND"),
        ("type0[]", "title"),
        ("lookfor0[]", title),
        ("type0[]", "author"),
        ("lookfor0[]", aulast),
    ]


def test_lambda_handler_workspace_missing(monkeypatch):
    monkeypatch.delenv("WORKSPACE")
    reload(wcd2reshare)
    with pytest.raises(ValueError, match="WORKSPACE environment variable is required"):
        wcd2reshare.lambda_handler({}, {})


def test_lambda_handler_workspace_found(caplog):
    reload(wcd2reshare)
    wcd2reshare.lambda_handler({}, {})
    assert "Required WORKSPACE env is None" not in caplog.text


def test_lambda_handler_with_query(base_url):
    event = {"queryStringParameters": {"rft.isbn": "978-3-16-148410-0"}}
    quer_string = "type=ISN&lookfor=978-3-16-148410-0"
    wcd2reshare.select_search_strategy = MagicMock(return_value=quer_string)
    response = wcd2reshare.lambda_handler(event, _context={})
    expected_status_code = 307
    assert response["statusCode"] == expected_status_code
    assert response["headers"]["Location"] == base_url + quer_string


def test_lambda_handler_with_multiple_query(base_url):
    event = {"queryStringParameters": {"rft.title": "salad days", "rft.aulast": "ranch"}}
    query_string = (
        "join=AND&type0%5B%5D=title&lookfor0%5B%5D=salad+days&"
        "type0%5B%5D=author&lookfor0%5B%5D=ranch"
    )
    wcd2reshare.select_search_strategy = MagicMock(return_value=query_string)
    response = wcd2reshare.lambda_handler(event, _context={})
    expected_status_code = 307
    assert response["statusCode"] == expected_status_code
    assert response["headers"]["Location"] == base_url + query_string


def test_lambda_handler_without_query(base_url):
    response = wcd2reshare.lambda_handler(event={}, _context={})
    expected_status_code = 307
    assert response["statusCode"] == expected_status_code
    assert response["headers"]["Location"] == base_url


def test_lambda_handler_with_garbage_query(base_url):
    wcd2reshare.select_search_strategy = MagicMock(return_value="")
    response = wcd2reshare.lambda_handler(
        event={"queryStringParameters": {"door": "knob"}}, _context={}
    )
    expected_status_code = 307
    assert response["statusCode"] == expected_status_code
    assert response["headers"]["Location"] == base_url
